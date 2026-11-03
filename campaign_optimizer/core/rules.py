"""Rule engine for daily campaign optimization."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class RuleResult:
    severity: str
    rule_name: str
    action: str
    platform: str
    campaign: str
    entity_level: str
    entity_name: str
    reason: str
    should_pause: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_rows(rows: Iterable[dict], client: dict, allow_pause: bool = True) -> list[RuleResult]:
    results: list[RuleResult] = []
    waste_limit = float(client.get("waste_limit") or 100)
    target_cpl = float(client.get("target_cpl") or 0)
    min_ctr = float(client.get("min_ctr") or 0.8)
    max_frequency = float(client.get("max_frequency") or 3.0)

    for row in rows:
        spend = float(row.get("spend") or 0)
        leads = int(row.get("leads") or 0)
        ctr = float(row.get("ctr") or 0)
        cpl = float(row.get("cpl") or 0)
        frequency = float(row.get("frequency") or 0)
        platform = row.get("platform", "unknown")
        campaign = row.get("campaign", "Campanha sem nome")
        entity_name = row.get("ad_name") or row.get("ad_group") or campaign
        entity_level = "ad" if row.get("ad_name") else "ad_group" if row.get("ad_group") else "campaign"

        if spend >= waste_limit and leads == 0:
            results.append(
                RuleResult(
                    severity="vermelho",
                    rule_name="gasto_sem_lead",
                    action="pausar" if allow_pause else "revisar",
                    platform=platform,
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    should_pause=allow_pause,
                    reason=f"Gastou R$ {spend:.2f} sem gerar lead. Limite configurado: R$ {waste_limit:.2f}.",
                )
            )

        if target_cpl > 0 and leads > 0 and cpl > target_cpl:
            results.append(
                RuleResult(
                    severity="amarelo",
                    rule_name="cpl_acima_da_meta",
                    action="revisar",
                    platform=platform,
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"CPL em R$ {cpl:.2f}, acima da meta de R$ {target_cpl:.2f}.",
                )
            )

        if ctr > 0 and ctr < min_ctr:
            results.append(
                RuleResult(
                    severity="amarelo",
                    rule_name="ctr_baixo",
                    action="trocar_criativo_ou_copy",
                    platform=platform,
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"CTR em {ctr:.2f}%, abaixo do minimo de {min_ctr:.2f}%.",
                )
            )

        if platform == "meta_ads" and frequency > max_frequency:
            results.append(
                RuleResult(
                    severity="amarelo",
                    rule_name="frequencia_alta",
                    action="trocar_criativo_ou_publico",
                    platform=platform,
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"Frequencia em {frequency:.2f}, acima do limite de {max_frequency:.2f}.",
                )
            )

    return results


def summarize_kpis(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    spend = sum(float(r.get("spend") or 0) for r in rows)
    leads = sum(int(r.get("leads") or 0) for r in rows)
    clicks = sum(int(r.get("clicks") or 0) for r in rows)
    impressions = sum(int(r.get("impressions") or 0) for r in rows)
    return {
        "spend": round(spend, 2),
        "leads": leads,
        "clicks": clicks,
        "impressions": impressions,
        "cpl": round(spend / leads, 2) if leads else 0,
        "cpc": round(spend / clicks, 2) if clicks else 0,
        "ctr": round(clicks / impressions * 100, 2) if impressions else 0,
    }
