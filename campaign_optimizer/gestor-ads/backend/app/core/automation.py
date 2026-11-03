"""Auto-pause automation engine.

Reuses the existing rules engine (app.core.rules) unchanged — the only rule
flagged should_pause=True today is "gasto_sem_lead" (spend with zero leads),
which is the one condition safe enough to act on without a human in the loop.

Auto-pause and server scheduling are both OFF by default per account
(automation_settings row). This module never pauses anything unless the
account has explicitly opted in.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from supabase import Client

from app.auth.models import User
from app.config import Settings
from app.core.account_data import build_metrics, get_account_campaigns, get_account_thresholds, get_ad_account
from app.core.notify import notify
from app.core.rules import RuleResult, evaluate
from app.dependencies import build_meta_client
from app.shared.dates import date_preset_to_start_date

logger = logging.getLogger(__name__)


@dataclass
class AutomationRunResult:
    alerts_found: int = 0
    paused_count: int = 0
    errors: list[str] = field(default_factory=list)


def select_alerts_to_pause(alerts: list[RuleResult]) -> list[RuleResult]:
    """Pure filter: which alerts are both flagged should_pause and actionable
    (have a Meta entity id to actually pause). Kept separate from I/O for
    easy unit testing."""
    return [a for a in alerts if a.should_pause and a.meta_entity_id]


def _get_automation_settings(supabase: Client, owner_id: str, ad_account_id: str) -> dict | None:
    rows = (
        supabase.table("automation_settings")
        .select("*")
        .eq("owner_id", owner_id)
        .eq("ad_account_id", ad_account_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


async def run_automation_for_account(
    supabase: Client,
    settings: Settings,
    owner_id: str,
    act_id: str,
    trigger: str = "manual",
    date_preset: str = "last_7d",
) -> AutomationRunResult:
    """Evaluate one account's campaigns and, if auto-pause is enabled,
    pause the ones the rules engine flags as should_pause. Always logs the
    run and notifies the owner when there's something to report.
    """
    acc = get_ad_account(supabase, owner_id, act_id)
    thresholds = get_account_thresholds(acc)
    automation = _get_automation_settings(supabase, owner_id, acc["id"])

    auto_pause_enabled = bool(automation and automation.get("auto_pause_enabled"))
    notify_email = bool(automation.get("notify_email", True)) if automation else True
    notify_whatsapp = bool(automation and automation.get("notify_whatsapp"))
    owner_email = (automation or {}).get("owner_email", "")

    campaigns = get_account_campaigns(supabase, owner_id, acc["id"])
    since = date_preset_to_start_date(date_preset)
    metrics = build_metrics(campaigns, supabase, owner_id, since=since)
    alerts = evaluate(metrics, thresholds)

    to_pause = select_alerts_to_pause(alerts) if auto_pause_enabled else []
    paused_count = 0
    errors: list[str] = []

    if to_pause:
        meta = await build_meta_client(act_id, User(id=owner_id, email=owner_email), supabase, settings)
        try:
            for alert in to_pause:
                try:
                    await meta.update_status(alert.meta_entity_id, "PAUSED")
                    supabase.table("campaigns").update({"status": "PAUSED"}).eq(
                        "meta_campaign_id", alert.meta_entity_id
                    ).eq("owner_id", owner_id).execute()
                    paused_count += 1
                except Exception as exc:
                    logger.error("Auto-pause failed for %s: %s", alert.campaign, exc, exc_info=True)
                    errors.append(f"{alert.campaign}: {exc}")
        finally:
            await meta.close()

    try:
        supabase.table("automation_runs").insert(
            {
                "owner_id": owner_id,
                "ad_account_id": acc["id"],
                "trigger": trigger,
                "alerts_found": len(alerts),
                "paused_count": paused_count,
                "error": "; ".join(errors) if errors else None,
            }
        ).execute()
    except Exception as exc:
        logger.error("Failed to log automation_runs: %s", exc, exc_info=True)

    if alerts:
        account_name = acc.get("name") or act_id
        if paused_count:
            title = f"{paused_count} campanha(s) pausada(s) em {account_name}"
            body = (
                f"{paused_count} campanha(s) pausada(s) automaticamente por gasto sem lead. "
                f"Total de {len(alerts)} alerta(s) encontrados nessa checagem."
            )
            severity = "critical"
        else:
            title = f"{len(alerts)} alerta(s) em {account_name}"
            body = (
                f"{len(alerts)} alerta(s) encontrados nas regras de performance. "
                "Pausa automática desligada ou não necessária."
            )
            severity = "warning"

        await notify(
            supabase=supabase,
            settings=settings,
            owner_id=owner_id,
            ad_account_id=acc["id"],
            title=title,
            body=body,
            severity=severity,
            notify_email=notify_email,
            notify_whatsapp=notify_whatsapp,
            owner_email=owner_email,
        )

    return AutomationRunResult(alerts_found=len(alerts), paused_count=paused_count, errors=errors)
