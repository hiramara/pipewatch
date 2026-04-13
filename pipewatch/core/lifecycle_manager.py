"""Manages lifecycle tracking across all monitored pipelines."""

from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import PipelineStatus
from pipewatch.core.pipeline_lifecycle import LifecycleEvent, PipelineLifecycle


class LifecycleManager:
    """Observes a Monitor and records every pipeline status transition."""

    def __init__(self) -> None:
        self._lifecycles: Dict[str, PipelineLifecycle] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe(self, monitor: Monitor) -> List[LifecycleEvent]:
        """Snapshot current pipeline statuses and record any transitions.

        Returns the list of new LifecycleEvents produced in this pass.
        """
        new_events: List[LifecycleEvent] = []
        for name, pipeline in monitor.pipelines.items():
            lc = self._get_or_create(name)
            event = lc.record(pipeline.status)
            if event is not None:
                new_events.append(event)
        return new_events

    def get(self, pipeline_name: str) -> Optional[PipelineLifecycle]:
        return self._lifecycles.get(pipeline_name)

    def all_events(self) -> List[LifecycleEvent]:
        events: List[LifecycleEvent] = []
        for lc in self._lifecycles.values():
            events.extend(lc.events)
        events.sort(key=lambda e: e.timestamp)
        return events

    def transitions_for(self, pipeline_name: str) -> List[LifecycleEvent]:
        lc = self._lifecycles.get(pipeline_name)
        return lc.events if lc else []

    def pipelines_that_degraded(self) -> List[str]:
        """Return names of pipelines whose last transition moved to a worse state."""
        _worse = {PipelineStatus.FAILING, PipelineStatus.UNKNOWN}
        result = []
        for name, lc in self._lifecycles.items():
            last = lc.last_transition()
            if last and last.to_status in _worse:
                result.append(name)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create(self, name: str) -> PipelineLifecycle:
        if name not in self._lifecycles:
            self._lifecycles[name] = PipelineLifecycle(name)
        return self._lifecycles[name]
