"""Tests for pipewatch.core.aggregator."""

from __future__ import annotations

import pytest

from pipewatch.core.aggregator import AggregateGroup, Aggregator, by_status, by_tag
from pipewatch.core.pipeline import PipelineStatus
from pipewatch.core.reporter import PipelineSummary


def _make_summary(name: str, status: PipelineStatus, tags=None, health: float = 1.0) -> PipelineSummary:
    meta = {"tags": tags or []}
    return PipelineSummary(
        pipeline_name=name,
        status=status,
        health_score=health,
        total_checks=1,
        passed_checks=1 if status == PipelineStatus.HEALTHY else 0,
        failed_checks=0 if status == PipelineStatus.HEALTHY else 1,
        alerts=[],
        metadata=meta,
    )


class TestAggregateGroup:
    def test_count(self):
        g = AggregateGroup(key="healthy")
        g.summaries.append(_make_summary("p1", PipelineStatus.HEALTHY))
        assert g.count == 1

    def test_average_health_empty(self):
        g = AggregateGroup(key="x")
        assert g.average_health == 0.0

    def test_average_health_computed(self):
        g = AggregateGroup(key="x")
        g.summaries.append(_make_summary("p1", PipelineStatus.HEALTHY, health=0.8))
        g.summaries.append(_make_summary("p2", PipelineStatus.HEALTHY, health=0.6))
        assert abs(g.average_health - 0.7) < 1e-6

    def test_failing_count(self):
        g = AggregateGroup(key="x")
        g.summaries.append(_make_summary("p1", PipelineStatus.HEALTHY))
        g.summaries.append(_make_summary("p2", PipelineStatus.FAILING))
        assert g.failing_count == 1

    def test_to_dict_keys(self):
        g = AggregateGroup(key="ok")
        d = g.to_dict()
        assert set(d.keys()) == {"key", "count", "average_health", "failing_count", "pipelines"}


class TestAggregator:
    def _make_report(self, summaries):
        from pipewatch.core.reporter import Report
        return Report(pipelines=summaries, total=len(summaries),
                      healthy=0, failing=0, degraded=0)

    def test_by_status_groups_correctly(self):
        summaries = [
            _make_summary("a", PipelineStatus.HEALTHY),
            _make_summary("b", PipelineStatus.HEALTHY),
            _make_summary("c", PipelineStatus.FAILING),
        ]
        report = self._make_report(summaries)
        agg = Aggregator(by_status)
        groups = agg.aggregate(report)
        assert "healthy" in groups
        assert groups["healthy"].count == 2
        assert groups["failing"].count == 1

    def test_by_tag_groups_correctly(self):
        summaries = [
            _make_summary("a", PipelineStatus.HEALTHY, tags=["finance"]),
            _make_summary("b", PipelineStatus.HEALTHY, tags=["ops"]),
        ]
        report = self._make_report(summaries)
        agg = Aggregator(by_tag("finance"))
        groups = agg.aggregate(report)
        assert groups["finance"].count == 1
        assert groups["_other"].count == 1

    def test_to_dicts_returns_list(self):
        report = self._make_report([_make_summary("x", PipelineStatus.HEALTHY)])
        agg = Aggregator(by_status)
        result = agg.to_dicts(report)
        assert isinstance(result, list)
        assert result[0]["key"] == "healthy"
