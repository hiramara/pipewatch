"""Export pipeline annotations to JSON or CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import List, Optional

from pipewatch.core.pipeline_annotator import Annotation, PipelineAnnotator


class AnnotationExporter:
    """Serialise annotations from a :class:`PipelineAnnotator`."""

    def __init__(
        self,
        annotator: PipelineAnnotator,
        pipeline_name: Optional[str] = None,
    ) -> None:
        self._annotator = annotator
        self._pipeline_name = pipeline_name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect(self) -> List[Annotation]:
        if self._pipeline_name is not None:
            return self._annotator.get(self._pipeline_name)
        notes: List[Annotation] = []
        for name in self._annotator.all_pipeline_names():
            notes.extend(self._annotator.get(name))
        return notes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def to_dicts(self) -> List[dict]:
        """Return a list of annotation dicts."""
        return [a.to_dict() for a in self._collect()]

    def to_json(self, indent: int = 2) -> str:
        """Serialise annotations to a JSON string."""
        return json.dumps(self.to_dicts(), indent=indent)

    def to_csv(self) -> str:
        """Serialise annotations to a CSV string."""
        fieldnames = ["pipeline_name", "author", "created_at", "text"]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in self.to_dicts():
            writer.writerow(row)
        return buf.getvalue()
