"""Load and persist threshold configurations from/to plain dicts or JSON files."""
import json
from pathlib import Path
from typing import List, Dict, Any

from pipewatch.core.threshold import Threshold


class ThresholdConfig:
    """Manages a named collection of Threshold objects."""

    def __init__(self, thresholds: List[Threshold] | None = None) -> None:
        self._thresholds: List[Threshold] = thresholds or []

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def add(self, threshold: Threshold) -> None:
        self._thresholds.append(threshold)

    def remove(self, name: str) -> bool:
        before = len(self._thresholds)
        self._thresholds = [t for t in self._thresholds if t.name != name]
        return len(self._thresholds) < before

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------
    @property
    def thresholds(self) -> List[Threshold]:
        return list(self._thresholds)

    def get(self, name: str) -> Threshold | None:
        return next((t for t in self._thresholds if t.name == name), None)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {"thresholds": [t.to_dict() for t in self._thresholds]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThresholdConfig":
        thresholds = [Threshold.from_dict(t) for t in data.get("thresholds", [])]
        return cls(thresholds=thresholds)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "ThresholdConfig":
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)

    def __len__(self) -> int:
        return len(self._thresholds)

    def __repr__(self) -> str:
        return f"ThresholdConfig(count={len(self._thresholds)})"
