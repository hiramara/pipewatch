"""Tests for LabelFilter."""
import pytest
from unittest.mock import MagicMock

from pipewatch.core.pipeline_labeler import PipelineLabeler
from pipewatch.core.label_filter import LabelFilter
from pipewatch.core.reporter import PipelineSummary


def _make_summary(name: str) -> PipelineSummary:
    s = MagicMock(spec=PipelineSummary)
    s.name = name
    return s


def _make_report(*names: str):
    report = MagicMock()
    report.pipelines = [_make_summary(n) for n in names]
    return report


@pytest.fixture()
def labeler():
    lb = PipelineLabeler()
    lb.set_label("pipe_a", "env", "prod")
    lb.set_label("pipe_b", "env", "prod")
    lb.set_label("pipe_b", "team", "data")
    lb.set_label("pipe_c", "env", "staging")
    return lb


@pytest.fixture()
def report():
    return _make_report("pipe_a", "pipe_b", "pipe_c", "pipe_d")


@pytest.fixture()
def lf(labeler):
    return LabelFilter(labeler)


class TestLabelFilter:
    def test_by_label_returns_matching(self, lf, report):
        result = lf.by_label(report, "env", "prod")
        names = {s.name for s in result}
        assert names == {"pipe_a", "pipe_b"}

    def test_by_label_no_match_returns_empty(self, lf, report):
        result = lf.by_label(report, "env", "nonexistent")
        assert result == []

    def test_by_all_labels_intersection(self, lf, report):
        result = lf.by_all_labels(report, {"env": "prod", "team": "data"})
        assert len(result) == 1
        assert result[0].name == "pipe_b"

    def test_by_all_labels_empty_criteria_returns_all(self, lf, report):
        result = lf.by_all_labels(report, {})
        assert len(result) == len(report.pipelines)

    def test_by_label_key_returns_pipelines_with_key(self, lf, report):
        result = lf.by_label_key(report, "team")
        assert len(result) == 1
        assert result[0].name == "pipe_b"

    def test_by_label_key_missing_key_returns_empty(self, lf, report):
        result = lf.by_label_key(report, "nonexistent")
        assert result == []

    def test_pipeline_not_in_report_not_returned(self, lf):
        small_report = _make_report("pipe_d")
        result = lf.by_label(small_report, "env", "prod")
        assert result == []
