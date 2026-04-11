"""Core Pipeline model."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pipewatch.core.tag import TagSet


class PipelineStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class Pipeline:
    name: str
    source: str
    status: PipelineStatus = PipelineStatus.UNKNOWN
    last_run: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    checks: List[Any] = field(default_factory=list)
    tags: TagSet = field(default_factory=TagSet)

    def update_status(self, status: PipelineStatus) -> None:
        self.status = status
        self.last_run = datetime.now(timezone.utc)

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def add_check(self, check: Any) -> None:
        self.checks.append(check)

    def run_checks(self) -> None:
        results = []
        for check in self.checks:
            result = check.execute()
            results.append(result)
        if all(r for r in results):
            self.update_status(PipelineStatus.HEALTHY)
        elif any(r for r in results):
            self.update_status(PipelineStatus.DEGRADED)
        else:
            self.update_status(PipelineStatus.FAILED)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "metadata": self.metadata,
            "checks": [c.to_dict() for c in self.checks],
            "tags": self.tags.to_list(),
        }

    def __repr__(self) -> str:
        return (
            f"Pipeline(name={self.name!r}, source={self.source!r}, "
            f"status={self.status.value!r}, tags={self.tags.to_list()})"
        )
