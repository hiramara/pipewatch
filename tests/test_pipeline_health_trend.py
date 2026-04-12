"""Tests for pipeline_health_trend and health_trend_analyzer."""
import pytest

from pipewatch.core.pipeline_health_trend import (
    HealthTrend,
    TrendDirection,
    compute_trend,
)


class TestComputeTrend:
    def test_insufficient_data_single_score(self):
        trend = compute_trend("p1", [0.8])
        assert trend.direction == TrendDirection.INSUFFICIENT_DATA
        assert trend.delta == 0.0

    def test_insufficient_data_empty(self):
        trend = compute_trend("p1", [])
        assert trend.direction == TrendDirection.INSUFFICIENT_DATA

    def test_stable_within_threshold(self):
        trend = compute_trend("p1", [0.9, 0.91], stable_threshold=0.05)
        assert trend.direction == TrendDirection.STABLE

    def test_improving(self):
        trend = compute_trend("p1", [0.5, 0.8])
        assert trend.direction == TrendDirection.IMPROVING
        assert pytest.approx(trend.delta, abs=1e-6) == 0.3

    def test_degrading(self):
        trend = compute_trend("p1", [0.9, 0.5])
        assert trend.direction == TrendDirection.DEGRADING
        assert trend.delta < 0

    def test_scores_stored(self):
        scores = [0.4, 0.6, 0.8]
        trend = compute_trend("p1", scores)
        assert trend.scores == scores

    def test_to_dict_keys(self):
        trend = compute_trend("pipe", [0.5, 0.9])
        d = trend.to_dict()
        assert set(d.keys()) == {"pipeline_name", "direction", "delta", "scores"}

    def test_to_dict_values(self):
        trend = compute_trend("pipe", [0.5, 0.9])
        d = trend.to_dict()
        assert d["pipeline_name"] == "pipe"
        assert d["direction"] == "improving"

    def test_custom_min_samples(self):
        trend = compute_trend("p1", [0.5, 0.6, 0.7], min_samples=3)
        assert trend.direction == TrendDirection.IMPROVING

    def test_exactly_at_stable_threshold_is_stable(self):
        trend = compute_trend("p1", [0.7, 0.75], stable_threshold=0.05)
        assert trend.direction == TrendDirection.STABLE
