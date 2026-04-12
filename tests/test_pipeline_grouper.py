"""Tests for PipelineGrouper and PipelineGrouperConfig."""

from __future__ import annotations

import pytest

from pipewatch.core.pipeline_grouper import PipelineGroup, PipelineGrouper
from pipewatch.core.pipeline_grouper_config import PipelineGrouperConfig
from pipewatch.core.pipeline import PipelineStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_summary(name: str, status: PipelineStatus, health: float):
    """Build a minimal PipelineSummary-like object."""
    from pipewatch.core.reporter import PipelineSummary
    return PipelineSummary(name=name, status=status, health_score=health, alerts=[])


def _make_report(summaries):
    from pipewatch.core.reporter import Report
    from pipewatch.core.pipeline import PipelineStatus
    return Report(
        pipelines=summaries,
        total=len(summaries),
        healthy=sum(1 for s in summaries if s.health_score == 1.0),
        failing=sum(1 for s in summaries if s.health_score < 1.0),
    )


@pytest.fixture()
def summaries():
    return [
        _make_summary("alpha", PipelineStatus.HEALTHY, 1.0),
        _make_summary("beta", PipelineStatus.FAILING, 0.5),
        _make_summary("gamma", PipelineStatus.FAILING, 0.0),
    ]


@pytest.fixture()
def report(summaries):
    return _make_report(summaries)


# ---------------------------------------------------------------------------
# PipelineGroup
# ---------------------------------------------------------------------------

class TestPipelineGroup:
    def test_count(self, summaries):
        group = PipelineGroup(key="test", summaries=summaries)
        assert group.count == 3

    def test_failing_count(self, summaries):
        group = PipelineGroup(key="test", summaries=summaries)
        assert group.failing_count == 2

    def test_average_health(self, summaries):
        group = PipelineGroup(key="test", summaries=summaries)
        assert abs(group.average_health - (1.0 + 0.5 + 0.0) / 3) < 1e-6

    def test_average_health_empty_group(self):
        group = PipelineGroup(key="empty", summaries=[])
        assert group.average_health == 1.0

    def test_to_dict_keys(self, summaries):
        group = PipelineGroup(key="k", summaries=summaries)
        d = group.to_dict()
        assert {"key", "count", "failing_count", "average_health", "pipelines"} <= d.keys()

    def test_to_dict_pipeline_names(self, summaries):
        group = PipelineGroup(key="k", summaries=summaries)
        assert group.to_dict()["pipelines"] == ["alpha", "beta", "gamma"]


# ---------------------------------------------------------------------------
# PipelineGrouper
# ---------------------------------------------------------------------------

class TestPipelineGrouper:
    def test_group_by_status(self, report):
        grouper = PipelineGrouper(key_fn=lambda s: s.status.value)
        groups = grouper.group(report)
        assert len(groups) == 2

    def test_group_keys_sorted(self, report):
        grouper = PipelineGrouper(key_fn=lambda s: s.status.value)
        keys = list(grouper.group(report).keys())
        assert keys == sorted(keys)

    def test_to_dicts_returns_list(self, report):
        grouper = PipelineGrouper(key_fn=lambda s: s.status.value)
        result = grouper.to_dicts(report)
        assert isinstance(result, list)
        assert all(isinstance(d, dict) for d in result)


# ---------------------------------------------------------------------------
# PipelineGrouperConfig
# ---------------------------------------------------------------------------

class TestPipelineGrouperConfig:
    def test_default_groupers_registered(self):
        cfg = PipelineGrouperConfig()
        assert "by_status" in cfg.names
        assert "by_first_letter" in cfg.names

    def test_add_registers_new_grouper(self):
        cfg = PipelineGrouperConfig()
        cfg.add("custom", lambda s: "all")
        assert "custom" in cfg.names

    def test_add_duplicate_raises(self):
        cfg = PipelineGrouperConfig()
        with pytest.raises(ValueError, match="already registered"):
            cfg.add("by_status", lambda s: "x")

    def test_remove_grouper(self):
        cfg = PipelineGrouperConfig()
        cfg.remove("by_first_letter")
        assert "by_first_letter" not in cfg.names

    def test_remove_nonexistent_does_not_raise(self):
        cfg = PipelineGrouperConfig()
        cfg.remove("nonexistent")  # should not raise

    def test_get_returns_grouper(self):
        cfg = PipelineGrouperConfig()
        assert isinstance(cfg.get("by_status"), PipelineGrouper)

    def test_get_unknown_returns_none(self):
        cfg = PipelineGrouperConfig()
        assert cfg.get("unknown") is None

    def test_len(self):
        cfg = PipelineGrouperConfig()
        assert len(cfg) == 2
