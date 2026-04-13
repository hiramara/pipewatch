"""Pipeline cost tracking: assign and report estimated run costs per pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CostEntry:
    pipeline_name: str
    cost_usd: float
    currency: str = "USD"
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "cost_usd": self.cost_usd,
            "currency": self.currency,
            "notes": self.notes,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"CostEntry({self.pipeline_name!r}, ${self.cost_usd:.4f})"


class CostRegistry:
    """Stores cost entries keyed by pipeline name."""

    def __init__(self) -> None:
        self._entries: Dict[str, CostEntry] = {}

    def set(self, pipeline_name: str, cost_usd: float, currency: str = "USD", notes: str = "") -> CostEntry:
        """Register or overwrite the cost for a pipeline."""
        if cost_usd < 0:
            raise ValueError(f"cost_usd must be non-negative, got {cost_usd}")
        entry = CostEntry(pipeline_name=pipeline_name, cost_usd=cost_usd, currency=currency, notes=notes)
        self._entries[pipeline_name] = entry
        return entry

    def get(self, pipeline_name: str) -> Optional[CostEntry]:
        return self._entries.get(pipeline_name)

    def remove(self, pipeline_name: str) -> None:
        self._entries.pop(pipeline_name, None)

    def all_entries(self) -> List[CostEntry]:
        return list(self._entries.values())

    def total_cost(self) -> float:
        return sum(e.cost_usd for e in self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)
