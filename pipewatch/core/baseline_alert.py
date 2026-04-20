"""Generate alerts when pipelines deviate from their baseline."""
from __future__ import annotations

from typing import List

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.baseline_manager import BaselineManager
from pipewatch.core.reporter import Report


class BaselineAlerter:
    """Compares a report against stored baselines and emits degradation alerts."""

    def __init__(
        self,
        manager: BaselineManager,
        tolerance: float = 0.1,
        level: AlertLevel = AlertLevel.WARNING,
    ) -> None:
        self._manager = manager
        self._tolerance = tolerance
        self._level = level

    def _build_message(self, name: str, health_score: float, avg: float) -> str:
        """Format a human-readable degradation message for a pipeline."""
        return (
            f"Pipeline '{name}' health score {health_score:.2f} "
            f"is below baseline average {avg:.2f} "
            f"(tolerance \u00b1{self._tolerance:.2f})"
        )

    def check(self, report: Report) -> List[Alert]:
        """Return a list of alerts for pipelines that have degraded below baseline."""
        alerts: List[Alert] = []
        for summary in report.pipelines:
            name = summary.pipeline_name
            if self._manager.is_degraded(name, summary.health_score, self._tolerance):
                baseline = self._manager.get(name)
                avg = baseline.get("health_score").average if baseline else None  # type: ignore[union-attr]
                message = self._build_message(name, summary.health_score, avg)
                alerts.append(
                    Alert(
                        pipeline=name,
                        level=self._level,
                        message=message,
                    )
                )
        return alerts

    def check_and_ingest(self, report: Report) -> List[Alert]:
        """Check for degradation, then update the baseline with the new report."""
        alerts = self.check(report)
        self._manager.ingest(report)
        return alerts
