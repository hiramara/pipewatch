"""Export audit log contents to dict, JSON, or CSV."""

import csv
import io
import json
from typing import List, Dict, Any, Optional

from pipewatch.core.audit import AuditLog, AuditEventType


class AuditExporter:
    """Serialises an AuditLog into various output formats."""

    def __init__(self, log: AuditLog) -> None:
        self._log = log

    def to_dicts(
        self,
        pipeline_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
    ) -> List[Dict[str, Any]]:
        events = self._log.all_events()
        if pipeline_id:
            events = [e for e in events if e.pipeline_id == pipeline_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events]

    def to_json(
        self,
        pipeline_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        indent: int = 2,
    ) -> str:
        return json.dumps(self.to_dicts(pipeline_id=pipeline_id, event_type=event_type), indent=indent)

    def to_csv(
        self,
        pipeline_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
    ) -> str:
        rows = self.to_dicts(pipeline_id=pipeline_id, event_type=event_type)
        if not rows:
            return ""
        buf = io.StringIO()
        fieldnames = ["event_type", "pipeline_id", "timestamp", "actor", "details"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            row["details"] = json.dumps(row.get("details", {}))
            writer.writerow(row)
        return buf.getvalue()
