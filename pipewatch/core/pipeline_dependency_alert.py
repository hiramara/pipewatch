"""Alert generation for pipelines affected by upstream dependency failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.dependency import DependencyGraph
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import PipelineStatus


@dataclass
class DependencyAlert:
    """An alert raised because an upstream pipeline is unhealthy."""

    pipeline_name: str
    upstream_name: str
    alert: Alert

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "upstream_name": self.upstream_name,
            "alert": self.alert.to_dict(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DependencyAlert(pipeline={self.pipeline_name!r}, "
            f"upstream={self.upstream_name!r}, level={self.alert.level.value})"
        )


class DependencyAlerter:
    """Inspect the dependency graph and raise alerts for pipelines whose
    upstreams are failing or degraded."""

    def __init__(
        self,
        monitor: Monitor,
        graph: DependencyGraph,
        level: AlertLevel = AlertLevel.WARNING,
    ) -> None:
        self._monitor = monitor
        self._graph = graph
        self._level = level

    # ------------------------------------------------------------------
    def check(self) -> List[DependencyAlert]:
        """Return one DependencyAlert per (pipeline, failing-upstream) pair."""
        results: List[DependencyAlert] = []
        pipelines = {p.name: p for p in self._monitor.pipelines}

        for name, pipeline in pipelines.items():
            for upstream_name in self._graph.upstreams_of(name):
                upstream = pipelines.get(upstream_name)
                if upstream is None:
                    continue
                if upstream.status in (PipelineStatus.FAILING, PipelineStatus.DEGRADED):
                    alert = Alert(
                        pipeline_name=name,
                        level=self._level,
                        message=(
                            f"Upstream pipeline '{upstream_name}' is "
                            f"{upstream.status.value}; '{name}' may be affected."
                        ),
                    )
                    results.append(
                        DependencyAlert(
                            pipeline_name=name,
                            upstream_name=upstream_name,
                            alert=alert,
                        )
                    )
        return results

    def affected_pipelines(self) -> List[str]:
        """Return unique names of pipelines with at least one failing upstream."""
        return list({da.pipeline_name for da in self.check()})
