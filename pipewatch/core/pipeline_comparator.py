"""Compare two pipeline snapshots to detect state changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.core.snapshot import PipelineSnapshot
from pipewatch.core.pipeline import PipelineStatus


@dataclass
class PipelineChange:
    """Represents a detected change between two snapshots of a pipeline."""

    pipeline_name: str
    previous_status: Optional[PipelineStatus]
    current_status: PipelineStatus
    health_delta: float  # current - previous (0.0 if no previous)
    newly_failing: bool
    newly_healthy: bool

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "previous_status": self.previous_status.value if self.previous_status else None,
            "current_status": self.current_status.value,
            "health_delta": round(self.health_delta, 4),
            "newly_failing": self.newly_failing,
            "newly_healthy": self.newly_healthy,
        }

    def __repr__(self) -> str:
        return (
            f"PipelineChange({self.pipeline_name!r}, "
            f"{self.previous_status} -> {self.current_status}, "
            f"delta={self.health_delta:+.2f})"
        )


@dataclass
class ComparisonResult:
    """Holds all changes detected between two snapshots."""

    changes: List[PipelineChange] = field(default_factory=list)

    @property
    def newly_failing(self) -> List[PipelineChange]:
        return [c for c in self.changes if c.newly_failing]

    @property
    def newly_healthy(self) -> List[PipelineChange]:
        return [c for c in self.changes if c.newly_healthy]

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict:
        return {
            "total_changes": len(self.changes),
            "newly_failing": len(self.newly_failing),
            "newly_healthy": len(self.newly_healthy),
            "changes": [c.to_dict() for c in self.changes],
        }


class PipelineComparator:
    """Compares two PipelineSnapshot instances and emits change records."""

    def compare(
        self,
        previous: Optional[PipelineSnapshot],
        current: PipelineSnapshot,
    ) -> ComparisonResult:
        result = ComparisonResult()

        prev_map = {s.name: s for s in (previous.summaries if previous else [])}
        curr_map = {s.name: s for s in current.summaries}

        for name, curr_summary in curr_map.items():
            prev_summary = prev_map.get(name)
            prev_status = PipelineStatus(prev_summary.status) if prev_summary else None
            curr_status = PipelineStatus(curr_summary.status)

            if prev_summary is None or prev_status != curr_status:
                prev_health = prev_summary.health_score if prev_summary else 0.0
                delta = curr_summary.health_score - prev_health

                change = PipelineChange(
                    pipeline_name=name,
                    previous_status=prev_status,
                    current_status=curr_status,
                    health_delta=delta,
                    newly_failing=(
                        curr_status == PipelineStatus.FAILING
                        and prev_status != PipelineStatus.FAILING
                    ),
                    newly_healthy=(
                        curr_status == PipelineStatus.HEALTHY
                        and prev_status is not None
                        and prev_status != PipelineStatus.HEALTHY
                    ),
                )
                result.changes.append(change)

        return result
