"""Threshold definitions for pipeline health checks."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ThresholdOperator(str, Enum):
    GT = "gt"   # greater than
    GTE = "gte" # greater than or equal
    LT = "lt"   # less than
    LTE = "lte" # less than or equal
    EQ = "eq"   # equal


@dataclass
class Threshold:
    """Defines a numeric boundary that triggers a check result."""
    name: str
    value: float
    operator: ThresholdOperator = ThresholdOperator.GT
    description: Optional[str] = None

    def evaluate(self, metric: float) -> bool:
        """Return True if the metric breaches this threshold."""
        ops = {
            ThresholdOperator.GT:  lambda a, b: a > b,
            ThresholdOperator.GTE: lambda a, b: a >= b,
            ThresholdOperator.LT:  lambda a, b: a < b,
            ThresholdOperator.LTE: lambda a, b: a <= b,
            ThresholdOperator.EQ:  lambda a, b: a == b,
        }
        return ops[self.operator](metric, self.value)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "operator": self.operator.value,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Threshold":
        return cls(
            name=data["name"],
            value=data["value"],
            operator=ThresholdOperator(data.get("operator", "gt")),
            description=data.get("description"),
        )

    def __repr__(self) -> str:
        return (
            f"Threshold(name={self.name!r}, "
            f"{self.operator.value} {self.value})"
        )
