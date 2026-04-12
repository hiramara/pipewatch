"""SLA tracking for pipelines — defines SLA rules and evaluates breaches."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from pipewatch.core.alert import Alert, AlertLevel


@dataclass
class SLARule:
    """Defines an SLA expectation for a pipeline."""
    pipeline_name: str
    max_duration_seconds: float
    description: str = ""

    def is_breached(self, duration_seconds: float) -> bool:
        return duration_seconds > self.max_duration_seconds

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "max_duration_seconds": self.max_duration_seconds,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SLARule":
        return cls(
            pipeline_name=data["pipeline_name"],
            max_duration_seconds=data["max_duration_seconds"],
            description=data.get("description", ""),
        )


@dataclass
class SLABreach:
    """Represents a detected SLA breach for a pipeline."""
    pipeline_name: str
    rule: SLARule
    actual_duration_seconds: float
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def to_alert(self) -> Alert:
        excess = self.actual_duration_seconds - self.rule.max_duration_seconds
        return Alert(
            pipeline_name=self.pipeline_name,
            level=AlertLevel.WARNING,
            message=(
                f"SLA breached: ran {self.actual_duration_seconds:.1f}s "
                f"(limit {self.rule.max_duration_seconds:.1f}s, "
                f"+{excess:.1f}s over)"
            ),
        )

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "actual_duration_seconds": self.actual_duration_seconds,
            "max_duration_seconds": self.rule.max_duration_seconds,
            "excess_seconds": self.actual_duration_seconds - self.rule.max_duration_seconds,
            "detected_at": self.detected_at.isoformat(),
        }


class SLAEvaluator:
    """Evaluates pipeline run durations against registered SLA rules."""

    def __init__(self) -> None:
        self._rules: dict[str, SLARule] = {}

    def add_rule(self, rule: SLARule) -> None:
        self._rules[rule.pipeline_name] = rule

    def remove_rule(self, pipeline_name: str) -> None:
        self._rules.pop(pipeline_name, None)

    def get_rule(self, pipeline_name: str) -> Optional[SLARule]:
        return self._rules.get(pipeline_name)

    def evaluate(self, pipeline_name: str, duration_seconds: float) -> Optional[SLABreach]:
        rule = self._rules.get(pipeline_name)
        if rule is None:
            return None
        if rule.is_breached(duration_seconds):
            return SLABreach(
                pipeline_name=pipeline_name,
                rule=rule,
                actual_duration_seconds=duration_seconds,
            )
        return None

    def rules(self) -> list[SLARule]:
        return list(self._rules.values())
