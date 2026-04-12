"""Configuration container for PipelineScorer weights and stability overrides."""
from __future__ import annotations

from typing import Dict, Optional

from pipewatch.core.pipeline_scorer import PipelineScorer, ScoringWeights


class ScoringConfig:
    """Manages scorer construction and per-pipeline stability hints."""

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        self._weights = weights or ScoringWeights()
        self._stability: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Stability overrides
    # ------------------------------------------------------------------

    def set_stability(self, pipeline_name: str, value: float) -> None:
        """Record a stability score (0.0-1.0) for a pipeline."""
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"Stability must be in [0, 1], got {value}")
        self._stability[pipeline_name] = value

    def remove_stability(self, pipeline_name: str) -> None:
        """Remove a stability override; scorer will default to 1.0."""
        self._stability.pop(pipeline_name, None)

    def get_stability(self, pipeline_name: str) -> Optional[float]:
        return self._stability.get(pipeline_name)

    # ------------------------------------------------------------------
    # Weights
    # ------------------------------------------------------------------

    @property
    def weights(self) -> ScoringWeights:
        return self._weights

    def set_weights(self, weights: ScoringWeights) -> None:
        self._weights = weights

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    def build_scorer(self) -> PipelineScorer:
        """Return a configured PipelineScorer instance."""
        return PipelineScorer(
            weights=self._weights,
            history_stability=dict(self._stability),
        )

    def to_dict(self) -> dict:
        return {
            "weights": {
                "health": self._weights.health,
                "check_pass_rate": self._weights.check_pass_rate,
                "history_stability": self._weights.history_stability,
            },
            "stability_overrides": dict(self._stability),
        }
