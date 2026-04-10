"""Collects run records from reporter output and feeds them into PipelineHistory."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipewatch.core.history import PipelineHistory, RunRecord
from pipewatch.core.reporter import Report


class HistoryCollector:
    """Bridges Reporter output into PipelineHistory storage."""

    def __init__(
        self,
        history: Optional[PipelineHistory] = None,
        persist_path: Optional[Path] = None,
    ) -> None:
        self.history = history or PipelineHistory()
        self.persist_path = persist_path

        if self.persist_path:
            self.history.load(self.persist_path)

    def collect(self, report: Report) -> None:
        """Extract pipeline summaries from a report and record them."""
        for summary in report.pipelines:
            record = RunRecord(
                pipeline_name=summary.name,
                status=summary.status,
                health_score=summary.health_score,
                metadata={
                    "total_checks": summary.total_checks,
                    "passed_checks": summary.passed_checks,
                    "failed_checks": summary.failed_checks,
                    "active_alerts": summary.active_alerts,
                },
            )
            self.history.record(record)

        if self.persist_path:
            self.history.save(self.persist_path)

    def trend_summary(self, pipeline_name: str, last_n: int = 5) -> dict:
        """Return a brief trend dict for a given pipeline."""
        records = self.history.get(pipeline_name)[-last_n:]
        if not records:
            return {"pipeline": pipeline_name, "records": 0}
        statuses = [r.status for r in records]
        scores = [r.health_score for r in records]
        return {
            "pipeline": pipeline_name,
            "records": len(records),
            "latest_status": statuses[-1],
            "avg_health": round(sum(scores) / len(scores), 4),
            "min_health": min(scores),
            "max_health": max(scores),
            "status_sequence": statuses,
        }
