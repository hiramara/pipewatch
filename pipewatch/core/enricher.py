"""Pipeline metadata enrichment — attaches contextual labels to pipeline reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.core.reporter import PipelineSummary, Report


@dataclass
class EnrichmentRule:
    """Maps a tag or metadata key/value to an additional label to inject."""

    match_key: str
    match_value: str
    label_key: str
    label_value: str

    def matches(self, summary: PipelineSummary) -> bool:
        """Return True if this rule applies to the given pipeline summary."""
        tags = getattr(summary.pipeline, "tags", None)
        if tags is not None and self.match_key == "tag":
            return tags.has(self.match_value)
        meta = summary.pipeline.metadata or {}
        return meta.get(self.match_key) == self.match_value

    def to_dict(self) -> Dict[str, str]:
        return {
            "match_key": self.match_key,
            "match_value": self.match_value,
            "label_key": self.label_key,
            "label_value": self.label_value,
        }


class Enricher:
    """Applies enrichment rules to a Report, returning annotated summaries."""

    def __init__(self, rules: Optional[List[EnrichmentRule]] = None) -> None:
        self._rules: List[EnrichmentRule] = list(rules or [])

    def add_rule(self, rule: EnrichmentRule) -> None:
        self._rules.append(rule)

    def remove_rule(self, rule: EnrichmentRule) -> None:
        self._rules = [r for r in self._rules if r is not rule]

    @property
    def rules(self) -> List[EnrichmentRule]:
        return list(self._rules)

    def enrich(self, report: Report) -> Dict[str, Dict[str, str]]:
        """Return a mapping of pipeline name -> injected labels for that report."""
        result: Dict[str, Dict[str, str]] = {}
        for summary in report.pipelines:
            labels: Dict[str, str] = {}
            for rule in self._rules:
                if rule.matches(summary):
                    labels[rule.label_key] = rule.label_value
            if labels:
                result[summary.pipeline.name] = labels
        return result

    def enrich_summary(self, summary: PipelineSummary) -> Dict[str, str]:
        """Return the labels that would be injected for a single pipeline summary.

        Useful for inspecting enrichment results without constructing a full Report.

        Args:
            summary: The pipeline summary to evaluate against all rules.

        Returns:
            A dict of label_key -> label_value for each matching rule.
        """
        return {
            rule.label_key: rule.label_value
            for rule in self._rules
            if rule.matches(summary)
        }
