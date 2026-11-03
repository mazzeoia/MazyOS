from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Query, UploadFile
from supabase import Client

from app.analysis.schemas import (
    AnalysisHistoryOut,
    AuditLogOut,
    CreativeOut,
    EvaluateRequest,
    EvaluateResponse,
    RuleResultOut,
    SummaryRequest,
    SummaryResponse,
)
from app.auth.models import User
from app.config import Settings, get_settings
from app.core.account_data import build_metrics, get_account_campaigns, get_account_thresholds, get_ad_account
from app.core.analysis import analyze_performance
from app.core.kpis import summarize_kpis
from app.core.rules import evaluate
from app.dependencies import get_current_user, get_supabase
from app.shared.dates import date_preset_to_start_date

router = APIRouter(tags=["analysis"])
logger = logging.getLogger(__name__)


@router.post("/analysis/evaluate", response_model=EvaluateResponse)
async def run_evaluation(
    body: EvaluateRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = get_ad_account(supabase, user.id, body.act_id)
    thresholds = get_account_thresholds(acc)

    campaigns = get_account_campaigns(supabase, user.id, acc["id"])

    since = date_preset_to_start_date(body.date_preset)
    metrics = build_metrics(campaigns, supabase, user.id, since=since)
    alerts = evaluate(metrics, thresholds)

    return EvaluateResponse(
        alerts=[
            RuleResultOut(
                severity=a.severity,
                rule_name=a.rule_name,
                action=a.action,
                campaign=a.campaign,
                reason=a.reason,
                should_pause=a.should_pause,
                meta_entity_id=a.meta_entity_id,
            )
            for a in alerts
        ],
        total=len(alerts),
    )


@router.post("/analysis/summary", response_model=SummaryResponse)
async def run_summary(
    body: SummaryRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    acc = get_ad_account(supabase, user.id, body.act_id)
    thresholds = get_account_thresholds(acc)

    campaigns = get_account_campaigns(supabase, user.id, acc["id"])

    since = date_preset_to_start_date(body.date_preset)
    metrics = build_metrics(campaigns, supabase, user.id, since=since)

    result = await analyze_performance(
        metrics=metrics,
        thresholds=thresholds,
        nivel_tecnico=body.nivel_tecnico,
        anthropic_api_key=settings.anthropic_api_key,
        anthropic_workspace_id=settings.anthropic_workspace_id,
    )

    kpis = summarize_kpis(metrics)
    kpis_dict = {
        "total_spend": kpis.total_spend,
        "total_leads": kpis.total_leads,
        "cpl_medio": kpis.cpl_medio,
        "ctr_medio": kpis.ctr_medio,
        "tendencia": kpis.tendencia,
        "melhor_campanha": kpis.melhor_campanha,
        "pior_campanha": kpis.pior_campanha,
    }

    # Best-effort: save to history. Never block the response on this.
    try:
        supabase.table("analysis_history").insert(
            {
                "owner_id": user.id,
                "ad_account_id": acc["id"],
                "nivel_tecnico": body.nivel_tecnico,
                "resumo": result.resumo,
                "recomendacoes": result.recomendacoes,
                "acoes": result.acoes,
                "kpis": kpis_dict,
            }
        ).execute()
    except Exception as exc:
        logger.error("Failed to save analysis_history: %s", exc, exc_info=True)

    return SummaryResponse(
        resumo=result.resumo,
        recomendacoes=result.recomendacoes,
        acoes=result.acoes,
        kpis=kpis_dict,
    )


@router.get("/analysis/history", response_model=list[AnalysisHistoryOut])
async def list_analysis_history(
    act_id: str,
    limit: int = Query(default=20, le=100),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = get_ad_account(supabase, user.id, act_id)

    rows = (
        supabase.table("analysis_history")
        .select("id, nivel_tecnico, resumo, recomendacoes, acoes, kpis, criado_em")
        .eq("owner_id", user.id)
        .eq("ad_account_id", acc["id"])
        .order("criado_em", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return rows


# === Creatives ===


@router.post("/creatives/upload", response_model=CreativeOut)
async def upload_creative(
    act_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = get_ad_account(supabase, user.id, act_id)

    content_type = file.content_type or ""
    tipo = "video" if "video" in content_type else "image"
    file_bytes = await file.read()

    # Upload to Supabase Storage
    storage_path = f"{user.id}/{acc['id']}/{file.filename}"
    supabase.storage.from_("creatives").upload(storage_path, file_bytes)

    # Schema: owner_id (not user_id)
    row = (
        supabase.table("creatives")
        .insert(
            {
                "owner_id": user.id,
                "ad_account_id": acc["id"],
                "tipo": tipo,
                "storage_path": storage_path,
            }
        )
        .execute()
        .data[0]
    )

    return CreativeOut(
        id=row["id"],
        tipo=row["tipo"],
        storage_path=row["storage_path"],
        meta_hash=row.get("meta_hash"),
        meta_video_id=row.get("meta_video_id"),
    )


@router.get("/creatives", response_model=list[CreativeOut])
async def list_creatives(
    act_id: str | None = None,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    # Schema: owner_id (not user_id)
    query = supabase.table("creatives").select("*").eq("owner_id", user.id)
    if act_id:
        acc = get_ad_account(supabase, user.id, act_id)
        query = query.eq("ad_account_id", acc["id"])
    rows = query.execute().data
    return [
        CreativeOut(
            id=r["id"],
            tipo=r["tipo"],
            storage_path=r["storage_path"],
            meta_hash=r.get("meta_hash"),
            meta_video_id=r.get("meta_video_id"),
        )
        for r in rows
    ]


# === Audit Log ===


@router.get("/audit-log", response_model=list[AuditLogOut])
async def list_audit_log(
    entidade: str | None = None,
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    # Schema: owner_id (not user_id), criado_em exists
    query = (
        supabase.table("audit_log")
        .select("id, acao, entidade, entidade_id, criado_em")
        .eq("owner_id", user.id)
        .order("criado_em", desc=True)
        .limit(limit)
    )
    if entidade:
        query = query.eq("entidade", entidade)
    rows = query.execute().data
    return rows
