"""Tests for pipewatch.core.alert module."""

import pytest
from datetime import datetime

from pipewatch.core.alert import Alert, AlertLevel, AlertManager


class TestAlert:
    def test_alert_defaults(self):
        alert = Alert(pipeline_id="pipe-1", message="Latency exceeded threshold")
        assert alert.pipeline_id == "pipe-1"
        assert alert.message == "Latency exceeded threshold"
        assert alert.level == AlertLevel.WARNING
        assert alert.check_name is None
        assert alert.resolved is False
        assert isinstance(alert.triggered_at, datetime)

    def test_alert_resolve(self):
        alert = Alert(pipeline_id="pipe-1", message="Row count mismatch", level=AlertLevel.CRITICAL)
        assert not alert.resolved
        alert.resolve()
        assert alert.resolved

    def test_alert_to_dict(self):
        alert = Alert(
            pipeline_id="pipe-2",
            message="Missing data",
            level=AlertLevel.INFO,
            check_name="null_check",
        )
        d = alert.to_dict()
        assert d["pipeline_id"] == "pipe-2"
        assert d["message"] == "Missing data"
        assert d["level"] == "info"
        assert d["check_name"] == "null_check"
        assert d["resolved"] is False
        assert "triggered_at" in d

    def test_alert_repr_active(self):
        alert = Alert(pipeline_id="pipe-3", message="Test", level=AlertLevel.CRITICAL)
        assert "ACTIVE" in repr(alert)
        assert "CRITICAL" in repr(alert)

    def test_alert_repr_resolved(self):
        alert = Alert(pipeline_id="pipe-3", message="Test")
        alert.resolve()
        assert "RESOLVED" in repr(alert)


class TestAlertManager:
    def _make_manager_with_alerts(self) -> AlertManager:
        manager = AlertManager()
        manager.trigger(Alert(pipeline_id="pipe-1", message="Warn A", level=AlertLevel.WARNING))
        manager.trigger(Alert(pipeline_id="pipe-1", message="Crit B", level=AlertLevel.CRITICAL))
        manager.trigger(Alert(pipeline_id="pipe-2", message="Info C", level=AlertLevel.INFO))
        return manager

    def test_trigger_and_all_alerts(self):
        manager = self._make_manager_with_alerts()
        assert len(manager.all_alerts()) == 3

    def test_active_alerts_all(self):
        manager = self._make_manager_with_alerts()
        assert len(manager.active_alerts()) == 3

    def test_active_alerts_filtered_by_pipeline(self):
        manager = self._make_manager_with_alerts()
        assert len(manager.active_alerts(pipeline_id="pipe-1")) == 2
        assert len(manager.active_alerts(pipeline_id="pipe-2")) == 1

    def test_resolve_all_for_pipeline(self):
        manager = self._make_manager_with_alerts()
        resolved_count = manager.resolve_all("pipe-1")
        assert resolved_count == 2
        assert len(manager.active_alerts(pipeline_id="pipe-1")) == 0
        assert len(manager.active_alerts(pipeline_id="pipe-2")) == 1

    def test_resolve_all_returns_zero_when_none_active(self):
        manager = AlertManager()
        assert manager.resolve_all("nonexistent") == 0

    def test_summary(self):
        manager = self._make_manager_with_alerts()
        summary = manager.summary()
        assert summary["warning"] == 1
        assert summary["critical"] == 1
        assert summary["info"] == 1

    def test_summary_excludes_resolved(self):
        manager = self._make_manager_with_alerts()
        manager.resolve_all("pipe-1")
        summary = manager.summary()
        assert summary["warning"] == 0
        assert summary["critical"] == 0
        assert summary["info"] == 1
