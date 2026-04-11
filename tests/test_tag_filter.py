"""Tests for TagFilter."""
import pytest
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.tag import TagSet
from pipewatch.core.tag_filter import TagFilter


def _make_pipeline(name: str, *tags: str) -> Pipeline:
    p = Pipeline(name=name, source="test")
    p.tags.add(*tags) if tags else None
    return p


@pytest.fixture
def monitor():
    m = Monitor()
    m.register_pipeline(_make_pipeline("pipe-a", "finance", "daily"))
    m.register_pipeline(_make_pipeline("pipe-b", "finance", "weekly"))
    m.register_pipeline(_make_pipeline("pipe-c", "ops", "daily"))
    m.register_pipeline(_make_pipeline("pipe-d"))  # untagged
    return m


@pytest.fixture
def tag_filter(monitor):
    return TagFilter(monitor)


class TestTagFilter:
    def test_by_tag_finance(self, tag_filter):
        result = tag_filter.by_tag("finance")
        names = {p.name for p in result}
        assert names == {"pipe-a", "pipe-b"}

    def test_by_tag_daily(self, tag_filter):
        result = tag_filter.by_tag("daily")
        names = {p.name for p in result}
        assert names == {"pipe-a", "pipe-c"}

    def test_by_tag_missing(self, tag_filter):
        assert tag_filter.by_tag("nonexistent") == []

    def test_by_any_tags(self, tag_filter):
        result = tag_filter.by_any_tags("weekly", "ops")
        names = {p.name for p in result}
        assert names == {"pipe-b", "pipe-c"}

    def test_by_all_tags(self, tag_filter):
        result = tag_filter.by_all_tags("finance", "daily")
        names = {p.name for p in result}
        assert names == {"pipe-a"}

    def test_by_all_tags_no_match(self, tag_filter):
        assert tag_filter.by_all_tags("finance", "ops") == []

    def test_group_by_tag_keys(self, tag_filter):
        groups = tag_filter.group_by_tag()
        assert set(groups.keys()) == {"finance", "daily", "weekly", "ops"}

    def test_group_by_tag_values(self, tag_filter):
        groups = tag_filter.group_by_tag()
        assert len(groups["finance"]) == 2
        assert len(groups["daily"]) == 2
        assert len(groups["weekly"]) == 1

    def test_untagged(self, tag_filter):
        result = tag_filter.untagged()
        assert len(result) == 1
        assert result[0].name == "pipe-d"
