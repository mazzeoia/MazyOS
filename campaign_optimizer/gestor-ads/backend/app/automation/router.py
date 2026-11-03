from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Query
from supabase import Client

from app.auth.models import User
from app.automation.schemas import (
    AutomationRunAllOut,
    AutomationRunOut,
    AutomationRunRequest,
    AutomationSettingsOut,
    AutomationSettingsUpdate,
    NotificationOut,
)
from app.config import Settings, get_settings
from app.core.account_data import get_ad_account
from app.core.automation import run_automation_for_account
from app.dependencies import get_current_user, get_supabase
from app.shared.exceptions import AutomationKeyInvalidError

router = APIRouter(tags=["automation"])
logger = logging.getLogger(__name__)


# === Settings ===


@router.get("/automation/settings", response_model=AutomationSettingsOut)
async def get_automation_settings(
    act_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = get_ad_account(supabase, user.id, act_id)
    rows = (
        supabase.table("automation_settings")
        .select("*")
        .eq("owner_id", user.id)
        .eq("ad_account_id", acc["id"])
        .limit(1)
        .execute()
        .data
    )
    row = rows[0] if rows else None
    return AutomationSettingsOut(
        auto_pause_enabled=bool(row and row.get("auto_pause_enabled")),
        server_schedule_enabled=bool(row and row.get("server_schedule_enabled")),
        notify_email=bool(row.get("notify_email", True)) if row else True,
        notify_whatsapp=bool(row and row.get("notify_whatsapp")),
    )


@router.put("/automation/settings", response_model=AutomationSettingsOut)
async def update_automation_settings(
    body: AutomationSettingsUpdate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = get_ad_account(supabase, user.id, body.act_id)

    supabase.table("automation_settings").upsert(
        {
            "owner_id": user.id,
            "ad_account_id": acc["id"],
            "owner_email": user.email,
            "auto_pause_enabled": body.auto_pause_enabled,
            "server_schedule_enabled": body.server_schedule_enabled,
            "notify_email": body.notify_email,
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="owner_id,ad_account_id",
    ).execute()

    return AutomationSettingsOut(
        auto_pause_enabled=body.auto_pause_enabled,
        server_schedule_enabled=body.server_schedule_enabled,
        notify_email=body.notify_email,
        notify_whatsapp=False,
    )


# === Run ===


@router.post("/automation/run", response_model=AutomationRunOut)
async def run_automation(
    body: AutomationRunRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    result = await run_automation_for_account(
        supabase=supabase,
        settings=settings,
        owner_id=user.id,
        act_id=body.act_id,
        trigger="manual",
        date_preset=body.date_preset,
    )
    return AutomationRunOut(
        alerts_found=result.alerts_found,
        paused_count=result.paused_count,
        errors=result.errors,
    )


@router.post("/automation/run-all", response_model=AutomationRunAllOut)
async def run_automation_all(
    x_automation_key: str = Header(default=""),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    """Triggered by the VPS cron job — every account with server_schedule_enabled.

    Auth is a shared secret header, not a user JWT, since this call has no
    logged-in user behind it.
    """
    if not settings.automation_cron_secret or x_automation_key != settings.automation_cron_secret:
        raise AutomationKeyInvalidError()

    rows = (
        supabase.table("automation_settings")
        .select("owner_id, ad_accounts!inner(external_id)")
        .eq("server_schedule_enabled", True)
        .execute()
        .data
    )

    total_alerts = 0
    total_paused = 0
    errors: list[str] = []

    for row in rows:
        owner_id = row["owner_id"]
        act_id = row["ad_accounts"]["external_id"]
        try:
            result = await run_automation_for_account(
                supabase=supabase,
                settings=settings,
                owner_id=owner_id,
                act_id=act_id,
                trigger="cron",
            )
            total_alerts += result.alerts_found
            total_paused += result.paused_count
            errors.extend(result.errors)
        except Exception as exc:
            logger.error("run-all failed for account %s: %s", act_id, exc, exc_info=True)
            errors.append(f"{act_id}: {exc}")

    return AutomationRunAllOut(
        accounts_checked=len(rows),
        total_alerts=total_alerts,
        total_paused=total_paused,
        errors=errors,
    )


# === Notifications ===


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    rows = (
        supabase.table("notifications")
        .select("id, title, body, severity, lida, criado_em")
        .eq("owner_id", user.id)
        .order("criado_em", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return rows


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    supabase.table("notifications").update({"lida": True}).eq("id", notification_id).eq(
        "owner_id", user.id
    ).execute()
    return {"success": True}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    supabase.table("notifications").update({"lida": True}).eq("owner_id", user.id).eq("lida", False).execute()
    return {"success": True}
