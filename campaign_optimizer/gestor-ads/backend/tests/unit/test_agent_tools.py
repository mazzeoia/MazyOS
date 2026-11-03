from unittest.mock import AsyncMock

import pytest

from app.agent.tools import (
    ToolContext,
    consultar_metricas,
    aprovar_campanha,
    criar_campanha,
    normalize_objective,
    listar_contas,
    localizacao_por_raio,
    pausar_campanha,
    propor_campanha,
    selecionar_conta,
)
from app.shared.exceptions import DraftValidationError


def _ctx(fake_supabase, **overrides):
    defaults = dict(supabase=fake_supabase, settings=None, user_id="user-1", conversation_id="conv-1", ad_account_id=None)
    defaults.update(overrides)
    return ToolContext(**defaults)


async def test_listar_contas(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec", "external_id": "act_1"},
        {"id": "acc-2", "name": "Marca Imobiliária", "external_id": "act_2"},
    ]
    result = await listar_contas(_ctx(fake_supabase))
    assert len(result["contas"]) == 2
    assert result["contas"][0]["name"] == "Fortec"


async def test_selecionar_conta_by_number(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec", "external_id": "act_1"},
        {"id": "acc-2", "name": "Marca Imobiliária", "external_id": "act_2"},
    ]
    result = await selecionar_conta(_ctx(fake_supabase), conta="2")
    assert result["ad_account_id"] == "acc-2"


async def test_selecionar_conta_ambiguous_raises(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec Imóveis", "external_id": "act_1"},
        {"id": "acc-2", "name": "Fortec Consórcio", "external_id": "act_2"},
    ]
    with pytest.raises(DraftValidationError):
        await selecionar_conta(_ctx(fake_supabase), conta="fortec")


async def test_selecionar_conta_by_name(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec Imóveis", "external_id": "act_1"},
    ]
    result = await selecionar_conta(_ctx(fake_supabase), conta="fortec")
    assert result["ad_account_id"] == "acc-1"


async def test_consultar_metricas(fake_supabase):
    meta_client = AsyncMock()
    meta_client.get_insights.return_value = [
        {"spend": "100", "actions": [{"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "5"}]}
    ]
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await consultar_metricas(ctx, meta_client)
    assert result["total_spend"] == 100.0
    assert result["total_leads"] == 5


async def test_pausar_campanha(fake_supabase):
    meta_client = AsyncMock()
    meta_client.update_status.return_value = {"success": True}
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await pausar_campanha(ctx, meta_client, campanha_id="123")
    meta_client.update_status.assert_called_once_with("123", "PAUSED")
    assert result["status"] == "PAUSED"


async def test_propor_campanha_creates_draft(fake_supabase, monkeypatch):
    async def fake_strategy(briefing, **kwargs):
        from app.core.analysis import CampaignStrategy

        return CampaignStrategy(
            verba_diaria=50.0, dias=20, estrutura="CBO", publico=briefing.publico_alvo,
            copy="copy gerada", justificativa="R$50/dia evita fase de aprendizado longa",
        )

    monkeypatch.setattr("app.agent.tools.generate_campaign_strategy", fake_strategy)
    fake_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "draft-1", "status": "rascunho", "payload": {}}
    ]

    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await propor_campanha(
        ctx, produto="imóvel alto padrão", objetivo="LEAD_GENERATION", verba_total=1000.0,
        dias=20, publico_alvo="Fortaleza, 30-55 anos", destino_lead="whatsapp", marca="Fortec",
    )
    assert result["draft_id"] == "draft-1"
    assert result["justificativa"] == "R$50/dia evita fase de aprendizado longa"


async def test_criar_campanha_requires_approved_draft(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1", "status": "rascunho", "payload": {}
    }
    meta_client = AsyncMock()
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    with pytest.raises(DraftValidationError):
        await criar_campanha(ctx, meta_client, draft_id="draft-1")
    meta_client.create_campaign.assert_not_called()


async def test_criar_campanha_creates_when_approved(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1",
        "status": "aprovado",
        "payload": {"marca": "Fortec", "objetivo": "trafego", "publico": "Fortaleza", "verba_diaria": 50.0},
        "conversation_id": "conv-1",
        "ad_account_id": "acc-1",
    }
    meta_client = AsyncMock()
    meta_client.create_campaign.return_value = {"id": "camp-123"}
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await criar_campanha(ctx, meta_client, draft_id="draft-1")
    assert result["meta_campaign_id"] == "camp-123"
    _, kwargs = meta_client.create_campaign.call_args
    assert kwargs.get("name", "").startswith("[Fortec]")


async def test_criar_campanha_rejects_draft_from_other_conversation(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1",
        "status": "aprovado",
        "payload": {"marca": "Fortec", "objetivo": "trafego", "publico": "Fortaleza", "verba_diaria": 50.0},
        "conversation_id": "conv-OUTRA",
        "ad_account_id": "acc-1",
    }
    meta_client = AsyncMock()
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    with pytest.raises(DraftValidationError):
        await criar_campanha(ctx, meta_client, draft_id="draft-1")
    meta_client.create_campaign.assert_not_called()


def test_localizacao_por_raio():
    result = localizacao_por_raio(latitude=-3.7319, longitude=-38.5267, raio_km=3.0)
    assert result["custom_locations"] == [{"latitude": -3.7319, "longitude": -38.5267, "radius": 3.0, "distance_unit": "kilometer"}]


# --- objective validation (I2) ---


def test_normalize_objective_passes_through_meta_enum():
    assert normalize_objective("OUTCOME_LEADS") == "OUTCOME_LEADS"


def test_normalize_objective_maps_portuguese():
    assert normalize_objective("gerar leads") == "OUTCOME_LEADS"
    assert normalize_objective("tráfego pro site") == "OUTCOME_TRAFFIC"
    assert normalize_objective("vendas no ecommerce") == "OUTCOME_SALES"


def test_normalize_objective_rejects_unknown():
    with pytest.raises(DraftValidationError):
        normalize_objective("virar unicórnio")


# --- propor_campanha guards (I1) ---


async def test_propor_campanha_requires_ad_account(fake_supabase):
    ctx = _ctx(fake_supabase, ad_account_id=None)
    with pytest.raises(DraftValidationError):
        await propor_campanha(
            ctx, produto="curso", objetivo="leads", verba_total=1000, dias=20,
            publico_alvo="Fortaleza", destino_lead="whatsapp", marca="Fortec",
        )


# --- aprovar_campanha (C6) ---


async def test_aprovar_campanha_approves_rascunho(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1", "status": "rascunho", "payload": {}, "conversation_id": "conv-1", "ad_account_id": "acc-1",
    }
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await aprovar_campanha(ctx, draft_id="draft-1")
    assert result == {"draft_id": "draft-1", "status": "aprovado"}
    fake_supabase.table.return_value.update.assert_called_once_with({"status": "aprovado"})


async def test_aprovar_campanha_rejects_other_conversation(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1", "status": "rascunho", "payload": {}, "conversation_id": "conv-OUTRA", "ad_account_id": "acc-1",
    }
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    with pytest.raises(DraftValidationError):
        await aprovar_campanha(ctx, draft_id="draft-1")


async def test_aprovar_campanha_rejects_non_rascunho(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1", "status": "criado", "payload": {}, "conversation_id": "conv-1", "ad_account_id": "acc-1",
    }
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    with pytest.raises(DraftValidationError):
        await aprovar_campanha(ctx, draft_id="draft-1")
