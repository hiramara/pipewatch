"""Tests for RateLimiter and RateLimitFilter."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.rate_limiter import RateLimiter, RateLimitRule
from pipewatch.core.rate_limit_filter import RateLimitFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_alert(pipeline: str = "pipe_a", level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(pipeline_name=pipeline, message="test alert", level=level)


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter()


@pytest.fixture
def mock_channel():
    ch = MagicMock()
    ch.send = MagicMock()
    return ch


@pytest.fixture
def rate_filter(mock_channel, limiter):
    return RateLimitFilter(channel=mock_channel, limiter=limiter)


# ---------------------------------------------------------------------------
# RateLimitRule
# ---------------------------------------------------------------------------

class TestRateLimitRule:
    def test_defaults(self):
        rule = RateLimitRule()
        assert rule.max_alerts == 5
        assert rule.window_seconds == 60

    def test_to_dict(self):
        rule = RateLimitRule(max_alerts=3, window_seconds=30)
        d = rule.to_dict()
        assert d["max_alerts"] == 3
        assert d["window_seconds"] == 30

    def test_from_dict_roundtrip(self):
        rule = RateLimitRule(max_alerts=2, window_seconds=10)
        restored = RateLimitRule.from_dict(rule.to_dict())
        assert restored.max_alerts == rule.max_alerts
        assert restored.window_seconds == rule.window_seconds


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def test_allows_up_to_max(self, limiter):
        limiter.set_rule("pipe", RateLimitRule(max_alerts=3, window_seconds=60))
        now = datetime.utcnow()
        assert limiter.is_allowed("pipe", now) is True
        assert limiter.is_allowed("pipe", now) is True
        assert limiter.is_allowed("pipe", now) is True
        assert limiter.is_allowed("pipe", now) is False

    def test_window_resets_after_expiry(self, limiter):
        limiter.set_rule("pipe", RateLimitRule(max_alerts=1, window_seconds=10))
        now = datetime.utcnow()
        assert limiter.is_allowed("pipe", now) is True
        assert limiter.is_allowed("pipe", now) is False
        future = now + timedelta(seconds=11)
        assert limiter.is_allowed("pipe", future) is True

    def test_current_count_returns_zero_for_unknown(self, limiter):
        assert limiter.current_count("unknown") == 0

    def test_reset_clears_window(self, limiter):
        limiter.set_rule("pipe", RateLimitRule(max_alerts=1, window_seconds=60))
        now = datetime.utcnow()
        limiter.is_allowed("pipe", now)
        limiter.reset("pipe")
        assert limiter.is_allowed("pipe", now) is True

    def test_uses_default_rule_when_none_set(self, limiter):
        now = datetime.utcnow()
        for _ in range(5):
            assert limiter.is_allowed("pipe", now) is True
        assert limiter.is_allowed("pipe", now) is False


# ---------------------------------------------------------------------------
# RateLimitFilter
# ---------------------------------------------------------------------------

class TestRateLimitFilter:
    def test_sends_within_limit(self, rate_filter, mock_channel, limiter):
        limiter.set_rule("pipe_a", RateLimitRule(max_alerts=2, window_seconds=60))
        alert = _make_alert()
        assert rate_filter.send(alert) is True
        mock_channel.send.assert_called_once_with(alert)

    def test_suppresses_over_limit(self, rate_filter, mock_channel, limiter):
        limiter.set_rule("pipe_a", RateLimitRule(max_alerts=1, window_seconds=60))
        a1 = _make_alert()
        a2 = _make_alert()
        rate_filter.send(a1)
        result = rate_filter.send(a2)
        assert result is False
        assert a2 in rate_filter.suppressed

    def test_clear_suppressed(self, rate_filter, limiter):
        limiter.set_rule("pipe_a", RateLimitRule(max_alerts=0, window_seconds=60))
        rate_filter.send(_make_alert())
        assert len(rate_filter.suppressed) == 1
        rate_filter.clear_suppressed()
        assert len(rate_filter.suppressed) == 0

    def test_reset_pipeline_clears_its_suppressions(self, rate_filter, limiter):
        limiter.set_rule("pipe_a", RateLimitRule(max_alerts=0, window_seconds=60))
        rate_filter.send(_make_alert("pipe_a"))
        rate_filter.send(_make_alert("pipe_b"))
        rate_filter.reset_pipeline("pipe_a")
        names = [a.pipeline_name for a in rate_filter.suppressed]
        assert "pipe_a" not in names
