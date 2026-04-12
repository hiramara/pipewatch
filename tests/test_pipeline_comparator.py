"""Tests for PipelineComparator."""

import pytest
from unittest.mock import MagicMock

from pipewatch.core.pipeline_comparator import PipelineComparator, ComparisonResult
from pipewatch.core.pipeline import PipelineStatus


def _make_summary(name: str, status: str, health: float):
    s = MagicMock()
    s.name = name
    s.status = status
    s.health_score = health
    return s


def _make_snapshot(*summaries):
    snap = MagicMock()
    snap.summaries = list(summaries)
    return snap


@pytest.fixture
def comparator():
    return PipelineComparator()


class TestPipelineComparator:
    def test_no_previous_all_current_are_changes(self, comparator):
        curr = _make_snapshot(
            _make_summary("pipe_a", "healthy", 1.0),
            _make_summary("pipe_b", "failing", 0.5),
        )
        result = comparator.compare(None, curr)
        assert len(result.changes) == 2

    def test_no_change_returns_empty(self, comparator):
        prev = _make_snapshot(_make_summary("pipe_a", "healthy", 1.0))
        curr = _make_snapshot(_make_summary("pipe_a", "healthy", 1.0))
        result = comparator.compare(prev, curr)
        assert not result.has_changes

    def test_status_change_detected(self, comparator):
        prev = _make_snapshot(_make_summary("pipe_a", "healthy", 1.0))
        curr = _make_snapshot(_make_summary("pipe_a", "failing", 0.3))
        result = comparator.compare(prev, curr)
        assert len(result.changes) == 1
        change = result.changes[0]
        assert change.pipeline_name == "pipe_a"
        assert change.previous_status == PipelineStatus.HEALTHY
        assert change.current_status == PipelineStatus.FAILING

    def test_newly_failing_flag(self, comparator):
        prev = _make_snapshot(_make_summary("pipe_a", "healthy", 1.0))
        curr = _make_snapshot(_make_summary("pipe_a", "failing", 0.4))
        result = comparator.compare(prev, curr)
        assert len(result.newly_failing) == 1
        assert result.newly_failing[0].pipeline_name == "pipe_a"

    def test_newly_healthy_flag(self, comparator):
        prev = _make_snapshot(_make_summary("pipe_a", "failing", 0.4))
        curr = _make_snapshot(_make_summary("pipe_a", "healthy", 1.0))
        result = comparator.compare(prev, curr)
        assert len(result.newly_healthy) == 1

    def test_health_delta_computed(self, comparator):
        prev = _make_snapshot(_make_summary("pipe_a", "healthy", 0.8))
        curr = _make_snapshot(_make_summary("pipe_a", "failing", 0.5))
        result = comparator.compare(prev, curr)
        assert result.changes[0].health_delta == pytest.approx(-0.3, abs=1e-4)

    def test_new_pipeline_no_previous_status(self, comparator):
        prev = _make_snapshot()
        curr = _make_snapshot(_make_summary("pipe_new", "healthy", 1.0))
        result = comparator.compare(prev, curr)
        assert result.changes[0].previous_status is None
        assert not result.changes[0].newly_healthy  # no prior status

    def test_to_dict_structure(self, comparator):
        prev = _make_snapshot(_make_summary("pipe_a", "healthy", 1.0))
        curr = _make_snapshot(_make_summary("pipe_a", "failing", 0.5))
        result = comparator.compare(prev, curr)
        d = result.to_dict()
        assert "total_changes" in d
        assert "newly_failing" in d
        assert "newly_healthy" in d
        assert isinstance(d["changes"], list)

    def test_change_repr(self, comparator):
        prev = _make_snapshot(_make_summary("pipe_a", "healthy", 1.0))
        curr = _make_snapshot(_make_summary("pipe_a", "failing", 0.4))
        result = comparator.compare(prev, curr)
        r = repr(result.changes[0])
        assert "pipe_a" in r
        assert "->" in r
