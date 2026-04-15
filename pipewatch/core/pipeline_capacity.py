"""Pipeline capacity tracking — records resource usage and warns when limits are approached."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CapacityLimit:
    """Defines a named resource limit for a pipeline."""
    pipeline_name: str
    resource: str
    limit: float
    warn_threshold: float = 0.80  # fraction of limit that triggers a warning

    def utilization(self, current: float) -> float:
        """Return utilisation as a fraction (0.0 – 1.0+)."""
        if self.limit <= 0:
            return 0.0
        return current / self.limit

    def is_breached(self, current: float) -> bool:
        return self.utilization(current) >= 1.0

    def is_warning(self, current: float) -> bool:
        return self.warn_threshold <= self.utilization(current) < 1.0

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "resource": self.resource,
            "limit": self.limit,
            "warn_threshold": self.warn_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CapacityLimit":
        return cls(
            pipeline_name=data["pipeline_name"],
            resource=data["resource"],
            limit=data["limit"],
            warn_threshold=data.get("warn_threshold", 0.80),
        )

    def __repr__(self) -> str:
        return (
            f"CapacityLimit(pipeline={self.pipeline_name!r}, "
            f"resource={self.resource!r}, limit={self.limit})"
        )


@dataclass
class CapacityStatus:
    """Snapshot of current usage vs. limit for one resource."""
    limit: CapacityLimit
    current: float

    @property
    def utilization(self) -> float:
        return self.limit.utilization(self.current)

    @property
    def breached(self) -> bool:
        return self.limit.is_breached(self.current)

    @property
    def warning(self) -> bool:
        return self.limit.is_warning(self.current)

    def to_dict(self) -> dict:
        return {
            **self.limit.to_dict(),
            "current": self.current,
            "utilization": round(self.utilization, 4),
            "breached": self.breached,
            "warning": self.warning,
        }


class CapacityRegistry:
    """Stores capacity limits and evaluates current usage."""

    def __init__(self) -> None:
        self._limits: Dict[str, Dict[str, CapacityLimit]] = {}

    def add(self, limit: CapacityLimit) -> None:
        self._limits.setdefault(limit.pipeline_name, {})[limit.resource] = limit

    def remove(self, pipeline_name: str, resource: str) -> None:
        self._limits.get(pipeline_name, {}).pop(resource, None)

    def get(self, pipeline_name: str, resource: str) -> Optional[CapacityLimit]:
        return self._limits.get(pipeline_name, {}).get(resource)

    def evaluate(self, pipeline_name: str, usage: Dict[str, float]) -> List[CapacityStatus]:
        """Return CapacityStatus for every tracked resource of *pipeline_name*."""
        results: List[CapacityStatus] = []
        for resource, limit in self._limits.get(pipeline_name, {}).items():
            current = usage.get(resource, 0.0)
            results.append(CapacityStatus(limit=limit, current=current))
        return results

    def all_limits(self) -> List[CapacityLimit]:
        return [
            lim
            for resources in self._limits.values()
            for lim in resources.values()
        ]
