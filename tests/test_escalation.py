"""Tests for EscalationPolicy and EscalationManager."""
import pytest
from datetime import datetime, timezone, timedelta

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.escalation import EscalationManager, EscalationPolicy


@pytest.fixture
def policy():
    return EscalationPolicy(warning_to_critical=3, cooldown_seconds=60)


@pytest.fixture
def manager(policy):
    return EscalationManager(policy)


def _warning(pipeline_id="pipe-1"):
    return Alert(pipeline_id=pipeline_id, message="slow", level=AlertLevel.WARNING)


def _critical(pipeline_id="pipe-1"):
    return Alert(pipeline_id=pipeline_id, message="down", level=AlertLevel.CRITICAL)


class TestEscalationPolicy:
    def test_defaults(self):
        p = EscalationPolicy()
        assert p.warning_to_critical == 3
        assert p.cooldown_seconds == 300

    def test_to_dict_roundtrip(self):
        p = EscalationPolicy(warning_to_critical=5, cooldown_seconds=120)
        p2 = EscalationPolicy.from_dict(p.to_dict())
        assert p2.warning_to_critical == 5
        assert p2.cooldown_seconds == 120


class TestEscalationManager:
    def test_initial_count_is_zero(self, manager):
        assert manager.breach_count("pipe-1") == 0

    def test_record_breach_increments(self, manager):
        manager.record_breach("pipe-1")
        manager.record_breach("pipe-1")
        assert manager.breach_count("pipe-1") == 2

    def test_no_escalation_below_threshold(self, manager):
        manager.record_breach("pipe-1")
        manager.record_breach("pipe-1")  # count == 2, threshold == 3
        alert = _warning()
        result = manager.escalate(alert)
        assert result.level == AlertLevel.WARNING

    def test_escalation_at_threshold(self, manager):
        for _ in range(3):
            manager.record_breach("pipe-1")
        alert = _warning()
        result = manager.escalate(alert)
        assert result.level == AlertLevel.CRITICAL
        assert result.message.startswith("[ESCALATED]")

    def test_critical_alert_not_modified(self, manager):
        for _ in range(5):
            manager.record_breach("pipe-1")
        alert = _critical()
        result = manager.escalate(alert)
        assert result.level == AlertLevel.CRITICAL
        assert not result.message.startswith("[ESCALATED]")

    def test_clear_resets_counter(self, manager):
        manager.record_breach("pipe-1")
        manager.clear("pipe-1")
        assert manager.breach_count("pipe-1") == 0

    def test_cooldown_resets_counter(self, manager):
        manager.record_breach("pipe-1")
        # Manually backdate last_seen beyond cooldown
        counter = manager._counters["pipe-1"]
        counter.last_seen = datetime.now(timezone.utc) - timedelta(seconds=120)
        manager.record_breach("pipe-1")  # should reset then increment -> count == 1
        assert manager.breach_count("pipe-1") == 1

    def test_independent_pipelines(self, manager):
        for _ in range(3):
            manager.record_breach("pipe-A")
        manager.record_breach("pipe-B")
        assert manager.breach_count("pipe-A") == 3
        assert manager.breach_count("pipe-B") == 1
