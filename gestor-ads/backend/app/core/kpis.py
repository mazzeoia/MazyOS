"""KPI aggregator — migrated from campaign_optimizer/core/rules.py summarize_kpis().

Expanded with: melhor/pior campanha, tendencia.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KPISummary:
    total_spend: float
    total_leads: int
    total_clicks: int
    total_impressions: int
    cpl_medio: float
    cpc_medio: float
    ctr_medio: float
    melhor_campanha: str | None
    pior_campanha: str | None
    tendencia: str  # 'subindo' | 'estavel' | 'caindo'


def summarize_kpis(metrics: list[dict]) -> KPISummary:
    """Aggregate metrics for a period."""
    if not metrics:
        return KPISummary(
            total_spend=0,
            total_leads=0,
            total_clicks=0,
            total_impressions=0,
            cpl_medio=0,
            cpc_medio=0,
            ctr_medio=0,
            melhor_campanha=None,
            pior_campanha=None,
            tendencia="estavel",
        )

    total_spend = sum(float(r.get("spend") or 0) for r in metrics)
    total_leads = sum(int(r.get("leads") or 0) for r in metrics)
    total_clicks = sum(int(r.get("clicks") or 0) for r in metrics)
    total_impressions = sum(int(r.get("impressions") or 0) for r in metrics)

    cpl = round(total_spend / total_leads, 2) if total_leads else 0
    cpc = round(total_spend / total_clicks, 2) if total_clicks else 0
    ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions else 0

    # Best / worst campaign by CPL (lower is better, must have leads)
    by_campaign: dict[str, dict] = {}
    for r in metrics:
        name = r.get("campaign", "?")
        if name not in by_campaign:
            by_campaign[name] = {"spend": 0, "leads": 0}
        by_campaign[name]["spend"] += float(r.get("spend") or 0)
        by_campaign[name]["leads"] += int(r.get("leads") or 0)

    campaigns_with_leads = {k: v for k, v in by_campaign.items() if v["leads"] > 0}
    melhor = None
    pior = None
    if campaigns_with_leads:
        melhor = min(
            campaigns_with_leads,
            key=lambda k: campaigns_with_leads[k]["spend"] / campaigns_with_leads[k]["leads"],
        )
        pior = max(
            campaigns_with_leads,
            key=lambda k: campaigns_with_leads[k]["spend"] / campaigns_with_leads[k]["leads"],
        )
    elif by_campaign:
        pior = max(by_campaign, key=lambda k: by_campaign[k]["spend"])

    # Trend: compare first half vs second half by lead rate
    half = len(metrics) // 2
    if half > 0:
        first_leads = sum(int(r.get("leads") or 0) for r in metrics[:half])
        second_leads = sum(int(r.get("leads") or 0) for r in metrics[half:])
        if second_leads > first_leads * 1.2:
            tendencia = "subindo"
        elif first_leads > second_leads * 1.2:
            tendencia = "caindo"
        else:
            tendencia = "estavel"
    else:
        tendencia = "estavel"

    return KPISummary(
        total_spend=round(total_spend, 2),
        total_leads=total_leads,
        total_clicks=total_clicks,
        total_impressions=total_impressions,
        cpl_medio=cpl,
        cpc_medio=cpc,
        ctr_medio=ctr,
        melhor_campanha=melhor,
        pior_campanha=pior,
        tendencia=tendencia,
    )
