"""Tests for LifecycleManager."""

import pytest
from unittest.mock import MagicMock

from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.lifecycle_manager import LifecycleManager


def _make_pipeline(name: str, status: PipelineStatus) -> Pipeline:
    p = Pipeline(name=name)
    p.update_status(status)
    return p


@pytest.fixture
def monitor():
    m = MagicMock()
    m.pipelines = {
        "alpha": _make_pipeline("alpha", PipelineStatus.HEALTHY),
        "beta": _make_pipeline("beta", PipelineStatus.FAILING),
    }
    return m


@pytest.fixture
def manager():
    return LifecycleManager()


class TestLifecycleManager:
    def test_observe_returns_events_on_first_call(self, manager, monitor):
        events = manager.observe(monitor)
        assert len(events) == 2

    def test_observe_no_change_returns_empty(self, manager, monitor):
        manager.observe(monitor)
        events = manager.observe(monitor)
        assert events == []

    def test_observe_detects_status_change(self, manager, monitor):
        manager.observe(monitor)
        monitor.pipelines["alpha"].update_status(PipelineStatus.FAILING)
        events = manager.observe(monitor)
        assert len(events) == 1
        assert events[0].pipeline_name == "alpha"

    def test_get_returns_lifecycle_after_observe(self, manager, monitor):
        manager.observe(monitor)
        lc = manager.get("alpha")
        assert lc is not None
        assert lc.pipeline_name == "alpha"

    def test_get_unknown_returns_none(self, manager):
        assert manager.get("ghost") is None

    def test_all_events_sorted_by_timestamp(self, manager, monitor):
        manager.observe(monitor)
        events = manager.all_events()
        timestamps = [e.timestamp for e in events]
        assert timestamps == sorted(timestamps)

    def test_transitions_for_filters_by_pipeline(self, manager, monitor):
        manager.observe(monitor)
        events = manager.transitions_for("alpha")
        assert all(e.pipeline_name == "alpha" for e in events)

    def test_pipelines_that_degraded(self, manager, monitor):
        manager.observe(monitor)
        degraded = manager.pipelines_that_degraded()
        assert "beta" in degraded
        assert "alpha" not in degraded
