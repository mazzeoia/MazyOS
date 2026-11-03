from __future__ import annotations

from app.core.kpis import summarize_kpis


def _row(campaign="Camp", spend=0, leads=0, clicks=0, impressions=0, **kw):
    return {"campaign": campaign, "spend": spend, "leads": leads, "clicks": clicks, "impressions": impressions, **kw}


def test_basic_aggregation():
    rows = [
        _row(spend=100, leads=5, clicks=50, impressions=1000),
        _row(spend=200, leads=10, clicks=100, impressions=2000),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.total_spend == 300
    assert kpi.total_leads == 15
    assert kpi.total_clicks == 150
    assert kpi.total_impressions == 3000
    assert kpi.cpl_medio == 20.0
    assert kpi.cpc_medio == 2.0
    assert kpi.ctr_medio == 5.0


def test_zero_leads_cpl_is_zero():
    rows = [_row(spend=100, leads=0, clicks=10, impressions=500)]
    kpi = summarize_kpis(rows)
    assert kpi.cpl_medio == 0


def test_empty_rows():
    kpi = summarize_kpis([])
    assert kpi.total_spend == 0
    assert kpi.total_leads == 0
    assert kpi.melhor_campanha is None
    assert kpi.pior_campanha is None
    assert kpi.tendencia == "estavel"


def test_melhor_pior_campanha():
    rows = [
        _row(campaign="Best", spend=100, leads=10, clicks=50, impressions=1000),
        _row(campaign="Worst", spend=200, leads=2, clicks=20, impressions=500),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.melhor_campanha == "Best"
    assert kpi.pior_campanha == "Worst"


def test_tendencia_subindo():
    """First half worse than second half -> subindo."""
    rows = [
        _row(campaign="A", spend=100, leads=2, clicks=20, impressions=500, date="2026-08-20"),
        _row(campaign="A", spend=100, leads=8, clicks=80, impressions=500, date="2026-08-25"),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.tendencia == "subindo"


def test_tendencia_caindo():
    """First half better than second half -> caindo."""
    rows = [
        _row(campaign="A", spend=100, leads=10, clicks=80, impressions=500, date="2026-08-20"),
        _row(campaign="A", spend=100, leads=1, clicks=5, impressions=500, date="2026-08-25"),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.tendencia == "caindo"
