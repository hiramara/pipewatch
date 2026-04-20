"""Tests for PipelineChangelog and ChangelogEntry."""

from datetime import datetime, timezone

import pytest

from pipewatch.core.pipeline_changelog import ChangelogEntry, PipelineChangelog


@pytest.fixture()
def changelog() -> PipelineChangelog:
    return PipelineChangelog()


class TestChangelogEntry:
    def test_to_dict_keys(self):
        entry = ChangelogEntry(
            pipeline_name="etl_orders",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            description="Initial deploy",
            author="alice",
            tags=["deploy"],
        )
        assert set(entry.to_dict().keys()) == {
            "pipeline_name", "timestamp", "description", "author", "tags"
        }

    def test_to_dict_values(self):
        ts = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        entry = ChangelogEntry(
            pipeline_name="etl_orders",
            timestamp=ts,
            description="Hotfix",
            author="bob",
            tags=["fix", "urgent"],
        )
        d = entry.to_dict()
        assert d["pipeline_name"] == "etl_orders"
        assert d["author"] == "bob"
        assert d["tags"] == ["fix", "urgent"]
        assert d["timestamp"] == ts.isoformat()

    def test_default_author_is_none(self):
        entry = ChangelogEntry(
            pipeline_name="p",
            timestamp=datetime.now(timezone.utc),
            description="x",
        )
        assert entry.author is None
        assert entry.to_dict()["author"] is None


class TestPipelineChangelog:
    def test_record_returns_entry(self, changelog):
        entry = changelog.record("etl_orders", "Initial deploy", author="alice")
        assert isinstance(entry, ChangelogEntry)
        assert entry.pipeline_name == "etl_orders"

    def test_entries_for_filters_by_pipeline(self, changelog):
        changelog.record("etl_orders", "deploy")
        changelog.record("etl_users", "deploy")
        changelog.record("etl_orders", "hotfix")
        results = changelog.entries_for("etl_orders")
        assert len(results) == 2
        assert all(e.pipeline_name == "etl_orders" for e in results)

    def test_all_entries_returns_everything(self, changelog):
        changelog.record("a", "x")
        changelog.record("b", "y")
        assert len(changelog.all_entries()) == 2

    def test_clear_specific_pipeline(self, changelog):
        changelog.record("a", "x")
        changelog.record("b", "y")
        changelog.clear("a")
        assert changelog.entries_for("a") == []
        assert len(changelog.entries_for("b")) == 1

    def test_clear_all(self, changelog):
        changelog.record("a", "x")
        changelog.record("b", "y")
        changelog.clear()
        assert changelog.all_entries() == []

    def test_custom_timestamp_preserved(self, changelog):
        ts = datetime(2023, 3, 10, tzinfo=timezone.utc)
        entry = changelog.record("p", "deploy", timestamp=ts)
        assert entry.timestamp == ts

    def test_tags_stored(self, changelog):
        entry = changelog.record("p", "deploy", tags=["ci", "prod"])
        assert entry.tags == ["ci", "prod"]
