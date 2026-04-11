"""Tests for EscalationHandler."""
import pytest
from unittest.mock import MagicMock

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.escalation import EscalationPolicy
from pipewatch.core.escalation_handler import EscalationHandler


def _make_alert(pid="pipe-1", level=AlertLevel.WARNING, msg="issue"):
    return Alert(pipeline_id=pid, message=msg, level=level)


@pytest.fixture
def mock_monitor():
    return MagicMock()


@pytest.fixture
def handler(mock_monitor):
    policy = EscalationPolicy(warning_to_critical=2, cooldown_seconds=60)
    return EscalationHandler(mock_monitor, policy=policy)


class TestEscalationHandler:
    def test_no_alerts_returns_empty(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = []
        assert handler.process() == []

    def test_single_warning_not_yet_escalated(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = [_make_alert()]
        alerts = handler.process()
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING

    def test_escalation_after_threshold_breaches(self, handler, mock_monitor):
        alert = _make_alert()
        mock_monitor.evaluate.return_value = [alert]
        handler.process()  # count -> 1
        result = handler.process()  # count -> 2 >= threshold
        assert result[0].level == AlertLevel.CRITICAL

    def test_recovery_clears_counter(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = [_make_alert()]
        handler.process()
        handler.process()  # escalated
        # Simulate recovery: no alerts
        mock_monitor.evaluate.return_value = []
        handler.manager.breach_count("pipe-1") == 0

    def test_critical_alert_passes_through_unchanged(self, handler, mock_monitor):
        alert = _make_alert(level=AlertLevel.CRITICAL, msg="down")
        mock_monitor.evaluate.return_value = [alert]
        result = handler.process()
        assert result[0].level == AlertLevel.CRITICAL
        assert not result[0].message.startswith("[ESCALATED]")

    def test_multiple_pipelines_independent(self, handler, mock_monitor):
        a1 = _make_alert(pid="pipe-A")
        a2 = _make_alert(pid="pipe-B")
        mock_monitor.evaluate.return_value = [a1, a2]
        handler.process()  # both count -> 1
        result = handler.process()  # both count -> 2 >= threshold
        levels = {r.pipeline_id: r.level for r in result}
        assert levels["pipe-A"] == AlertLevel.CRITICAL
        assert levels["pipe-B"] == AlertLevel.CRITICAL
