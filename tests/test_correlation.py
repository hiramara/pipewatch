"""Tests for CorrelationEngine and Incident."""
from datetime import datetime, timedelta

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.correlation import CorrelationEngine, Incident


def _alert(pipeline: str = "pipe_a", check: str = "row_count") -> Alert:
    return Alert(
        pipeline_name=pipeline,
        check_name=check,
        level=AlertLevel.WARNING,
        message="test alert",
    )


# ---------------------------------------------------------------------------
# Incident unit tests
# ---------------------------------------------------------------------------

class TestIncident:
    def test_empty_incident_level_is_info(self):
        inc = Incident()
        assert inc.level == AlertLevel.INFO

    def test_level_reflects_highest_alert(self):
        inc = Incident(alerts=[_alert()])
        inc.alerts.append(
            Alert("pipe_a", "latency", AlertLevel.CRITICAL, "bad")
        )
        assert inc.level == AlertLevel.CRITICAL

    def test_pipeline_names_deduplicated(self):
        inc = Incident(alerts=[_alert("pipe_a"), _alert("pipe_a"), _alert("pipe_b")])
        assert sorted(inc.pipeline_names) == ["pipe_a", "pipe_b"]

    def test_resolve_marks_incident_and_alerts(self):
        a = _alert()
        inc = Incident(alerts=[a])
        inc.resolve()
        assert inc.resolved is True
        assert a.resolved is True

    def test_to_dict_keys(self):
        inc = Incident(alerts=[_alert()])
        d = inc.to_dict()
        for key in ("incident_id", "resolved", "level", "pipeline_names", "alert_count", "created_at"):
            assert key in d

    def test_to_dict_alert_count(self):
        inc = Incident(alerts=[_alert(), _alert("pipe_b")])
        assert inc.to_dict()["alert_count"] == 2


# ---------------------------------------------------------------------------
# CorrelationEngine tests
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> CorrelationEngine:
    return CorrelationEngine(window_seconds=300)


class TestCorrelationEngine:
    def test_first_alert_creates_incident(self, engine):
        inc = engine.ingest(_alert())
        assert len(engine.all_incidents()) == 1
        assert len(inc.alerts) == 1

    def test_same_pipeline_grouped(self, engine):
        inc1 = engine.ingest(_alert("pipe_a", "check_1"))
        inc2 = engine.ingest(_alert("pipe_a", "check_2"))
        assert inc1.incident_id == inc2.incident_id
        assert len(inc1.alerts) == 2

    def test_different_pipeline_separate_incident(self, engine):
        engine.ingest(_alert("pipe_a"))
        engine.ingest(_alert("pipe_b"))
        assert len(engine.all_incidents()) == 2

    def test_open_incidents_excludes_resolved(self, engine):
        inc = engine.ingest(_alert())
        inc.resolve()
        assert engine.open_incidents() == []

    def test_expired_window_creates_new_incident(self):
        eng = CorrelationEngine(window_seconds=1)
        inc1 = eng.ingest(_alert("pipe_a"))
        # Manually age the incident
        inc1.created_at = datetime.utcnow() - timedelta(seconds=10)
        inc2 = eng.ingest(_alert("pipe_a"))
        assert inc1.incident_id != inc2.incident_id

    def test_resolve_for_pipeline_returns_count(self, engine):
        engine.ingest(_alert("pipe_a"))
        engine.ingest(_alert("pipe_a"))
        count = engine.resolve_for_pipeline("pipe_a")
        assert count == 1  # both alerts were in one incident

    def test_resolve_for_unknown_pipeline_returns_zero(self, engine):
        engine.ingest(_alert("pipe_a"))
        assert engine.resolve_for_pipeline("pipe_z") == 0
