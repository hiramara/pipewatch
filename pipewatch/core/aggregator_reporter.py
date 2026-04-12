"""High-level helper that runs all registered aggregators over a Report."""

from __future__ import annotations

from typing import Dict, List

from pipewatch.core.aggregator import AggregateGroup
from pipewatch.core.aggregator_config import AggregatorConfig
from pipewatch.core.reporter import Report


class AggregatorReporter:
    """Runs every aggregator in an AggregatorConfig against a Report."""

    def __init__(self, config: AggregatorConfig) -> None:
        self._config = config

    def run_all(self, report: Report) -> Dict[str, Dict[str, AggregateGroup]]:
        """Return a mapping of aggregator_name -> {group_key -> AggregateGroup}."""
        results: Dict[str, Dict[str, AggregateGroup]] = {}
        for name in self._config.names():
            agg = self._config.get(name)
            if agg is not None:
                results[name] = agg.aggregate(report)
        return results

    def run(self, name: str, report: Report) -> Dict[str, AggregateGroup]:
        """Run a single named aggregator."""
        agg = self._config.get(name)
        if agg is None:
            raise KeyError(f"Aggregator '{name}' not found.")
        return agg.aggregate(report)

    def to_dicts(self, report: Report) -> Dict[str, List[dict]]:
        """Serialise all aggregation results to plain dicts."""
        return {
            name: [g.to_dict() for g in groups.values()]
            for name, groups in self.run_all(report).items()
        }
