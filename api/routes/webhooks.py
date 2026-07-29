"""Pipedrive webhook ingestion."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request, status

from api.config import settings
from api.services.supabase_client import get_supabase
from api.services.onboarding import enqueue_onboarding

router = APIRouter()


def _verify_pipedrive(secret: str | None) -> None:
    if not settings.pipedrive_webhook_secret:
        return  # allow in local/dev when unset
    if secret != settings.pipedrive_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")


@router.post("/pipedrive")
async def pipedrive_webhook(
    request: Request,
    x_pipedrive_signature: str | None = Header(default=None, alias="X-Pipedrive-Signature"),
):
    _verify_pipedrive(x_pipedrive_signature)
    body: Dict[str, Any] = await request.json()

    # Pipedrive sends meta + current deal state
    meta = body.get("meta", {})
    current = body.get("current", body)
    deal_id = str(current.get("id") or meta.get("id") or "")
    status_name = (current.get("status") or "").lower()
    title = current.get("title") or f"Deal {deal_id}"
    org_name = (current.get("org_id") or {}).get("name") if isinstance(current.get("org_id"), dict) else current.get("org_name")
    person_name = (current.get("person_id") or {}).get("name") if isinstance(current.get("person_id"), dict) else current.get("person_name")

    sb = get_supabase()
    event = {
        "event_type": "pipedrive_webhook",
        "payload": {
            "deal_id": deal_id,
            "status": status_name,
            "title": title,
            "org_name": org_name,
            "person_name": person_name,
            "raw": body,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    sb.table("system_events").insert(event).execute()

    if status_name == "won" and deal_id:
        run = enqueue_onboarding(
            deal_id=deal_id,
            title=title,
            org_name=org_name or title,
            person_name=person_name,
            source="pipedrive",
        )
        return {"accepted": True, "onboarding_run_id": run.get("id"), "action": "enqueued"}

    return {"accepted": True, "action": "ignored", "reason": f"status={status_name}"}
