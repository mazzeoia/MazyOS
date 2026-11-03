# gestor-ads/backend/tests/unit/test_analysis.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.analysis import (
    AnalysisResult,
    CampaignBriefing,
    CampaignStrategy,
    analyze_performance,
    fallback_analysis,
    generate_campaign_strategy,
)
from app.core.rules import AccountThresholds


def _row(**kw):
    base = {
        "campaign": "C1",
        "spend": 100,
        "leads": 5,
        "clicks": 50,
        "impressions": 1000,
        "ctr": 5.0,
        "cpl": 20,
        "frequency": 1.5,
        "effective_status": "ACTIVE",
        "entity_level": "campaign",
        "entity_name": "C1",
        "meta_entity_id": "c1",
    }
    base.update(kw)
    return base


# --- fallback_analysis ---


def test_fallback_no_alerts():
    rows = [_row()]
    result = fallback_analysis(rows, [])
    assert "R$ 100" in result
    assert "5" in result  # leads


def test_fallback_with_red_alerts():
    rows = [_row(spend=200, leads=0)]
    alerts = [{"severity": "vermelho", "rule_name": "gasto_sem_lead"}]
    result = fallback_analysis(rows, alerts)
    assert "critico" in result.lower() or "crítico" in result.lower()


def test_fallback_with_yellow_alerts():
    rows = [_row()]
    alerts = [{"severity": "amarelo", "rule_name": "ctr_baixo"}]
    result = fallback_analysis(rows, alerts)
    assert "alerta" in result.lower()


def test_fallback_zero_leads_warning():
    rows = [_row(spend=50, leads=0)]
    result = fallback_analysis(rows, [])
    assert "lead" in result.lower()


# --- analyze_performance ---


@pytest.mark.asyncio
async def test_analyze_performance_uses_claude():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Análise: CTR ok, CPL bom.")]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_msg)

    with patch("app.core.analysis.anthropic.AsyncAnthropic", return_value=mock_client):
        result = await analyze_performance(
            metrics=[_row()],
            thresholds=AccountThresholds(),
            nivel_tecnico="avancado",
            anthropic_api_key="sk-test",
        )
    assert isinstance(result, AnalysisResult)
    assert "CTR" in result.resumo or "CPL" in result.resumo


@pytest.mark.asyncio
async def test_analyze_performance_fallback_on_error():
    with patch("app.core.analysis.anthropic.AsyncAnthropic", side_effect=Exception("API down")):
        result = await analyze_performance(
            metrics=[_row()],
            thresholds=AccountThresholds(),
            nivel_tecnico="avancado",
            anthropic_api_key="sk-test",
        )
    assert isinstance(result, AnalysisResult)
    assert "R$ 100" in result.resumo  # fallback output


@pytest.mark.asyncio
async def test_analyze_performance_without_api_key():
    result = await analyze_performance(
        metrics=[_row()],
        thresholds=AccountThresholds(),
        nivel_tecnico="leigo",
        anthropic_api_key="",
    )
    assert isinstance(result, AnalysisResult)
    assert result.resumo  # fallback works


# --- generate_campaign_strategy ---


@pytest.mark.asyncio
async def test_generate_strategy():
    mock_msg = MagicMock()
    mock_msg.content = [
        MagicMock(
            text=(
                '{"verba_diaria": 50, "dias": 20, "estrutura": "CBO 2 conjuntos",'
                ' "publico": "SP 25-45", "copy": "Texto aqui", "justificativa": "Razão"}'
            )
        )
    ]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_msg)

    with patch("app.core.analysis.anthropic.AsyncAnthropic", return_value=mock_client):
        briefing = CampaignBriefing(
            produto="Apartamento alto padrão",
            objetivo="leads-whatsapp",
            verba_total=1000,
            dias=20,
            publico_alvo="homens 30-50 SP",
            destino_lead="whatsapp",
            marca="FORTEC",
        )
        result = await generate_campaign_strategy(
            briefing=briefing,
            account_history=None,
            nivel_tecnico="avancado",
            anthropic_api_key="sk-test",
        )
    assert isinstance(result, CampaignStrategy)
    assert result.verba_diaria > 0
