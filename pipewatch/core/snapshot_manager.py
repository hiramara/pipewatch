"""SnapshotManager: builds snapshots from a Monitor and tracks history."""

from __future__ import annotations

from collections import deque
from typing import Deque, List, Optional

from pipewatch.core.monitor import Monitor
from pipewatch.core.reporter import Reporter
from pipewatch.core.snapshot import PipelineSnapshot, Snapshot


class SnapshotManager:
    """Captures system snapshots and exposes diff / trend helpers."""

    def __init__(self, monitor: Monitor, maxlen: int = 50) -> None:
        self._monitor = monitor
        self._reporter = Reporter(monitor)
        self._history: Deque[Snapshot] = deque(maxlen=maxlen)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture(self) -> Snapshot:
        """Generate a snapshot from the current monitor state."""
        report = self._reporter.generate()
        snapshot = Snapshot()
        for summary in report.pipelines:
            ps = PipelineSnapshot(
                pipeline_id=summary.pipeline_id,
                name=summary.name,
                status=summary.status,
                health_score=summary.health_score,
            )
            snapshot.add(ps)
        self._history.append(snapshot)
        return snapshot

    def latest(self) -> Optional[Snapshot]:
        """Return the most recently captured snapshot."""
        return self._history[-1] if self._history else None

    def previous(self) -> Optional[Snapshot]:
        """Return the snapshot before the latest one."""
        if len(self._history) < 2:
            return None
        return self._history[-2]

    def last_diff(self) -> List[dict]:
        """Diff between the two most recent snapshots."""
        latest = self.latest()
        previous = self.previous()
        if latest is None or previous is None:
            return []
        return latest.diff(previous)

    def all_snapshots(self) -> List[Snapshot]:
        return list(self._history)

    @property
    def history_size(self) -> int:
        return len(self._history)
