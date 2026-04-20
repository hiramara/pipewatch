"""Tests for ChangelogExporter."""

import json

import pytest

from pipewatch.core.pipeline_changelog import PipelineChangelog
from pipewatch.core.changelog_exporter import ChangelogExporter


@pytest.fixture()
def changelog() -> PipelineChangelog:
    cl = PipelineChangelog()
    cl.record("etl_orders", "Initial deploy", author="alice", tags=["deploy"])
    cl.record("etl_orders", "Hotfix", author="bob", tags=["fix"])
    cl.record("etl_users", "Schema migration", author="carol")
    return cl


@pytest.fixture()
def exporter(changelog) -> ChangelogExporter:
    return ChangelogExporter(changelog)


class TestChangelogExporter:
    def test_to_dicts_returns_all(self, exporter):
        result = exporter.to_dicts()
        assert len(result) == 3

    def test_to_dicts_filtered_by_pipeline(self, exporter):
        result = exporter.to_dicts(pipeline_name="etl_orders")
        assert len(result) == 2
        assert all(r["pipeline_name"] == "etl_orders" for r in result)

    def test_to_dicts_unknown_pipeline_returns_empty(self, exporter):
        assert exporter.to_dicts(pipeline_name="does_not_exist") == []

    def test_to_json_valid_json(self, exporter):
        raw = exporter.to_json()
        parsed = json.loads(raw)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_to_json_filtered(self, exporter):
        raw = exporter.to_json(pipeline_name="etl_users")
        parsed = json.loads(raw)
        assert len(parsed) == 1
        assert parsed[0]["pipeline_name"] == "etl_users"

    def test_to_csv_contains_header(self, exporter):
        csv_output = exporter.to_csv()
        assert "pipeline_name" in csv_output
        assert "description" in csv_output

    def test_to_csv_tags_pipe_separated(self, exporter):
        csv_output = exporter.to_csv(pipeline_name="etl_orders")
        assert "deploy" in csv_output

    def test_to_csv_empty_returns_empty_string(self):
        empty_cl = PipelineChangelog()
        exp = ChangelogExporter(empty_cl)
        assert exp.to_csv() == ""

    def test_to_dicts_dict_keys(self, exporter):
        rows = exporter.to_dicts()
        for row in rows:
            assert "pipeline_name" in row
            assert "timestamp" in row
            assert "description" in row
            assert "author" in row
            assert "tags" in row
