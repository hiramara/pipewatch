"""Tests for pipeline SLA evaluation and configuration."""
import pytest

from pipewatch.core.pipeline_sla import SLABreach, SLAEvaluator, SLARule
from pipewatch.core.sla_config import SLAConfig
from pipewatch.core.alert import AlertLevel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def evaluator() -> SLAEvaluator:
    ev = SLAEvaluator()
    ev.add_rule(SLARule(pipeline_name="orders", max_duration_seconds=60.0, description="Orders ETL"))
    return ev


@pytest.fixture
def config() -> SLAConfig:
    cfg = SLAConfig()
    cfg.add("orders", 60.0, "Orders ETL")
    cfg.add("inventory", 120.0)
    return cfg


# ---------------------------------------------------------------------------
# SLARule
# ---------------------------------------------------------------------------

class TestSLARule:
    def test_breached_when_over_limit(self):
        rule = SLARule(pipeline_name="p", max_duration_seconds=30.0)
        assert rule.is_breached(31.0) is True

    def test_not_breached_at_limit(self):
        rule = SLARule(pipeline_name="p", max_duration_seconds=30.0)
        assert rule.is_breached(30.0) is False

    def test_to_dict_keys(self):
        rule = SLARule(pipeline_name="p", max_duration_seconds=30.0, description="desc")
        d = rule.to_dict()
        assert set(d.keys()) == {"pipeline_name", "max_duration_seconds", "description"}

    def test_from_dict_roundtrip(self):
        rule = SLARule(pipeline_name="p", max_duration_seconds=45.0, description="test")
        restored = SLARule.from_dict(rule.to_dict())
        assert restored.pipeline_name == rule.pipeline_name
        assert restored.max_duration_seconds == rule.max_duration_seconds
        assert restored.description == rule.description


# ---------------------------------------------------------------------------
# SLABreach
# ---------------------------------------------------------------------------

class TestSLABreach:
    def test_to_alert_is_warning(self):
        rule = SLARule(pipeline_name="orders", max_duration_seconds=60.0)
        breach = SLABreach(pipeline_name="orders", rule=rule, actual_duration_seconds=75.0)
        alert = breach.to_alert()
        assert alert.level == AlertLevel.WARNING
        assert alert.pipeline_name == "orders"

    def test_to_alert_message_contains_excess(self):
        rule = SLARule(pipeline_name="orders", max_duration_seconds=60.0)
        breach = SLABreach(pipeline_name="orders", rule=rule, actual_duration_seconds=75.0)
        assert "+15.0s" in breach.to_alert().message

    def test_to_dict_excess_computed(self):
        rule = SLARule(pipeline_name="orders", max_duration_seconds=60.0)
        breach = SLABreach(pipeline_name="orders", rule=rule, actual_duration_seconds=80.0)
        d = breach.to_dict()
        assert d["excess_seconds"] == pytest.approx(20.0)
        assert "detected_at" in d


# ---------------------------------------------------------------------------
# SLAEvaluator
# ---------------------------------------------------------------------------

class TestSLAEvaluator:
    def test_no_rule_returns_none(self, evaluator):
        assert evaluator.evaluate("unknown", 999.0) is None

    def test_within_sla_returns_none(self, evaluator):
        assert evaluator.evaluate("orders", 59.0) is None

    def test_breach_returns_sla_breach(self, evaluator):
        result = evaluator.evaluate("orders", 90.0)
        assert isinstance(result, SLABreach)
        assert result.pipeline_name == "orders"

    def test_remove_rule_stops_evaluation(self, evaluator):
        evaluator.remove_rule("orders")
        assert evaluator.evaluate("orders", 999.0) is None

    def test_rules_returns_list(self, evaluator):
        assert len(evaluator.rules()) == 1


# ---------------------------------------------------------------------------
# SLAConfig
# ---------------------------------------------------------------------------

class TestSLAConfig:
    def test_add_and_get(self, config):
        rule = config.get("orders")
        assert rule is not None
        assert rule.max_duration_seconds == 60.0

    def test_add_duplicate_raises(self, config):
        with pytest.raises(ValueError):
            config.add("orders", 30.0)

    def test_update_replaces_rule(self, config):
        config.update("orders", 90.0)
        assert config.get("orders").max_duration_seconds == 90.0

    def test_update_unknown_raises(self, config):
        with pytest.raises(KeyError):
            config.update("nonexistent", 10.0)

    def test_remove(self, config):
        config.remove("orders")
        assert config.get("orders") is None

    def test_len(self, config):
        assert len(config) == 2

    def test_iter(self, config):
        names = {r.pipeline_name for r in config}
        assert names == {"orders", "inventory"}
