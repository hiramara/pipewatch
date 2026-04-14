"""Pipeline quota tracking — enforce run count and data volume limits."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class QuotaRule:
    """Defines a quota limit for a pipeline."""
    pipeline_name: str
    max_runs: Optional[int] = None          # max runs within the window
    max_records: Optional[int] = None       # max records processed within the window
    window_seconds: int = 86400             # default: 24-hour window

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "max_runs": self.max_runs,
            "max_records": self.max_records,
            "window_seconds": self.window_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuotaRule":
        return cls(
            pipeline_name=data["pipeline_name"],
            max_runs=data.get("max_runs"),
            max_records=data.get("max_records"),
            window_seconds=data.get("window_seconds", 86400),
        )


@dataclass
class QuotaUsage:
    """Tracks usage events for a single pipeline within a rolling window."""
    pipeline_name: str
    _run_timestamps: List[float] = field(default_factory=list)
    _record_counts: List[tuple] = field(default_factory=list)  # (timestamp, count)

    def record_run(self, ts: Optional[float] = None) -> None:
        self._run_timestamps.append(ts or datetime.now(timezone.utc).timestamp())

    def record_records(self, count: int, ts: Optional[float] = None) -> None:
        self._record_counts.append((ts or datetime.now(timezone.utc).timestamp(), count))

    def runs_in_window(self, window_seconds: int) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - window_seconds
        return sum(1 for t in self._run_timestamps if t >= cutoff)

    def records_in_window(self, window_seconds: int) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - window_seconds
        return sum(c for t, c in self._record_counts if t >= cutoff)


@dataclass
class QuotaBreach:
    pipeline_name: str
    rule: QuotaRule
    runs_used: int
    records_used: int
    breached_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def run_limit_exceeded(self) -> bool:
        return self.rule.max_runs is not None and self.runs_used > self.rule.max_runs

    @property
    def record_limit_exceeded(self) -> bool:
        return self.rule.max_records is not None and self.records_used > self.rule.max_records

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "runs_used": self.runs_used,
            "records_used": self.records_used,
            "run_limit_exceeded": self.run_limit_exceeded,
            "record_limit_exceeded": self.record_limit_exceeded,
            "breached_at": self.breached_at.isoformat(),
        }


class QuotaEvaluator:
    """Evaluates quota rules against current usage."""

    def __init__(self) -> None:
        self._rules: Dict[str, QuotaRule] = {}
        self._usage: Dict[str, QuotaUsage] = {}

    def add_rule(self, rule: QuotaRule) -> None:
        self._rules[rule.pipeline_name] = rule

    def remove_rule(self, pipeline_name: str) -> None:
        self._rules.pop(pipeline_name, None)

    def usage(self, pipeline_name: str) -> QuotaUsage:
        if pipeline_name not in self._usage:
            self._usage[pipeline_name] = QuotaUsage(pipeline_name=pipeline_name)
        return self._usage[pipeline_name]

    def record_run(self, pipeline_name: str, ts: Optional[float] = None) -> None:
        self.usage(pipeline_name).record_run(ts)

    def record_records(self, pipeline_name: str, count: int, ts: Optional[float] = None) -> None:
        self.usage(pipeline_name).record_records(count, ts)

    def check(self, pipeline_name: str) -> Optional[QuotaBreach]:
        rule = self._rules.get(pipeline_name)
        if rule is None:
            return None
        u = self.usage(pipeline_name)
        runs = u.runs_in_window(rule.window_seconds)
        records = u.records_in_window(rule.window_seconds)
        run_breached = rule.max_runs is not None and runs > rule.max_runs
        rec_breached = rule.max_records is not None and records > rule.max_records
        if run_breached or rec_breached:
            return QuotaBreach(
                pipeline_name=pipeline_name,
                rule=rule,
                runs_used=runs,
                records_used=records,
            )
        return None

    def check_all(self) -> List[QuotaBreach]:
        return [b for name in self._rules if (b := self.check(name)) is not None]
