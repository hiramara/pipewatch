"""Registry for managing compliance rules."""
from __future__ import annotations

from typing import Dict, List

from pipewatch.core.pipeline_compliance import ComplianceRule


class ComplianceConfig:
    """Stores and retrieves ComplianceRule instances by name."""

    def __init__(self) -> None:
        self._rules: Dict[str, ComplianceRule] = {}

    def add(self, rule: ComplianceRule) -> None:
        """Register a rule. Raises ValueError if name already exists."""
        if rule.name in self._rules:
            raise ValueError(f"Compliance rule '{rule.name}' already registered.")
        self._rules[rule.name] = rule

    def remove(self, name: str) -> None:
        """Remove a rule by name. Raises KeyError if not found."""
        if name not in self._rules:
            raise KeyError(f"No compliance rule named '{name}'.")
        del self._rules[name]

    def get(self, name: str) -> ComplianceRule:
        """Retrieve a rule by name."""
        if name not in self._rules:
            raise KeyError(f"No compliance rule named '{name}'.")
        return self._rules[name]

    @property
    def rules(self) -> List[ComplianceRule]:
        """Return all registered rules."""
        return list(self._rules.values())

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, name: str) -> bool:
        return name in self._rules
