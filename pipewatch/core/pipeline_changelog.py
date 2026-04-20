"""Pipeline changelog: records and exposes human-readable change events per pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ChangelogEntry:
    pipeline_name: str
    timestamp: datetime
    description: str
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "author": self.author,
            "tags": list(self.tags),
        }

    def __repr__(self) -> str:  # pragma: no cover
        author_part = f" by {self.author}" if self.author else ""
        return (
            f"<ChangelogEntry pipeline={self.pipeline_name!r}"
            f" at={self.timestamp.isoformat()}{author_part}>"
        )


class PipelineChangelog:
    """Stores ordered changelog entries for one or more pipelines."""

    def __init__(self) -> None:
        self._entries: List[ChangelogEntry] = []

    def record(
        self,
        pipeline_name: str,
        description: str,
        *,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> ChangelogEntry:
        entry = ChangelogEntry(
            pipeline_name=pipeline_name,
            timestamp=timestamp or datetime.now(timezone.utc),
            description=description,
            author=author,
            tags=tags or [],
        )
        self._entries.append(entry)
        return entry

    def entries_for(self, pipeline_name: str) -> List[ChangelogEntry]:
        return [e for e in self._entries if e.pipeline_name == pipeline_name]

    def all_entries(self) -> List[ChangelogEntry]:
        return list(self._entries)

    def clear(self, pipeline_name: Optional[str] = None) -> None:
        if pipeline_name is None:
            self._entries.clear()
        else:
            self._entries = [e for e in self._entries if e.pipeline_name != pipeline_name]
