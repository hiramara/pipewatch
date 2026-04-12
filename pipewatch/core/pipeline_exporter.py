"""Export pipeline summaries to various formats for external consumption."""

from __future__ import annotations

import csv
import io
import json
from typing import List, Optional

from pipewatch.core.reporter import PipelineSummary, Report


class PipelineExporter:
    """Exports pipeline summary data from a Report to JSON, CSV, or plain dicts."""

    def __init__(self, report: Report) -> None:
        self._report = report

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def to_dicts(self, pipeline_names: Optional[List[str]] = None) -> List[dict]:
        """Return a list of dicts for each pipeline summary.

        Args:
            pipeline_names: Optional list of names to include. If None, all
                pipelines are exported.
        """
        summaries = self._filter(pipeline_names)
        return [self._summary_to_dict(s) for s in summaries]

    def to_json(self, pipeline_names: Optional[List[str]] = None, indent: int = 2) -> str:
        """Serialize pipeline summaries to a JSON string."""
        return json.dumps(self.to_dicts(pipeline_names), indent=indent, default=str)

    def to_csv(self, pipeline_names: Optional[List[str]] = None) -> str:
        """Serialize pipeline summaries to a CSV string."""
        rows = self.to_dicts(pipeline_names)
        if not rows:
            return ""
        buf = io.StringIO()
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _filter(self, names: Optional[List[str]]) -> List[PipelineSummary]:
        summaries = self._report.pipelines
        if names is not None:
            name_set = set(names)
            summaries = [s for s in summaries if s.name in name_set]
        return summaries

    @staticmethod
    def _summary_to_dict(summary: PipelineSummary) -> dict:
        return {
            "name": summary.name,
            "status": summary.status.value,
            "health_score": summary.health_score,
            "total_checks": summary.total_checks,
            "passed_checks": summary.passed_checks,
            "failed_checks": summary.failed_checks,
            "last_updated": summary.last_updated,
        }
