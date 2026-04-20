"""Tests for IncidentLogExporter."""
from __future__ import annotations

import json

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.incident_log_exporter import IncidentLogExporter
from pipewatch.core.pipeline_incident_log import PipelineIncidentLog


def _make_alert(name: str, level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(pipeline_name=name, level=level, message=f"{name} issue")


@pytest.fixture
def log() -> PipelineIncidentLog:
    il = PipelineIncidentLog()
    il.record(_make_alert("alpha"))
    il.record(_make_alert("beta", AlertLevel.CRITICAL))
    il.record(_make_alert("alpha", AlertLevel.CRITICAL))
    return il


@pytest.fixture
def exporter(log) -> IncidentLogExporter:
    return IncidentLogExporter(log)


class TestIncidentLogExporter:
    def test_to_dicts_returns_all(self, exporter):
        result = exporter.to_dicts()
        assert len(result) == 3

    def test_to_dicts_filtered_by_pipeline(self, exporter):
        result = exporter.to_dicts(pipeline_name="alpha")
        assert len(result) == 2
        assert all(r["pipeline_name"] == "alpha" for r in result)

    def test_to_dicts_unknown_pipeline_returns_empty(self, exporter):
        assert exporter.to_dicts(pipeline_name="ghost") == []

    def test_to_json_is_valid_json(self, exporter):
        raw = exporter.to_json()
        parsed = json.loads(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_to_json_filtered(self, exporter):
        raw = exporter.to_json(pipeline_name="beta")
        parsed = json.loads(raw)
        assert len(parsed) == 1
        assert parsed[0]["pipeline_name"] == "beta"

    def test_to_csv_contains_header(self, exporter):
        csv_output = exporter.to_csv()
        assert "pipeline_name" in csv_output
        assert "alert_level" in csv_output

    def test_to_csv_empty_log_returns_empty_string(self):
        empty_log = PipelineIncidentLog()
        exp = IncidentLogExporter(empty_log)
        assert exp.to_csv() == ""

    def test_to_csv_row_count(self, exporter):
        csv_output = exporter.to_csv()
        lines = [l for l in csv_output.strip().splitlines() if l]
        # 1 header + 3 data rows
        assert len(lines) == 4
