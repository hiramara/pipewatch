"""Tests for HealthTrendAnalyzer and TrendExporter."""
import json
import pytest
from unittest.mock import MagicMock

from pipewatch.core.pipeline_health_trend import TrendDirection
from pipewatch.core.health_trend_analyzer import HealthTrendAnalyzer
from pipewatch.core.trend_exporter import TrendExporter


def _make_summary(name: str):
    s = MagicMock()
    s.name = name
    return s


def _make_report(*names: str):
    r = MagicMock()
    r.pipelines = [_make_summary(n) for n in names]
    return r


@pytest.fixture()
def collector():
    c = MagicMock()
    c.trend_summary.side_effect = lambda name: {
        "alpha": [0.9, 0.5],
        "beta": [0.5, 0.8],
        "gamma": [0.7, 0.72],
    }.get(name, [])
    return c


@pytest.fixture()
def analyzer(collector):
    return HealthTrendAnalyzer(collector)


@pytest.fixture()
def report():
    return _make_report("alpha", "beta", "gamma")


class TestHealthTrendAnalyzer:
    def test_analyze_returns_all_pipelines(self, analyzer, report):
        result = analyzer.analyze(report)
        assert set(result.keys()) == {"alpha", "beta", "gamma"}

    def test_degrading_pipeline_detected(self, analyzer, report):
        result = analyzer.analyze(report)
        assert result["alpha"].direction == TrendDirection.DEGRADING

    def test_improving_pipeline_detected(self, analyzer, report):
        result = analyzer.analyze(report)
        assert result["beta"].direction == TrendDirection.IMPROVING

    def test_stable_pipeline_detected(self, analyzer, report):
        result = analyzer.analyze(report)
        assert result["gamma"].direction == TrendDirection.STABLE

    def test_degrading_filter(self, analyzer, report):
        degrading = analyzer.degrading(report)
        assert len(degrading) == 1
        assert degrading[0].pipeline_name == "alpha"

    def test_improving_filter(self, analyzer, report):
        improving = analyzer.improving(report)
        assert len(improving) == 1
        assert improving[0].pipeline_name == "beta"

    def test_to_dicts_returns_list(self, analyzer, report):
        dicts = analyzer.to_dicts(report)
        assert isinstance(dicts, list)
        assert all(isinstance(d, dict) for d in dicts)


class TestTrendExporter:
    def test_to_json_valid(self, analyzer, report):
        exporter = TrendExporter(analyzer)
        result = json.loads(exporter.to_json(report))
        assert isinstance(result, list)
        assert len(result) == 3

    def test_to_csv_has_header(self, analyzer, report):
        exporter = TrendExporter(analyzer)
        csv_out = exporter.to_csv(report)
        assert "pipeline_name" in csv_out
        assert "direction" in csv_out

    def test_to_csv_empty_report(self, analyzer):
        exporter = TrendExporter(analyzer)
        empty_report = _make_report()
        assert exporter.to_csv(empty_report) == ""
