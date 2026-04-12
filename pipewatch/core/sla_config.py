"""Configuration manager for SLA rules — add, update, and remove rules."""
from __future__ import annotations

from typing import Iterator, Optional

from pipewatch.core.pipeline_sla import SLAEvaluator, SLARule


class SLAConfig:
    """Manages a collection of SLA rules backed by an SLAEvaluator."""

    def __init__(self, evaluator: Optional[SLAEvaluator] = None) -> None:
        self._evaluator = evaluator or SLAEvaluator()

    @property
    def evaluator(self) -> SLAEvaluator:
        return self._evaluator

    def add(self, pipeline_name: str, max_duration_seconds: float, description: str = "") -> SLARule:
        if self._evaluator.get_rule(pipeline_name) is not None:
            raise ValueError(f"SLA rule already exists for pipeline '{pipeline_name}'")
        rule = SLARule(
            pipeline_name=pipeline_name,
            max_duration_seconds=max_duration_seconds,
            description=description,
        )
        self._evaluator.add_rule(rule)
        return rule

    def update(self, pipeline_name: str, max_duration_seconds: float, description: Optional[str] = None) -> SLARule:
        existing = self._evaluator.get_rule(pipeline_name)
        if existing is None:
            raise KeyError(f"No SLA rule found for pipeline '{pipeline_name}'")
        new_rule = SLARule(
            pipeline_name=pipeline_name,
            max_duration_seconds=max_duration_seconds,
            description=description if description is not None else existing.description,
        )
        self._evaluator.add_rule(new_rule)
        return new_rule

    def remove(self, pipeline_name: str) -> None:
        self._evaluator.remove_rule(pipeline_name)

    def get(self, pipeline_name: str) -> Optional[SLARule]:
        return self._evaluator.get_rule(pipeline_name)

    def all_rules(self) -> list[SLARule]:
        return self._evaluator.rules()

    def __iter__(self) -> Iterator[SLARule]:
        return iter(self._evaluator.rules())

    def __len__(self) -> int:
        return len(self._evaluator.rules())
