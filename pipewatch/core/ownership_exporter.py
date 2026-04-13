"""Export pipeline ownership data to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List, Optional

from pipewatch.core.pipeline_ownership import OwnershipRegistry


class OwnershipExporter:
    """Serialises an OwnershipRegistry to various output formats."""

    def __init__(self, registry: OwnershipRegistry) -> None:
        self._registry = registry

    def to_dicts(self, pipeline: Optional[str] = None) -> List[dict]:
        """Return ownership records, optionally filtered to one pipeline."""
        records = self._registry.to_dicts()
        if pipeline is not None:
            records = [r for r in records if r["pipeline"] == pipeline]
        return records

    def to_json(self, pipeline: Optional[str] = None, indent: int = 2) -> str:
        """Serialise ownership records to a JSON string."""
        return json.dumps(self.to_dicts(pipeline), indent=indent)

    def to_csv(self, pipeline: Optional[str] = None) -> str:
        """Serialise ownership records to a CSV string."""
        records = self.to_dicts(pipeline)
        if not records:
            return ""
        fieldnames = ["pipeline", "name", "email", "team"]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({k: record.get(k, "") or "" for k in fieldnames})
        return buf.getvalue()
