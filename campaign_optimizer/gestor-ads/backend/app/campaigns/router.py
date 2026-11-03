from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from supabase import Client

from app.auth.models import User
from app.campaigns.schemas import (
    AccountOut,
    CampaignOut,
    DraftCreate,
    DraftOut,
    DraftUpdate,
    SyncRequest,
    SyncResponse,
)
from app.config import Settings, get_settings
from app.dependencies import build_meta_client, get_current_user, get_supabase
from app.meta.client import MetaAdsClient, extract_metric
from app.shared.exceptions import AppError, CampaignSafetyError, DraftValidationError

router = APIRouter(tags=["campaigns"])


# === Accounts ===


@router.get("/accounts", response_model=list[AccountOut])
async def list_accounts(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    rows = (
        supabase.table("ad_accounts")
        .select("id, external_id, name, currency, timezone, status")
        .eq("client_id", user.id)
        .execute()
        .data
    )
    return rows


@router.get("/accounts/{act_id}", response_model=AccountOut)
async def get_account(
    act_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    row = (
        supabase.table("ad_accounts")
        .select("id, external_id, name, currency, timezone, status")
        .eq("client_id", user.id)
        .eq("external_id", act_id)
        .single()
        .execute()
        .data
    )
    return row


# === Campaigns ===


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    act_id: str | None = None,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    query = supabase.table("campaigns").select("*").eq("client_id", user.id)
    if act_id:
        acc = (
            supabase.table("ad_accounts")
            .select("id")
            .eq("client_id", user.id)
            .eq("external_id", act_id)
            .single()
            .execute()
            .data
        )
        query = query.eq("ad_account_id", acc["id"])
    rows = query.execute().data
    return [
        CampaignOut(
            id=r["id"],
            meta_campaign_id=r.get("meta_campaign_id"),
            name=r.get("name", ""),
            objective=r.get("objective"),
            status=r.get("status", "UNKNOWN"),
            daily_budget=r.get("daily_budget"),
            lifetime_budget=r.get("lifetime_budget"),
        )
        for r in rows
    ]


@router.get("/campaigns/{campaign_id}/insights")
async def campaign_insights(
    campaign_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    rows = (
        supabase.table("campaign_daily_metrics")
        .select("*")
        .eq("campaign_id", campaign_id)
        .eq("owner_id", user.id)
        .execute()
        .data
    )
    return rows


# === Sync ===


@router.post("/campaigns/sync", response_model=SyncResponse)
async def sync_campaigns(
    body: SyncRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    meta = await build_meta_client(body.act_id, user, supabase, settings)

    try:
        # Get account ID from DB
        acc = (
            supabase.table("ad_accounts")
            .select("id")
            .eq("client_id", user.id)
            .eq("external_id", body.act_id)
            .single()
            .execute()
            .data
        )
        account_db_id = acc["id"]

        # List campaigns from Meta
        campaigns = await meta.list_campaigns()
        errors: list[dict] = []
        synced = 0
        metrics_count = 0

        for camp in campaigns:
            try:
                meta_camp_id = camp["id"]
                eff_status = camp.get("effective_status", camp.get("status", "UNKNOWN"))

                # Upsert campaign — schema: unique(client_id, platform, external_id)
                supabase.table("campaigns").upsert(
                    {
                        "client_id": user.id,
                        "owner_id": user.id,
                        "ad_account_id": account_db_id,
                        "platform": "meta_ads",
                        "external_id": meta_camp_id,
                        "meta_campaign_id": meta_camp_id,
                        "name": camp.get("name", ""),
                        "objective": camp.get("objective", ""),
                        "status": eff_status,
                        "effective_status": eff_status,
                        "daily_budget": float(camp.get("daily_budget", 0) or 0) / 100,
                        "lifetime_budget": float(camp.get("lifetime_budget", 0) or 0) / 100,
                    },
                    on_conflict="client_id,platform,external_id",
                ).execute()

                # Get local campaign ID
                local = (
                    supabase.table("campaigns")
                    .select("id")
                    .eq("client_id", user.id)
                    .eq("platform", "meta_ads")
                    .eq("external_id", meta_camp_id)
                    .single()
                    .execute()
                    .data
                )

                # Fetch insights
                insights = await meta.get_insights(meta_camp_id, date_preset=body.date_preset)
                for row in insights:
                    leads = int(
                        extract_metric(
                            row.get("actions"),
                            ("messaging_conversation_started", "lead", "contact", "omni_lead"),
                        )
                    )
                    cpl = extract_metric(
                        row.get("cost_per_action_type"),
                        ("messaging_conversation_started", "lead", "contact", "omni_lead"),
                    )
                    spend = float(row.get("spend", 0) or 0)
                    metric_date = row.get("date_start", datetime.now(timezone.utc).date().isoformat())

                    # Schema: unique(client_id, platform, metric_date,
                    # campaign_external_id, ad_group_external_id, ad_external_id)
                    supabase.table("campaign_daily_metrics").upsert(
                        {
                            "client_id": user.id,
                            "owner_id": user.id,
                            "campaign_id": local["id"],
                            "platform": "meta_ads",
                            "metric_date": metric_date,
                            "campaign_external_id": meta_camp_id,
                            "campaign_name": camp.get("name", ""),
                            "ad_group_external_id": "",
                            "ad_group_name": "",
                            "ad_external_id": "",
                            "ad_name": "",
                            "impressions": int(float(row.get("impressions", 0) or 0)),
                            "reach": int(float(row.get("reach", 0) or 0)),
                            "clicks": int(float(row.get("clicks", 0) or 0)),
                            "conversions": 0,
                            "ctr": round(float(row.get("ctr", 0) or 0), 4),
                            "cpc": round(float(row.get("cpc", 0) or 0), 4),
                            "cpm": round(float(row.get("cpm", 0) or 0), 4),
                            "frequency": round(float(row.get("frequency", 0) or 0), 4),
                            "spend": round(spend, 2),
                            "leads": leads,
                            "cpl": round(cpl or (spend / leads if leads else 0), 2),
                            "source": "meta_api",
                            "raw_payload": row,
                        },
                        on_conflict="client_id,platform,metric_date,campaign_external_id,ad_group_external_id,ad_external_id",
                    ).execute()
                    metrics_count += 1

                synced += 1
            except Exception as exc:
                errors.append({"campaign": camp.get("name", camp["id"]), "error": str(exc)})

        return SyncResponse(campaigns_synced=synced, metrics_upserted=metrics_count, errors=errors)
    finally:
        await meta.close()


# === Drafts ===


@router.post("/campaigns/drafts", response_model=DraftOut)
async def create_draft(
    body: DraftCreate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = (
        supabase.table("ad_accounts")
        .select("id")
        .eq("client_id", user.id)
        .eq("external_id", body.act_id)
        .single()
        .execute()
        .data
    )

    # Validate required fields in payload
    required = ["name", "objective"]
    missing = [f for f in required if f not in body.payload]
    if missing:
        raise DraftValidationError(f"Campos obrigatórios faltando: {', '.join(missing)}")

    row = (
        supabase.table("campaign_drafts")
        .insert(
            {
                "owner_id": user.id,
                "ad_account_id": acc["id"],
                "payload": body.payload,
                "status": "rascunho",
            }
        )
        .execute()
        .data[0]
    )
    return DraftOut(
        id=row["id"],
        status=row["status"],
        payload=row["payload"],
        meta_campaign_id=row.get("meta_campaign_id"),
        erro_detalhes=row.get("erro_detalhes"),
    )


@router.patch("/campaigns/drafts/{draft_id}", response_model=DraftOut)
async def update_draft(
    draft_id: str,
    body: DraftUpdate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    row = (
        supabase.table("campaign_drafts")
        .update({"payload": body.payload, "atualizado_em": datetime.now(timezone.utc).isoformat()})
        .eq("id", draft_id)
        .eq("owner_id", user.id)
        .execute()
        .data[0]
    )
    return DraftOut(
        id=row["id"],
        status=row["status"],
        payload=row["payload"],
        meta_campaign_id=row.get("meta_campaign_id"),
        erro_detalhes=row.get("erro_detalhes"),
    )


@router.post("/campaigns/drafts/{draft_id}/publish", response_model=DraftOut)
async def publish_draft(
    draft_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    # Get draft with ad account info
    draft = (
        supabase.table("campaign_drafts")
        .select("*, ad_accounts!inner(external_id)")
        .eq("id", draft_id)
        .eq("owner_id", user.id)
        .single()
        .execute()
        .data
    )

    if draft["status"] not in ("rascunho", "aprovado", "erro"):
        raise AppError(f"Draft não pode ser publicado no status '{draft['status']}'")

    # Update status to publishing
    supabase.table("campaign_drafts").update(
        {"status": "publicando", "atualizado_em": datetime.now(timezone.utc).isoformat()}
    ).eq("id", draft_id).execute()

    act_id = draft["ad_accounts"]["external_id"]
    meta = await build_meta_client(act_id, user, supabase, settings)

    try:
        payload = draft["payload"]
        result = await meta.create_campaign(
            name=payload["name"],
            objective=payload["objective"],
            special_ad_categories=payload.get("special_ad_categories", []),
            daily_budget_cents=payload.get("daily_budget_cents"),
            lifetime_budget_cents=payload.get("lifetime_budget_cents"),
        )

        # Success — update draft and create campaign
        meta_id = result["id"]
        supabase.table("campaign_drafts").update(
            {
                "status": "criado",
                "meta_campaign_id": meta_id,
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", draft_id).execute()

        acc = (
            supabase.table("ad_accounts")
            .select("id")
            .eq("client_id", user.id)
            .eq("external_id", act_id)
            .single()
            .execute()
            .data
        )
        supabase.table("campaigns").insert(
            {
                "ad_account_id": acc["id"],
                "owner_id": user.id,
                "meta_campaign_id": meta_id,
                "name": payload["name"],
                "objective": payload["objective"],
                "status": "PAUSED",
                "daily_budget": (payload.get("daily_budget_cents") or 0) / 100,
                "lifetime_budget": (payload.get("lifetime_budget_cents") or 0) / 100,
                "platform": "meta",
            }
        ).execute()

        updated = supabase.table("campaign_drafts").select("*").eq("id", draft_id).single().execute().data
        return DraftOut(
            id=updated["id"],
            status=updated["status"],
            payload=updated["payload"],
            meta_campaign_id=updated.get("meta_campaign_id"),
            erro_detalhes=updated.get("erro_detalhes"),
        )

    except Exception as exc:
        supabase.table("campaign_drafts").update(
            {
                "status": "erro",
                "erro_detalhes": str(exc),
                "atualizado_em": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", draft_id).execute()
        raise
    finally:
        await meta.close()


# === Activate / Pause ===


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    camp = (
        supabase.table("campaigns")
        .select("*, ad_accounts!inner(external_id)")
        .eq("id", campaign_id)
        .eq("owner_id", user.id)
        .single()
        .execute()
        .data
    )

    if camp["status"] != "PAUSED":
        raise CampaignSafetyError()

    act_id = camp["ad_accounts"]["external_id"]
    meta = await build_meta_client(act_id, user, supabase, settings)

    try:
        await meta.update_status(camp["meta_campaign_id"], "ACTIVE")
        supabase.table("campaigns").update({"status": "ACTIVE"}).eq("id", campaign_id).execute()
        return {"success": True, "status": "ACTIVE"}
    finally:
        await meta.close()


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    camp = (
        supabase.table("campaigns")
        .select("*, ad_accounts!inner(external_id)")
        .eq("id", campaign_id)
        .eq("owner_id", user.id)
        .single()
        .execute()
        .data
    )

    act_id = camp["ad_accounts"]["external_id"]
    meta = await build_meta_client(act_id, user, supabase, settings)

    try:
        await meta.update_status(camp["meta_campaign_id"], "PAUSED")
        supabase.table("campaigns").update({"status": "PAUSED"}).eq("id", campaign_id).execute()
        return {"success": True, "status": "PAUSED"}
    finally:
        await meta.close()
