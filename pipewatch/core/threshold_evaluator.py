"""Evaluates a set of thresholds against pipeline metrics and emits alerts."""
from typing import List, Dict, Any
from datetime import datetime, timezone

from pipewatch.core.threshold import Threshold
from pipewatch.core.alert import Alert, AlertLevel


class ThresholdEvaluator:
    """Runs a collection of thresholds against a metric dict and produces alerts."""

    def __init__(self, thresholds: List[Threshold]) -> None:
        self.thresholds = thresholds

    def evaluate(self, pipeline_name: str, metrics: Dict[str, float]) -> List[Alert]:
        """Return a list of Alert objects for every breached threshold."""
        alerts: List[Alert] = []
        for threshold in self.thresholds:
            metric_value = metrics.get(threshold.name)
            if metric_value is None:
                continue
            if threshold.evaluate(metric_value):
                alert = Alert(
                    pipeline_name=pipeline_name,
                    level=self._level_for(threshold),
                    message=(
                        f"Metric '{threshold.name}' breached threshold: "
                        f"{metric_value} {threshold.operator.value} {threshold.value}"
                    ),
                    triggered_at=datetime.now(timezone.utc),
                )
                alerts.append(alert)
        return alerts

    @staticmethod
    def _level_for(threshold: Threshold) -> AlertLevel:
        """Derive an alert level from the threshold name convention."""
        name_lower = threshold.name.lower()
        if "critical" in name_lower or "error" in name_lower:
            return AlertLevel.CRITICAL
        if "warn" in name_lower:
            return AlertLevel.WARNING
        return AlertLevel.INFO

    def summary(self) -> Dict[str, Any]:
        return {
            "threshold_count": len(self.thresholds),
            "thresholds": [t.to_dict() for t in self.thresholds],
        }
