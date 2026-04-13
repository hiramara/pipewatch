"""Tests for pipeline ownership tracking and exporter."""
import json
import pytest

from pipewatch.core.pipeline_ownership import Owner, OwnershipRegistry
from pipewatch.core.ownership_exporter import OwnershipExporter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def registry() -> OwnershipRegistry:
    return OwnershipRegistry()


@pytest.fixture()
def alice() -> Owner:
    return Owner(name="Alice", email="alice@example.com", team="data-eng")


@pytest.fixture()
def bob() -> Owner:
    return Owner(name="Bob", team="data-eng")


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class TestOwner:
    def test_to_dict_keys(self, alice):
        d = alice.to_dict()
        assert set(d.keys()) == {"name", "email", "team"}

    def test_to_dict_values(self, alice):
        d = alice.to_dict()
        assert d["name"] == "Alice"
        assert d["email"] == "alice@example.com"
        assert d["team"] == "data-eng"

    def test_from_dict_roundtrip(self, alice):
        restored = Owner.from_dict(alice.to_dict())
        assert restored.name == alice.name
        assert restored.email == alice.email
        assert restored.team == alice.team

    def test_repr_contains_name(self, alice):
        assert "Alice" in repr(alice)

    def test_repr_contains_team(self, alice):
        assert "data-eng" in repr(alice)


# ---------------------------------------------------------------------------
# OwnershipRegistry
# ---------------------------------------------------------------------------

class TestOwnershipRegistry:
    def test_assign_and_get(self, registry, alice):
        registry.assign("pipeline_a", alice)
        owners = registry.get("pipeline_a")
        assert len(owners) == 1
        assert owners[0].name == "Alice"

    def test_get_unknown_pipeline_returns_empty(self, registry):
        assert registry.get("nonexistent") == []

    def test_assign_duplicate_raises(self, registry, alice):
        registry.assign("pipeline_a", alice)
        with pytest.raises(ValueError, match="already assigned"):
            registry.assign("pipeline_a", Owner(name="Alice"))

    def test_multiple_owners(self, registry, alice, bob):
        registry.assign("pipeline_a", alice)
        registry.assign("pipeline_a", bob)
        assert len(registry.get("pipeline_a")) == 2

    def test_unassign_removes_owner(self, registry, alice, bob):
        registry.assign("pipeline_a", alice)
        registry.assign("pipeline_a", bob)
        registry.unassign("pipeline_a", "Alice")
        names = [o.name for o in registry.get("pipeline_a")]
        assert "Alice" not in names
        assert "Bob" in names

    def test_by_team_filters_correctly(self, registry, alice, bob):
        registry.assign("pipeline_a", alice)
        registry.assign("pipeline_b", Owner(name="Charlie", team="ops"))
        result = registry.by_team("data-eng")
        assert "pipeline_a" in result
        assert "pipeline_b" not in result

    def test_all_pipelines_excludes_empty(self, registry, alice):
        registry.assign("pipeline_a", alice)
        registry.assign("pipeline_b", Owner(name="Dave"))
        registry.unassign("pipeline_b", "Dave")
        assert "pipeline_a" in registry.all_pipelines()
        assert "pipeline_b" not in registry.all_pipelines()

    def test_to_dicts_structure(self, registry, alice):
        registry.assign("pipeline_a", alice)
        records = registry.to_dicts()
        assert len(records) == 1
        assert records[0]["pipeline"] == "pipeline_a"
        assert records[0]["name"] == "Alice"


# ---------------------------------------------------------------------------
# OwnershipExporter
# ---------------------------------------------------------------------------

class TestOwnershipExporter:
    def test_to_json_is_valid(self, registry, alice):
        registry.assign("pipeline_a", alice)
        exporter = OwnershipExporter(registry)
        parsed = json.loads(exporter.to_json())
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "Alice"

    def test_to_json_filter_by_pipeline(self, registry, alice, bob):
        registry.assign("pipeline_a", alice)
        registry.assign("pipeline_b", bob)
        exporter = OwnershipExporter(registry)
        parsed = json.loads(exporter.to_json(pipeline="pipeline_a"))
        assert all(r["pipeline"] == "pipeline_a" for r in parsed)

    def test_to_csv_contains_header(self, registry, alice):
        registry.assign("pipeline_a", alice)
        exporter = OwnershipExporter(registry)
        csv_output = exporter.to_csv()
        assert "pipeline" in csv_output
        assert "name" in csv_output

    def test_to_csv_empty_registry_returns_empty_string(self, registry):
        exporter = OwnershipExporter(registry)
        assert exporter.to_csv() == ""

    def test_to_dicts_filter_by_pipeline(self, registry, alice, bob):
        registry.assign("pipeline_a", alice)
        registry.assign("pipeline_b", bob)
        exporter = OwnershipExporter(registry)
        records = exporter.to_dicts(pipeline="pipeline_b")
        assert len(records) == 1
        assert records[0]["name"] == "Bob"
