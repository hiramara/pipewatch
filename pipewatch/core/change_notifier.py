"""Notify channels when pipeline state changes are detected."""

from __future__ import annotations

from typing import List, Optional

from pipewatch.core.pipeline_comparator import PipelineComparator, ComparisonResult
from pipewatch.core.snapshot import PipelineSnapshot
from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.notifier import NotificationChannel


class ChangeNotifier:
    """Detects pipeline state changes between snapshots and dispatches alerts."""

    def __init__(
        self,
        channels: Optional[List[NotificationChannel]] = None,
        comparator: Optional[PipelineComparator] = None,
    ) -> None:
        self._channels: List[NotificationChannel] = channels or []
        self._comparator = comparator or PipelineComparator()
        self._previous: Optional[PipelineSnapshot] = None
        self._last_result: Optional[ComparisonResult] = None

    def add_channel(self, channel: NotificationChannel) -> None:
        self._channels.append(channel)

    def observe(self, current: PipelineSnapshot) -> ComparisonResult:
        """Compare *current* against the last observed snapshot and send alerts."""
        result = self._comparator.compare(self._previous, current)
        self._last_result = result
        self._previous = current

        if result.has_changes:
            self._dispatch(result)

        return result

    def _dispatch(self, result: ComparisonResult) -> None:
        for change in result.newly_failing:
            alert = Alert(
                pipeline_name=change.pipeline_name,
                level=AlertLevel.CRITICAL,
                message=(
                    f"Pipeline '{change.pipeline_name}' transitioned to FAILING "
                    f"(health delta: {change.health_delta:+.2f})"
                ),
            )
            for channel in self._channels:
                channel.send(alert)

        for change in result.newly_healthy:
            alert = Alert(
                pipeline_name=change.pipeline_name,
                level=AlertLevel.INFO,
                message=(
                    f"Pipeline '{change.pipeline_name}' recovered to HEALTHY "
                    f"(health delta: {change.health_delta:+.2f})"
                ),
            )
            for channel in self._channels:
                channel.send(alert)

    @property
    def last_result(self) -> Optional[ComparisonResult]:
        return self._last_result

    @property
    def has_previous(self) -> bool:
        return self._previous is not None
