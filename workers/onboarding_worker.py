"""Poll pending onboarding_runs and provision GitHub + ClickUp + client row."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict

from api.config import settings
from api.services.supabase_client import get_supabase
from api.services.github_provision import provision_client_repo
from api.services.clickup_provision import provision_clickup_space

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("worker.onboarding")

POLL_INTERVAL_SEC = 10


def _claim_next_run() -> Dict[str, Any] | None:
    sb = get_supabase()
    # Simple claim: select oldest pending, then update to running
    result = (
        sb.table("onboarding_runs")
        .select("*")
        .eq("status", "pending")
        .order("created_at")
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return None
    run = rows[0]
    sb.table("onboarding_runs").update(
        {
            "status": "running",
            "attempts": (run.get("attempts") or 0) + 1,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", run["id"]).execute()
    return run


def _process(run: Dict[str, Any]) -> None:
    sb = get_supabase()
    deal_id = run.get("deal_id") or ""
    org_name = run.get("org_name") or run.get("title") or "Unknown Client"

    logger.info("Processing onboarding run %s for %s", run["id"], org_name)

    try:
        gh = provision_client_repo(org_name, deal_id)
        cu = provision_clickup_space(org_name, deal_id)

        client_row = {
            "org_name": org_name,
            "deal_id": deal_id or None,
            "person_name": run.get("person_name"),
            "status": "active",
            "github_repo": gh.get("repo"),
            "clickup_space_id": cu.get("space_id"),
            "metadata": {"github": gh, "clickup": cu},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        client_res = sb.table("clients").upsert(client_row, on_conflict="deal_id").execute()
        client_id = (client_res.data or [{}])[0].get("id")

        sb.table("onboarding_runs").update(
            {
                "status": "succeeded",
                "client_id": client_id,
                "result": {"github": gh, "clickup": cu},
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", run["id"]).execute()

        sb.table("system_events").insert(
            {
                "event_type": "onboarding_completed",
                "payload": {
                    "run_id": run["id"],
                    "client_id": client_id,
                    "org_name": org_name,
                    "status": "succeeded",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        ).execute()
        logger.info("Onboarding succeeded for %s", org_name)

    except Exception as exc:
        logger.exception("Onboarding failed for run %s", run["id"])
        attempts = (run.get("attempts") or 0) + 1
        max_attempts = run.get("max_attempts") or 5
        new_status = "dead_letter" if attempts >= max_attempts else "pending"
        sb.table("onboarding_runs").update(
            {
                "status": new_status,
                "last_error": str(exc)[:2000],
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat() if new_status == "dead_letter" else None,
            }
        ).eq("id", run["id"]).execute()

        sb.table("system_events").insert(
            {
                "event_type": "onboarding_failed",
                "payload": {
                    "run_id": run["id"],
                    "org_name": org_name,
                    "status": new_status,
                    "error": str(exc)[:500],
                    "attempts": attempts,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        ).execute()


def main() -> None:
    logger.info("Onboarding worker started (poll every %ss)", POLL_INTERVAL_SEC)
    while True:
        try:
            run = _claim_next_run()
            if run:
                _process(run)
            else:
                time.sleep(POLL_INTERVAL_SEC)
        except Exception:
            logger.exception("Worker loop error")
            time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
