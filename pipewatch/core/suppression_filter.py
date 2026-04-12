"""Notification filter that drops alerts for suppressed pipelines."""

from __future__ import annotations

from typing import List

from pipewatch.core.alert import Alert
from pipewatch.core.notifier import NotificationChannel
from pipewatch.core.suppression import SuppressionManager


class SuppressionFilter(NotificationChannel):
    """Wraps a NotificationChannel and silences alerts for suppressed pipelines."""

    def __init__(
        self,
        inner: NotificationChannel,
        manager: SuppressionManager,
    ) -> None:
        self._inner = inner
        self._manager = manager
        self._suppressed: List[Alert] = []

    @property
    def name(self) -> str:
        return f"SuppressionFilter({self._inner.name})"

    def send(self, alert: Alert) -> None:
        """Forward the alert unless the pipeline is currently suppressed."""
        pipeline_name = alert.pipeline_name
        if self._manager.is_suppressed(pipeline_name):
            self._suppressed.append(alert)
            return
        self._inner.send(alert)

    @property
    def suppressed(self) -> List[Alert]:
        """Return a copy of alerts that were suppressed."""
        return list(self._suppressed)

    def clear_suppressed(self) -> None:
        """Clear the suppressed alert history."""
        self._suppressed.clear()
