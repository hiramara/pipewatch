"""Group pipelines by a shared attribute for batch reporting or alerting."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List

from pipewatch.core.reporter import PipelineSummary, Report


class PipelineGroup:
    """A named collection of pipeline summaries sharing a common grouping key."""

    def __init__(self, key: str, summaries: List[PipelineSummary]) -> None:
        self.key = key
        self._summaries = list(summaries)

    @property
    def summaries(self) -> List[PipelineSummary]:
        return list(self._summaries)

    @property
    def count(self) -> int:
        return len(self._summaries)

    @property
    def failing_count(self) -> int:
        return sum(1 for s in self._summaries if s.health_score < 1.0)

    @property
    def average_health(self) -> float:
        if not self._summaries:
            return 1.0
        return sum(s.health_score for s in self._summaries) / len(self._summaries)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "count": self.count,
            "failing_count": self.failing_count,
            "average_health": round(self.average_health, 4),
            "pipelines": [s.name for s in self._summaries],
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"PipelineGroup(key={self.key!r}, count={self.count})"


class PipelineGrouper:
    """Groups pipeline summaries from a Report using a key function."""

    def __init__(self, key_fn: Callable[[PipelineSummary], str]) -> None:
        self._key_fn = key_fn

    def group(self, report: Report) -> Dict[str, PipelineGroup]:
        """Return a mapping of group key -> PipelineGroup."""
        buckets: Dict[str, List[PipelineSummary]] = defaultdict(list)
        for summary in report.pipelines:
            bucket_key = self._key_fn(summary)
            buckets[bucket_key].append(summary)
        return {
            k: PipelineGroup(key=k, summaries=v)
            for k, v in sorted(buckets.items())
        }

    def to_dicts(self, report: Report) -> List[dict]:
        """Return a list of group dicts, sorted by key."""
        return [g.to_dict() for g in self.group(report).values()]
