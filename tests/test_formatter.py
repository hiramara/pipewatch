"""Tests for pipewatch.core.formatter."""

from __future__ import annotations

import json
import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.check import Check
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.reporter import Reporter
from pipewatch.core.formatter import render, FORMAT_HANDLERS


@pytest.fixture()
def simple_report():
    monitor = Monitor()

    p1 = Pipeline(name="orders-etl", source="postgres")
    p1.update_status(PipelineStatus.HEALTHY)
    check = Check(name="row-count", description="Rows > 0")
    check.mark_pass()
    p1.add_check(check)

    p2 = Pipeline(name="payments-etl", source="stripe")
    p2.update_status(PipelineStatus.CRITICAL)
    alert = Alert(
        pipeline_name="payments-etl",
        level=AlertLevel.CRITICAL,
        message="No rows ingested in 2 hours",
    )
    p2.add_alert(alert)

    monitor.register_pipeline(p1)
    monitor.register_pipeline(p2)

    reporter = Reporter(monitor)
    return reporter.generate()


class TestRenderText:
    def test_contains_header(self, simple_report):
        output = render(simple_report, fmt="text")
        assert "PipeWatch Report" in output

    def test_contains_pipeline_names(self, simple_report):
        output = render(simple_report, fmt="text")
        assert "orders-etl" in output
        assert "payments-etl" in output

    def test_contains_status(self, simple_report):
        output = render(simple_report, fmt="text")
        assert "healthy" in output.lower()
        assert "critical" in output.lower()

    def test_alert_message_shown(self, simple_report):
        output = render(simple_report, fmt="text")
        assert "No rows ingested in 2 hours" in output


class TestRenderJson:
    def test_valid_json(self, simple_report):
        output = render(simple_report, fmt="json")
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_has_pipeline_summaries(self, simple_report):
        parsed = json.loads(render(simple_report, fmt="json"))
        assert "pipeline_summaries" in parsed
        assert len(parsed["pipeline_summaries"]) == 2

    def test_json_has_counts(self, simple_report):
        parsed = json.loads(render(simple_report, fmt="json"))
        assert parsed["total_pipelines"] == 2


class TestRenderCsv:
    def test_csv_has_header(self, simple_report):
        output = render(simple_report, fmt="csv")
        assert "pipeline_name" in output
        assert "health_score" in output

    def test_csv_row_count(self, simple_report):
        lines = [l for l in render(simple_report, fmt="csv").strip().splitlines() if l]
        # header + 2 data rows
        assert len(lines) == 3

    def test_csv_contains_pipeline_names(self, simple_report):
        output = render(simple_report, fmt="csv")
        assert "orders-etl" in output
        assert "payments-etl" in output


class TestRenderDispatch:
    def test_unknown_format_raises(self, simple_report):
        with pytest.raises(ValueError, match="Unknown format"):
            render(simple_report, fmt="xml")

    def test_all_registered_formats_work(self, simple_report):
        for fmt in FORMAT_HANDLERS:
            result = render(simple_report, fmt=fmt)
            assert isinstance(result, str)
            assert len(result) > 0
