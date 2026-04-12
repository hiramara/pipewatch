"""Composite scoring for pipelines based on health, checks, and history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.core.reporter import PipelineSummary


@dataclass
class ScoringWeights:
    """Weights used to compute a composite pipeline score (must sum to 1.0)."""

    health: float = 0.5
    check_pass_rate: float = 0.3
    history_stability: float = 0.2

    def __post_init__(self) -> None:
        total = self.health + self.check_pass_rate + self.history_stability
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")


@dataclass
class PipelineScore:
    """Composite score for a single pipeline."""

    pipeline_name: str
    composite: float  # 0.0 – 1.0
    health_component: float
    check_component: float
    history_component: float
    grade: str = field(init=False)

    def __post_init__(self) -> None:
        self.grade = _grade(self.composite)

    def to_dict(self) -> Dict:
        return {
            "pipeline": self.pipeline_name,
            "composite": round(self.composite, 4),
            "grade": self.grade,
            "components": {
                "health": round(self.health_component, 4),
                "check_pass_rate": round(self.check_component, 4),
                "history_stability": round(self.history_component, 4),
            },
        }


def _grade(score: float) -> str:
    if score >= 0.90:
        return "A"
    if score >= 0.75:
        return "B"
    if score >= 0.60:
        return "C"
    if score >= 0.40:
        return "D"
    return "F"


class PipelineScorer:
    """Computes composite scores for all pipelines in a report."""

    def __init__(
        self,
        weights: Optional[ScoringWeights] = None,
        history_stability: Optional[Dict[str, float]] = None,
    ) -> None:
        self._weights = weights or ScoringWeights()
        # Optional external stability values keyed by pipeline name (0.0-1.0).
        self._stability: Dict[str, float] = history_stability or {}

    def score(self, summary: PipelineSummary) -> PipelineScore:
        """Return a PipelineScore for a single PipelineSummary."""
        w = self._weights
        health_val = summary.health_score
        check_val = _check_pass_rate(summary)
        stability_val = self._stability.get(summary.name, 1.0)

        composite = (
            w.health * health_val
            + w.check_pass_rate * check_val
            + w.history_stability * stability_val
        )
        return PipelineScore(
            pipeline_name=summary.name,
            composite=min(max(composite, 0.0), 1.0),
            health_component=health_val,
            check_component=check_val,
            history_component=stability_val,
        )

    def score_all(self, summaries: List[PipelineSummary]) -> List[PipelineScore]:
        """Return scores for a list of summaries, sorted best-first."""
        scores = [self.score(s) for s in summaries]
        scores.sort(key=lambda ps: ps.composite, reverse=True)
        return scores


def _check_pass_rate(summary: PipelineSummary) -> float:
    checks = summary.checks
    if not checks:
        return 1.0
    passed = sum(1 for c in checks if c.get("status") == "pass")
    return passed / len(checks)
