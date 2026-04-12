"""Configuration container for PipelineWatchdog staleness rules."""

from __future__ import annotations

from typing import Dict, Iterator, List

from pipewatch.core.pipeline_watchdog import PipelineWatchdog, StalenessRule


class WatchdogConfig:
    """Manages a collection of StalenessRules and applies them to a watchdog."""

    def __init__(self, default_max_silence_seconds: int = 300) -> None:
        self._default = default_max_silence_seconds
        self._rules: Dict[str, StalenessRule] = {}

    def add(self, pipeline_name: str, max_silence_seconds: int) -> None:
        if pipeline_name in self._rules:
            raise ValueError(f"Rule for '{pipeline_name}' already exists.")
        self._rules[pipeline_name] = StalenessRule(pipeline_name, max_silence_seconds)

    def update(self, pipeline_name: str, max_silence_seconds: int) -> None:
        self._rules[pipeline_name] = StalenessRule(pipeline_name, max_silence_seconds)

    def remove(self, pipeline_name: str) -> None:
        if pipeline_name not in self._rules:
            raise KeyError(f"No rule for '{pipeline_name}'.")
        del self._rules[pipeline_name]

    def get(self, pipeline_name: str) -> StalenessRule | None:
        return self._rules.get(pipeline_name)

    def rules(self) -> List[StalenessRule]:
        return list(self._rules.values())

    def __iter__(self) -> Iterator[StalenessRule]:
        return iter(self._rules.values())

    def __len__(self) -> int:
        return len(self._rules)

    def build_watchdog(self) -> PipelineWatchdog:
        """Create a PipelineWatchdog pre-loaded with all configured rules."""
        wd = PipelineWatchdog(default_max_silence_seconds=self._default)
        for rule in self._rules.values():
            wd.add_rule(rule)
        return wd
