"""Exports health trend data to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List, Optional

from pipewatch.core.health_trend_analyzer import HealthTrendAnalyzer
from pipewatch.core.reporter import Report


class TrendExporter:
    """Serialises health trend analysis results."""

    def __init__(self, analyzer: HealthTrendAnalyzer) -> None:
        self._analyzer = analyzer

    def to_dicts(self, report: Report) -> List[dict]:
        return self._analyzer.to_dicts(report)

    def to_json(self, report: Report, indent: int = 2) -> str:
        return json.dumps(self.to_dicts(report), indent=indent)

    def to_csv(self, report: Report) -> str:
        rows = self.to_dicts(report)
        if not rows:
            return ""
        buf = io.StringIO()
        fieldnames = ["pipeline_name", "direction", "delta", "scores"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            row = dict(row)
            row["scores"] = "|".join(str(s) for s in row.get("scores", []))
            writer.writerow(row)
        return buf.getvalue()
