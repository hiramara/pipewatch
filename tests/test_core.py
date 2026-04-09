"""Tests for core pipeline and check functionality."""

import pytest
from datetime import datetime
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.check import Check, CheckStatus


class TestPipeline:
    """Test Pipeline class."""

    def test_pipeline_initialization(self):
        """Test basic pipeline creation."""
        pipeline = Pipeline(
            name="test_pipeline",
            source="airflow",
            description="Test pipeline",
            tags=["test", "daily"],
        )
        assert pipeline.name == "test_pipeline"
        assert pipeline.source == "airflow"
        assert pipeline.status == PipelineStatus.UNKNOWN
        assert len(pipeline.tags) == 2

    def test_pipeline_status_update(self):
        """Test updating pipeline status."""
        pipeline = Pipeline(name="test", source="custom")
        assert pipeline.last_check is None

        pipeline.update_status(PipelineStatus.HEALTHY)
        assert pipeline.status == PipelineStatus.HEALTHY
        assert pipeline.last_check is not None

    def test_pipeline_metadata(self):
        """Test adding metadata to pipeline."""
        pipeline = Pipeline(name="test", source="custom")
        pipeline.add_metadata("owner", "data-team")
        pipeline.add_metadata("frequency", "hourly")

        assert pipeline.metadata["owner"] == "data-team"
        assert pipeline.metadata["frequency"] == "hourly"

    def test_pipeline_to_dict(self):
        """Test pipeline serialization."""
        pipeline = Pipeline(name="test", source="databricks")
        pipeline.update_status(PipelineStatus.HEALTHY)

        result = pipeline.to_dict()
        assert result["name"] == "test"
        assert result["source"] == "databricks"
        assert result["status"] == "healthy"


class TestCheck:
    """Test Check class."""

    def test_check_initialization(self):
        """Test basic check creation."""
        check = Check(
            name="freshness_check",
            check_type="freshness",
            description="Check data freshness",
        )
        assert check.name == "freshness_check"
        assert check.check_type == "freshness"
        assert check.status == CheckStatus.SKIPPED

    def test_check_mark_pass(self):
        """Test marking check as passed."""
        check = Check(name="test", check_type="custom")
        check.mark_pass(message="All good", rows_checked=1000)

        assert check.status == CheckStatus.PASS
        assert check.message == "All good"
        assert check.details["rows_checked"] == 1000
        assert check.executed_at is not None

    def test_check_mark_fail(self):
        """Test marking check as failed."""
        check = Check(name="test", check_type="custom")
        check.mark_fail(message="Data too old", hours_old=48)

        assert check.status == CheckStatus.FAIL
        assert check.message == "Data too old"
        assert check.details["hours_old"] == 48

    def test_check_to_dict(self):
        """Test check serialization."""
        check = Check(name="row_count", check_type="row_count")
        check.mark_warning(message="Low row count")

        result = check.to_dict()
        assert result["name"] == "row_count"
        assert result["status"] == "warning"
        assert result["message"] == "Low row count"
