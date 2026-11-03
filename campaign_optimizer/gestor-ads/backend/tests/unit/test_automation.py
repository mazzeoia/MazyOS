from __future__ import annotations

from app.core.automation import select_alerts_to_pause
from app.core.rules import RuleResult


def _alert(**overrides) -> RuleResult:
    base = {
        "severity": "vermelho",
        "rule_name": "gasto_sem_lead",
        "action": "pausar",
        "campaign": "Test Campaign",
        "entity_level": "campaign",
        "entity_name": "Test Campaign",
        "reason": "Gastou sem lead.",
        "should_pause": True,
        "meta_entity_id": "c_123",
    }
    base.update(overrides)
    return RuleResult(**base)


def test_selects_should_pause_alerts_with_entity_id():
    alerts = [_alert()]
    assert select_alerts_to_pause(alerts) == alerts


def test_excludes_alerts_not_flagged_should_pause():
    alerts = [_alert(should_pause=False, rule_name="ctr_baixo")]
    assert select_alerts_to_pause(alerts) == []


def test_excludes_alerts_without_meta_entity_id():
    """A should_pause alert with no entity id can't actually be paused."""
    alerts = [_alert(meta_entity_id=None)]
    assert select_alerts_to_pause(alerts) == []


def test_mixed_alerts_keeps_only_actionable_ones():
    keep = _alert(campaign="A")
    drop_no_pause = _alert(campaign="B", should_pause=False)
    drop_no_id = _alert(campaign="C", meta_entity_id=None)
    result = select_alerts_to_pause([keep, drop_no_pause, drop_no_id])
    assert result == [keep]
