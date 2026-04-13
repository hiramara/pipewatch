"""Tests for CostReporter and CostSummary."""
import pytest

from pipewatch.core.pipeline_cost import CostRegistry
from pipewatch.core.cost_reporter import CostReporter, CostSummary


@pytest.fixture()
def registry() -> CostRegistry:
    r = CostRegistry()
    r.set("pipe_a", 5.0, notes="expensive")
    r.set("pipe_b", 1.0)
    r.set("pipe_c", 3.5)
    return r


@pytest.fixture()
def reporter(registry) -> CostReporter:
    return CostReporter(registry)


class TestCostSummary:
    def test_to_dict_keys(self, reporter):
        summary = reporter.summary()
        d = summary.to_dict()
        assert set(d.keys()) == {"pipeline_count", "total_usd", "entries"}

    def test_pipeline_count(self, reporter):
        assert reporter.summary().pipeline_count == 3

    def test_total_usd(self, reporter):
        assert reporter.summary().total_usd == pytest.approx(9.5)

    def test_entries_are_cost_entry_dicts(self, reporter):
        summary = reporter.summary()
        d = summary.to_dict()
        for entry in d["entries"]:
            assert "pipeline_name" in entry
            assert "cost_usd" in entry


class TestCostReporter:
    def test_top_n_returns_descending(self, reporter):
        top = reporter.top_n(2)
        assert top[0].pipeline_name == "pipe_a"
        assert top[1].pipeline_name == "pipe_c"

    def test_top_n_clamps_to_available(self, reporter):
        top = reporter.top_n(10)
        assert len(top) == 3

    def test_top_n_invalid_raises(self, reporter):
        with pytest.raises(ValueError, match="at least 1"):
            reporter.top_n(0)

    def test_below_threshold(self, reporter):
        results = reporter.below_threshold(3.5)
        names = {e.pipeline_name for e in results}
        assert names == {"pipe_b"}

    def test_above_threshold(self, reporter):
        results = reporter.above_threshold(3.5)
        names = {e.pipeline_name for e in results}
        assert names == {"pipe_a", "pipe_c"}

    def test_empty_registry(self):
        reporter = CostReporter(CostRegistry())
        summary = reporter.summary()
        assert summary.pipeline_count == 0
        assert summary.total_usd == 0.0
        assert summary.entries == []

    def test_top_n_empty_registry(self):
        reporter = CostReporter(CostRegistry())
        assert reporter.top_n(3) == []
