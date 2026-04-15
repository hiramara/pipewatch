"""Runbook entries linked to pipelines for operational guidance."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class RunbookEntry:
    pipeline_name: str
    title: str
    steps: List[str]
    owner: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "title": self.title,
            "steps": list(self.steps),
            "owner": self.owner,
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<RunbookEntry pipeline={self.pipeline_name!r} title={self.title!r}>"


class RunbookRegistry:
    """Stores and retrieves runbook entries keyed by pipeline name."""

    def __init__(self) -> None:
        self._entries: Dict[str, List[RunbookEntry]] = {}

    def add(self, entry: RunbookEntry) -> None:
        self._entries.setdefault(entry.pipeline_name, []).append(entry)

    def get(self, pipeline_name: str) -> List[RunbookEntry]:
        return list(self._entries.get(pipeline_name, []))

    def remove(self, pipeline_name: str, title: str) -> bool:
        entries = self._entries.get(pipeline_name, [])
        before = len(entries)
        self._entries[pipeline_name] = [e for e in entries if e.title != title]
        return len(self._entries[pipeline_name]) < before

    def all_pipelines(self) -> List[str]:
        return list(self._entries.keys())

    def all_entries(self) -> List[RunbookEntry]:
        return [e for entries in self._entries.values() for e in entries]
