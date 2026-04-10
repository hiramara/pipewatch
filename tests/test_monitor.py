"""Tests for the Monitor module."""

import pytest
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.check import Check, CheckStatus
from pipewatch.core.alert import AlertLevel


@pytest.fixture
def monitor():
    return Monitor(name="test-monitor")


@pytest.fixture
def pipeline_with_failing_check():
    p = Pipeline(pipeline_id="pipe-1", name="ETL Pipeline")
    check = Check(name="row_count", description="Ensure row count > 0")
    check.mark_fail(reason="Row count was 0")
    p.add_check(check)
    p.update_status(PipelineStatus.FAILED)
    return p


@pytest.fixture
def healthy_pipeline():
    p = Pipeline(pipeline_id="pipe-2", name="Healthy Pipeline")
    check = Check(name="schema_valid", description="Schema validation")
    check.mark_pass()
    p.add_check(check)
    p.update_status(PipelineStatus.SUCCESS)
    return p


class TestMonitor:
    def test_monitor_initialization(self, monitor):
        assert monitor.name == "test-monitor"
        assert monitor.pipelines == {}
        assert monitor.alerts == []
        assert monitor.last_evaluated is None

    def test_register_pipeline(self, monitor, healthy_pipeline):
        monitor.register_pipeline(healthy_pipeline)
        assert "pipe-2" in monitor.pipelines

    def test_register_duplicate_pipeline_raises(self, monitor, healthy_pipeline):
        monitor.register_pipeline(healthy_pipeline)
        with pytest.raises(ValueError, match="already registered"):
            monitor.register_pipeline(healthy_pipeline)

    def test_unregister_pipeline(self, monitor, healthy_pipeline):
        monitor.register_pipeline(healthy_pipeline)
        monitor.unregister_pipeline("pipe-2")
        assert "pipe-2" not in monitor.pipelines

    def test_unregister_nonexistent_pipeline_raises(self, monitor):
        with pytest.raises(KeyError):
            monitor.unregister_pipeline("nonexistent")

    def test_evaluate_generates_alerts_for_failures(self, monitor, pipeline_with_failing_check):
        monitor.register_pipeline(pipeline_with_failing_check)
        new_alerts = monitor.evaluate()
        assert len(new_alerts) == 1
        assert new_alerts[0].check_name == "row_count"
        assert new_alerts[0].level == AlertLevel.CRITICAL

    def test_evaluate_no_alerts_for_healthy_pipeline(self, monitor, healthy_pipeline):
        monitor.register_pipeline(healthy_pipeline)
        new_alerts = monitor.evaluate()
        assert new_alerts == []

    def test_evaluate_sets_last_evaluated(self, monitor, healthy_pipeline):
        monitor.register_pipeline(healthy_pipeline)
        assert monitor.last_evaluated is None
        monitor.evaluate()
        assert monitor.last_evaluated is not None

    def test_active_alerts_excludes_resolved(self, monitor, pipeline_with_failing_check):
        monitor.register_pipeline(pipeline_with_failing_check)
        monitor.evaluate()
        monitor.alerts[0].resolve()
        assert monitor.active_alerts() == []

    def test_summary_structure(self, monitor, pipeline_with_failing_check):
        monitor.register_pipeline(pipeline_with_failing_check)
        monitor.evaluate()
        summary = monitor.summary()
        assert summary["monitor"] == "test-monitor"
        assert summary["pipelines"] == 1
        assert summary["active_alerts"] == 1
        assert summary["total_alerts"] == 1
        assert summary["last_evaluated"] is not None

    def test_repr(self, monitor):
        result = repr(monitor)
        assert "test-monitor" in result
        assert "Monitor(" in result
