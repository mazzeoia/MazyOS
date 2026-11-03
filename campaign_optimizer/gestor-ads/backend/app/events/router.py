from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Response
from supabase import Client

from app.auth.models import User
from app.dependencies import get_current_user, get_supabase
from app.events.schemas import EventsSummaryResponse, ProductEventRequest

router = APIRouter(tags=["events"])
logger = logging.getLogger(__name__)


@router.post("/events", status_code=204)
async def record_event(
    body: ProductEventRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> Response:
    """Registra um evento leve de uso do produto (login, troca de conta,
    sync, análise IA, export PDF, automação, navegação entre seções).

    Instrumentação nunca deve travar o fluxo do usuário — falha aqui vira
    log e retorna 204 do mesmo jeito.
    """
    try:
        supabase.table("product_events").insert(
            {
                "owner_id": user.id,
                "evento": body.evento,
                "metadata": body.metadata,
            }
        ).execute()
    except Exception as exc:
        logger.error("Failed to record product_event %s: %s", body.evento, exc, exc_info=True)
    return Response(status_code=204)


@router.get("/events/summary", response_model=EventsSummaryResponse)
async def events_summary(
    days: int = Query(default=30, le=365),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Contagem de eventos por tipo nos últimos N dias — visão rápida de
    quais funcionalidades estão sendo usadas, sem precisar abrir o
    Supabase direto."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = (
        supabase.table("product_events")
        .select("evento, criado_em")
        .eq("owner_id", user.id)
        .gte("criado_em", since)
        .execute()
        .data
    )
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["evento"]] = counts.get(r["evento"], 0) + 1
    return EventsSummaryResponse(since_days=days, total=len(rows), by_event=counts)
