"""Agent tools — thin async wrappers the WhatsApp agent calls to act on Meta
ad accounts: list/select accounts, pull KPI summaries, pause campaigns."""

from __future__ import annotations

from dataclasses import dataclass

from app.agent.conversation import link_ad_account
from app.core.analysis import CampaignBriefing, generate_campaign_strategy
from app.core.kpis import summarize_kpis
from app.core.naming import campaign_name
from app.meta.client import MetaAdsClient, extract_metric
from app.shared.exceptions import DraftValidationError, NotFoundError

# action_type substrings (Meta insights "actions" array) counted as leads.
LEAD_ACTION_TERMS = ("lead", "messaging_conversation_started")

# Meta Marketing API campaign objectives (v23). Anything sent to Meta must be
# one of these literals — a free-form objective would just 400 at the API.
META_OBJECTIVES = {
    "OUTCOME_TRAFFIC",
    "OUTCOME_LEADS",
    "OUTCOME_ENGAGEMENT",
    "OUTCOME_AWARENESS",
    "OUTCOME_SALES",
    "OUTCOME_APP_PROMOTION",
}

# Common free-form ways users/the LLM describe an objective.
_OBJECTIVE_SYNONYMS = {
    "trafego": "OUTCOME_TRAFFIC",
    "tráfego": "OUTCOME_TRAFFIC",
    "traffic": "OUTCOME_TRAFFIC",
    "visitas": "OUTCOME_TRAFFIC",
    "cliques": "OUTCOME_TRAFFIC",
    "lead": "OUTCOME_LEADS",
    "leads": "OUTCOME_LEADS",
    "cadastro": "OUTCOME_LEADS",
    "cadastros": "OUTCOME_LEADS",
    "conversao": "OUTCOME_LEADS",
    "conversão": "OUTCOME_LEADS",
    "engajamento": "OUTCOME_ENGAGEMENT",
    "engagement": "OUTCOME_ENGAGEMENT",
    "mensagens": "OUTCOME_ENGAGEMENT",
    "whatsapp": "OUTCOME_ENGAGEMENT",
    "reconhecimento": "OUTCOME_AWARENESS",
    "alcance": "OUTCOME_AWARENESS",
    "awareness": "OUTCOME_AWARENESS",
    "marca": "OUTCOME_AWARENESS",
    "vendas": "OUTCOME_SALES",
    "sales": "OUTCOME_SALES",
    "compras": "OUTCOME_SALES",
    "ecommerce": "OUTCOME_SALES",
    "app": "OUTCOME_APP_PROMOTION",
    "aplicativo": "OUTCOME_APP_PROMOTION",
    "instalacoes": "OUTCOME_APP_PROMOTION",
    "instalações": "OUTCOME_APP_PROMOTION",
}


def normalize_objective(objetivo: str) -> str:
    """Map a free-form objective to a real Meta objective enum value.

    Raises DraftValidationError when it can't be resolved, so the agent asks
    the user instead of letting Meta reject the campaign with a raw 400.
    """
    raw = (objetivo or "").strip()
    upper = raw.upper().replace(" ", "_")
    if upper in META_OBJECTIVES:
        return upper
    lowered = raw.lower()
    for term, value in _OBJECTIVE_SYNONYMS.items():
        if term in lowered:
            return value
    raise DraftValidationError(
        f"Não reconheci o objetivo '{objetivo}'. Use um destes: "
        + ", ".join(sorted(META_OBJECTIVES))
    )


def _load_draft_for_conversation(ctx: ToolContext, draft_id: str) -> dict:
    """Fetch a draft and refuse it if it doesn't belong to this conversation."""
    draft = (
        ctx.supabase.table("campaign_drafts")
        .select("id,status,payload,conversation_id,ad_account_id")
        .eq("id", draft_id)
        .single()
        .execute()
        .data
    )
    if not draft:
        raise DraftValidationError("Não encontrei essa campanha.")
    if draft.get("conversation_id") != ctx.conversation_id:
        raise DraftValidationError(
            "Essa campanha não pertence a esta conversa. Não posso mexer nela a partir daqui."
        )
    return draft


@dataclass
class ToolContext:
    """Everything a tool needs, assembled once per agent turn."""

    supabase: object
    settings: object
    user_id: str
    conversation_id: str
    ad_account_id: str | None


async def listar_contas(ctx: ToolContext) -> dict:
    rows = (
        ctx.supabase.table("ad_accounts")
        .select("id,name,external_id")
        .eq("client_id", ctx.user_id)
        .execute()
        .data
    )
    return {"contas": rows}


async def selecionar_conta(ctx: ToolContext, *, conta: str) -> dict:
    """Resolve the user's answer (a number from the listed order, or a
    name/partial name) to an ad_account_id, and link it to the conversation."""
    rows = (
        ctx.supabase.table("ad_accounts")
        .select("id,name,external_id")
        .eq("client_id", ctx.user_id)
        .execute()
        .data
    )
    if not rows:
        raise NotFoundError("Nenhuma conta de anúncio encontrada.")

    chosen = None
    if conta.strip().isdigit():
        idx = int(conta.strip()) - 1
        if 0 <= idx < len(rows):
            chosen = rows[idx]
    else:
        matches = [r for r in rows if conta.lower() in r["name"].lower()]
        if len(matches) == 1:
            chosen = matches[0]
        elif len(matches) > 1:
            names = ", ".join(m["name"] for m in matches)
            raise DraftValidationError(f"Encontrei mais de uma conta com esse nome ({names}). Qual delas?")

    if chosen is None:
        raise NotFoundError(f"Não encontrei a conta '{conta}'. Tente o número da lista ou o nome exato.")

    await link_ad_account(ctx.supabase, ctx.conversation_id, chosen["id"])
    return {"ad_account_id": chosen["id"], "name": chosen["name"]}


def _normalize_insight_row(row: dict) -> dict:
    """Map a raw Meta insights row (actions array, string numerics) to the
    flat shape `summarize_kpis` expects."""
    return {
        "campaign": row.get("campaign_name", "?"),
        "spend": row.get("spend", 0),
        "leads": extract_metric(row.get("actions"), LEAD_ACTION_TERMS),
        "clicks": row.get("clicks", 0),
        "impressions": row.get("impressions", 0),
    }


async def consultar_metricas(ctx: ToolContext, meta_client: MetaAdsClient) -> dict:
    insights = await meta_client.get_insights(meta_client.act_id)
    normalized = [_normalize_insight_row(row) for row in insights]
    kpis = summarize_kpis(normalized)
    return {
        "total_spend": kpis.total_spend,
        "total_leads": kpis.total_leads,
        "cpl_medio": kpis.cpl_medio,
        "ctr_medio": kpis.ctr_medio,
        "tendencia": kpis.tendencia,
    }


async def pausar_campanha(ctx: ToolContext, meta_client: MetaAdsClient, *, campanha_id: str) -> dict:
    await meta_client.update_status(campanha_id, "PAUSED")
    return {"campanha_id": campanha_id, "status": "PAUSED"}


async def propor_campanha(
    ctx: ToolContext,
    *,
    produto: str,
    objetivo: str,
    verba_total: float,
    dias: int,
    publico_alvo: str,
    destino_lead: str,
    marca: str,
) -> dict:
    """Ask Claude (via core.analysis) for a justified strategy, save it as a
    campaign_drafts row with status='rascunho', linked to this conversation."""
    if ctx.ad_account_id is None:
        raise DraftValidationError(
            "Antes de propor uma campanha, escolha a conta de anúncio primeiro."
        )
    objetivo = normalize_objective(objetivo)

    briefing = CampaignBriefing(
        produto=produto, objetivo=objetivo, verba_total=verba_total, dias=dias,
        publico_alvo=publico_alvo, destino_lead=destino_lead, marca=marca,
    )
    settings = ctx.settings
    strategy = await generate_campaign_strategy(
        briefing,
        anthropic_api_key=getattr(settings, "anthropic_api_key", ""),
        anthropic_workspace_id=getattr(settings, "anthropic_workspace_id", ""),
    )

    payload = {
        "marca": marca,
        "objetivo": objetivo,
        "publico": strategy.publico,
        "verba_diaria": strategy.verba_diaria,
        "dias": strategy.dias,
        "estrutura": strategy.estrutura,
        "copy": strategy.copy,
        "justificativa": strategy.justificativa,
    }
    row = (
        ctx.supabase.table("campaign_drafts")
        .insert(
            {
                "owner_id": ctx.user_id,
                "ad_account_id": ctx.ad_account_id,
                "conversation_id": ctx.conversation_id,
                "payload": payload,
                "status": "rascunho",
            }
        )
        .execute()
        .data[0]
    )
    return {"draft_id": row["id"], **payload}


async def aprovar_campanha(ctx: ToolContext, *, draft_id: str) -> dict:
    """Record the user's explicit approval of a draft — the auditable step
    between propor_campanha and criar_campanha."""
    draft = _load_draft_for_conversation(ctx, draft_id)
    if draft["status"] != "rascunho":
        raise DraftValidationError(
            f"Essa campanha não está em rascunho (status atual: {draft['status']}). Não dá pra aprovar de novo."
        )
    ctx.supabase.table("campaign_drafts").update({"status": "aprovado"}).eq("id", draft_id).execute()
    return {"draft_id": draft_id, "status": "aprovado"}


async def criar_campanha(ctx: ToolContext, meta_client: MetaAdsClient, *, draft_id: str) -> dict:
    """Create the campaign on Meta — ALWAYS PAUSED. Refuses if the draft
    linked to this conversation isn't approved yet (spec §4, §7)."""
    draft = _load_draft_for_conversation(ctx, draft_id)
    if draft["status"] != "aprovado":
        raise DraftValidationError(
            "Essa campanha ainda não foi aprovada. Confirme a estratégia antes de eu criar."
        )
    if ctx.ad_account_id is not None and draft.get("ad_account_id") != ctx.ad_account_id:
        raise DraftValidationError(
            "Essa campanha não pertence a esta conta de anúncio. Não posso criar a partir daqui."
        )

    payload = draft["payload"]
    objetivo = normalize_objective(payload["objetivo"])
    name = campaign_name(payload["marca"], payload["objetivo"], payload["publico"])
    daily_cents = int(round(payload["verba_diaria"] * 100))

    result = await meta_client.create_campaign(
        name=name,
        objective=objetivo,
        daily_budget_cents=daily_cents,
    )

    ctx.supabase.table("campaign_drafts").update(
        {"status": "criado", "meta_campaign_id": result["id"]}
    ).eq("id", draft_id).execute()

    return {"meta_campaign_id": result["id"], "name": name, "status": "PAUSED"}


def localizacao_por_raio(*, latitude: float, longitude: float, raio_km: float) -> dict:
    """Build the Meta `custom_locations` targeting payload for a radius
    around a point (from a shared pin or a Google Maps link, already
    resolved to lat/lng before this tool is called — spec §4)."""
    return {
        "custom_locations": [
            {"latitude": latitude, "longitude": longitude, "radius": raio_km, "distance_unit": "kilometer"}
        ]
    }
