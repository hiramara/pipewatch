"""Filter pipelines by status, health score, or custom predicates."""

from __future__ import annotations

from typing import Callable, List, Optional

from pipewatch.core.pipeline import Pipeline, PipelineStatus


class PipelineFilter:
    """Provides filtering utilities for collections of Pipeline objects."""

    def __init__(self, pipelines: List[Pipeline]) -> None:
        self._pipelines = list(pipelines)

    # ------------------------------------------------------------------
    # Status-based filters
    # ------------------------------------------------------------------

    def by_status(self, status: PipelineStatus) -> List[Pipeline]:
        """Return pipelines whose current status matches *status*."""
        return [p for p in self._pipelines if p.status == status]

    def healthy(self) -> List[Pipeline]:
        """Return pipelines with a HEALTHY status."""
        return self.by_status(PipelineStatus.HEALTHY)

    def failing(self) -> List[Pipeline]:
        """Return pipelines with a FAILING status."""
        return self.by_status(PipelineStatus.FAILING)

    def unknown(self) -> List[Pipeline]:
        """Return pipelines with an UNKNOWN status."""
        return self.by_status(PipelineStatus.UNKNOWN)

    # ------------------------------------------------------------------
    # Metadata / name filters
    # ------------------------------------------------------------------

    def by_name(self, name: str) -> Optional[Pipeline]:
        """Return the first pipeline whose name matches *name*, or None."""
        for p in self._pipelines:
            if p.name == name:
                return p
        return None

    def by_name_prefix(self, prefix: str) -> List[Pipeline]:
        """Return pipelines whose names start with *prefix*."""
        return [p for p in self._pipelines if p.name.startswith(prefix)]

    def by_metadata(self, key: str, value: object) -> List[Pipeline]:
        """Return pipelines whose metadata contains *key* equal to *value*."""
        return [
            p for p in self._pipelines
            if p.metadata.get(key) == value
        ]

    # ------------------------------------------------------------------
    # Generic predicate filter
    # ------------------------------------------------------------------

    def where(self, predicate: Callable[[Pipeline], bool]) -> List[Pipeline]:
        """Return pipelines that satisfy *predicate*."""
        return [p for p in self._pipelines if predicate(p)]

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def all(self) -> List[Pipeline]:
        """Return all pipelines held by this filter."""
        return list(self._pipelines)

    def __len__(self) -> int:
        return len(self._pipelines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"PipelineFilter(count={len(self._pipelines)})"
