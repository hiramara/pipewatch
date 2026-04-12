"""Configuration for named aggregators registered in pipewatch."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from pipewatch.core.aggregator import Aggregator, by_status
from pipewatch.core.reporter import PipelineSummary


class AggregatorConfig:
    """Registry of named Aggregator instances."""

    def __init__(self) -> None:
        self._aggregators: Dict[str, Aggregator] = {}
        # Register a sensible default
        self._aggregators["by_status"] = Aggregator(by_status)

    def add(self, name: str, key_fn: Callable[[PipelineSummary], str]) -> None:
        """Register a new aggregator under *name*."""
        if name in self._aggregators:
            raise ValueError(f"Aggregator '{name}' already registered.")
        self._aggregators[name] = Aggregator(key_fn)

    def remove(self, name: str) -> None:
        """Remove a registered aggregator. Raises KeyError if not found."""
        if name not in self._aggregators:
            raise KeyError(f"Aggregator '{name}' not found.")
        del self._aggregators[name]

    def get(self, name: str) -> Optional[Aggregator]:
        return self._aggregators.get(name)

    def names(self) -> list:
        return list(self._aggregators.keys())

    def __len__(self) -> int:
        return len(self._aggregators)

    def __contains__(self, name: str) -> bool:
        return name in self._aggregators
