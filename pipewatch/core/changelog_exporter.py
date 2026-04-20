"""Exports pipeline changelog entries to JSON or CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import List, Optional

from pipewatch.core.pipeline_changelog import PipelineChangelog


class ChangelogExporter:
    def __init__(self, changelog: PipelineChangelog) -> None:
        self._changelog = changelog

    def _collect(self, pipeline_name: Optional[str] = None) -> List[dict]:
        if pipeline_name is not None:
            entries = self._changelog.entries_for(pipeline_name)
        else:
            entries = self._changelog.all_entries()
        return [e.to_dict() for e in entries]

    def to_dicts(self, pipeline_name: Optional[str] = None) -> List[dict]:
        return self._collect(pipeline_name)

    def to_json(self, pipeline_name: Optional[str] = None, indent: int = 2) -> str:
        return json.dumps(self._collect(pipeline_name), indent=indent)

    def to_csv(self, pipeline_name: Optional[str] = None) -> str:
        rows = self._collect(pipeline_name)
        if not rows:
            return ""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            row = dict(row)
            row["tags"] = "|".join(row["tags"])
            writer.writerow(row)
        return buf.getvalue()
