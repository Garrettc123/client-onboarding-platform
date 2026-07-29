"""Provision a ClickUp space for a new client."""
from __future__ import annotations

from typing import Any, Dict

import httpx

from api.config import settings


def provision_clickup_space(org_name: str, deal_id: str) -> Dict[str, Any]:
    """Create a ClickUp space under the configured team."""
    if not settings.clickup_api_token or not settings.clickup_team_id:
        return {"skipped": True, "reason": "CLICKUP_API_TOKEN or CLICKUP_TEAM_ID not set"}

    headers = {"Authorization": settings.clickup_api_token, "Content-Type": "application/json"}
    payload = {
        "name": f"{org_name} ({deal_id[:8]})" if deal_id else org_name,
        "multiple_assignees": True,
        "features": {
            "due_dates": {"enabled": True, "start_date": True, "remap_due_dates": True},
            "time_tracking": {"enabled": True},
            "tags": {"enabled": True},
            "custom_fields": {"enabled": True},
        },
    }
    url = f"https://api.clickup.com/api/v2/team/{settings.clickup_team_id}/space"

    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code in (200, 201):
            data = resp.json()
            space = data.get("id") or data
            return {"space_id": space if isinstance(space, str) else data.get("id"), "raw": data}
        resp.raise_for_status()
        return {"error": resp.text}
