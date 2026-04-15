"""Generate budget utilization reports from a CostRegistry + BudgetRegistry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from pipewatch.core.pipeline_budget import BudgetBreach, BudgetRegistry
from pipewatch.core.pipeline_cost import CostRegistry


@dataclass
class BudgetUtilization:
    pipeline_name: str
    limit: float
    actual: float
    utilization: float
    currency: str
    period: str
    breached: bool

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "limit": self.limit,
            "actual": self.actual,
            "utilization": self.utilization,
            "currency": self.currency,
            "period": self.period,
            "breached": self.breached,
        }


class BudgetReporter:
    """Cross-reference CostRegistry totals against BudgetRegistry limits."""

    def __init__(
        self,
        budget_registry: BudgetRegistry,
        cost_registry: CostRegistry,
    ) -> None:
        self._budgets = budget_registry
        self._costs = cost_registry

    def utilization(self) -> List[BudgetUtilization]:
        results: List[BudgetUtilization] = []
        for limit in self._budgets.all():
            actual = self._costs.total_for(limit.pipeline_name)
            results.append(
                BudgetUtilization(
                    pipeline_name=limit.pipeline_name,
                    limit=limit.limit,
                    actual=actual,
                    utilization=limit.utilization(actual),
                    currency=limit.currency,
                    period=limit.period,
                    breached=limit.is_exceeded(actual),
                )
            )
        return results

    def breaches(self) -> List[BudgetBreach]:
        result: List[BudgetBreach] = []
        for limit in self._budgets.all():
            actual = self._costs.total_for(limit.pipeline_name)
            breach = self._budgets.evaluate(limit.pipeline_name, actual)
            if breach is not None:
                result.append(breach)
        return result

    def summary(self) -> Dict[str, object]:
        utils = self.utilization()
        breached = [u for u in utils if u.breached]
        return {
            "total_pipelines": len(utils),
            "breached_count": len(breached),
            "healthy_count": len(utils) - len(breached),
        }
