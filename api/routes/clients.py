"""Client listing and status endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from api.services.supabase_client import get_supabase

router = APIRouter()


@router.get("")
async def list_clients(
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
) -> Dict[str, Any]:
    sb = get_supabase()
    q = sb.table("clients").select("*").order("created_at", desc=True).limit(limit)
    if status_filter:
        q = q.eq("status", status_filter)
    result = q.execute()
    return {"clients": result.data or [], "count": len(result.data or [])}


@router.get("/{client_id}")
async def get_client(client_id: str) -> Dict[str, Any]:
    sb = get_supabase()
    result = sb.table("clients").select("*").eq("id", client_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return result.data[0]


@router.get("/{client_id}/runs")
async def client_runs(client_id: str) -> Dict[str, List[Any]]:
    sb = get_supabase()
    result = (
        sb.table("onboarding_runs")
        .select("*")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"runs": result.data or []}
