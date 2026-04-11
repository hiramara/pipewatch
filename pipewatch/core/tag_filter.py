"""Filter and group Monitor pipelines by tags."""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from pipewatch.core.pipeline import Pipeline
    from pipewatch.core.monitor import Monitor


class TagFilter:
    """Query pipelines registered in a Monitor by their tag sets."""

    def __init__(self, monitor: "Monitor") -> None:
        self._monitor = monitor

    def _pipelines(self) -> List["Pipeline"]:
        return list(self._monitor.pipelines.values())

    def by_tag(self, tag: str) -> List["Pipeline"]:
        """Return all pipelines that have *tag*."""
        return [p for p in self._pipelines() if p.tags.has(tag)]

    def by_any_tags(self, *tags: str) -> List["Pipeline"]:
        """Return pipelines that have at least one of the given tags."""
        return [p for p in self._pipelines() if p.tags.matches_any(tags)]

    def by_all_tags(self, *tags: str) -> List["Pipeline"]:
        """Return pipelines that have ALL of the given tags."""
        return [p for p in self._pipelines() if p.tags.matches_all(tags)]

    def group_by_tag(self) -> Dict[str, List["Pipeline"]]:
        """Return a dict mapping each unique tag to its matching pipelines."""
        groups: Dict[str, List["Pipeline"]] = {}
        for pipeline in self._pipelines():
            for tag in pipeline.tags:
                groups.setdefault(tag, []).append(pipeline)
        return groups

    def untagged(self) -> List["Pipeline"]:
        """Return pipelines with no tags."""
        return [p for p in self._pipelines() if len(p.tags) == 0]
