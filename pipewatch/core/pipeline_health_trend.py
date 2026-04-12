"""Computes health trend direction for pipelines over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class HealthTrend:
    pipeline_name: str
    scores: List[float] = field(default_factory=list)
    direction: TrendDirection = TrendDirection.INSUFFICIENT_DATA
    delta: float = 0.0

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "direction": self.direction.value,
            "delta": round(self.delta, 4),
            "scores": [round(s, 4) for s in self.scores],
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<HealthTrend pipeline={self.pipeline_name!r} "
            f"direction={self.direction.value} delta={self.delta:.4f}>"
        )


def compute_trend(
    pipeline_name: str,
    scores: List[float],
    min_samples: int = 2,
    stable_threshold: float = 0.05,
) -> HealthTrend:
    """Derive trend direction from an ordered list of health scores.

    Args:
        pipeline_name: Identifier of the pipeline.
        scores: Health scores ordered oldest-first (0.0–1.0).
        min_samples: Minimum number of scores required to determine direction.
        stable_threshold: Absolute delta below which trend is considered stable.

    Returns:
        A :class:`HealthTrend` instance.
    """
    trend = HealthTrend(pipeline_name=pipeline_name, scores=list(scores))

    if len(scores) < min_samples:
        return trend

    delta = scores[-1] - scores[0]
    trend.delta = delta

    if abs(delta) < stable_threshold:
        trend.direction = TrendDirection.STABLE
    elif delta > 0:
        trend.direction = TrendDirection.IMPROVING
    else:
        trend.direction = TrendDirection.DEGRADING

    return trend
