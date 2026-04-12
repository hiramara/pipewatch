"""Pipeline watchdog: detects stale pipelines that haven't reported in a given window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.core.pipeline import Pipeline


@dataclass
class StalenessRule:
    """Defines the maximum allowed silence duration for a pipeline."""

    pipeline_name: str
    max_silence_seconds: int

    def is_stale(self, last_updated: datetime, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return (now - last_updated).total_seconds() > self.max_silence_seconds

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "max_silence_seconds": self.max_silence_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StalenessRule":
        return cls(
            pipeline_name=data["pipeline_name"],
            max_silence_seconds=data["max_silence_seconds"],
        )


@dataclass
class StalePipelineResult:
    """Result of a watchdog evaluation for a single pipeline."""

    pipeline_name: str
    last_updated: datetime
    stale: bool
    silence_seconds: float

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "last_updated": self.last_updated.isoformat(),
            "stale": self.stale,
            "silence_seconds": round(self.silence_seconds, 2),
        }


class PipelineWatchdog:
    """Checks registered pipelines for staleness based on configurable rules."""

    def __init__(self, default_max_silence_seconds: int = 300) -> None:
        self._default_max_silence = default_max_silence_seconds
        self._rules: Dict[str, StalenessRule] = {}

    def add_rule(self, rule: StalenessRule) -> None:
        self._rules[rule.pipeline_name] = rule

    def remove_rule(self, pipeline_name: str) -> None:
        self._rules.pop(pipeline_name, None)

    def evaluate(
        self, pipelines: List[Pipeline], now: Optional[datetime] = None
    ) -> List[StalePipelineResult]:
        now = now or datetime.utcnow()
        results = []
        for pipeline in pipelines:
            last_updated = pipeline.last_updated or datetime.utcfromtimestamp(0)
            rule = self._rules.get(
                pipeline.name,
                StalenessRule(pipeline.name, self._default_max_silence),
            )
            silence = (now - last_updated).total_seconds()
            results.append(
                StalePipelineResult(
                    pipeline_name=pipeline.name,
                    last_updated=last_updated,
                    stale=rule.is_stale(last_updated, now),
                    silence_seconds=silence,
                )
            )
        return results

    def stale_only(
        self, pipelines: List[Pipeline], now: Optional[datetime] = None
    ) -> List[StalePipelineResult]:
        return [r for r in self.evaluate(pipelines, now) if r.stale]
