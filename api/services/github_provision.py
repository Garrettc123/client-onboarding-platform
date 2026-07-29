"""Provision a private GitHub repository for a new client."""
from __future__ import annotations

from typing import Any, Dict

import httpx

from api.config import settings


def provision_client_repo(org_name: str, deal_id: str) -> Dict[str, Any]:
    """Create a private repo under GITHUB_ORG named client-<slug>."""
    if not settings.github_token:
        return {"skipped": True, "reason": "GITHUB_TOKEN not set"}

    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in org_name.lower()).strip("-")[:40]
    repo_name = f"client-{slug}-{deal_id[:8]}" if deal_id else f"client-{slug}"
    owner = settings.github_org or "Garrettc123"

    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "name": repo_name,
        "private": True,
        "description": f"Client workspace for {org_name} (deal {deal_id})",
        "auto_init": True,
    }

    url = f"https://api.github.com/orgs/{owner}/repos" if settings.github_org else "https://api.github.com/user/repos"
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code in (201, 200):
            data = resp.json()
            return {"repo": data.get("full_name"), "html_url": data.get("html_url"), "id": data.get("id")}
        if resp.status_code == 422 and "already exists" in resp.text.lower():
            return {"repo": f"{owner}/{repo_name}", "exists": True}
        resp.raise_for_status()
        return {"error": resp.text}
