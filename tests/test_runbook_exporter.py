"""Tests for RunbookExporter."""
import csv
import io
import json
import pytest

from pipewatch.core.pipeline_runbook import RunbookEntry, RunbookRegistry
from pipewatch.core.runbook_exporter import RunbookExporter


@pytest.fixture
def registry() -> RunbookRegistry:
    reg = RunbookRegistry()
    reg.add(RunbookEntry(
        pipeline_name="sales_etl",
        title="Handle stale data",
        steps=["Check source", "Restart"],
        owner="alice",
        tags=["stale"],
    ))
    reg.add(RunbookEntry(
        pipeline_name="finance_etl",
        title="Fix schema drift",
        steps=["Compare schemas", "Apply migration"],
        owner="bob",
        tags=["schema"],
    ))
    return reg


@pytest.fixture
def exporter(registry) -> RunbookExporter:
    return RunbookExporter(registry)


class TestRunbookExporter:
    def test_to_dicts_returns_all(self, exporter):
        dicts = exporter.to_dicts()
        assert len(dicts) == 2

    def test_to_dicts_dict_keys(self, exporter):
        d = exporter.to_dicts()[0]
        assert "pipeline_name" in d
        assert "title" in d
        assert "steps" in d

    def test_to_json_is_valid(self, exporter):
        result = json.loads(exporter.to_json())
        assert isinstance(result, list)
        assert len(result) == 2

    def test_to_csv_has_header(self, exporter):
        csv_text = exporter.to_csv()
        assert "pipeline_name" in csv_text
        assert "title" in csv_text

    def test_to_csv_contains_data(self, exporter):
        csv_text = exporter.to_csv()
        assert "sales_etl" in csv_text
        assert "finance_etl" in csv_text

    def test_to_csv_steps_joined_by_pipe(self, exporter):
        csv_text = exporter.to_csv()
        assert "Check source|Restart" in csv_text

    def test_filter_limits_output(self, registry):
        exp = RunbookExporter(registry, pipeline_filter=lambda n: n == "sales_etl")
        dicts = exp.to_dicts()
        assert len(dicts) == 1
        assert dicts[0]["pipeline_name"] == "sales_etl"

    def test_to_csv_empty_registry(self):
        exp = RunbookExporter(RunbookRegistry())
        assert exp.to_csv() == ""

    def test_to_json_empty_registry(self):
        exp = RunbookExporter(RunbookRegistry())
        assert json.loads(exp.to_json()) == []
