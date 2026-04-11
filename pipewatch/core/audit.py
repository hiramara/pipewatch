"""Audit log for pipeline status changes and alert events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum


class AuditEventType(str, Enum):
    STATUS_CHANGE = "status_change"
    ALERT_RAISED = "alert_raised"
    ALERT_RESOLVED = "alert_resolved"
    PIPELINE_REGISTERED = "pipeline_registered"
    PIPELINE_UNREGISTERED = "pipeline_unregistered"
    CHECK_EXECUTED = "check_executed"


@dataclass
class AuditEvent:
    event_type: AuditEventType
    pipeline_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = field(default_factory=dict)
    actor: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "pipeline_id": self.pipeline_id,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "actor": self.actor,
        }

    def __repr__(self) -> str:
        return (
            f"AuditEvent(type={self.event_type.value!r}, "
            f"pipeline={self.pipeline_id!r}, "
            f"ts={self.timestamp.isoformat()!r})"
        )


class AuditLog:
    """In-memory audit log that records pipeline lifecycle events."""

    def __init__(self, max_events: int = 1000) -> None:
        self._events: List[AuditEvent] = []
        self._max_events = max_events

    def record(self, event: AuditEvent) -> None:
        """Append an event, evicting the oldest if at capacity."""
        if len(self._events) >= self._max_events:
            self._events.pop(0)
        self._events.append(event)

    def events_for(self, pipeline_id: str) -> List[AuditEvent]:
        """Return all events for a given pipeline, oldest first."""
        return [e for e in self._events if e.pipeline_id == pipeline_id]

    def events_by_type(self, event_type: AuditEventType) -> List[AuditEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def all_events(self) -> List[AuditEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:
        return len(self._events)
