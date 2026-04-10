"""Snapshot module: capture and compare pipeline state at a point in time."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.core.pipeline import PipelineStatus


@dataclass
class PipelineSnapshot:
    """Immutable snapshot of a single pipeline's state."""

    pipeline_id: str
    name: str
    status: PipelineStatus
    health_score: float
    captured_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "status": self.status.value,
            "health_score": self.health_score,
            "captured_at": self.captured_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PipelineSnapshot":
        return cls(
            pipeline_id=data["pipeline_id"],
            name=data["name"],
            status=PipelineStatus(data["status"]),
            health_score=data["health_score"],
            captured_at=datetime.datetime.fromisoformat(data["captured_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Snapshot:
    """Full system snapshot containing all pipeline states."""

    captured_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    pipelines: List[PipelineSnapshot] = field(default_factory=list)

    def add(self, pipeline_snapshot: PipelineSnapshot) -> None:
        self.pipelines.append(pipeline_snapshot)

    def get(self, pipeline_id: str) -> Optional[PipelineSnapshot]:
        return next((p for p in self.pipelines if p.pipeline_id == pipeline_id), None)

    def diff(self, other: "Snapshot") -> List[Dict]:
        """Return pipelines whose status changed between this and another snapshot."""
        changes = []
        other_map = {p.pipeline_id: p for p in other.pipelines}
        for snap in self.pipelines:
            prev = other_map.get(snap.pipeline_id)
            if prev and prev.status != snap.status:
                changes.append({
                    "pipeline_id": snap.pipeline_id,
                    "name": snap.name,
                    "previous_status": prev.status.value,
                    "current_status": snap.status.value,
                })
        return changes

    def to_dict(self) -> Dict:
        return {
            "captured_at": self.captured_at.isoformat(),
            "pipelines": [p.to_dict() for p in self.pipelines],
        }
