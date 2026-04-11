"""Escalation policy: promote alert level after repeated breaches."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from pipewatch.core.alert import Alert, AlertLevel


@dataclass
class EscalationPolicy:
    """Defines how many consecutive breaches trigger an escalation."""

    warning_to_critical: int = 3   # breaches before WARNING -> CRITICAL
    cooldown_seconds: float = 300  # seconds of silence before counter resets

    def to_dict(self) -> dict:
        return {
            "warning_to_critical": self.warning_to_critical,
            "cooldown_seconds": self.cooldown_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EscalationPolicy":
        return cls(
            warning_to_critical=data.get("warning_to_critical", 3),
            cooldown_seconds=data.get("cooldown_seconds", 300),
        )


@dataclass
class _PipelineCounter:
    count: int = 0
    last_seen: Optional[datetime] = None


class EscalationManager:
    """Tracks consecutive breach counts per pipeline and escalates alerts."""

    def __init__(self, policy: Optional[EscalationPolicy] = None) -> None:
        self._policy = policy or EscalationPolicy()
        self._counters: Dict[str, _PipelineCounter] = {}

    @property
    def policy(self) -> EscalationPolicy:
        return self._policy

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _counter(self, pipeline_id: str) -> _PipelineCounter:
        if pipeline_id not in self._counters:
            self._counters[pipeline_id] = _PipelineCounter()
        return self._counters[pipeline_id]

    def record_breach(self, pipeline_id: str) -> None:
        """Increment the breach counter, respecting cooldown."""
        now = self._now()
        c = self._counter(pipeline_id)
        if c.last_seen is not None:
            elapsed = (now - c.last_seen).total_seconds()
            if elapsed > self._policy.cooldown_seconds:
                c.count = 0
        c.count += 1
        c.last_seen = now

    def clear(self, pipeline_id: str) -> None:
        """Reset counter when a pipeline recovers."""
        self._counters.pop(pipeline_id, None)

    def escalate(self, alert: Alert) -> Alert:
        """Return a (possibly escalated) copy of *alert*."""
        if alert.level != AlertLevel.WARNING:
            return alert
        c = self._counter(alert.pipeline_id)
        if c.count >= self._policy.warning_to_critical:
            return Alert(
                pipeline_id=alert.pipeline_id,
                message=f"[ESCALATED] {alert.message}",
                level=AlertLevel.CRITICAL,
                source=alert.source,
            )
        return alert

    def breach_count(self, pipeline_id: str) -> int:
        return self._counters.get(pipeline_id, _PipelineCounter()).count
