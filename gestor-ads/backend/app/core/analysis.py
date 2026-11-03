"""AI analysis layer with deterministic fallback.

Migrated from campaign_optimizer/core/ai.py — OpenAI → Claude (Anthropic SDK).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import anthropic

from app.core.kpis import summarize_kpis
from app.core.rules import AccountThresholds, evaluate

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    resumo: str
    recomendacoes: list[str] = field(default_factory=list)
    acoes: list[dict] = field(default_factory=list)


@dataclass
class CampaignBriefing:
    produto: str
    objetivo: str
    verba_total: float
    dias: int
    publico_alvo: str
    destino_lead: str
    marca: str


@dataclass
class CampaignStrategy:
    verba_diaria: float
    dias: int
    estrutura: str
    publico: str
    copy: str
    justificativa: str


# --- Deterministic fallback (migrated from campaign_optimizer) ---


def fallback_analysis(metrics: list[dict], alerts: list[dict]) -> str:
    """Deterministic analysis when Claude is unavailable.

    Priority: gasto sem lead > yellow alerts > no alerts.
    """
    kpis = summarize_kpis(metrics)
    red = [a for a in alerts if a.get("severity") == "vermelho"]
    yellow = [a for a in alerts if a.get("severity") == "amarelo"]

    lines = [
        "Diagnóstico rápido:",
        f"Investimento: R$ {kpis.total_spend:.2f}. Leads: {kpis.total_leads}. CPL médio: R$ {kpis.cpl_medio:.2f}.",
    ]
    if red:
        lines.append(f"Tem {len(red)} ponto(s) crítico(s) queimando dinheiro. Prioridade: pausar ou revisar agora.")
    elif yellow:
        lines.append(
            f"Sem desperdício grave, mas existem {len(yellow)} alerta(s) para otimizar criativo, público ou copy."
        )
    else:
        lines.append("Sem alerta crítico nas regras atuais. Acompanhe a consistência dos leads antes de escalar.")

    if kpis.total_leads == 0 and kpis.total_spend > 0:
        lines.append("Atenção: sem conversão registrada. A leitura é de tráfego, não de lead qualificado.")

    lines.append("Próxima ação: resolva primeiro o que gastou sem lead, depois mexa em CTR, frequência e CPL.")
    return "\n".join(lines)


# --- AI-powered analysis ---


async def analyze_performance(
    metrics: list[dict],
    thresholds: AccountThresholds,
    nivel_tecnico: str = "avancado",
    anthropic_api_key: str = "",
    model: str = "claude-sonnet-5",
) -> AnalysisResult:
    """Run rules + KPIs, then send to Claude for analysis.

    nivel_tecnico changes only the prompt language, not the analysis depth.
    Falls back to deterministic analysis if Claude fails.
    """
    alerts = evaluate(metrics, thresholds)
    alerts_dicts = [
        {"severity": a.severity, "rule_name": a.rule_name, "reason": a.reason, "campaign": a.campaign}
        for a in alerts
    ]
    kpis = summarize_kpis(metrics)

    if not anthropic_api_key:
        return AnalysisResult(
            resumo=fallback_analysis(metrics, alerts_dicts),
            recomendacoes=[a.reason for a in alerts[:5]],
            acoes=[{"entity_id": a.meta_entity_id, "action": a.action} for a in alerts if a.meta_entity_id],
        )

    lang_instruction = (
        "Use termos técnicos (CTR, CPM, CPA, CPL, CBO) normalmente."
        if nivel_tecnico == "avancado"
        else "Traduza toda métrica para consequência prática. Nunca use sigla sem explicar."
    )

    prompt = (
        "Você é analista de tráfego da Creative Agência Marketing. "
        "Escreva em português brasileiro simples, direto e útil. "
        "Não invente números. Explique o que fazer hoje.\n\n"
        f"Nível técnico do usuário: {nivel_tecnico}. {lang_instruction}\n\n"
        f"KPIs: spend={kpis.total_spend}, leads={kpis.total_leads}, "
        f"CPL={kpis.cpl_medio}, CTR={kpis.ctr_medio}%, tendência={kpis.tendencia}\n\n"
        f"Alertas: {json.dumps(alerts_dicts[:20], ensure_ascii=False)}"
    )

    try:
        client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text

        return AnalysisResult(
            resumo=text,
            recomendacoes=[a.reason for a in alerts[:5]],
            acoes=[{"entity_id": a.meta_entity_id, "action": a.action} for a in alerts if a.meta_entity_id],
        )

    except Exception as exc:
        logger.warning("Claude analysis failed, using fallback: %s", exc)
        fb = fallback_analysis(metrics, alerts_dicts)
        return AnalysisResult(
            resumo=fb,
            recomendacoes=[a.reason for a in alerts[:5]],
            acoes=[{"entity_id": a.meta_entity_id, "action": a.action} for a in alerts if a.meta_entity_id],
        )


async def generate_campaign_strategy(
    briefing: CampaignBriefing,
    account_history: list[dict] | None = None,
    nivel_tecnico: str = "avancado",
    anthropic_api_key: str = "",
    model: str = "claude-sonnet-5",
) -> CampaignStrategy:
    """Generate a complete campaign strategy with justification."""
    prompt = (
        "Você é gestor de tráfego da Creative Agência Marketing. "
        "Gere uma estratégia completa com justificativa para cada decisão.\n\n"
        f"Produto/serviço: {briefing.produto}\n"
        f"Objetivo: {briefing.objetivo}\n"
        f"Verba total: R$ {briefing.verba_total:.2f}\n"
        f"Prazo: {briefing.dias} dias\n"
        f"Público-alvo: {briefing.publico_alvo}\n"
        f"Destino do lead: {briefing.destino_lead}\n"
        f"Marca: {briefing.marca}\n\n"
        "Responda APENAS com JSON no formato:\n"
        '{"verba_diaria": X, "dias": X, "estrutura": "...", "publico": "...", "copy": "...", "justificativa": "..."}'
    )

    if account_history:
        prompt += f"\n\nHistórico da conta: {json.dumps(account_history[:10], ensure_ascii=False)}"

    try:
        client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text

        # Parse JSON from response (may be wrapped in markdown)
        json_str = text
        if "```" in text:
            json_str = text.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        data = json.loads(json_str.strip())

        return CampaignStrategy(
            verba_diaria=float(data.get("verba_diaria", briefing.verba_total / briefing.dias)),
            dias=int(data.get("dias", briefing.dias)),
            estrutura=data.get("estrutura", "CBO com 2 conjuntos"),
            publico=data.get("publico", briefing.publico_alvo),
            copy=data.get("copy", ""),
            justificativa=data.get("justificativa", ""),
        )

    except Exception as exc:
        logger.warning("Strategy generation failed: %s", exc)
        daily = round(briefing.verba_total / briefing.dias, 2)
        return CampaignStrategy(
            verba_diaria=daily,
            dias=briefing.dias,
            estrutura="CBO com 2 conjuntos de anúncios",
            publico=briefing.publico_alvo,
            copy="",
            justificativa=f"Estratégia padrão: R$ {daily}/dia × {briefing.dias} dias. IA indisponível.",
        )
