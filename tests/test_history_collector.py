"""Tests for HistoryCollector."""

import pytest
from unittest.mock import MagicMock

from pipewatch.core.history import PipelineHistory
from pipewatch.core.history_collector import HistoryCollector
from pipewatch.core.reporter import PipelineSummary, Report


def make_summary(name, status="healthy", health_score=1.0, **kwargs):
    return PipelineSummary(
        name=name,
        status=status,
        health_score=health_score,
        total_checks=kwargs.get("total_checks", 2),
        passed_checks=kwargs.get("passed_checks", 2),
        failed_checks=kwargs.get("failed_checks", 0),
        active_alerts=kwargs.get("active_alerts", 0),
    )


def make_report(*summaries):
    report = MagicMock(spec=Report)
    report.pipelines = list(summaries)
    return report


@pytest.fixture
def collector():
    return HistoryCollector()


class TestHistoryCollector:
    def test_collect_records_pipeline(self, collector):
        report = make_report(make_summary("sales_etl"))
        collector.collect(report)
        records = collector.history.get("sales_etl")
        assert len(records) == 1
        assert records[0].status == "healthy"
        assert records[0].health_score == 1.0

    def test_collect_multiple_pipelines(self, collector):
        report = make_report(
            make_summary("pipe_a", health_score=0.9),
            make_summary("pipe_b", status="degraded", health_score=0.4),
        )
        collector.collect(report)
        assert len(collector.history.get("pipe_a")) == 1
        assert len(collector.history.get("pipe_b")) == 1
        assert collector.history.last_status("pipe_b") == "degraded"

    def test_metadata_stored_in_record(self, collector):
        report = make_report(
            make_summary("pipe", total_checks=4, passed_checks=3, failed_checks=1, active_alerts=2)
        )
        collector.collect(report)
        record = collector.history.get("pipe")[0]
        assert record.metadata["total_checks"] == 4
        assert record.metadata["failed_checks"] == 1
        assert record.metadata["active_alerts"] == 2

    def test_persist_on_collect(self, tmp_path):
        path = tmp_path / "history.json"
        collector = HistoryCollector(persist_path=path)
        report = make_report(make_summary("etl", health_score=0.75))
        collector.collect(report)
        assert path.exists()

    def test_loads_existing_history_on_init(self, tmp_path):
        path = tmp_path / "history.json"
        pre = HistoryCollector(persist_path=path)
        pre.collect(make_report(make_summary("old_pipe", health_score=0.5)))

        reloaded = HistoryCollector(persist_path=path)
        records = reloaded.history.get("old_pipe")
        assert len(records) == 1
        assert records[0].health_score == 0.5

    def test_trend_summary_returns_correct_keys(self, collector):
        for score in [0.6, 0.8, 1.0]:
            collector.history.record(
                __import__("pipewatch.core.history", fromlist=["RunRecord"]).RunRecord(
                    "pipe", "healthy", score
                )
            )
        trend = collector.trend_summary("pipe")
        assert trend["records"] == 3
        assert "avg_health" in trend
        assert "status_sequence" in trend

    def test_trend_summary_unknown_pipeline(self, collector):
        result = collector.trend_summary("ghost")
        assert result["records"] == 0
