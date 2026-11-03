from __future__ import annotations

from app.core.rules import AccountThresholds, evaluate


def _thresholds(**overrides) -> AccountThresholds:
    defaults = {"target_cpl": 40.0, "waste_limit": 100.0, "min_ctr": 0.8, "max_frequency": 3.0}
    defaults.update(overrides)
    return AccountThresholds(**defaults)


def _row(**overrides) -> dict:
    base = {
        "campaign": "Test Campaign",
        "entity_level": "campaign",
        "entity_name": "Test Campaign",
        "meta_entity_id": "c_123",
        "spend": 0,
        "leads": 0,
        "ctr": 0,
        "cpl": 0,
        "frequency": 0,
        "impressions": 0,
        "effective_status": "ACTIVE",
    }
    base.update(overrides)
    return base


def test_gasto_sem_lead():
    """R$ 150 gastos, 0 leads -> vermelho, pausar."""
    rows = [_row(spend=150, leads=0)]
    results = evaluate(rows, _thresholds())
    red = [r for r in results if r.rule_name == "gasto_sem_lead"]
    assert len(red) == 1
    assert red[0].severity == "vermelho"
    assert red[0].should_pause is True
    assert "150" in red[0].reason


def test_gasto_sem_lead_below_limit():
    """R$ 50 gastos, 0 leads but below waste_limit -> no alert."""
    rows = [_row(spend=50, leads=0)]
    results = evaluate(rows, _thresholds(waste_limit=100))
    assert not any(r.rule_name == "gasto_sem_lead" for r in results)


def test_cpl_acima_meta():
    """CPL R$ 60 when target is R$ 40 (30% margin = 52) -> amarelo."""
    rows = [_row(leads=5, cpl=60)]
    results = evaluate(rows, _thresholds(target_cpl=40))
    yellow = [r for r in results if r.rule_name == "cpl_acima_meta"]
    assert len(yellow) == 1
    assert yellow[0].severity == "amarelo"


def test_cpl_within_margin():
    """CPL R$ 50 when target is R$ 40 (margin at 52) -> no alert."""
    rows = [_row(leads=5, cpl=50)]
    results = evaluate(rows, _thresholds(target_cpl=40))
    assert not any(r.rule_name == "cpl_acima_meta" for r in results)


def test_ctr_baixo():
    """CTR 0.5% below min 0.8% -> amarelo."""
    rows = [_row(ctr=0.5)]
    results = evaluate(rows, _thresholds(min_ctr=0.8))
    low_ctr = [r for r in results if r.rule_name == "ctr_baixo"]
    assert len(low_ctr) == 1
    assert low_ctr[0].action == "trocar_criativo_ou_copy"


def test_frequencia_alta():
    """Frequency 4.5 above max 3.0 -> amarelo."""
    rows = [_row(frequency=4.5)]
    results = evaluate(rows, _thresholds(max_frequency=3.0))
    freq = [r for r in results if r.rule_name == "frequencia_alta"]
    assert len(freq) == 1
    assert freq[0].action == "trocar_criativo_ou_publico"


def test_sem_impressao():
    """Spend > 0 but impressions = 0 -> vermelho."""
    rows = [_row(spend=50, impressions=0)]
    results = evaluate(rows, _thresholds())
    no_imp = [r for r in results if r.rule_name == "sem_impressao"]
    assert len(no_imp) == 1
    assert no_imp[0].severity == "vermelho"


def test_criativo_reprovado():
    """effective_status = DISAPPROVED -> vermelho."""
    rows = [_row(effective_status="DISAPPROVED")]
    results = evaluate(rows, _thresholds())
    disap = [r for r in results if r.rule_name == "criativo_reprovado"]
    assert len(disap) == 1
    assert disap[0].severity == "vermelho"
    assert disap[0].action == "trocar_criativo"


def test_healthy_campaign_no_alerts():
    rows = [_row(spend=80, leads=5, cpl=16, ctr=2.5, frequency=1.2, impressions=5000)]
    results = evaluate(rows, _thresholds())
    assert len(results) == 0


def test_multiple_rules_fire():
    """One row triggers multiple rules."""
    rows = [_row(spend=200, leads=0, ctr=0.3, frequency=5.0, impressions=1000)]
    results = evaluate(rows, _thresholds())
    names = {r.rule_name for r in results}
    assert "gasto_sem_lead" in names
    assert "ctr_baixo" in names
    assert "frequencia_alta" in names


def test_results_have_meta_entity_id():
    rows = [_row(spend=150, leads=0, meta_entity_id="c_999")]
    results = evaluate(rows, _thresholds())
    assert results[0].meta_entity_id == "c_999"


def test_results_sorted_by_severity():
    """vermelho before amarelo."""
    rows = [_row(spend=150, leads=0, ctr=0.5, impressions=1000)]
    results = evaluate(rows, _thresholds())
    severities = [r.severity for r in results]
    assert severities.index("vermelho") < severities.index("amarelo")
