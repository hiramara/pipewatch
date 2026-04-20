"""Tests for DependencyAlerter."""
from __future__ import annotations

import pytest

from pipewatch.core.alert import AlertLevel
from pipewatch.core.dependency import DependencyGraph
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.pipeline_dependency_alert import DependencyAlert, DependencyAlerter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pipeline(name: str, status: PipelineStatus) -> Pipeline:
    p = Pipeline(name=name)
    p.update_status(status)
    return p


@pytest.fixture()
def graph() -> DependencyGraph:
    g = DependencyGraph()
    # downstream "orders" depends on upstream "ingest"
    g.add_dependency(upstream="ingest", downstream="orders")
    # downstream "report" depends on upstream "orders"
    g.add_dependency(upstream="orders", downstream="report")
    return g


@pytest.fixture()
def monitor() -> Monitor:
    m = Monitor()
    m.register_pipeline(_make_pipeline("ingest", PipelineStatus.FAILING))
    m.register_pipeline(_make_pipeline("orders", PipelineStatus.HEALTHY))
    m.register_pipeline(_make_pipeline("report", PipelineStatus.HEALTHY))
    return m


@pytest.fixture()
def alerter(monitor: Monitor, graph: DependencyGraph) -> DependencyAlerter:
    return DependencyAlerter(monitor=monitor, graph=graph)


# ---------------------------------------------------------------------------
# DependencyAlert
# ---------------------------------------------------------------------------

class TestDependencyAlert:
    def test_to_dict_keys(self):
        from pipewatch.core.alert import Alert
        alert = Alert(pipeline_name="orders", level=AlertLevel.WARNING, message="x")
        da = DependencyAlert(pipeline_name="orders", upstream_name="ingest", alert=alert)
        d = da.to_dict()
        assert "pipeline_name" in d
        assert "upstream_name" in d
        assert "alert" in d

    def test_to_dict_values(self):
        from pipewatch.core.alert import Alert
        alert = Alert(pipeline_name="orders", level=AlertLevel.WARNING, message="x")
        da = DependencyAlert(pipeline_name="orders", upstream_name="ingest", alert=alert)
        d = da.to_dict()
        assert d["pipeline_name"] == "orders"
        assert d["upstream_name"] == "ingest"


# ---------------------------------------------------------------------------
# DependencyAlerter
# ---------------------------------------------------------------------------

class TestDependencyAlerter:
    def test_failing_upstream_raises_alert(self, alerter: DependencyAlerter):
        results = alerter.check()
        pipeline_names = [r.pipeline_name for r in results]
        assert "orders" in pipeline_names

    def test_healthy_upstream_no_alert(self, alerter: DependencyAlerter):
        # "report" depends on "orders" which is HEALTHY — no alert for report
        results = alerter.check()
        pipeline_names = [r.pipeline_name for r in results]
        assert "report" not in pipeline_names

    def test_alert_message_contains_upstream_name(self, alerter: DependencyAlerter):
        results = alerter.check()
        orders_alerts = [r for r in results if r.pipeline_name == "orders"]
        assert len(orders_alerts) == 1
        assert "ingest" in orders_alerts[0].alert.message

    def test_default_level_is_warning(self, alerter: DependencyAlerter):
        results = alerter.check()
        assert all(r.alert.level == AlertLevel.WARNING for r in results)

    def test_custom_level_propagated(self, monitor: Monitor, graph: DependencyGraph):
        alerter = DependencyAlerter(monitor=monitor, graph=graph, level=AlertLevel.CRITICAL)
        results = alerter.check()
        assert all(r.alert.level == AlertLevel.CRITICAL for r in results)

    def test_affected_pipelines_unique(self, alerter: DependencyAlerter):
        affected = alerter.affected_pipelines()
        assert len(affected) == len(set(affected))
        assert "orders" in affected

    def test_no_failing_upstreams_returns_empty(self, graph: DependencyGraph):
        m = Monitor()
        m.register_pipeline(_make_pipeline("ingest", PipelineStatus.HEALTHY))
        m.register_pipeline(_make_pipeline("orders", PipelineStatus.HEALTHY))
        alerter = DependencyAlerter(monitor=m, graph=graph)
        assert alerter.check() == []

    def test_unknown_upstream_skipped(self, graph: DependencyGraph):
        """If an upstream is in the graph but not registered in the monitor, skip it."""
        m = Monitor()
        # only register downstream, not the upstream
        m.register_pipeline(_make_pipeline("orders", PipelineStatus.HEALTHY))
        alerter = DependencyAlerter(monitor=m, graph=graph)
        assert alerter.check() == []
