"""Pipeline lifecycle state tracking — records transitions between pipeline statuses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.core.pipeline import PipelineStatus


@dataclass
class LifecycleEvent:
    pipeline_name: str
    from_status: Optional[PipelineStatus]
    to_status: PipelineStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "from_status": self.from_status.value if self.from_status else None,
            "to_status": self.to_status.value,
            "timestamp": self.timestamp.isoformat(),
            "note": self.note,
        }

    def __repr__(self) -> str:
        frm = self.from_status.value if self.from_status else "none"
        return (
            f"<LifecycleEvent {self.pipeline_name}: {frm} -> {self.to_status.value}>"
        )


class PipelineLifecycle:
    """Tracks status transitions for a single pipeline."""

    def __init__(self, pipeline_name: str) -> None:
        self._name = pipeline_name
        self._events: List[LifecycleEvent] = []
        self._current: Optional[PipelineStatus] = None

    @property
    def pipeline_name(self) -> str:
        return self._name

    @property
    def current_status(self) -> Optional[PipelineStatus]:
        return self._current

    @property
    def events(self) -> List[LifecycleEvent]:
        return list(self._events)

    def record(self, status: PipelineStatus, note: str = "") -> Optional[LifecycleEvent]:
        """Record a new status.  Returns an event only when the status changes."""
        if status == self._current:
            return None
        event = LifecycleEvent(
            pipeline_name=self._name,
            from_status=self._current,
            to_status=status,
            note=note,
        )
        self._events.append(event)
        self._current = status
        return event

    def last_transition(self) -> Optional[LifecycleEvent]:
        return self._events[-1] if self._events else None

    def transition_count(self) -> int:
        return len(self._events)
