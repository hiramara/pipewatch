"""Persistent incident log for tracking pipeline alert events over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.core.alert import Alert, AlertLevel


@dataclass
class IncidentLogEntry:
    pipeline_name: str
    alert_level: AlertLevel
    message: str
    raised_at: datetime
    resolved_at: Optional[datetime] = None

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.resolved_at is None:
            return None
        return (self.resolved_at - self.raised_at).total_seconds()

    def resolve(self, at: Optional[datetime] = None) -> None:
        self.resolved_at = at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "alert_level": self.alert_level.value,
            "message": self.message,
            "raised_at": self.raised_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "is_resolved": self.is_resolved,
            "duration_seconds": self.duration_seconds,
        }

    def __repr__(self) -> str:
        status = "resolved" if self.is_resolved else "open"
        return f"<IncidentLogEntry {self.pipeline_name!r} [{self.alert_level.value}] {status}>"


class PipelineIncidentLog:
    """Stores and queries incident log entries across pipelines."""

    def __init__(self) -> None:
        self._entries: List[IncidentLogEntry] = []

    def record(self, alert: Alert, raised_at: Optional[datetime] = None) -> IncidentLogEntry:
        entry = IncidentLogEntry(
            pipeline_name=alert.pipeline_name,
            alert_level=alert.level,
            message=alert.message,
            raised_at=raised_at or datetime.now(timezone.utc),
        )
        self._entries.append(entry)
        return entry

    def resolve_open(self, pipeline_name: str, at: Optional[datetime] = None) -> List[IncidentLogEntry]:
        resolved = []
        for entry in self._entries:
            if entry.pipeline_name == pipeline_name and not entry.is_resolved:
                entry.resolve(at)
                resolved.append(entry)
        return resolved

    def open_incidents(self) -> List[IncidentLogEntry]:
        return [e for e in self._entries if not e.is_resolved]

    def for_pipeline(self, pipeline_name: str) -> List[IncidentLogEntry]:
        return [e for e in self._entries if e.pipeline_name == pipeline_name]

    def all_entries(self) -> List[IncidentLogEntry]:
        return list(self._entries)

    def counts_by_pipeline(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for entry in self._entries:
            counts[entry.pipeline_name] = counts.get(entry.pipeline_name, 0) + 1
        return counts
