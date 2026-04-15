"""Tests for pipeline_capacity and capacity_config modules."""
import pytest

from pipewatch.core.pipeline_capacity import CapacityLimit, CapacityStatus, CapacityRegistry
from pipewatch.core.capacity_config import CapacityConfig


# ---------------------------------------------------------------------------
# CapacityLimit
# ---------------------------------------------------------------------------

class TestCapacityLimit:
    def test_utilization_at_half(self):
        lim = CapacityLimit("pipe", "rows", limit=1000.0)
        assert lim.utilization(500.0) == pytest.approx(0.5)

    def test_utilization_zero_limit_returns_zero(self):
        lim = CapacityLimit("pipe", "rows", limit=0.0)
        assert lim.utilization(100.0) == 0.0

    def test_is_breached_at_limit(self):
        lim = CapacityLimit("pipe", "rows", limit=100.0)
        assert lim.is_breached(100.0) is True

    def test_is_breached_below_limit(self):
        lim = CapacityLimit("pipe", "rows", limit=100.0)
        assert lim.is_breached(99.9) is False

    def test_is_warning_in_zone(self):
        lim = CapacityLimit("pipe", "rows", limit=100.0, warn_threshold=0.80)
        assert lim.is_warning(85.0) is True

    def test_is_warning_below_zone(self):
        lim = CapacityLimit("pipe", "rows", limit=100.0, warn_threshold=0.80)
        assert lim.is_warning(70.0) is False

    def test_is_warning_false_when_breached(self):
        lim = CapacityLimit("pipe", "rows", limit=100.0, warn_threshold=0.80)
        assert lim.is_warning(100.0) is False

    def test_to_dict_keys(self):
        lim = CapacityLimit("pipe", "rows", limit=500.0)
        d = lim.to_dict()
        assert {"pipeline_name", "resource", "limit", "warn_threshold"} <= d.keys()

    def test_from_dict_roundtrip(self):
        lim = CapacityLimit("pipe", "rows", limit=200.0, warn_threshold=0.75)
        assert CapacityLimit.from_dict(lim.to_dict()).limit == 200.0

    def test_repr_contains_pipeline_and_resource(self):
        lim = CapacityLimit("etl", "memory_mb", limit=4096.0)
        r = repr(lim)
        assert "etl" in r and "memory_mb" in r


# ---------------------------------------------------------------------------
# CapacityStatus
# ---------------------------------------------------------------------------

class TestCapacityStatus:
    def _make_status(self, current: float, limit: float = 100.0) -> CapacityStatus:
        lim = CapacityLimit("pipe", "rows", limit=limit)
        return CapacityStatus(limit=lim, current=current)

    def test_to_dict_contains_current_and_utilization(self):
        s = self._make_status(50.0)
        d = s.to_dict()
        assert d["current"] == 50.0
        assert d["utilization"] == pytest.approx(0.5)

    def test_to_dict_breached_flag(self):
        assert self._make_status(100.0).to_dict()["breached"] is True
        assert self._make_status(99.0).to_dict()["breached"] is False

    def test_to_dict_warning_flag(self):
        assert self._make_status(85.0).to_dict()["warning"] is True


# ---------------------------------------------------------------------------
# CapacityConfig
# ---------------------------------------------------------------------------

@pytest.fixture
def config() -> CapacityConfig:
    c = CapacityConfig()
    c.add("etl_daily", "rows", limit=10_000.0, warn_threshold=0.80)
    c.add("etl_daily", "memory_mb", limit=2048.0)
    return c


class TestCapacityConfig:
    def test_len_reflects_added_limits(self, config):
        assert len(config) == 2

    def test_get_returns_limit(self, config):
        lim = config.get("etl_daily", "rows")
        assert lim is not None
        assert lim.limit == 10_000.0

    def test_get_unknown_returns_none(self, config):
        assert config.get("nonexistent", "rows") is None

    def test_evaluate_returns_statuses(self, config):
        statuses = config.evaluate("etl_daily", {"rows": 5000.0, "memory_mb": 1024.0})
        assert len(statuses) == 2

    def test_breached_filters_correctly(self, config):
        breached = config.breached("etl_daily", {"rows": 10_001.0, "memory_mb": 100.0})
        assert len(breached) == 1
        assert breached[0].limit.resource == "rows"

    def test_warnings_filters_correctly(self, config):
        warnings = config.warnings("etl_daily", {"rows": 8500.0, "memory_mb": 100.0})
        assert len(warnings) == 1
        assert warnings[0].limit.resource == "rows"

    def test_remove_reduces_count(self, config):
        config.remove("etl_daily", "rows")
        assert len(config) == 1

    def test_remove_unknown_does_not_raise(self, config):
        config.remove("ghost", "rows")  # should not raise

    def test_all_limits_returns_list(self, config):
        limits = config.all_limits()
        assert isinstance(limits, list)
        assert all(isinstance(l, CapacityLimit) for l in limits)
