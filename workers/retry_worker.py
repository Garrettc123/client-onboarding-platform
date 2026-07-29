"""Re-queue failed runs that have remaining attempts (safety net)."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone, timedelta

from api.config import settings
from api.services.supabase_client import get_supabase

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("worker.retry")

POLL_INTERVAL_SEC = 60
STALE_RUNNING_MINUTES = 30


def main() -> None:
    logger.info("Retry worker started")
    sb = get_supabase()
    while True:
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=STALE_RUNNING_MINUTES)).isoformat()
            # Reset stuck 'running' jobs older than cutoff back to pending
            stuck = (
                sb.table("onboarding_runs")
                .select("id")
                .eq("status", "running")
                .lt("started_at", cutoff)
                .execute()
            )
            for row in stuck.data or []:
                sb.table("onboarding_runs").update(
                    {
                        "status": "pending",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "last_error": "reset_by_retry_worker: stale running",
                    }
                ).eq("id", row["id"]).execute()
                logger.warning("Reset stale run %s to pending", row["id"])
        except Exception:
            logger.exception("Retry worker error")
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
