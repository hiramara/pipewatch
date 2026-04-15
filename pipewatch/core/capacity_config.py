"""Configuration layer for pipeline capacity limits."""
from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.core.pipeline_capacity import CapacityLimit, CapacityRegistry, CapacityStatus


class CapacityConfig:
    """High-level interface for managing and querying capacity limits."""

    def __init__(self) -> None:
        self._registry = CapacityRegistry()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, pipeline_name: str, resource: str, limit: float, warn_threshold: float = 0.80) -> None:
        """Register or replace a capacity limit."""
        self._registry.add(
            CapacityLimit(
                pipeline_name=pipeline_name,
                resource=resource,
                limit=limit,
                warn_threshold=warn_threshold,
            )
        )

    def remove(self, pipeline_name: str, resource: str) -> None:
        """Remove a capacity limit; silently ignores unknown entries."""
        self._registry.remove(pipeline_name, resource)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, pipeline_name: str, resource: str) -> Optional[CapacityLimit]:
        return self._registry.get(pipeline_name, resource)

    def evaluate(self, pipeline_name: str, usage: Dict[str, float]) -> List[CapacityStatus]:
        """Evaluate *usage* dict against configured limits for *pipeline_name*."""
        return self._registry.evaluate(pipeline_name, usage)

    def breached(self, pipeline_name: str, usage: Dict[str, float]) -> List[CapacityStatus]:
        """Return only statuses where the limit is fully breached."""
        return [s for s in self.evaluate(pipeline_name, usage) if s.breached]

    def warnings(self, pipeline_name: str, usage: Dict[str, float]) -> List[CapacityStatus]:
        """Return only statuses in the warning zone (not yet breached)."""
        return [s for s in self.evaluate(pipeline_name, usage) if s.warning]

    def all_limits(self) -> List[CapacityLimit]:
        return self._registry.all_limits()

    def __len__(self) -> int:
        return len(self.all_limits())
