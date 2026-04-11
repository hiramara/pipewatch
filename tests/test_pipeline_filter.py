"""Tests for pipewatch.core.pipeline_filter."""

import pytest

from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.pipeline_filter import PipelineFilter


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_pipeline(
    name: str,
    status: PipelineStatus = PipelineStatus.HEALTHY,
    metadata: dict | None = None,
) -> Pipeline:
    p = Pipeline(name=name)
    p.update_status(status)
    if metadata:
        for k, v in metadata.items():
            p.add_metadata(k, v)
    return p


@pytest.fixture()
def pipelines() -> list[Pipeline]:
    return [
        _make_pipeline("finance.daily", PipelineStatus.HEALTHY, {"team": "finance"}),
        _make_pipeline("finance.weekly", PipelineStatus.FAILING, {"team": "finance"}),
        _make_pipeline("ops.hourly", PipelineStatus.HEALTHY, {"team": "ops"}),
        _make_pipeline("ops.nightly", PipelineStatus.UNKNOWN, {"team": "ops"}),
        _make_pipeline("data.etl", PipelineStatus.FAILING, {"team": "data"}),
    ]


@pytest.fixture()
def pf(pipelines) -> PipelineFilter:
    return PipelineFilter(pipelines)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestPipelineFilterInit:
    def test_len(self, pf, pipelines):
        assert len(pf) == len(pipelines)

    def test_all_returns_copy(self, pf, pipelines):
        result = pf.all()
        assert result == pipelines
        assert result is not pf._pipelines


# ---------------------------------------------------------------------------
# Status filters
# ---------------------------------------------------------------------------

class TestStatusFilters:
    def test_healthy(self, pf):
        result = pf.healthy()
        assert len(result) == 2
        assert all(p.status == PipelineStatus.HEALTHY for p in result)

    def test_failing(self, pf):
        result = pf.failing()
        assert len(result) == 2
        assert all(p.status == PipelineStatus.FAILING for p in result)

    def test_unknown(self, pf):
        result = pf.unknown()
        assert len(result) == 1
        assert result[0].name == "ops.nightly"

    def test_by_status_explicit(self, pf):
        result = pf.by_status(PipelineStatus.HEALTHY)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Name filters
# ---------------------------------------------------------------------------

class TestNameFilters:
    def test_by_name_found(self, pf):
        result = pf.by_name("ops.hourly")
        assert result is not None
        assert result.name == "ops.hourly"

    def test_by_name_not_found(self, pf):
        assert pf.by_name("nonexistent") is None

    def test_by_name_prefix(self, pf):
        result = pf.by_name_prefix("finance")
        assert len(result) == 2
        assert all(p.name.startswith("finance") for p in result)


# ---------------------------------------------------------------------------
# Metadata filter
# ---------------------------------------------------------------------------

class TestMetadataFilter:
    def test_by_metadata_team_finance(self, pf):
        result = pf.by_metadata("team", "finance")
        assert len(result) == 2

    def test_by_metadata_no_match(self, pf):
        result = pf.by_metadata("team", "marketing")
        assert result == []


# ---------------------------------------------------------------------------
# Predicate filter
# ---------------------------------------------------------------------------

class TestWhereFilter:
    def test_where_custom_predicate(self, pf):
        result = pf.where(lambda p: "nightly" in p.name)
        assert len(result) == 1
        assert result[0].name == "ops.nightly"

    def test_where_no_match(self, pf):
        assert pf.where(lambda p: False) == []
