from __future__ import annotations

from app.analysis.schemas import (
    AuditLogOut,
    CreativeOut,
    EvaluateRequest,
    EvaluateResponse,
    RuleResultOut,
    SummaryRequest,
    SummaryResponse,
)


def test_evaluate_request_schema():
    req = EvaluateRequest(act_id="act_123")
    assert req.date_preset == "last_7d"


def test_evaluate_response_schema():
    alert = RuleResultOut(
        severity="vermelho",
        rule_name="gasto_sem_lead",
        action="pausar",
        campaign="Campanha Teste",
        reason="Gastou R$ 150.00 sem gerar lead.",
        should_pause=True,
        meta_entity_id="123456",
    )
    resp = EvaluateResponse(alerts=[alert], total=1)
    assert resp.total == 1
    assert resp.alerts[0].should_pause is True
    assert resp.alerts[0].severity == "vermelho"


def test_summary_request_schema():
    req = SummaryRequest(act_id="act_123", nivel_tecnico="leigo")
    assert req.nivel_tecnico == "leigo"
    assert req.date_preset == "last_7d"


def test_summary_response_schema():
    resp = SummaryResponse(
        resumo="Resumo da análise",
        recomendacoes=["Pausar campanha X", "Trocar criativo Y"],
        acoes=[{"entity_id": "123", "action": "pausar"}],
        kpis={"total_spend": 500.0, "total_leads": 10, "cpl_medio": 50.0},
    )
    assert len(resp.recomendacoes) == 2
    assert resp.kpis["cpl_medio"] == 50.0


def test_creative_out_schema():
    creative = CreativeOut(
        id="c1",
        tipo="image",
        storage_path="user1/acc1/banner.jpg",
        meta_hash=None,
        meta_video_id=None,
    )
    assert creative.tipo == "image"
    assert creative.meta_hash is None


def test_audit_log_out_schema():
    log = AuditLogOut(
        id="a1",
        acao="create_campaign",
        entidade="campaign",
        entidade_id="camp_123",
        criado_em="2026-08-28T10:00:00Z",
    )
    assert log.acao == "create_campaign"
    assert log.entidade_id == "camp_123"
