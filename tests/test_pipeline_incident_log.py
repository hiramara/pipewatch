"""Tests for PipelineIncidentLog and IncidentLogEntry."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.pipeline_incident_log import IncidentLogEntry, PipelineIncidentLog


def _make_alert(name: str = "pipe_a", level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(pipeline_name=name, level=level, message=f"{name} alert")


@pytest.fixture
def log() -> PipelineIncidentLog:
    return PipelineIncidentLog()


class TestIncidentLogEntry:
    def test_to_dict_keys(self):
        entry = IncidentLogEntry(
            pipeline_name="p",
            alert_level=AlertLevel.CRITICAL,
            message="bad",
            raised_at=datetime.now(timezone.utc),
        )
        keys = entry.to_dict().keys()
        assert "pipeline_name" in keys
        assert "alert_level" in keys
        assert "raised_at" in keys
        assert "resolved_at" in keys
        assert "is_resolved" in keys
        assert "duration_seconds" in keys

    def test_not_resolved_by_default(self):
        entry = IncidentLogEntry(
            pipeline_name="p",
            alert_level=AlertLevel.WARNING,
            message="warn",
            raised_at=datetime.now(timezone.utc),
        )
        assert not entry.is_resolved
        assert entry.duration_seconds is None

    def test_resolve_sets_resolved_at(self):
        entry = IncidentLogEntry(
            pipeline_name="p",
            alert_level=AlertLevel.WARNING,
            message="warn",
            raised_at=datetime.now(timezone.utc),
        )
        entry.resolve()
        assert entry.is_resolved
        assert entry.duration_seconds is not None
        assert entry.duration_seconds >= 0

    def test_repr_contains_pipeline_and_status(self):
        entry = IncidentLogEntry(
            pipeline_name="my_pipe",
            alert_level=AlertLevel.CRITICAL,
            message="x",
            raised_at=datetime.now(timezone.utc),
        )
        r = repr(entry)
        assert "my_pipe" in r
        assert "open" in r


class TestPipelineIncidentLog:
    def test_record_creates_entry(self, log):
        alert = _make_alert()
        entry = log.record(alert)
        assert entry.pipeline_name == "pipe_a"
        assert len(log.all_entries()) == 1

    def test_open_incidents_excludes_resolved(self, log):
        a1 = _make_alert("p1")
        a2 = _make_alert("p2")
        log.record(a1)
        e2 = log.record(a2)
        e2.resolve()
        open_ = log.open_incidents()
        assert len(open_) == 1
        assert open_[0].pipeline_name == "p1"

    def test_resolve_open_resolves_all_for_pipeline(self, log):
        alert = _make_alert("pipe_x")
        log.record(alert)
        log.record(alert)
        resolved = log.resolve_open("pipe_x")
        assert len(resolved) == 2
        assert all(e.is_resolved for e in resolved)

    def test_for_pipeline_filters_correctly(self, log):
        log.record(_make_alert("a"))
        log.record(_make_alert("b"))
        log.record(_make_alert("a"))
        assert len(log.for_pipeline("a")) == 2
        assert len(log.for_pipeline("b")) == 1

    def test_counts_by_pipeline(self, log):
        log.record(_make_alert("x"))
        log.record(_make_alert("x"))
        log.record(_make_alert("y"))
        counts = log.counts_by_pipeline()
        assert counts["x"] == 2
        assert counts["y"] == 1
