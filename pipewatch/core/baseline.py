"""Baseline tracking for pipeline health metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class BaselineMetric:
    """A single tracked metric with its computed baseline value."""
    name: str
    values: List[float] = field(default_factory=list)
    updated_at: Optional[datetime] = None

    @property
    def average(self) -> Optional[float]:
        if not self.values:
            return None
        return sum(self.values) / len(self.values)

    @property
    def minimum(self) -> Optional[float]:
        return min(self.values) if self.values else None

    @property
    def maximum(self) -> Optional[float]:
        return max(self.values) if self.values else None

    def record(self, value: float) -> None:
        self.values.append(value)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "average": self.average,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "sample_count": len(self.values),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Baseline:
    """Stores and computes baseline metrics for a named pipeline."""

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name = pipeline_name
        self._metrics: Dict[str, BaselineMetric] = {}

    def record(self, metric_name: str, value: float) -> None:
        if metric_name not in self._metrics:
            self._metrics[metric_name] = BaselineMetric(name=metric_name)
        self._metrics[metric_name].record(value)

    def get(self, metric_name: str) -> Optional[BaselineMetric]:
        return self._metrics.get(metric_name)

    def metric_names(self) -> List[str]:
        return list(self._metrics.keys())

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline_name,
            "metrics": {k: v.to_dict() for k, v in self._metrics.items()},
        }
