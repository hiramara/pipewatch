"""Manager for collecting and querying baselines across pipelines."""
from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.core.baseline import Baseline
from pipewatch.core.reporter import Report


class BaselineManager:
    """Collects health-score baselines from successive reports."""

    def __init__(self) -> None:
        self._baselines: Dict[str, Baseline] = {}

    def ingest(self, report: Report) -> None:
        """Extract health scores from a report and record them."""
        for summary in report.pipelines:
            name = summary.pipeline_name
            if name not in self._baselines:
                self._baselines[name] = Baseline(pipeline_name=name)
            self._baselines[name].record("health_score", summary.health_score)

    def record(self, pipeline_name: str, metric_name: str, value: float) -> None:
        """Manually record an arbitrary metric for a pipeline."""
        if pipeline_name not in self._baselines:
            self._baselines[pipeline_name] = Baseline(pipeline_name=pipeline_name)
        self._baselines[pipeline_name].record(metric_name, value)

    def get(self, pipeline_name: str) -> Optional[Baseline]:
        return self._baselines.get(pipeline_name)

    def pipeline_names(self) -> List[str]:
        return list(self._baselines.keys())

    def is_degraded(
        self,
        pipeline_name: str,
        current_score: float,
        tolerance: float = 0.1,
    ) -> bool:
        """Return True if current_score is below baseline average by more than tolerance."""
        baseline = self.get(pipeline_name)
        if baseline is None:
            return False
        metric = baseline.get("health_score")
        if metric is None or metric.average is None:
            return False
        return current_score < (metric.average - tolerance)

    def to_dict(self) -> dict:
        return {
            name: b.to_dict() for name, b in self._baselines.items()
        }
