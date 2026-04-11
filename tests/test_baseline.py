"""Tests for Baseline and BaselineMetric."""
import pytest
from pipewatch.core.baseline import Baseline, BaselineMetric


class TestBaselineMetric:
    def test_initial_state(self):
        m = BaselineMetric(name="health_score")
        assert m.average is None
        assert m.minimum is None
        assert m.maximum is None
        assert m.values == []

    def test_record_updates_values(self):
        m = BaselineMetric(name="health_score")
        m.record(0.8)
        m.record(0.6)
        assert len(m.values) == 2
        assert m.average == pytest.approx(0.7)

    def test_minimum_and_maximum(self):
        m = BaselineMetric(name="score")
        for v in [0.5, 0.9, 0.3]:
            m.record(v)
        assert m.minimum == pytest.approx(0.3)
        assert m.maximum == pytest.approx(0.9)

    def test_to_dict_keys(self):
        m = BaselineMetric(name="score")
        m.record(1.0)
        d = m.to_dict()
        assert set(d.keys()) == {"name", "average", "minimum", "maximum", "sample_count", "updated_at"}
        assert d["sample_count"] == 1

    def test_updated_at_set_on_record(self):
        m = BaselineMetric(name="score")
        assert m.updated_at is None
        m.record(0.5)
        assert m.updated_at is not None


class TestBaseline:
    def test_record_and_get(self):
        b = Baseline(pipeline_name="etl_sales")
        b.record("health_score", 0.9)
        metric = b.get("health_score")
        assert metric is not None
        assert metric.average == pytest.approx(0.9)

    def test_get_unknown_metric_returns_none(self):
        b = Baseline(pipeline_name="etl_sales")
        assert b.get("nonexistent") is None

    def test_metric_names(self):
        b = Baseline(pipeline_name="etl_sales")
        b.record("health_score", 1.0)
        b.record("latency", 200.0)
        assert set(b.metric_names()) == {"health_score", "latency"}

    def test_to_dict_structure(self):
        b = Baseline(pipeline_name="etl_sales")
        b.record("health_score", 0.8)
        d = b.to_dict()
        assert d["pipeline"] == "etl_sales"
        assert "health_score" in d["metrics"]
