"""Tests for PipelineScorer, ScoringWeights, and ScoringConfig."""
import pytest

from pipewatch.core.pipeline_scorer import (
    PipelineScore,
    PipelineScorer,
    ScoringWeights,
    _grade,
)
from pipewatch.core.scoring_config import ScoringConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeSummary:
    """Minimal stand-in for PipelineSummary."""

    def __init__(self, name: str, health_score: float, checks=None):
        self.name = name
        self.health_score = health_score
        self.checks = checks or []


def _make_summary(name="pipe", health=1.0, checks=None):
    return _FakeSummary(name, health, checks)


# ---------------------------------------------------------------------------
# ScoringWeights
# ---------------------------------------------------------------------------

class TestScoringWeights:
    def test_default_weights_sum_to_one(self):
        w = ScoringWeights()
        assert abs(w.health + w.check_pass_rate + w.history_stability - 1.0) < 1e-9

    def test_invalid_weights_raise(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            ScoringWeights(health=0.5, check_pass_rate=0.5, history_stability=0.5)

    def test_custom_valid_weights(self):
        w = ScoringWeights(health=0.6, check_pass_rate=0.2, history_stability=0.2)
        assert w.health == 0.6


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

class TestGrade:
    @pytest.mark.parametrize("score,expected", [
        (1.0, "A"), (0.90, "A"), (0.89, "B"), (0.75, "B"),
        (0.74, "C"), (0.60, "C"), (0.59, "D"), (0.40, "D"),
        (0.39, "F"), (0.0, "F"),
    ])
    def test_grade_boundaries(self, score, expected):
        assert _grade(score) == expected


# ---------------------------------------------------------------------------
# PipelineScorer
# ---------------------------------------------------------------------------

class TestPipelineScorer:
    def test_perfect_pipeline_scores_one(self):
        scorer = PipelineScorer()
        summary = _make_summary(
            health=1.0,
            checks=[{"status": "pass"}, {"status": "pass"}],
        )
        result = scorer.score(summary)
        assert result.composite == pytest.approx(1.0)
        assert result.grade == "A"

    def test_failing_checks_lower_score(self):
        scorer = PipelineScorer()
        summary = _make_summary(
            health=1.0,
            checks=[{"status": "pass"}, {"status": "fail"}],
        )
        result = scorer.score(summary)
        assert result.composite < 1.0

    def test_stability_override_applied(self):
        scorer = PipelineScorer(history_stability={"pipe": 0.0})
        summary = _make_summary(name="pipe", health=1.0)
        result = scorer.score(summary)
        w = ScoringWeights()
        expected = w.health * 1.0 + w.check_pass_rate * 1.0 + w.history_stability * 0.0
        assert result.composite == pytest.approx(expected)

    def test_score_all_sorted_best_first(self):
        scorer = PipelineScorer()
        s1 = _make_summary(name="bad", health=0.0)
        s2 = _make_summary(name="good", health=1.0)
        scores = scorer.score_all([s1, s2])
        assert scores[0].pipeline_name == "good"

    def test_to_dict_keys(self):
        scorer = PipelineScorer()
        result = scorer.score(_make_summary()).to_dict()
        assert "pipeline" in result
        assert "composite" in result
        assert "grade" in result
        assert "components" in result


# ---------------------------------------------------------------------------
# ScoringConfig
# ---------------------------------------------------------------------------

class TestScoringConfig:
    def test_default_builds_scorer(self):
        cfg = ScoringConfig()
        scorer = cfg.build_scorer()
        assert isinstance(scorer, PipelineScorer)

    def test_set_stability_stored(self):
        cfg = ScoringConfig()
        cfg.set_stability("pipe", 0.75)
        assert cfg.get_stability("pipe") == 0.75

    def test_invalid_stability_raises(self):
        cfg = ScoringConfig()
        with pytest.raises(ValueError):
            cfg.set_stability("pipe", 1.5)

    def test_remove_stability(self):
        cfg = ScoringConfig()
        cfg.set_stability("pipe", 0.5)
        cfg.remove_stability("pipe")
        assert cfg.get_stability("pipe") is None

    def test_set_weights(self):
        cfg = ScoringConfig()
        new_w = ScoringWeights(health=0.6, check_pass_rate=0.2, history_stability=0.2)
        cfg.set_weights(new_w)
        assert cfg.weights.health == 0.6

    def test_to_dict_structure(self):
        cfg = ScoringConfig()
        cfg.set_stability("pipe", 0.8)
        d = cfg.to_dict()
        assert "weights" in d
        assert "stability_overrides" in d
        assert d["stability_overrides"]["pipe"] == 0.8
