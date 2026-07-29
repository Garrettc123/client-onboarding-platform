"""Surface dead-letter onboarding runs (notify / log)."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from api.config import settings
from api.services.supabase_client import get_supabase

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("worker.dead_letter")

POLL_INTERVAL_SEC = 120


def _notify_linear(title: str, body: str) -> None:
    if not settings.linear_api_key or not settings.linear_team_id:
        logger.info("Linear not configured — skipping incident for: %s", title)
        return
    query = """
    mutation($title: String!, $teamId: String!, $description: String) {
      issueCreate(input: { title: $title, teamId: $teamId, description: $description, priority: 2 }) {
        success
      }
    }
    """
    with httpx.Client(timeout=20) as client:
        client.post(
            "https://api.linear.app/graphql",
            headers={"Authorization": settings.linear_api_key, "Content-Type": "application/json"},
            json={
                "query": query,
                "variables": {"title": title, "teamId": settings.linear_team_id, "description": body},
            },
        )


def main() -> None:
    logger.info("Dead-letter worker started")
    sb = get_supabase()
    seen: set[str] = set()
    while True:
        try:
            result = (
                sb.table("onboarding_runs")
                .select("*")
                .eq("status", "dead_letter")
                .order("updated_at", desc=True)
                .limit(20)
                .execute()
            )
            for run in result.data or []:
                rid = run["id"]
                if rid in seen:
                    continue
                seen.add(rid)
                title = f"🚨 Onboarding dead-letter: {run.get('org_name')}"
                body = f"run_id={rid}\ndeal_id={run.get('deal_id')}\nerror={run.get('last_error')}\nattempts={run.get('attempts')}"
                logger.error(title)
                _notify_linear(title, body)
                sb.table("system_events").insert(
                    {
                        "event_type": "incident",
                        "payload": {
                            "run_id": rid,
                            "org_name": run.get("org_name"),
                            "status": "dead_letter",
                            "error": run.get("last_error"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                ).execute()
        except Exception:
            logger.exception("Dead-letter worker error")
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
