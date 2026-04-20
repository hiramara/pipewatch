"""Export incident log entries to various formats."""
from __future__ import annotations

import csv
import io
import json
from typing import List, Optional

from pipewatch.core.pipeline_incident_log import IncidentLogEntry, PipelineIncidentLog


class IncidentLogExporter:
    """Serialises incident log entries to dicts, JSON, or CSV."""

    def __init__(self, log: PipelineIncidentLog) -> None:
        self._log = log

    def _collect(self, pipeline_name: Optional[str] = None) -> List[IncidentLogEntry]:
        if pipeline_name:
            return self._log.for_pipeline(pipeline_name)
        return self._log.all_entries()

    def to_dicts(self, pipeline_name: Optional[str] = None) -> List[dict]:
        return [e.to_dict() for e in self._collect(pipeline_name)]

    def to_json(self, pipeline_name: Optional[str] = None, indent: int = 2) -> str:
        return json.dumps(self.to_dicts(pipeline_name), indent=indent)

    def to_csv(self, pipeline_name: Optional[str] = None) -> str:
        rows = self.to_dicts(pipeline_name)
        if not rows:
            return ""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()
