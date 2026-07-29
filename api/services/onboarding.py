"""Enqueue and track onboarding runs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from api.services.supabase_client import get_supabase


def enqueue_onboarding(
    *,
    deal_id: str,
    title: str,
    org_name: str,
    person_name: Optional[str] = None,
    source: str = "pipedrive",
) -> Dict[str, Any]:
    """Create an onboarding_runs row in `pending` state for the worker to pick up."""
    sb = get_supabase()
    row = {
        "deal_id": deal_id,
        "title": title,
        "org_name": org_name,
        "person_name": person_name,
        "source": source,
        "status": "pending",
        "attempts": 0,
        "max_attempts": 5,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = sb.table("onboarding_runs").insert(row).execute()
    return (result.data or [{}])[0]
