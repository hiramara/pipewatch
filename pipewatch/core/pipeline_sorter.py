"""Sorting utilities for pipeline summaries and reports."""

from __future__ import annotations

from enum import Enum
from typing import List

from pipewatch.core.reporter import PipelineSummary, Report


class SortKey(str, Enum):
    NAME = "name"
    STATUS = "status"
    HEALTH = "health"
    FAILING_CHECKS = "failing_checks"


# Status ordering: failing pipelines bubble to the top
_STATUS_ORDER = {
    "failing": 0,
    "unknown": 1,
    "healthy": 2,
}


class PipelineSorter:
    """Sort a list of PipelineSummary objects by one or more keys."""

    def __init__(self, key: SortKey = SortKey.NAME, reverse: bool = False) -> None:
        if not isinstance(key, SortKey):
            key = SortKey(key)
        self._key = key
        self._reverse = reverse

    @property
    def key(self) -> SortKey:
        return self._key

    @property
    def reverse(self) -> bool:
        return self._reverse

    def sort(self, summaries: List[PipelineSummary]) -> List[PipelineSummary]:
        """Return a new sorted list; original is not mutated."""
        key_fn = self._key_fn()
        return sorted(summaries, key=key_fn, reverse=self._reverse)

    def sort_report(self, report: Report) -> Report:
        """Return a new Report whose pipelines list is sorted."""
        sorted_pipelines = self.sort(report.pipelines)
        return Report(
            pipelines=sorted_pipelines,
            total=report.total,
            healthy=report.healthy,
            failing=report.failing,
            generated_at=report.generated_at,
        )

    def _key_fn(self):
        if self._key == SortKey.NAME:
            return lambda s: s.name.lower()
        if self._key == SortKey.STATUS:
            return lambda s: _STATUS_ORDER.get(s.status, 99)
        if self._key == SortKey.HEALTH:
            return lambda s: s.health_score
        if self._key == SortKey.FAILING_CHECKS:
            return lambda s: s.failing_checks
        raise ValueError(f"Unknown sort key: {self._key}")
