"""Tests for RunbookEntry and RunbookRegistry."""
import pytest
from pipewatch.core.pipeline_runbook import RunbookEntry, RunbookRegistry


@pytest.fixture
def registry() -> RunbookRegistry:
    return RunbookRegistry()


@pytest.fixture
def entry() -> RunbookEntry:
    return RunbookEntry(
        pipeline_name="sales_etl",
        title="Handle stale data",
        steps=["Check source", "Restart job", "Verify output"],
        owner="alice",
        tags=["stale", "etl"],
    )


class TestRunbookEntry:
    def test_to_dict_keys(self, entry):
        d = entry.to_dict()
        assert set(d.keys()) == {"pipeline_name", "title", "steps", "owner", "tags", "created_at"}

    def test_to_dict_values(self, entry):
        d = entry.to_dict()
        assert d["pipeline_name"] == "sales_etl"
        assert d["title"] == "Handle stale data"
        assert d["owner"] == "alice"
        assert d["steps"] == ["Check source", "Restart job", "Verify output"]
        assert d["tags"] == ["stale", "etl"]

    def test_repr_contains_name_and_title(self, entry):
        r = repr(entry)
        assert "sales_etl" in r
        assert "Handle stale data" in r

    def test_created_at_is_iso_string(self, entry):
        d = entry.to_dict()
        assert "T" in d["created_at"]


class TestRunbookRegistry:
    def test_add_and_get(self, registry, entry):
        registry.add(entry)
        results = registry.get("sales_etl")
        assert len(results) == 1
        assert results[0].title == "Handle stale data"

    def test_get_unknown_returns_empty(self, registry):
        assert registry.get("nonexistent") == []

    def test_multiple_entries_same_pipeline(self, registry, entry):
        entry2 = RunbookEntry(pipeline_name="sales_etl", title="Retry logic", steps=["Step A"])
        registry.add(entry)
        registry.add(entry2)
        assert len(registry.get("sales_etl")) == 2

    def test_remove_existing_entry(self, registry, entry):
        registry.add(entry)
        removed = registry.remove("sales_etl", "Handle stale data")
        assert removed is True
        assert registry.get("sales_etl") == []

    def test_remove_nonexistent_returns_false(self, registry):
        removed = registry.remove("sales_etl", "Nonexistent")
        assert removed is False

    def test_all_pipelines(self, registry, entry):
        registry.add(entry)
        registry.add(RunbookEntry(pipeline_name="other_etl", title="Fix", steps=[]))
        names = registry.all_pipelines()
        assert "sales_etl" in names
        assert "other_etl" in names

    def test_all_entries(self, registry, entry):
        registry.add(entry)
        assert len(registry.all_entries()) == 1
