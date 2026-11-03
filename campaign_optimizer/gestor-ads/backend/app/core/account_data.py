"""Shared account/metrics fetch helpers.

Extracted from app.analysis.router so both the analysis endpoints and the
automation engine (app.core.automation) can reuse the exact same
account-lookup and metrics-fetching logic without duplicating it.
"""

from __future__ import annotations

from supabase import Client

from app.core.rules import AccountThresholds
from app.shared.exceptions import NotFoundError


def get_ad_account(supabase: Client, user_id: str, act_id: str) -> dict:
    """Fetch ad_account or raise 404-style NotFoundError."""
    rows = (
        supabase.table("ad_accounts")
        .select("*")
        .eq("client_id", user_id)
        .eq("external_id", act_id)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise NotFoundError(f"Conta {act_id} não encontrada. Conecte sua conta Meta primeiro.")
    return rows[0]


def get_account_thresholds(acc: dict) -> AccountThresholds:
    """Build thresholds from ad_account row.

    Schema note: ad_accounts may NOT have threshold columns (target_cpl, etc.).
    Falls back to AccountThresholds defaults when columns are absent.
    """
    return AccountThresholds(
        target_cpl=float(acc.get("target_cpl") or 0),
        waste_limit=float(acc.get("waste_limit") or 100),
        min_ctr=float(acc.get("min_ctr") or 0.8),
        max_frequency=float(acc.get("max_frequency") or 3.0),
    )


def get_account_campaigns(supabase: Client, user_id: str, ad_account_id: str) -> list[dict]:
    """Fetch campaigns for an account (id, name, meta_campaign_id only)."""
    return (
        supabase.table("campaigns")
        .select("id, name, meta_campaign_id")
        .eq("ad_account_id", ad_account_id)
        .eq("owner_id", user_id)
        .execute()
        .data
    )


def build_metrics(
    campaigns: list[dict], supabase: Client, user_id: str, since: str | None = None
) -> list[dict]:
    """Fetch campaign_daily_metrics and enrich with campaign name + meta_entity_id.

    Schema adaptation: campaigns uses `name` (not `nome`),
    campaign_daily_metrics uses `owner_id` (not `user_id`).

    `since` (ISO date) restricts to rows with metric_date >= since, when given.
    """
    metrics: list[dict] = []
    for camp in campaigns:
        query = (
            supabase.table("campaign_daily_metrics")
            .select("*")
            .eq("campaign_id", camp["id"])
            .eq("owner_id", user_id)
        )
        if since:
            query = query.gte("metric_date", since)
        rows = query.execute().data
        for r in rows:
            r["campaign"] = camp.get("name", "Campanha sem nome")
            r["meta_entity_id"] = camp.get("meta_campaign_id")
            r["entity_level"] = "campaign"
            r["entity_name"] = camp.get("name", "Campanha sem nome")
        metrics.extend(rows)
    return metrics
