"""Pipeline run history tracking for trend analysis and persistence."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, List, Optional

from pipewatch.core.pipeline import PipelineStatus


@dataclass
class RunRecord:
    """A single historical record of a pipeline evaluation."""

    pipeline_name: str
    status: str
    health_score: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "pipeline_name": self.pipeline_name,
            "status": self.status,
            "health_score": self.health_score,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RunRecord":
        return cls(
            pipeline_name=data["pipeline_name"],
            status=data["status"],
            health_score=data["health_score"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )


class PipelineHistory:
    """Maintains a capped history of run records per pipeline."""

    def __init__(self, max_records: int = 100) -> None:
        self.max_records = max_records
        self._records: Dict[str, Deque[RunRecord]] = {}

    def record(self, run: RunRecord) -> None:
        name = run.pipeline_name
        if name not in self._records:
            self._records[name] = deque(maxlen=self.max_records)
        self._records[name].append(run)

    def get(self, pipeline_name: str) -> List[RunRecord]:
        return list(self._records.get(pipeline_name, []))

    def all_pipeline_names(self) -> List[str]:
        return list(self._records.keys())

    def last_status(self, pipeline_name: str) -> Optional[str]:
        records = self.get(pipeline_name)
        return records[-1].status if records else None

    def average_health(self, pipeline_name: str, last_n: int = 10) -> Optional[float]:
        records = self.get(pipeline_name)[-last_n:]
        if not records:
            return None
        return round(sum(r.health_score for r in records) / len(records), 4)

    def save(self, path: Path) -> None:
        data = {
            name: [r.to_dict() for r in recs]
            for name, recs in self._records.items()
        }
        path.write_text(json.dumps(data, indent=2))

    def load(self, path: Path) -> None:
        if not path.exists():
            return
        data = json.loads(path.read_text())
        for name, records in data.items():
            self._records[name] = deque(
                (RunRecord.from_dict(r) for r in records), maxlen=self.max_records
            )
