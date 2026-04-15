"""Export runbook entries to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import Callable, List, Optional

from pipewatch.core.pipeline_runbook import RunbookEntry, RunbookRegistry


class RunbookExporter:
    def __init__(
        self,
        registry: RunbookRegistry,
        pipeline_filter: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self._registry = registry
        self._filter = pipeline_filter

    def _collect(self) -> List[RunbookEntry]:
        entries = self._registry.all_entries()
        if self._filter:
            entries = [e for e in entries if self._filter(e.pipeline_name)]
        return entries

    def to_dicts(self) -> List[dict]:
        return [e.to_dict() for e in self._collect()]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dicts(), indent=indent)

    def to_csv(self) -> str:
        dicts = self.to_dicts()
        if not dicts:
            return ""
        buf = io.StringIO()
        fieldnames = ["pipeline_name", "title", "owner", "tags", "steps", "created_at"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in dicts:
            row = dict(row)
            row["tags"] = "|".join(row.get("tags", []))
            row["steps"] = "|".join(row.get("steps", []))
            writer.writerow(row)
        return buf.getvalue()
