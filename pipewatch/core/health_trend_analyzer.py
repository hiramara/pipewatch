"""Analyzes health trends across all pipelines in a report."""
from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.core.pipeline_health_trend import (
    HealthTrend,
    TrendDirection,
    compute_trend,
)
from pipewatch.core.history_collector import HistoryCollector
from pipewatch.core.reporter import Report


class HealthTrendAnalyzer:
    """Computes per-pipeline health trends using collected history."""

    def __init__(
        self,
        collector: HistoryCollector,
        min_samples: int = 2,
        stable_threshold: float = 0.05,
    ) -> None:
        self._collector = collector
        self._min_samples = min_samples
        self._stable_threshold = stable_threshold

    def analyze(self, report: Report) -> Dict[str, HealthTrend]:
        """Return a mapping of pipeline name → :class:`HealthTrend`."""
        trends: Dict[str, HealthTrend] = {}
        for summary in report.pipelines:
            name = summary.name
            scores = self._collector.trend_summary(name)
            trends[name] = compute_trend(
                name,
                scores,
                min_samples=self._min_samples,
                stable_threshold=self._stable_threshold,
            )
        return trends

    def degrading(self, report: Report) -> List[HealthTrend]:
        """Return only pipelines whose trend is degrading."""
        return [
            t
            for t in self.analyze(report).values()
            if t.direction == TrendDirection.DEGRADING
        ]

    def improving(self, report: Report) -> List[HealthTrend]:
        """Return only pipelines whose trend is improving."""
        return [
            t
            for t in self.analyze(report).values()
            if t.direction == TrendDirection.IMPROVING
        ]

    def to_dicts(self, report: Report) -> List[dict]:
        """Return all trends serialised as plain dicts."""
        return [t.to_dict() for t in self.analyze(report).values()]
