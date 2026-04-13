"""Export lifecycle events to JSON or CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import List, Optional

from pipewatch.core.lifecycle_manager import LifecycleManager
from pipewatch.core.pipeline_lifecycle import LifecycleEvent


class LifecycleExporter:
    def __init__(self, manager: LifecycleManager) -> None:
        self._manager = manager

    def to_dicts(
        self, pipeline_name: Optional[str] = None
    ) -> List[dict]:
        if pipeline_name:
            events = self._manager.transitions_for(pipeline_name)
        else:
            events = self._manager.all_events()
        return [e.to_dict() for e in events]

    def to_json(
        self, pipeline_name: Optional[str] = None, indent: int = 2
    ) -> str:
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
