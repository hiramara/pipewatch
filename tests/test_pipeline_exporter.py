"""Tests for PipelineExporter."""

from __future__ import annotations

import json
import csv
import io
from unittest.mock import MagicMock

import pytest

from pipewatch.core.pipeline import PipelineStatus
from pipewatch.core.reporter import PipelineSummary, Report
from pipewatch.core.pipeline_exporter import PipelineExporter


def _make_summary(name: str, status: PipelineStatus = PipelineStatus.HEALTHY,
                  health: float = 1.0, total: int = 3, passed: int = 3,
                  failed: int = 0) -> PipelineSummary:
    s = MagicMock(spec=PipelineSummary)
    s.name = name
    s.status = status
    s.health_score = health
    s.total_checks = total
    s.passed_checks = passed
    s.failed_checks = failed
    s.last_updated = "2024-01-01T00:00:00"
    return s


@pytest.fixture()
def report() -> Report:
    r = MagicMock(spec=Report)
    r.pipelines = [
        _make_summary("alpha", PipelineStatus.HEALTHY, 1.0, 4, 4, 0),
        _make_summary("beta", PipelineStatus.FAILING, 0.5, 4, 2, 2),
        _make_summary("gamma", PipelineStatus.HEALTHY, 0.75, 4, 3, 1),
    ]
    return r


@pytest.fixture()
def exporter(report: Report) -> PipelineExporter:
    return PipelineExporter(report)


class TestPipelineExporterToDicts:
    def test_returns_all_when_no_filter(self, exporter):
        result = exporter.to_dicts()
        assert len(result) == 3

    def test_filtered_by_names(self, exporter):
        result = exporter.to_dicts(["alpha", "gamma"])
        names = [r["name"] for r in result]
        assert names == ["alpha", "gamma"]

    def test_unknown_name_excluded(self, exporter):
        result = exporter.to_dicts(["alpha", "unknown"])
        assert len(result) == 1
        assert result[0]["name"] == "alpha"

    def test_dict_contains_expected_keys(self, exporter):
        result = exporter.to_dicts(["beta"])
        keys = set(result[0].keys())
        assert {"name", "status", "health_score", "total_checks",
                "passed_checks", "failed_checks", "last_updated"} <= keys

    def test_status_is_string_value(self, exporter):
        result = exporter.to_dicts(["beta"])
        assert result[0]["status"] == PipelineStatus.FAILING.value


class TestPipelineExporterToJson:
    def test_returns_valid_json(self, exporter):
        raw = exporter.to_json()
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) == 3

    def test_filtered_json(self, exporter):
        raw = exporter.to_json(["alpha"])
        data = json.loads(raw)
        assert len(data) == 1
        assert data[0]["name"] == "alpha"


class TestPipelineExporterToCsv:
    def test_returns_non_empty_string(self, exporter):
        result = exporter.to_csv()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_csv_has_header_row(self, exporter):
        result = exporter.to_csv()
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 3
        assert "name" in reader.fieldnames

    def test_empty_filter_returns_empty_string(self, exporter):
        result = exporter.to_csv([])
        assert result == ""
