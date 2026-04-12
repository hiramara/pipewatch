"""Sends notifications for stale pipelines detected by the watchdog."""

from __future__ import annotations

from typing import List, Optional

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.notifier import Notifier
from pipewatch.core.pipeline_watchdog import PipelineWatchdog, StalePipelineResult
from pipewatch.core.pipeline import Pipeline


class WatchdogNotifier:
    """Combines watchdog evaluation with alert dispatch."""

    def __init__(self, watchdog: PipelineWatchdog, notifier: Notifier) -> None:
        self._watchdog = watchdog
        self._notifier = notifier

    def _build_alert(self, result: StalePipelineResult) -> Alert:
        return Alert(
            pipeline_name=result.pipeline_name,
            level=AlertLevel.WARNING,
            message=(
                f"Pipeline '{result.pipeline_name}' has been silent for "
                f"{result.silence_seconds:.0f}s (last updated: "
                f"{result.last_updated.isoformat()})."
            ),
        )

    def check_and_notify(
        self,
        pipelines: List[Pipeline],
        now=None,
    ) -> List[StalePipelineResult]:
        """Evaluate staleness; send alerts for stale pipelines. Returns stale results."""
        stale = self._watchdog.stale_only(pipelines, now=now)
        for result in stale:
            alert = self._build_alert(result)
            self._notifier.send(alert)
        return stale
