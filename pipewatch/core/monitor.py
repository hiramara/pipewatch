"""Monitor module for aggregating pipeline health and triggering alerts."""

from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.check import CheckStatus


class Monitor:
    """Aggregates pipeline health and manages alert lifecycle."""

    def __init__(self, name: str):
        self.name = name
        self.pipelines: Dict[str, Pipeline] = {}
        self.alerts: List[Alert] = []
        self.created_at: datetime = datetime.utcnow()
        self.last_evaluated: Optional[datetime] = None

    def register_pipeline(self, pipeline: Pipeline) -> None:
        """Register a pipeline for monitoring."""
        if pipeline.pipeline_id in self.pipelines:
            raise ValueError(f"Pipeline '{pipeline.pipeline_id}' is already registered.")
        self.pipelines[pipeline.pipeline_id] = pipeline

    def unregister_pipeline(self, pipeline_id: str) -> None:
        """Remove a pipeline from monitoring."""
        if pipeline_id not in self.pipelines:
            raise KeyError(f"Pipeline '{pipeline_id}' not found.")
        self.pipelines.pop(pipeline_id)

    def evaluate(self) -> List[Alert]:
        """Evaluate all registered pipelines and generate alerts for failures."""
        new_alerts: List[Alert] = []
        self.last_evaluated = datetime.utcnow()

        for pipeline in self.pipelines.values():
            for check in pipeline.checks:
                if check.status == CheckStatus.FAIL:
                    level = AlertLevel.CRITICAL if pipeline.status == PipelineStatus.FAILED else AlertLevel.WARNING
                    alert = Alert(
                        pipeline_id=pipeline.pipeline_id,
                        check_name=check.name,
                        level=level,
                        message=check.failure_reason or f"Check '{check.name}' failed.",
                    )
                    self.alerts.append(alert)
                    new_alerts.append(alert)

        return new_alerts

    def active_alerts(self) -> List[Alert]:
        """Return all unresolved alerts."""
        return [a for a in self.alerts if not a.resolved]

    def summary(self) -> Dict:
        """Return a summary of current monitor state."""
        return {
            "monitor": self.name,
            "pipelines": len(self.pipelines),
            "active_alerts": len(self.active_alerts()),
            "total_alerts": len(self.alerts),
            "last_evaluated": self.last_evaluated.isoformat() if self.last_evaluated else None,
        }

    def __repr__(self) -> str:
        return (
            f"Monitor(name={self.name!r}, pipelines={len(self.pipelines)}, "
            f"active_alerts={len(self.active_alerts())})"
        )
