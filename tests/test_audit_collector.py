"""Tests for AuditCollector."""

import pytest
from unittest.mock import MagicMock

from pipewatch.core.audit import AuditLog, AuditEventType
from pipewatch.core.audit_collector import AuditCollector
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.monitor import Monitor


@pytest.fixture
def monitor():
    return Monitor()


@pytest.fixture
def collector():
    return AuditCollector()


def _add_pipeline(monitor: Monitor, pid: str, status: PipelineStatus) -> Pipeline:
    p = Pipeline(id=pid, name=pid)
    p.update_status(status)
    monitor.register_pipeline(p)
    return p


class TestAuditCollector:
    def test_uses_provided_log(self):
        log = AuditLog()
        c = AuditCollector(log=log)
        assert c.log is log

    def test_first_observe_records_registered_events(self, monitor, collector):
        _add_pipeline(monitor, "pipe-a", PipelineStatus.HEALTHY)
        collector.observe(monitor)
        types = [e.event_type for e in collector.log.all_events()]
        assert AuditEventType.PIPELINE_REGISTERED in types

    def test_status_change_recorded(self, monitor, collector):
        p = _add_pipeline(monitor, "pipe-b", PipelineStatus.HEALTHY)
        collector.observe(monitor)
        p.update_status(PipelineStatus.FAILING)
        collector.observe(monitor)
        changes = collector.log.events_by_type(AuditEventType.STATUS_CHANGE)
        assert len(changes) == 1
        assert changes[0].details["from"] == PipelineStatus.HEALTHY.value
        assert changes[0].details["to"] == PipelineStatus.FAILING.value

    def test_no_change_does_not_record_status_event(self, monitor, collector):
        _add_pipeline(monitor, "pipe-c", PipelineStatus.HEALTHY)
        collector.observe(monitor)
        collector.observe(monitor)
        changes = collector.log.events_by_type(AuditEventType.STATUS_CHANGE)
        assert len(changes) == 0

    def test_record_alert_raised(self, collector):
        collector.record_alert_raised("pipe-d", "alert-1", "warning", actor="test")
        events = collector.log.events_by_type(AuditEventType.ALERT_RAISED)
        assert len(events) == 1
        assert events[0].details["alert_id"] == "alert-1"
        assert events[0].actor == "test"

    def test_record_alert_resolved(self, collector):
        collector.record_alert_resolved("pipe-d", "alert-1")
        events = collector.log.events_by_type(AuditEventType.ALERT_RESOLVED)
        assert len(events) == 1
        assert events[0].details["alert_id"] == "alert-1"

    def test_actor_propagated(self, monitor, collector):
        _add_pipeline(monitor, "pipe-e", PipelineStatus.HEALTHY)
        collector.observe(monitor, actor="ci-bot")
        event = collector.log.events_for("pipe-e")[0]
        assert event.actor == "ci-bot"
