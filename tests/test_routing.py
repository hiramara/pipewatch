"""Tests for AlertRouter and RoutingConfig."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.routing import AlertRouter, RoutingRule
from pipewatch.core.routing_config import RoutingConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_channel(name: str):
    ch = MagicMock()
    ch.name = name
    return ch


def _make_alert(
    pipeline: str = "pipe_a",
    level: AlertLevel = AlertLevel.WARNING,
    tags: list | None = None,
) -> Alert:
    alert = Alert(pipeline_name=pipeline, message="test", level=level)
    if tags:
        alert.metadata["tags"] = tags
    return alert


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def router():
    return AlertRouter()


@pytest.fixture
def channel():
    return _make_channel("slack")


# ---------------------------------------------------------------------------
# RoutingRule.matches
# ---------------------------------------------------------------------------

class TestRoutingRuleMatches:
    def test_matches_all_by_default(self, channel):
        rule = RoutingRule(channel=channel)
        assert rule.matches(_make_alert())

    def test_filters_by_pipeline_name(self, channel):
        rule = RoutingRule(channel=channel, pipeline_name="pipe_b")
        assert not rule.matches(_make_alert(pipeline="pipe_a"))
        assert rule.matches(_make_alert(pipeline="pipe_b"))

    def test_filters_by_min_level(self, channel):
        rule = RoutingRule(channel=channel, min_level=AlertLevel.CRITICAL)
        assert not rule.matches(_make_alert(level=AlertLevel.WARNING))
        assert rule.matches(_make_alert(level=AlertLevel.CRITICAL))

    def test_filters_by_tags(self, channel):
        rule = RoutingRule(channel=channel, tags=["finance"])
        assert not rule.matches(_make_alert(tags=["ops"]))
        assert rule.matches(_make_alert(tags=["finance", "ops"]))

    def test_to_dict_keys(self, channel):
        rule = RoutingRule(channel=channel, pipeline_name="p", min_level=AlertLevel.WARNING)
        d = rule.to_dict()
        assert {"channel", "pipeline_name", "min_level", "tags"} == set(d.keys())


# ---------------------------------------------------------------------------
# AlertRouter
# ---------------------------------------------------------------------------

class TestAlertRouter:
    def test_no_rules_returns_empty(self, router):
        alert = _make_alert()
        assert router.route(alert) == []

    def test_matching_rule_sends_and_returns_name(self, router, channel):
        rule = RoutingRule(channel=channel)
        router.add_rule(rule)
        sent = router.route(_make_alert())
        assert sent == ["slack"]
        channel.send.assert_called_once()

    def test_non_matching_rule_skipped(self, router, channel):
        rule = RoutingRule(channel=channel, pipeline_name="other")
        router.add_rule(rule)
        sent = router.route(_make_alert(pipeline="pipe_a"))
        assert sent == []

    def test_remove_rule(self, router, channel):
        rule = RoutingRule(channel=channel)
        router.add_rule(rule)
        router.remove_rule(rule)
        assert router.route(_make_alert()) == []

    def test_history_recorded(self, router, channel):
        rule = RoutingRule(channel=channel)
        router.add_rule(rule)
        alert = _make_alert()
        router.route(alert)
        assert len(router.history) == 1
        assert router.history[0][1] == "slack"

    def test_route_all(self, router, channel):
        rule = RoutingRule(channel=channel)
        router.add_rule(rule)
        alerts = [_make_alert(), _make_alert(pipeline="pipe_b")]
        result = router.route_all(alerts)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# RoutingConfig
# ---------------------------------------------------------------------------

class TestRoutingConfig:
    def test_add_and_get(self):
        ch = _make_channel("pagerduty")
        cfg = RoutingConfig()
        cfg.add("critical-only", ch, min_level=AlertLevel.CRITICAL)
        rule = cfg.get("critical-only")
        assert rule.min_level == AlertLevel.CRITICAL

    def test_duplicate_name_raises(self):
        ch = _make_channel("email")
        cfg = RoutingConfig()
        cfg.add("rule1", ch)
        with pytest.raises(ValueError, match="already registered"):
            cfg.add("rule1", ch)

    def test_remove_rule(self):
        ch = _make_channel("teams")
        cfg = RoutingConfig()
        cfg.add("r", ch)
        cfg.remove("r")
        assert "r" not in cfg.names

    def test_remove_unknown_raises(self):
        cfg = RoutingConfig()
        with pytest.raises(KeyError):
            cfg.remove("nonexistent")

    def test_to_dicts_contains_name(self):
        ch = _make_channel("slack")
        cfg = RoutingConfig()
        cfg.add("my-rule", ch)
        dicts = cfg.to_dicts()
        assert dicts[0]["name"] == "my-rule"

    def test_router_routes_via_config(self):
        ch = _make_channel("slack")
        cfg = RoutingConfig()
        cfg.add("all", ch)
        sent = cfg.router.route(_make_alert())
        assert "slack" in sent
