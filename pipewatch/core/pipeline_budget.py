"""Pipeline budget tracking: define spend limits and detect overruns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BudgetLimit:
    pipeline_name: str
    limit: float
    currency: str = "USD"
    period: str = "monthly"  # daily | weekly | monthly

    def is_exceeded(self, actual: float) -> bool:
        return actual > self.limit

    def utilization(self, actual: float) -> float:
        if self.limit <= 0:
            return 0.0
        return round(actual / self.limit, 4)

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "limit": self.limit,
            "currency": self.currency,
            "period": self.period,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetLimit":
        return cls(
            pipeline_name=data["pipeline_name"],
            limit=data["limit"],
            currency=data.get("currency", "USD"),
            period=data.get("period", "monthly"),
        )

    def __repr__(self) -> str:
        return (
            f"BudgetLimit(pipeline={self.pipeline_name!r}, "
            f"limit={self.limit} {self.currency}/{self.period})"
        )


@dataclass
class BudgetBreach:
    pipeline_name: str
    limit: float
    actual: float
    currency: str
    period: str

    @property
    def overage(self) -> float:
        return round(self.actual - self.limit, 4)

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "limit": self.limit,
            "actual": self.actual,
            "overage": self.overage,
            "currency": self.currency,
            "period": self.period,
        }


class BudgetRegistry:
    def __init__(self) -> None:
        self._limits: Dict[str, BudgetLimit] = {}

    def add(self, limit: BudgetLimit) -> None:
        if limit.pipeline_name in self._limits:
            raise ValueError(f"Budget already registered for {limit.pipeline_name!r}")
        self._limits[limit.pipeline_name] = limit

    def update(self, limit: BudgetLimit) -> None:
        self._limits[limit.pipeline_name] = limit

    def remove(self, pipeline_name: str) -> None:
        self._limits.pop(pipeline_name, None)

    def get(self, pipeline_name: str) -> Optional[BudgetLimit]:
        return self._limits.get(pipeline_name)

    def all(self) -> List[BudgetLimit]:
        return list(self._limits.values())

    def evaluate(self, pipeline_name: str, actual: float) -> Optional[BudgetBreach]:
        limit = self._limits.get(pipeline_name)
        if limit is None or not limit.is_exceeded(actual):
            return None
        return BudgetBreach(
            pipeline_name=pipeline_name,
            limit=limit.limit,
            actual=actual,
            currency=limit.currency,
            period=limit.period,
        )
