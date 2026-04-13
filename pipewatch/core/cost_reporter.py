"""Report cost summaries across pipelines using the CostRegistry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from pipewatch.core.pipeline_cost import CostEntry, CostRegistry


@dataclass
class CostSummary:
    entries: List[CostEntry]
    total_usd: float
    pipeline_count: int

    def to_dict(self) -> dict:
        return {
            "pipeline_count": self.pipeline_count,
            "total_usd": round(self.total_usd, 6),
            "entries": [e.to_dict() for e in self.entries],
        }


class CostReporter:
    """Generates cost summaries from a CostRegistry."""

    def __init__(self, registry: CostRegistry) -> None:
        self._registry = registry

    def summary(self) -> CostSummary:
        entries = self._registry.all_entries()
        return CostSummary(
            entries=entries,
            total_usd=self._registry.total_cost(),
            pipeline_count=len(entries),
        )

    def top_n(self, n: int) -> List[CostEntry]:
        """Return the n most expensive pipelines, descending."""
        if n < 1:
            raise ValueError("n must be at least 1")
        return sorted(self._registry.all_entries(), key=lambda e: e.cost_usd, reverse=True)[:n]

    def below_threshold(self, threshold_usd: float) -> List[CostEntry]:
        """Return entries whose cost is strictly below the threshold."""
        return [e for e in self._registry.all_entries() if e.cost_usd < threshold_usd]

    def above_threshold(self, threshold_usd: float) -> List[CostEntry]:
        """Return entries whose cost is at or above the threshold."""
        return [e for e in self._registry.all_entries() if e.cost_usd >= threshold_usd]
