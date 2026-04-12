"""Filter pipelines in a Report by label criteria."""
from __future__ import annotations

from typing import Dict, List

from pipewatch.core.reporter import PipelineSummary, Report
from pipewatch.core.pipeline_labeler import PipelineLabeler


class LabelFilter:
    """Select :class:`PipelineSummary` objects that match label predicates."""

    def __init__(self, labeler: PipelineLabeler) -> None:
        self._labeler = labeler

    def by_label(self, report: Report, key: str, value: str) -> List[PipelineSummary]:
        """Return summaries whose pipeline has label *key* == *value*."""
        matched = set(self._labeler.pipelines_with(key, value))
        return [s for s in report.pipelines if s.name in matched]

    def by_all_labels(self, report: Report, criteria: Dict[str, str]) -> List[PipelineSummary]:
        """Return summaries matching ALL key/value pairs in *criteria*."""
        result = []
        for summary in report.pipelines:
            ls = self._labeler.labels_for(summary.name)
            if all(ls.matches(k, v) for k, v in criteria.items()):
                result.append(summary)
        return result

    def by_label_key(self, report: Report, key: str) -> List[PipelineSummary]:
        """Return summaries whose pipeline has *key* set to any value."""
        return [
            s for s in report.pipelines
            if self._labeler.labels_for(s.name).has(key)
        ]
