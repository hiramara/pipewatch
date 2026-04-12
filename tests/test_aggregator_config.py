"""Tests for pipewatch.core.aggregator_config and aggregator_reporter."""

from __future__ import annotations

import pytest

from pipewatch.core.aggregator import by_status
from pipewatch.core.aggregator_config import AggregatorConfig
from pipewatch.core.aggregator_reporter import AggregatorReporter
from pipewatch.core.pipeline import PipelineStatus
from pipewatch.core.reporter import PipelineSummary, Report


def _make_report():
    s = PipelineSummary(
        pipeline_name="pipe1",
        status=PipelineStatus.HEALTHY,
        health_score=1.0,
        total_checks=1,
        passed_checks=1,
        failed_checks=0,
        alerts=[],
        metadata={},
    )
    return Report(pipelines=[s], total=1, healthy=1, failing=0, degraded=0)


class TestAggregatorConfig:
    def test_default_contains_by_status(self):
        cfg = AggregatorConfig()
        assert "by_status" in cfg

    def test_add_registers(self):
        cfg = AggregatorConfig()
        cfg.add("custom", by_status)
        assert "custom" in cfg
        assert len(cfg) == 2

    def test_add_duplicate_raises(self):
        cfg = AggregatorConfig()
        with pytest.raises(ValueError):
            cfg.add("by_status", by_status)

    def test_remove_existing(self):
        cfg = AggregatorConfig()
        cfg.remove("by_status")
        assert "by_status" not in cfg

    def test_remove_missing_raises(self):
        cfg = AggregatorConfig()
        with pytest.raises(KeyError):
            cfg.remove("nonexistent")

    def test_get_returns_aggregator(self):
        cfg = AggregatorConfig()
        agg = cfg.get("by_status")
        assert agg is not None

    def test_get_missing_returns_none(self):
        cfg = AggregatorConfig()
        assert cfg.get("nope") is None

    def test_names_lists_all(self):
        cfg = AggregatorConfig()
        assert "by_status" in cfg.names()


class TestAggregatorReporter:
    def test_run_all_returns_dict(self):
        cfg = AggregatorConfig()
        ar = AggregatorReporter(cfg)
        result = ar.run_all(_make_report())
        assert "by_status" in result

    def test_run_named(self):
        cfg = AggregatorConfig()
        ar = AggregatorReporter(cfg)
        groups = ar.run("by_status", _make_report())
        assert "healthy" in groups

    def test_run_missing_raises(self):
        cfg = AggregatorConfig()
        ar = AggregatorReporter(cfg)
        with pytest.raises(KeyError):
            ar.run("ghost", _make_report())

    def test_to_dicts_serialises(self):
        cfg = AggregatorConfig()
        ar = AggregatorReporter(cfg)
        result = ar.to_dicts(_make_report())
        assert isinstance(result["by_status"], list)
        assert result["by_status"][0]["key"] == "healthy"
