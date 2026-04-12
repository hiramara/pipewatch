"""Attach human-readable annotations (notes) to pipeline summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Annotation:
    """A timestamped note attached to a pipeline."""

    pipeline_name: str
    text: str
    author: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "text": self.text,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"Annotation(pipeline={self.pipeline_name!r}, "
            f"author={self.author!r}, text={self.text!r})"
        )


class PipelineAnnotator:
    """Store and retrieve annotations keyed by pipeline name."""

    def __init__(self) -> None:
        self._store: Dict[str, List[Annotation]] = {}

    def annotate(
        self,
        pipeline_name: str,
        text: str,
        author: str = "system",
    ) -> Annotation:
        """Add an annotation to *pipeline_name* and return it."""
        if not text.strip():
            raise ValueError("Annotation text must not be empty.")
        note = Annotation(pipeline_name=pipeline_name, text=text, author=author)
        self._store.setdefault(pipeline_name, []).append(note)
        return note

    def get(self, pipeline_name: str) -> List[Annotation]:
        """Return all annotations for *pipeline_name* (oldest first)."""
        return list(self._store.get(pipeline_name, []))

    def remove(self, pipeline_name: str, index: int) -> None:
        """Remove the annotation at *index* for *pipeline_name*."""
        notes = self._store.get(pipeline_name, [])
        if index < 0 or index >= len(notes):
            raise IndexError(f"No annotation at index {index} for {pipeline_name!r}.")
        notes.pop(index)

    def clear(self, pipeline_name: str) -> None:
        """Remove all annotations for *pipeline_name*."""
        self._store.pop(pipeline_name, None)

    def all_pipeline_names(self) -> List[str]:
        """Return names of pipelines that have at least one annotation."""
        return [name for name, notes in self._store.items() if notes]

    def latest(self, pipeline_name: str) -> Optional[Annotation]:
        """Return the most recent annotation for *pipeline_name*, or None."""
        notes = self._store.get(pipeline_name, [])
        return notes[-1] if notes else None
