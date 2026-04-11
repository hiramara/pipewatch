"""Rate limiter to throttle alert notifications per pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class RateLimitRule:
    """Defines how many alerts are allowed per window for a pipeline."""

    max_alerts: int = 5
    window_seconds: int = 60

    def to_dict(self) -> dict:
        return {
            "max_alerts": self.max_alerts,
            "window_seconds": self.window_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitRule":
        return cls(
            max_alerts=data.get("max_alerts", 5),
            window_seconds=data.get("window_seconds", 60),
        )


@dataclass
class _PipelineWindow:
    """Tracks alert timestamps within the current window for a pipeline."""

    timestamps: list = field(default_factory=list)

    def prune(self, cutoff: datetime) -> None:
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def count(self) -> int:
        return len(self.timestamps)

    def record(self, now: datetime) -> None:
        self.timestamps.append(now)


class RateLimiter:
    """Tracks per-pipeline alert rates and decides whether to allow sending."""

    DEFAULT_RULE = RateLimitRule()

    def __init__(self) -> None:
        self._rules: Dict[str, RateLimitRule] = {}
        self._windows: Dict[str, _PipelineWindow] = {}

    def set_rule(self, pipeline_name: str, rule: RateLimitRule) -> None:
        self._rules[pipeline_name] = rule

    def remove_rule(self, pipeline_name: str) -> None:
        self._rules.pop(pipeline_name, None)
        self._windows.pop(pipeline_name, None)

    def _rule_for(self, pipeline_name: str) -> RateLimitRule:
        return self._rules.get(pipeline_name, self.DEFAULT_RULE)

    def is_allowed(self, pipeline_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if an alert for this pipeline is within the rate limit."""
        now = now or datetime.utcnow()
        rule = self._rule_for(pipeline_name)
        window = self._windows.setdefault(pipeline_name, _PipelineWindow())
        cutoff = now - timedelta(seconds=rule.window_seconds)
        window.prune(cutoff)
        if window.count() < rule.max_alerts:
            window.record(now)
            return True
        return False

    def current_count(self, pipeline_name: str, now: Optional[datetime] = None) -> int:
        """Return the number of alerts recorded in the current window."""
        now = now or datetime.utcnow()
        rule = self._rule_for(pipeline_name)
        window = self._windows.get(pipeline_name)
        if window is None:
            return 0
        cutoff = now - timedelta(seconds=rule.window_seconds)
        window.prune(cutoff)
        return window.count()

    def reset(self, pipeline_name: str) -> None:
        """Clear the window for a pipeline (e.g. after a mute or resolve)."""
        self._windows.pop(pipeline_name, None)
