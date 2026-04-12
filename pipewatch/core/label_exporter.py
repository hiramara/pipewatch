"""Export pipeline labels to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List, Dict, Any

from pipewatch.core.pipeline_labeler import PipelineLabeler


class LabelExporter:
    """Serialise label data from a :class:`PipelineLabeler` instance."""

    def __init__(self, labeler: PipelineLabeler) -> None:
        self._labeler = labeler

    def to_dicts(self) -> List[Dict[str, Any]]:
        """Return a list of ``{pipeline, key, value}`` records."""
        records: List[Dict[str, Any]] = []
        for pipeline, labels in self._labeler.all_labels().items():
            for key, value in labels.items():
                records.append({"pipeline": pipeline, "key": key, "value": value})
        return records

    def to_json(self, indent: int = 2) -> str:
        """Serialise labels as a JSON string."""
        return json.dumps(self.to_dicts(), indent=indent)

    def to_csv(self) -> str:
        """Serialise labels as a CSV string with header."""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["pipeline", "key", "value"])
        writer.writeheader()
        writer.writerows(self.to_dicts())
        return buf.getvalue()
