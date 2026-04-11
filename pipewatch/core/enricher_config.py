"""Persistent configuration for enrichment rules, with serialisation support."""

from __future__ import annotations

from typing import Dict, List

from pipewatch.core.enricher import EnrichmentRule, Enricher


class EnricherConfig:
    """Manages a named collection of EnrichmentRules and builds an Enricher."""

    def __init__(self) -> None:
        self._rules: Dict[str, EnrichmentRule] = {}

    def add(self, name: str, rule: EnrichmentRule) -> None:
        """Register a rule under a unique name."""
        self._rules[name] = rule

    def remove(self, name: str) -> None:
        """Remove a rule by name; silently ignored if not present."""
        self._rules.pop(name, None)

    def get(self, name: str) -> EnrichmentRule | None:
        return self._rules.get(name)

    @property
    def names(self) -> List[str]:
        return list(self._rules.keys())

    def build(self) -> Enricher:
        """Construct an Enricher loaded with all current rules."""
        return Enricher(rules=list(self._rules.values()))

    def to_dict(self) -> Dict[str, dict]:
        return {name: rule.to_dict() for name, rule in self._rules.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, dict]) -> "EnricherConfig":
        config = cls()
        for name, rule_data in data.items():
            config.add(
                name,
                EnrichmentRule(
                    match_key=rule_data["match_key"],
                    match_value=rule_data["match_value"],
                    label_key=rule_data["label_key"],
                    label_value=rule_data["label_value"],
                ),
            )
        return config

    def __len__(self) -> int:
        return len(self._rules)

    def __repr__(self) -> str:  # pragma: no cover
        return f"EnricherConfig(rules={self.names})"
