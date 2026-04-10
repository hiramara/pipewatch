"""Tests for ThresholdEvaluator and ThresholdConfig."""
import json
import pytest
from pathlib import Path

from pipewatch.core.threshold import Threshold, ThresholdOperator
from pipewatch.core.threshold_evaluator import ThresholdEvaluator
from pipewatch.core.threshold_config import ThresholdConfig
from pipewatch.core.alert import AlertLevel


@pytest.fixture
def evaluator():
    return ThresholdEvaluator([
        Threshold("warn_latency", 300.0, ThresholdOperator.GT),
        Threshold("critical_error_rate", 0.1, ThresholdOperator.GTE),
        Threshold("throughput", 50.0, ThresholdOperator.LT),
    ])


class TestThresholdEvaluator:
    def test_no_breach_returns_empty(self, evaluator):
        alerts = evaluator.evaluate("pipe-a", {"warn_latency": 100.0})
        assert alerts == []

    def test_single_breach_returns_alert(self, evaluator):
        alerts = evaluator.evaluate("pipe-a", {"warn_latency": 500.0})
        assert len(alerts) == 1
        assert "warn_latency" in alerts[0].message

    def test_critical_level_assigned(self, evaluator):
        alerts = evaluator.evaluate("pipe-a", {"critical_error_rate": 0.2})
        assert alerts[0].level == AlertLevel.CRITICAL

    def test_warning_level_assigned(self, evaluator):
        alerts = evaluator.evaluate("pipe-a", {"warn_latency": 999.0})
        assert alerts[0].level == AlertLevel.WARNING

    def test_missing_metric_skipped(self, evaluator):
        alerts = evaluator.evaluate("pipe-a", {})
        assert alerts == []

    def test_pipeline_name_in_alert(self, evaluator):
        alerts = evaluator.evaluate("my-pipeline", {"warn_latency": 999.0})
        assert alerts[0].pipeline_name == "my-pipeline"

    def test_summary_contains_count(self, evaluator):
        s = evaluator.summary()
        assert s["threshold_count"] == 3


class TestThresholdConfig:
    def test_add_and_len(self):
        cfg = ThresholdConfig()
        cfg.add(Threshold("x", 1.0))
        assert len(cfg) == 1

    def test_remove_existing(self):
        cfg = ThresholdConfig([Threshold("x", 1.0)])
        removed = cfg.remove("x")
        assert removed is True
        assert len(cfg) == 0

    def test_remove_missing(self):
        cfg = ThresholdConfig()
        assert cfg.remove("nonexistent") is False

    def test_get_returns_threshold(self):
        t = Threshold("latency", 200.0)
        cfg = ThresholdConfig([t])
        assert cfg.get("latency") is t

    def test_get_missing_returns_none(self):
        cfg = ThresholdConfig()
        assert cfg.get("missing") is None

    def test_roundtrip_dict(self):
        cfg = ThresholdConfig([Threshold("err", 5.0, ThresholdOperator.GTE)])
        restored = ThresholdConfig.from_dict(cfg.to_dict())
        assert len(restored) == 1
        assert restored.get("err").value == 5.0

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "thresholds.json"
        cfg = ThresholdConfig([Threshold("warn_latency", 100.0)])
        cfg.save(path)
        loaded = ThresholdConfig.load(path)
        assert len(loaded) == 1
        assert loaded.get("warn_latency").value == 100.0

    def test_repr(self):
        cfg = ThresholdConfig([Threshold("a", 1.0)])
        assert "1" in repr(cfg)
