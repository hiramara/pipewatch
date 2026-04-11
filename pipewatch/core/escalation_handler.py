"""Wires EscalationManager into the Monitor evaluation loop."""
from __future__ import annotations

from typing import List

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.escalation import EscalationManager, EscalationPolicy
from pipewatch.core.monitor import Monitor


class EscalationHandler:
    """Processes alerts from a Monitor, applies escalation, and returns
    the final (possibly promoted) alert list.

    Usage::

        handler = EscalationHandler(monitor, policy=EscalationPolicy(warning_to_critical=2))
        final_alerts = handler.process()
    """

    def __init__(
        self,
        monitor: Monitor,
        policy: EscalationPolicy | None = None,
    ) -> None:
        self._monitor = monitor
        self._manager = EscalationManager(policy)

    @property
    def manager(self) -> EscalationManager:
        return self._manager

    def process(self) -> List[Alert]:
        """Evaluate the monitor, record breaches, and return escalated alerts."""
        raw_alerts = self._monitor.evaluate()
        pipeline_ids_with_alerts = {a.pipeline_id for a in raw_alerts}

        # Clear counters for pipelines that are now healthy
        for pid in list(self._manager._counters):
            if pid not in pipeline_ids_with_alerts:
                self._manager.clear(pid)

        result: List[Alert] = []
        for alert in raw_alerts:
            if alert.level in (AlertLevel.WARNING, AlertLevel.CRITICAL):
                self._manager.record_breach(alert.pipeline_id)
            result.append(self._manager.escalate(alert))

        return result
