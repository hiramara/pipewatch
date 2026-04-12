"""Tests for PipelineSorter."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from pipewatch.core.pipeline_sorter import PipelineSorter, SortKey
from pipewatch.core.reporter import PipelineSummary, Report


def _make_summary(name: str, status: str, health: float, failing: int) -> PipelineSummary:
    s = MagicMock(spec=PipelineSummary)
    s.name = name
    s.status = status
    s.health_score = health
    s.failing_checks = failing
    return s


@pytest.fixture()
def summaries():
    return [
        _make_summary("zebra", "healthy", 1.0, 0),
        _make_summary("alpha", "failing", 0.2, 3),
        _make_summary("mango", "unknown", 0.5, 1),
        _make_summary("beta",  "failing", 0.0, 5),
    ]


class TestSortByName:
    def test_ascending(self, summaries):
        sorter = PipelineSorter(key=SortKey.NAME)
        result = sorter.sort(summaries)
        assert [s.name for s in result] == ["alpha", "beta", "mango", "zebra"]

    def test_descending(self, summaries):
        sorter = PipelineSorter(key=SortKey.NAME, reverse=True)
        result = sorter.sort(summaries)
        assert result[0].name == "zebra"

    def test_original_not_mutated(self, summaries):
        original_order = [s.name for s in summaries]
        PipelineSorter(key=SortKey.NAME).sort(summaries)
        assert [s.name for s in summaries] == original_order


class TestSortByStatus:
    def test_failing_first(self, summaries):
        sorter = PipelineSorter(key=SortKey.STATUS)
        result = sorter.sort(summaries)
        assert result[0].status == "failing"
        assert result[1].status == "failing"
        assert result[-1].status == "healthy"


class TestSortByHealth:
    def test_lowest_health_first(self, summaries):
        sorter = PipelineSorter(key=SortKey.HEALTH)
        result = sorter.sort(summaries)
        assert result[0].health_score == 0.0
        assert result[-1].health_score == 1.0

    def test_highest_health_first(self, summaries):
        sorter = PipelineSorter(key=SortKey.HEALTH, reverse=True)
        result = sorter.sort(summaries)
        assert result[0].health_score == 1.0


class TestSortByFailingChecks:
    def test_fewest_failing_first(self, summaries):
        sorter = PipelineSorter(key=SortKey.FAILING_CHECKS)
        result = sorter.sort(summaries)
        assert result[0].failing_checks == 0
        assert result[-1].failing_checks == 5


class TestSortReport:
    def test_sort_report_returns_report(self, summaries):
        report = MagicMock(spec=Report)
        report.pipelines = summaries
        report.total = len(summaries)
        report.healthy = 1
        report.failing = 2
        report.generated_at = datetime.utcnow()

        sorter = PipelineSorter(key=SortKey.NAME)
        result = sorter.sort_report(report)
        assert isinstance(result, Report)
        assert result.pipelines[0].name == "alpha"


class TestInvalidKey:
    def test_invalid_key_raises(self):
        with pytest.raises(ValueError):
            PipelineSorter(key="nonexistent")
