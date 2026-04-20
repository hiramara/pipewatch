"""Configuration wrapper for DependencyAlerter."""
from __future__ import annotations

from typing import Optional

from pipewatch.core.alert import AlertLevel
from pipewatch.core.dependency import DependencyGraph
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline_dependency_alert import DependencyAlert, DependencyAlerter


class DependencyAlertConfig:
    """Holds the dependency graph and alerter settings; produces a ready-to-use
    :class:`DependencyAlerter` on demand.

    Example usage::

        config = DependencyAlertConfig()
        config.add_dependency(upstream="ingest", downstream="orders")
        config.level = AlertLevel.CRITICAL
        alerter = config.build(monitor)
        alerts = alerter.check()
    """

    def __init__(self, level: AlertLevel = AlertLevel.WARNING) -> None:
        self._graph: DependencyGraph = DependencyGraph()
        self.level: AlertLevel = level

    # ------------------------------------------------------------------
    # Graph management
    # ------------------------------------------------------------------

    def add_dependency(self, *, upstream: str, downstream: str) -> None:
        """Register that *downstream* depends on *upstream*."""
        self._graph.add_dependency(upstream=upstream, downstream=downstream)

    def remove_dependency(self, *, upstream: str, downstream: str) -> None:
        """Remove a previously registered dependency edge."""
        self._graph.remove_dependency(upstream=upstream, downstream=downstream)

    @property
    def graph(self) -> DependencyGraph:
        """Read-only access to the underlying :class:`DependencyGraph`."""
        return self._graph

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    def build(self, monitor: Monitor) -> DependencyAlerter:
        """Return a :class:`DependencyAlerter` configured with the current graph
        and alert level."""
        return DependencyAlerter(
            monitor=monitor,
            graph=self._graph,
            level=self.level,
        )

    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DependencyAlertConfig(level={self.level.value!r}, "
            f"edges={len(list(self._graph.all_edges()))})"
        )
