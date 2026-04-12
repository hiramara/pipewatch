"""Aggregates pipeline summaries into grouped statistics by tag, status, or custom key."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from pipewatch.core.reporter import PipelineSummary, Report


@dataclass
class AggregateGroup:
    """A named group of pipeline summaries with computed statistics."""

    key: str
    summaries: List[PipelineSummary] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.summaries)

    @property
    def average_health(self) -> float:
        if not self.summaries:
            return 0.0
        return sum(s.health_score for s in self.summaries) / len(self.summaries)

    @property
    def failing_count(self) -> int:
        return sum(1 for s in self.summaries if s.status.value in ("failing", "degraded"))

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "count": self.count,
            "average_health": round(self.average_health, 4),
            "failing_count": self.failing_count,
            "pipelines": [s.pipeline_name for s in self.summaries],
        }


class Aggregator:
    """Groups pipeline summaries from a Report by a key function."""

    def __init__(self, key_fn: Callable[[PipelineSummary], str]) -> None:
        self._key_fn = key_fn

    def aggregate(self, report: Report) -> Dict[str, AggregateGroup]:
        """Return a dict of AggregateGroup keyed by the result of key_fn."""
        groups: Dict[str, AggregateGroup] = defaultdict(lambda: AggregateGroup(key=""))
        for summary in report.pipelines:
            key = self._key_fn(summary)
            if key not in groups:
                groups[key] = AggregateGroup(key=key)
            groups[key].summaries.append(summary)
        return dict(groups)

    def to_dicts(self, report: Report) -> List[dict]:
        return [g.to_dict() for g in self.aggregate(report).values()]


def by_status(summary: PipelineSummary) -> str:
    return summary.status.value


def by_tag(tag: str) -> Callable[[PipelineSummary], str]:
    """Return a key function that groups by whether a pipeline has the given tag."""
    def _fn(summary: PipelineSummary) -> str:
        tags = summary.metadata.get("tags", [])
        return tag if tag in tags else "_other"
    return _fn
