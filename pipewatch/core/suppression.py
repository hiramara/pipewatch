"""Time-window based alert suppression for pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SuppressionWindow:
    """Defines a time window during which alerts for a pipeline are suppressed."""

    pipeline_name: str
    start: datetime
    end: datetime
    reason: str = ""

    def is_active(self, at: Optional[datetime] = None) -> bool:
        """Return True if the suppression window is currently active."""
        now = at or datetime.now(timezone.utc)
        return self.start <= now <= self.end

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "reason": self.reason,
            "active": self.is_active(),
        }

    def __repr__(self) -> str:
        status = "active" if self.is_active() else "inactive"
        return (
            f"SuppressionWindow(pipeline={self.pipeline_name!r}, "
            f"start={self.start.isoformat()}, end={self.end.isoformat()}, "
            f"status={status})"
        )


class SuppressionManager:
    """Manages suppression windows across pipelines."""

    def __init__(self) -> None:
        self._windows: Dict[str, List[SuppressionWindow]] = {}

    def add(self, window: SuppressionWindow) -> None:
        """Register a suppression window for a pipeline."""
        self._windows.setdefault(window.pipeline_name, []).append(window)

    def remove(self, pipeline_name: str, start: datetime) -> bool:
        """Remove a specific suppression window by pipeline name and start time."""
        windows = self._windows.get(pipeline_name, [])
        before = len(windows)
        self._windows[pipeline_name] = [
            w for w in windows if w.start != start
        ]
        return len(self._windows[pipeline_name]) < before

    def is_suppressed(self, pipeline_name: str, at: Optional[datetime] = None) -> bool:
        """Return True if any active window covers the given pipeline."""
        return any(
            w.is_active(at)
            for w in self._windows.get(pipeline_name, [])
        )

    def active_windows(self, at: Optional[datetime] = None) -> List[SuppressionWindow]:
        """Return all currently active suppression windows."""
        result = []
        for windows in self._windows.values():
            result.extend(w for w in windows if w.is_active(at))
        return result

    def purge_expired(self, at: Optional[datetime] = None) -> int:
        """Remove all expired windows; return the count removed."""
        now = at or datetime.now(timezone.utc)
        removed = 0
        for name in list(self._windows):
            before = len(self._windows[name])
            self._windows[name] = [w for w in self._windows[name] if w.end >= now]
            removed += before - len(self._windows[name])
        return removed
