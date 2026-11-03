"""Rule engine for campaign optimization.

Migrated from campaign_optimizer/core/rules.py and expanded with 2 new rules.
Thresholds come from ad_accounts (database), not hardcoded dicts.
"""

from __future__ import annotations

from dataclasses import dataclass

_SEVERITY_ORDER = {"vermelho": 0, "amarelo": 1, "verde": 2}


@dataclass
class RuleResult:
    severity: str
    rule_name: str
    action: str
    campaign: str
    entity_level: str
    entity_name: str
    reason: str
    should_pause: bool = False
    meta_entity_id: str | None = None


@dataclass
class AccountThresholds:
    """Per-account thresholds — stored in ad_accounts table."""

    target_cpl: float = 0.0
    waste_limit: float = 100.0
    min_ctr: float = 0.8
    max_frequency: float = 3.0


def evaluate(metrics: list[dict], thresholds: AccountThresholds) -> list[RuleResult]:
    """Run all rules against metrics and return results sorted by severity (vermelho first)."""
    results: list[RuleResult] = []

    for row in metrics:
        spend = float(row.get("spend") or 0)
        leads = int(row.get("leads") or 0)
        ctr = float(row.get("ctr") or 0)
        cpl = float(row.get("cpl") or 0)
        frequency = float(row.get("frequency") or 0)
        impressions = int(row.get("impressions") or 0)
        effective_status = str(row.get("effective_status", "")).upper()

        campaign = row.get("campaign", "Campanha sem nome")
        entity_name = row.get("entity_name", campaign)
        entity_level = row.get("entity_level", "campaign")
        meta_id = row.get("meta_entity_id")

        # Rule 1: gasto sem lead (migrated)
        if spend >= thresholds.waste_limit and leads == 0:
            results.append(
                RuleResult(
                    severity="vermelho",
                    rule_name="gasto_sem_lead",
                    action="pausar",
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"Gastou R$ {spend:.2f} sem gerar lead. Limite: R$ {thresholds.waste_limit:.2f}.",
                    should_pause=True,
                    meta_entity_id=meta_id,
                )
            )

        # Rule 2: CPL acima da meta (migrated, with 30% margin)
        margin = thresholds.target_cpl * 1.3
        if thresholds.target_cpl > 0 and leads > 0 and cpl > margin:
            results.append(
                RuleResult(
                    severity="amarelo",
                    rule_name="cpl_acima_meta",
                    action="revisar",
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"CPL em R$ {cpl:.2f}, acima de R$ {margin:.2f} (meta + 30%).",
                    meta_entity_id=meta_id,
                )
            )

        # Rule 3: CTR baixo (migrated)
        if ctr > 0 and ctr < thresholds.min_ctr:
            results.append(
                RuleResult(
                    severity="amarelo",
                    rule_name="ctr_baixo",
                    action="trocar_criativo_ou_copy",
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"CTR em {ctr:.2f}%, abaixo do mínimo de {thresholds.min_ctr:.2f}%.",
                    meta_entity_id=meta_id,
                )
            )

        # Rule 4: Frequência alta (migrated)
        if frequency > thresholds.max_frequency:
            results.append(
                RuleResult(
                    severity="amarelo",
                    rule_name="frequencia_alta",
                    action="trocar_criativo_ou_publico",
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"Frequência em {frequency:.2f}, acima do limite de {thresholds.max_frequency:.2f}.",
                    meta_entity_id=meta_id,
                )
            )

        # Rule 5: Sem impressão (new)
        if spend > 0 and impressions == 0:
            results.append(
                RuleResult(
                    severity="vermelho",
                    rule_name="sem_impressao",
                    action="revisar_conta",
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason=f"Gastou R$ {spend:.2f} mas registrou 0 impressões. Verificar conta/campanha.",
                    meta_entity_id=meta_id,
                )
            )

        # Rule 6: Criativo reprovado (new)
        if effective_status == "DISAPPROVED":
            results.append(
                RuleResult(
                    severity="vermelho",
                    rule_name="criativo_reprovado",
                    action="trocar_criativo",
                    campaign=campaign,
                    entity_level=entity_level,
                    entity_name=entity_name,
                    reason="Criativo reprovado pela Meta. Substitua para a campanha voltar a rodar.",
                    meta_entity_id=meta_id,
                )
            )

    results.sort(key=lambda r: _SEVERITY_ORDER.get(r.severity, 99))
    return results
