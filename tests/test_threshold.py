"""Tests for Threshold and ThresholdOperator."""
import pytest
from pipewatch.core.threshold import Threshold, ThresholdOperator


class TestThresholdEvaluate:
    def test_gt_breached(self):
        t = Threshold("error_rate", 0.05, ThresholdOperator.GT)
        assert t.evaluate(0.10) is True

    def test_gt_not_breached(self):
        t = Threshold("error_rate", 0.05, ThresholdOperator.GT)
        assert t.evaluate(0.03) is False

    def test_gte_boundary(self):
        t = Threshold("latency", 500.0, ThresholdOperator.GTE)
        assert t.evaluate(500.0) is True

    def test_lt_breached(self):
        t = Threshold("throughput", 100.0, ThresholdOperator.LT)
        assert t.evaluate(50.0) is True

    def test_lte_not_breached(self):
        t = Threshold("throughput", 100.0, ThresholdOperator.LTE)
        assert t.evaluate(150.0) is False

    def test_eq_breached(self):
        t = Threshold("retries", 3.0, ThresholdOperator.EQ)
        assert t.evaluate(3.0) is True


class TestThresholdSerialisation:
    def test_to_dict_keys(self):
        t = Threshold("warn_latency", 200.0, ThresholdOperator.GT, "High latency")
        d = t.to_dict()
        assert d["name"] == "warn_latency"
        assert d["value"] == 200.0
        assert d["operator"] == "gt"
        assert d["description"] == "High latency"

    def test_from_dict_roundtrip(self):
        original = Threshold("critical_errors", 10.0, ThresholdOperator.GTE)
        restored = Threshold.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.value == original.value
        assert restored.operator == original.operator

    def test_from_dict_default_operator(self):
        t = Threshold.from_dict({"name": "x", "value": 1.0})
        assert t.operator == ThresholdOperator.GT

    def test_repr(self):
        t = Threshold("foo", 42.0)
        assert "foo" in repr(t)
        assert "42.0" in repr(t)
