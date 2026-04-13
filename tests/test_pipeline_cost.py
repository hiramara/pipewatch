"""Tests for CostEntry and CostRegistry."""
import pytest

from pipewatch.core.pipeline_cost import CostEntry, CostRegistry


@pytest.fixture()
def registry() -> CostRegistry:
    return CostRegistry()


class TestCostEntry:
    def test_to_dict_keys(self):
        entry = CostEntry(pipeline_name="etl_sales", cost_usd=1.25, notes="daily run")
        d = entry.to_dict()
        assert set(d.keys()) == {"pipeline_name", "cost_usd", "currency", "notes"}

    def test_to_dict_values(self):
        entry = CostEntry(pipeline_name="etl_sales", cost_usd=1.25, currency="USD", notes="daily run")
        d = entry.to_dict()
        assert d["pipeline_name"] == "etl_sales"
        assert d["cost_usd"] == 1.25
        assert d["currency"] == "USD"
        assert d["notes"] == "daily run"

    def test_default_currency_is_usd(self):
        entry = CostEntry(pipeline_name="p", cost_usd=0.5)
        assert entry.currency == "USD"


class TestCostRegistry:
    def test_set_and_get(self, registry):
        registry.set("pipe_a", 2.50)
        entry = registry.get("pipe_a")
        assert entry is not None
        assert entry.cost_usd == 2.50

    def test_get_unknown_returns_none(self, registry):
        assert registry.get("unknown") is None

    def test_set_negative_raises(self, registry):
        with pytest.raises(ValueError, match="non-negative"):
            registry.set("pipe_a", -1.0)

    def test_overwrite_existing(self, registry):
        registry.set("pipe_a", 1.0)
        registry.set("pipe_a", 3.0)
        assert registry.get("pipe_a").cost_usd == 3.0

    def test_remove(self, registry):
        registry.set("pipe_a", 1.0)
        registry.remove("pipe_a")
        assert registry.get("pipe_a") is None

    def test_remove_nonexistent_does_not_raise(self, registry):
        registry.remove("nope")  # should not raise

    def test_total_cost(self, registry):
        registry.set("a", 1.0)
        registry.set("b", 2.5)
        assert registry.total_cost() == pytest.approx(3.5)

    def test_total_cost_empty(self, registry):
        assert registry.total_cost() == 0.0

    def test_len(self, registry):
        registry.set("a", 1.0)
        registry.set("b", 0.5)
        assert len(registry) == 2

    def test_all_entries_returns_list(self, registry):
        registry.set("a", 1.0)
        entries = registry.all_entries()
        assert isinstance(entries, list)
        assert len(entries) == 1
