"""Tests for PipelineHistory and RunRecord."""

import json
import pytest
from pathlib import Path

from pipewatch.core.history import PipelineHistory, RunRecord


@pytest.fixture
def history():
    return PipelineHistory(max_records=5)


@pytest.fixture
def sample_record():
    return RunRecord(
        pipeline_name="etl_sales",
        status="healthy",
        health_score=1.0,
        timestamp="2024-01-01T00:00:00",
    )


class TestRunRecord:
    def test_to_dict(self, sample_record):
        d = sample_record.to_dict()
        assert d["pipeline_name"] == "etl_sales"
        assert d["status"] == "healthy"
        assert d["health_score"] == 1.0

    def test_from_dict_roundtrip(self, sample_record):
        restored = RunRecord.from_dict(sample_record.to_dict())
        assert restored.pipeline_name == sample_record.pipeline_name
        assert restored.health_score == sample_record.health_score
        assert restored.timestamp == sample_record.timestamp


class TestPipelineHistory:
    def test_record_and_get(self, history, sample_record):
        history.record(sample_record)
        records = history.get("etl_sales")
        assert len(records) == 1
        assert records[0].status == "healthy"

    def test_max_records_enforced(self, history):
        for i in range(10):
            history.record(RunRecord("pipe", "healthy", float(i)))
        assert len(history.get("pipe")) == 5

    def test_last_status(self, history):
        history.record(RunRecord("pipe", "healthy", 1.0))
        history.record(RunRecord("pipe", "degraded", 0.5))
        assert history.last_status("pipe") == "degraded"

    def test_last_status_unknown_pipeline(self, history):
        assert history.last_status("missing") is None

    def test_average_health(self, history):
        for score in [0.8, 1.0, 0.6]:
            history.record(RunRecord("pipe", "healthy", score))
        avg = history.average_health("pipe")
        assert avg == pytest.approx(0.8, rel=1e-3)

    def test_average_health_no_records(self, history):
        assert history.average_health("nonexistent") is None

    def test_all_pipeline_names(self, history):
        history.record(RunRecord("a", "healthy", 1.0))
        history.record(RunRecord("b", "healthy", 1.0))
        assert set(history.all_pipeline_names()) == {"a", "b"}

    def test_save_and_load(self, history, tmp_path):
        history.record(RunRecord("etl", "healthy", 0.9, "2024-01-01T00:00:00"))
        path = tmp_path / "history.json"
        history.save(path)

        new_history = PipelineHistory()
        new_history.load(path)
        records = new_history.get("etl")
        assert len(records) == 1
        assert records[0].health_score == 0.9

    def test_load_missing_file_is_noop(self, history, tmp_path):
        history.load(tmp_path / "nonexistent.json")  # should not raise
        assert history.all_pipeline_names() == []
