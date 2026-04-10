"""Tests for the Reporter module."""

import pytest
from unittest.mock import MagicMock

from pipewatch.core.reporter import Reporter, Report, PipelineSummary
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.check import Check, CheckStatus
from pipewatch.core.alert import Alert, AlertLevel


@pytest.fixture
def monitor_with_pipelines():
    monitor = Monitor(name="test-monitor")

    healthy = Pipeline(name="healthy-pipeline")
    check_pass = Check(name="row_count", description="Row count check")
    check_pass.mark_pass()
    healthy.add_check(check_pass)
    healthy.update_status(PipelineStatus.HEALTHY)

    failing = Pipeline(name="failing-pipeline")
    check_fail = Check(name="schema_check", description="Schema validation")
    check_fail.mark_fail(reason="Column missing")
    failing.add_check(check_fail)
    failing.update_status(PipelineStatus.FAILED)
    alert = Alert(
        pipeline_name="failing-pipeline",
        message="Schema check failed",
        level=AlertLevel.CRITICAL,
    )
    failing.add_alert(alert)

    monitor.register_pipeline(healthy)
    monitor.register_pipeline(failing)
    return monitor


class TestReporter:
    def test_reporter_initialization(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        assert reporter.monitor is monitor_with_pipelines

    def test_generate_returns_report(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        assert isinstance(report, Report)

    def test_report_pipeline_counts(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        assert report.total_pipelines == 2
        assert report.healthy_pipelines == 1
        assert report.failed_pipelines == 1
        assert report.degraded_pipelines == 0

    def test_report_critical_alerts(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        assert report.critical_alerts == 1

    def test_report_summaries_length(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        assert len(report.summaries) == 2

    def test_pipeline_summary_health_score(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        healthy_summary = next(s for s in report.summaries if s.name == "healthy-pipeline")
        assert healthy_summary.health_score == 1.0

    def test_pipeline_summary_failed_health_score(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        failing_summary = next(s for s in report.summaries if s.name == "failing-pipeline")
        assert failing_summary.health_score == 0.0

    def test_report_to_dict_structure(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        d = report.to_dict()
        assert "generated_at" in d
        assert "total_pipelines" in d
        assert "summaries" in d
        assert isinstance(d["summaries"], list)

    def test_health_score_no_checks():
        summary = PipelineSummary(
            name="empty",
            status="healthy",
            total_checks=0,
            passed_checks=0,
            failed_checks=0,
        )
        assert summary.health_score == 1.0

    def test_report_generated_at_is_string(self, monitor_with_pipelines):
        reporter = Reporter(monitor=monitor_with_pipelines)
        report = reporter.generate()
        assert isinstance(report.generated_at, str)
        assert "T" in report.generated_at
