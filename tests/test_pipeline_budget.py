"""Tests for pipeline_budget and budget_reporter."""
import pytest

from pipewatch.core.pipeline_budget import BudgetBreach, BudgetLimit, BudgetRegistry
from pipewatch.core.pipeline_cost import CostEntry, CostRegistry
from pipewatch.core.budget_reporter import BudgetReporter, BudgetUtilization


# ---------------------------------------------------------------------------
# BudgetLimit
# ---------------------------------------------------------------------------

class TestBudgetLimit:
    def test_is_exceeded_when_over(self):
        bl = BudgetLimit("pipe_a", limit=100.0)
        assert bl.is_exceeded(101.0) is True

    def test_not_exceeded_at_limit(self):
        bl = BudgetLimit("pipe_a", limit=100.0)
        assert bl.is_exceeded(100.0) is False

    def test_utilization_half(self):
        bl = BudgetLimit("pipe_a", limit=200.0)
        assert bl.utilization(100.0) == 0.5

    def test_utilization_zero_limit_returns_zero(self):
        bl = BudgetLimit("pipe_a", limit=0.0)
        assert bl.utilization(50.0) == 0.0

    def test_to_dict_keys(self):
        bl = BudgetLimit("pipe_a", limit=500.0, currency="EUR", period="weekly")
        d = bl.to_dict()
        assert set(d.keys()) == {"pipeline_name", "limit", "currency", "period"}

    def test_from_dict_roundtrip(self):
        bl = BudgetLimit("pipe_b", limit=300.0, currency="GBP", period="daily")
        restored = BudgetLimit.from_dict(bl.to_dict())
        assert restored.pipeline_name == bl.pipeline_name
        assert restored.limit == bl.limit
        assert restored.currency == bl.currency
        assert restored.period == bl.period

    def test_repr_contains_name(self):
        bl = BudgetLimit("my_pipe", limit=50.0)
        assert "my_pipe" in repr(bl)


# ---------------------------------------------------------------------------
# BudgetBreach
# ---------------------------------------------------------------------------

class TestBudgetBreach:
    def test_overage_computed(self):
        breach = BudgetBreach("p", limit=100.0, actual=150.0, currency="USD", period="monthly")
        assert breach.overage == 50.0

    def test_to_dict_contains_overage(self):
        breach = BudgetBreach("p", limit=100.0, actual=120.0, currency="USD", period="monthly")
        d = breach.to_dict()
        assert "overage" in d
        assert d["overage"] == 20.0


# ---------------------------------------------------------------------------
# BudgetRegistry
# ---------------------------------------------------------------------------

@pytest.fixture
def registry():
    return BudgetRegistry()


class TestBudgetRegistry:
    def test_add_and_get(self, registry):
        bl = BudgetLimit("pipe_x", limit=100.0)
        registry.add(bl)
        assert registry.get("pipe_x") is bl

    def test_add_duplicate_raises(self, registry):
        registry.add(BudgetLimit("pipe_x", limit=100.0))
        with pytest.raises(ValueError):
            registry.add(BudgetLimit("pipe_x", limit=200.0))

    def test_update_replaces(self, registry):
        registry.add(BudgetLimit("pipe_x", limit=100.0))
        registry.update(BudgetLimit("pipe_x", limit=999.0))
        assert registry.get("pipe_x").limit == 999.0

    def test_remove(self, registry):
        registry.add(BudgetLimit("pipe_x", limit=100.0))
        registry.remove("pipe_x")
        assert registry.get("pipe_x") is None

    def test_evaluate_returns_none_when_within_budget(self, registry):
        registry.add(BudgetLimit("pipe_x", limit=100.0))
        assert registry.evaluate("pipe_x", 80.0) is None

    def test_evaluate_returns_breach_when_over(self, registry):
        registry.add(BudgetLimit("pipe_x", limit=100.0))
        breach = registry.evaluate("pipe_x", 150.0)
        assert isinstance(breach, BudgetBreach)
        assert breach.actual == 150.0

    def test_evaluate_unknown_pipeline_returns_none(self, registry):
        assert registry.evaluate("unknown", 999.0) is None


# ---------------------------------------------------------------------------
# BudgetReporter
# ---------------------------------------------------------------------------

@pytest.fixture
def budget_reporter():
    budgets = BudgetRegistry()
    budgets.add(BudgetLimit("pipe_a", limit=100.0))
    budgets.add(BudgetLimit("pipe_b", limit=50.0))

    costs = CostRegistry()
    costs.record(CostEntry("pipe_a", amount=80.0))
    costs.record(CostEntry("pipe_b", amount=60.0))  # exceeds limit

    return BudgetReporter(budgets, costs)


class TestBudgetReporter:
    def test_utilization_returns_all_pipelines(self, budget_reporter):
        utils = budget_reporter.utilization()
        assert len(utils) == 2

    def test_utilization_breached_flag(self, budget_reporter):
        utils = {u.pipeline_name: u for u in budget_reporter.utilization()}
        assert utils["pipe_a"].breached is False
        assert utils["pipe_b"].breached is True

    def test_breaches_returns_only_exceeded(self, budget_reporter):
        breaches = budget_reporter.breaches()
        assert len(breaches) == 1
        assert breaches[0].pipeline_name == "pipe_b"

    def test_summary_counts(self, budget_reporter):
        s = budget_reporter.summary()
        assert s["total_pipelines"] == 2
        assert s["breached_count"] == 1
        assert s["healthy_count"] == 1
