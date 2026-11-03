from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field

from ..auth import CurrentUser, get_current_user
from ..supabase_client import get_supabase_admin


router = APIRouter(prefix="/actions", tags=["actions"])

ActionStatus = Literal["open", "approved", "rejected", "done"]


class ActionItemPayload(BaseModel):
    period: str = Field(min_length=1, max_length=80)
    campaign_external_id: str | None = None
    campaign_name: str = Field(min_length=1, max_length=240)
    title: str = Field(min_length=1, max_length=160)
    action: str = Field(min_length=1, max_length=600)
    impact: str = Field(default="", max_length=600)
    severity: int = Field(default=1, ge=1, le=3)
    tone: str = Field(default="blue", max_length=20)
    status: ActionStatus = "open"


@router.get("/{client_id}")
def list_action_items(
    client_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    period: str = Query(...),
) -> dict[str, object]:
    client = get_supabase_admin()
    try:
        result = (
            client.table("action_items")
            .select("*")
            .eq("owner_id", user.id)
            .eq("client_id", client_id)
            .eq("period", period)
            .order("updated_at", desc=True)
            .execute()
        )
    except APIError as exc:
        if "action_items" in exc.message:
            raise HTTPException(
                status_code=500,
                detail="Tabela action_items nao existe. Aplique saas/supabase/schema.sql no Supabase.",
            ) from exc
        raise HTTPException(status_code=500, detail=exc.message) from exc
    return {"ok": True, "actions": result.data or []}


@router.post("/{client_id}")
def upsert_action_item(
    client_id: str,
    payload: ActionItemPayload,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, object]:
    client = get_supabase_admin()
    now = datetime.now(UTC).isoformat()
    match = {
        "owner_id": user.id,
        "client_id": client_id,
        "period": payload.period,
        "campaign_external_id": payload.campaign_external_id or "",
        "title": payload.title,
    }
    row = {
        **match,
        "campaign_name": payload.campaign_name,
        "action": payload.action,
        "impact": payload.impact,
        "severity": payload.severity,
        "tone": payload.tone,
        "status": payload.status,
        "updated_at": now,
    }
    if payload.status == "approved":
        row["approved_at"] = now
    if payload.status == "rejected":
        row["rejected_at"] = now
    if payload.status == "done":
        row["completed_at"] = now

    try:
        existing = (
            client.table("action_items")
            .select("id")
            .match(match)
            .limit(1)
            .execute()
        )
        if existing.data:
            result = client.table("action_items").update(row).eq("id", existing.data[0]["id"]).execute()
        else:
            result = client.table("action_items").insert(row).execute()
    except APIError as exc:
        if "action_items" in exc.message:
            raise HTTPException(
                status_code=500,
                detail="Tabela action_items nao existe. Aplique saas/supabase/schema.sql no Supabase.",
            ) from exc
        raise HTTPException(status_code=500, detail=exc.message) from exc

    if not result.data:
        raise HTTPException(status_code=500, detail="Nao foi possivel salvar a acao.")
    return {"ok": True, "action": result.data[0]}
