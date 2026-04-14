"""Configuration container for pipeline quota rules."""
from __future__ import annotations

from typing import Dict, Iterator, List

from pipewatch.core.pipeline_quota import QuotaEvaluator, QuotaRule


class QuotaConfig:
    """Manages a collection of QuotaRules and wires them to a QuotaEvaluator."""

    def __init__(self, evaluator: QuotaEvaluator | None = None) -> None:
        self._evaluator = evaluator or QuotaEvaluator()
        self._rules: Dict[str, QuotaRule] = {}

    @property
    def evaluator(self) -> QuotaEvaluator:
        return self._evaluator

    def add(self, rule: QuotaRule) -> None:
        """Register a quota rule, replacing any existing rule for the same pipeline."""
        self._rules[rule.pipeline_name] = rule
        self._evaluator.add_rule(rule)

    def update(self, rule: QuotaRule) -> None:
        """Update an existing rule; raises KeyError if not found."""
        if rule.pipeline_name not in self._rules:
            raise KeyError(f"No quota rule for pipeline '{rule.pipeline_name}'")
        self.add(rule)

    def remove(self, pipeline_name: str) -> None:
        """Remove a quota rule by pipeline name."""
        self._rules.pop(pipeline_name, None)
        self._evaluator.remove_rule(pipeline_name)

    def get(self, pipeline_name: str) -> QuotaRule | None:
        return self._rules.get(pipeline_name)

    def all_rules(self) -> List[QuotaRule]:
        return list(self._rules.values())

    def __iter__(self) -> Iterator[QuotaRule]:
        return iter(self._rules.values())

    def __len__(self) -> int:
        return len(self._rules)

    def to_dicts(self) -> List[dict]:
        return [r.to_dict() for r in self._rules.values()]

    @classmethod
    def from_dicts(cls, data: List[dict]) -> "QuotaConfig":
        cfg = cls()
        for item in data:
            cfg.add(QuotaRule.from_dict(item))
        return cfg
