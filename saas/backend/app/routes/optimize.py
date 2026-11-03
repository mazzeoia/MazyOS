from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field

from ..auth import CurrentUser, get_current_user
from ..config import get_settings
from ..supabase_client import get_supabase_admin


router = APIRouter(prefix="/optimize", tags=["optimize"])


class PriorityPayload(BaseModel):
    campaign_name: str
    title: str
    action: str
    impact: str
    severity: int


class TotalsPayload(BaseModel):
    spend: float = 0
    metaResults: float = 0
    resultLabel: str = "Resultados"
    costPerResult: float = 0
    ctr: float = 0
    cpm: float = 0
    cpl: float = 0
    reach: float = 0
    clicks: float = 0
    impressions: float = 0


class ClientContextPayload(BaseModel):
    monthly_budget: float = 0
    target_cpl: float = 0
    account_manager: str = ""
    business_goal: str = ""
    qualified_lead_definition: str = ""


class RecommendationRequest(BaseModel):
    period: str
    period_label: str
    client_name: str
    client_context: ClientContextPayload = Field(default_factory=ClientContextPayload)
    totals: TotalsPayload
    priorities: list[PriorityPayload] = Field(default_factory=list)


def _currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _build_prompt(payload: RecommendationRequest) -> tuple[str, str]:
    system_prompt = (
        "Voce e o consultor de trafego pago da Creative Agencia Marketing. Recebe um diagnostico "
        "deterministico (gasto, resultado e prioridades ja calculadas por regras) de um cliente e "
        "transforma isso num texto consultivo curto seguido de um plano de acao priorizado. "
        "Regra fixa: nao invente nenhum numero, use somente os dados do diagnostico recebido. "
        "Escreva em portugues do Brasil, direto, como uma pessoa falando com outra, sem formalidade "
        "excessiva, sem cliche, sem travessao. Isso e um relatorio, nao uma conversa: nunca termine com "
        "pergunta, oferta de ajuda adicional ou convite para o usuario responder. "
        "Formato obrigatorio, sem excecao: um paragrafo de no maximo 2 frases resumindo a situacao, "
        "seguido de uma unica lista com no maximo 4 acoes (as mais urgentes primeiro), uma linha curta "
        "cada, sem sublistas nem secoes extras como 'proximos passos'. Nao repita os numeros que ja "
        "estao no resumo do periodo. Nada de texto depois da lista."
    )

    lines = [
        f"Cliente: {payload.client_name}",
        f"Periodo analisado: {payload.period_label}",
        "",
        "Contexto comercial configurado:",
        f"- Orcamento mensal: {_currency(payload.client_context.monthly_budget)}",
        f"- CPL alvo: {_currency(payload.client_context.target_cpl)}",
        f"- Responsavel: {payload.client_context.account_manager or 'Nao informado'}",
        f"- Objetivo comercial: {payload.client_context.business_goal or 'Nao informado'}",
        f"- Lead qualificado: {payload.client_context.qualified_lead_definition or 'Nao informado'}",
        "",
        "Resumo do periodo:",
        f"- Investimento: {_currency(payload.totals.spend)}",
        f"- {payload.totals.resultLabel}: {payload.totals.metaResults:.0f}",
        f"- Custo medio por resultado: {_currency(payload.totals.costPerResult)}",
        f"- CTR: {payload.totals.ctr:.2f}%",
        f"- CPM: {_currency(payload.totals.cpm)}",
        f"- Alcance: {payload.totals.reach:.0f}",
        f"- Cliques: {payload.totals.clicks:.0f}",
        f"- Impressoes: {payload.totals.impressions:.0f}",
        "",
    ]

    if payload.priorities:
        lines.append("Prioridades identificadas pelo motor de regras:")
        for index, priority in enumerate(payload.priorities, start=1):
            lines.append(
                f"{index}. [{priority.title}] Campanha: {priority.campaign_name} | "
                f"Severidade: {priority.severity} | Impacto: {priority.impact} | "
                f"Acao sugerida pelo motor: {priority.action}"
            )
    else:
        lines.append("Nenhuma prioridade critica identificada pelo motor de regras no periodo.")

    return system_prompt, "\n".join(lines)


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY nao configurada no backend.")

    from openai import OpenAI, OpenAIError

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=1200,
            reasoning_effort="low",
        )
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao chamar a OpenAI: {exc}") from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise HTTPException(status_code=502, detail="A OpenAI nao retornou nenhum texto.")
    return content


@router.get("/{client_id}")
def get_latest_recommendation(
    client_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    period: str = Query(...),
) -> dict[str, object]:
    client = get_supabase_admin()
    result = (
        client.table("recommendations")
        .select("*")
        .eq("owner_id", user.id)
        .eq("client_id", client_id)
        .eq("period", period)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return {"ok": True, "recommendation": result.data[0] if result.data else None}


@router.post("/{client_id}")
def generate_recommendation(
    client_id: str,
    payload: RecommendationRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, object]:
    settings = get_settings()
    system_prompt, user_prompt = _build_prompt(payload)
    content = _call_openai(system_prompt, user_prompt)

    client = get_supabase_admin()
    row = {
        "owner_id": user.id,
        "client_id": client_id,
        "title": f"Plano de acao consultivo ({payload.period_label})",
        "generated_by": "openai",
        "period": payload.period,
        "snapshot": payload.model_dump(),
        "content": content,
        "model": settings.openai_model,
    }
    try:
        result = client.table("recommendations").insert(row).execute()
    except APIError as exc:
        raise HTTPException(status_code=500, detail=exc.message) from exc
    if not result.data:
        raise HTTPException(status_code=500, detail="Nao foi possivel salvar a recomendacao.")
    return {"ok": True, "recommendation": result.data[0]}
