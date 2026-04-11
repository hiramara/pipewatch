"""Tests for AuditLog and AuditEvent."""

from datetime import datetime, timezone
import pytest

from pipewatch.core.audit import AuditEvent, AuditEventType, AuditLog


@pytest.fixture
def log() -> AuditLog:
    return AuditLog()


@pytest.fixture
def sample_event() -> AuditEvent:
    return AuditEvent(
        event_type=AuditEventType.STATUS_CHANGE,
        pipeline_id="pipe-1",
        details={"from": "healthy", "to": "failing"},
        actor="scheduler",
    )


class TestAuditEvent:
    def test_to_dict_keys(self, sample_event):
        d = sample_event.to_dict()
        assert set(d.keys()) == {"event_type", "pipeline_id", "timestamp", "details", "actor"}

    def test_to_dict_values(self, sample_event):
        d = sample_event.to_dict()
        assert d["event_type"] == "status_change"
        assert d["pipeline_id"] == "pipe-1"
        assert d["actor"] == "scheduler"

    def test_repr_contains_type_and_pipeline(self, sample_event):
        r = repr(sample_event)
        assert "status_change" in r
        assert "pipe-1" in r

    def test_default_timestamp_is_utc(self, sample_event):
        assert sample_event.timestamp.tzinfo is not None


class TestAuditLog:
    def test_initial_length_is_zero(self, log):
        assert len(log) == 0

    def test_record_increments_length(self, log, sample_event):
        log.record(sample_event)
        assert len(log) == 1

    def test_events_for_filters_by_pipeline(self, log):
        e1 = AuditEvent(AuditEventType.STATUS_CHANGE, "pipe-1")
        e2 = AuditEvent(AuditEventType.STATUS_CHANGE, "pipe-2")
        log.record(e1)
        log.record(e2)
        result = log.events_for("pipe-1")
        assert len(result) == 1
        assert result[0].pipeline_id == "pipe-1"

    def test_events_by_type_filters_correctly(self, log):
        log.record(AuditEvent(AuditEventType.ALERT_RAISED, "pipe-1"))
        log.record(AuditEvent(AuditEventType.STATUS_CHANGE, "pipe-1"))
        result = log.events_by_type(AuditEventType.ALERT_RAISED)
        assert len(result) == 1

    def test_max_events_evicts_oldest(self):
        small_log = AuditLog(max_events=3)
        for i in range(5):
            small_log.record(AuditEvent(AuditEventType.CHECK_EXECUTED, f"pipe-{i}"))
        assert len(small_log) == 3
        ids = [e.pipeline_id for e in small_log.all_events()]
        assert ids == ["pipe-2", "pipe-3", "pipe-4"]

    def test_clear_empties_log(self, log, sample_event):
        log.record(sample_event)
        log.clear()
        assert len(log) == 0
