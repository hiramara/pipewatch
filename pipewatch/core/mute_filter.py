"""Wraps a Notifier to skip alerts for muted pipelines."""

from __future__ import annotations

from typing import List

from pipewatch.core.alert import Alert
from pipewatch.core.mute_manager import MuteManager
from pipewatch.core.notifier import Notifier


class MuteFilter:
    """Decorates a Notifier, suppressing alerts whose pipeline is muted."""

    def __init__(self, notifier: Notifier, mute_manager: MuteManager) -> None:
        self._notifier = notifier
        self._mute_manager = mute_manager
        self._suppressed: List[Alert] = []

    def send(self, alerts: List[Alert]) -> None:
        """Forward only alerts whose pipeline is not muted."""
        allowed: List[Alert] = []
        for alert in alerts:
            if self._mute_manager.is_muted(alert.pipeline_name):
                self._suppressed.append(alert)
            else:
                allowed.append(alert)
        if allowed:
            self._notifier.send(allowed)

    @property
    def suppressed(self) -> List[Alert]:
        """Alerts suppressed since this filter was created."""
        return list(self._suppressed)

    def clear_suppressed(self) -> None:
        self._suppressed.clear()
