"""Tests for BaselineManager and BaselineAlerter."""
import pytest
from unittest.mock import MagicMock

from pipewatch.core.baseline_manager import BaselineManager
from pipewatch.core.baseline_alert import BaselineAlerter
from pipewatch.core.alert import AlertLevel


def _make_summary(name: str, score: float):
    s = MagicMock()
    s.pipeline_name = name
    s.health_score = score
    return s


def _make_report(*summaries):
    r = MagicMock()
    r.pipelines = list(summaries)
    return r


@pytest.fixture
def manager():
    return BaselineManager()


class TestBaselineManager:
    def test_ingest_creates_baseline(self, manager):
        report = _make_report(_make_summary("pipe_a", 0.9))
        manager.ingest(report)
        assert "pipe_a" in manager.pipeline_names()

    def test_ingest_multiple_reports(self, manager):
        for score in [0.8, 0.9, 1.0]:
            manager.ingest(_make_report(_make_summary("pipe_a", score)))
        metric = manager.get("pipe_a").get("health_score")
        assert metric.average == pytest.approx(0.9)

    def test_manual_record(self, manager):
        manager.record("pipe_b", "latency", 300.0)
        metric = manager.get("pipe_b").get("latency")
        assert metric is not None
        assert metric.average == pytest.approx(300.0)

    def test_is_degraded_true(self, manager):
        for score in [0.9, 0.9, 0.9]:
            manager.ingest(_make_report(_make_summary("pipe_a", score)))
        assert manager.is_degraded("pipe_a", 0.5, tolerance=0.1) is True

    def test_is_degraded_false_within_tolerance(self, manager):
        for score in [0.9, 0.9, 0.9]:
            manager.ingest(_make_report(_make_summary("pipe_a", score)))
        assert manager.is_degraded("pipe_a", 0.85, tolerance=0.1) is False

    def test_is_degraded_unknown_pipeline(self, manager):
        assert manager.is_degraded("unknown", 0.0) is False

    def test_to_dict_contains_all_pipelines(self, manager):
        manager.ingest(_make_report(_make_summary("pipe_a", 0.8)))
        manager.ingest(_make_report(_make_summary("pipe_b", 0.6)))
        d = manager.to_dict()
        assert "pipe_a" in d and "pipe_b" in d


class TestBaselineAlerter:
    def test_no_alerts_when_healthy(self, manager):
        for score in [0.9, 0.9, 0.9]:
            manager.ingest(_make_report(_make_summary("pipe_a", score)))
        alerter = BaselineAlerter(manager, tolerance=0.1)
        report = _make_report(_make_summary("pipe_a", 0.88))
        assert alerter.check(report) == []

    def test_alert_emitted_when_degraded(self, manager):
        for score in [0.9, 0.9, 0.9]:
            manager.ingest(_make_report(_make_summary("pipe_a", score)))
        alerter = BaselineAlerter(manager, tolerance=0.1)
        report = _make_report(_make_summary("pipe_a", 0.5))
        alerts = alerter.check(report)
        assert len(alerts) == 1
        assert "pipe_a" in alerts[0].pipeline

    def test_check_and_ingest_updates_baseline(self, manager):
        for score in [0.9, 0.9, 0.9]:
            manager.ingest(_make_report(_make_summary("pipe_a", score)))
        alerter = BaselineAlerter(manager, tolerance=0.1)
        report = _make_report(_make_summary("pipe_a", 0.7))
        alerter.check_and_ingest(report)
        metric = manager.get("pipe_a").get("health_score")
        assert metric.sample_count == 4

    def test_custom_alert_level(self, manager):
        for score in [0.9, 0.9]:
            manager.ingest(_make_report(_make_summary("pipe_a", score)))
        alerter = BaselineAlerter(manager, tolerance=0.05, level=AlertLevel.CRITICAL)
        report = _make_report(_make_summary("pipe_a", 0.5))
        alerts = alerter.check(report)
        assert alerts[0].level == AlertLevel.CRITICAL
