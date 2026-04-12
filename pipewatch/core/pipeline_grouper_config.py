"""Registry of named PipelineGrouper instances."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from pipewatch.core.pipeline_grouper import PipelineGrouper
from pipewatch.core.reporter import PipelineSummary


class PipelineGrouperConfig:
    """Stores named groupers and provides a default set of built-in groupers."""

    def __init__(self) -> None:
        self._groupers: Dict[str, PipelineGrouper] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.add("by_status", lambda s: s.status.value)
        self.add("by_first_letter", lambda s: s.name[0].upper() if s.name else "?")

    def add(self, name: str, key_fn: Callable[[PipelineSummary], str]) -> None:
        """Register a new named grouper."""
        if name in self._groupers:
            raise ValueError(f"Grouper {name!r} is already registered.")
        self._groupers[name] = PipelineGrouper(key_fn)

    def remove(self, name: str) -> None:
        """Unregister a grouper by name."""
        self._groupers.pop(name, None)

    def get(self, name: str) -> Optional[PipelineGrouper]:
        """Return the grouper registered under *name*, or None."""
        return self._groupers.get(name)

    @property
    def names(self) -> list:
        return sorted(self._groupers.keys())

    def __len__(self) -> int:
        return len(self._groupers)
