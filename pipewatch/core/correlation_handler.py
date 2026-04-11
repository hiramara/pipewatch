"""High-level handler that wires the CorrelationEngine into the monitor loop."""
from __future__ import annotations

from typing import List

from pipewatch.core.alert import Alert
from pipewatch.core.correlation import CorrelationEngine, Incident
from pipewatch.core.monitor import Monitor


class CorrelationHandler:
    """Processes alerts produced by a Monitor and groups them into incidents."""

    def __init__(
        self,
        monitor: Monitor,
        engine: CorrelationEngine | None = None,
        window_seconds: int = 300,
    ) -> None:
        self._monitor = monitor
        self._engine = engine or CorrelationEngine(window_seconds=window_seconds)

    @property
    def engine(self) -> CorrelationEngine:
        return self._engine

    def process(self) -> List[Incident]:
        """Evaluate all pipelines and correlate any raised alerts.

        Returns the list of incidents that received at least one new alert
        during this call.
        """
        alerts: List[Alert] = self._monitor.evaluate()
        touched: List[Incident] = []
        seen_ids: set[str] = set()

        for alert in alerts:
            incident = self._engine.ingest(alert)
            if incident.incident_id not in seen_ids:
                seen_ids.add(incident.incident_id)
                touched.append(incident)

        return touched

    def open_incidents(self) -> List[Incident]:
        return self._engine.open_incidents()

    def resolve_pipeline(self, pipeline_name: str) -> int:
        """Resolve all open incidents for *pipeline_name* and return count."""
        return self._engine.resolve_for_pipeline(pipeline_name)
