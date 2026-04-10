"""Tests for snapshot.py and snapshot_manager.py."""

import pytest

from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.check import Check
from pipewatch.core.monitor import Monitor
from pipewatch.core.snapshot import PipelineSnapshot, Snapshot
from pipewatch.core.snapshot_manager import SnapshotManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def healthy_pipeline():
    p = Pipeline("p1", "Healthy Pipeline")
    p.update_status(PipelineStatus.HEALTHY)
    return p


@pytest.fixture
def failing_pipeline():
    p = Pipeline("p2", "Failing Pipeline")
    p.update_status(PipelineStatus.FAILING)
    return p


@pytest.fixture
def monitor(healthy_pipeline, failing_pipeline):
    m = Monitor()
    m.register_pipeline(healthy_pipeline)
    m.register_pipeline(failing_pipeline)
    return m


@pytest.fixture
def manager(monitor):
    return SnapshotManager(monitor)


# ---------------------------------------------------------------------------
# PipelineSnapshot tests
# ---------------------------------------------------------------------------

class TestPipelineSnapshot:
    def test_to_dict_contains_required_keys(self):
        ps = PipelineSnapshot("p1", "My Pipeline", PipelineStatus.HEALTHY, 1.0)
        d = ps.to_dict()
        assert {"pipeline_id", "name", "status", "health_score", "captured_at", "metadata"} <= d.keys()

    def test_from_dict_roundtrip(self):
        ps = PipelineSnapshot("p1", "My Pipeline", PipelineStatus.FAILING, 0.5)
        restored = PipelineSnapshot.from_dict(ps.to_dict())
        assert restored.pipeline_id == ps.pipeline_id
        assert restored.status == ps.status
        assert restored.health_score == ps.health_score


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------

class TestSnapshot:
    def test_add_and_get(self):
        snap = Snapshot()
        ps = PipelineSnapshot("p1", "Pipeline", PipelineStatus.HEALTHY, 1.0)
        snap.add(ps)
        assert snap.get("p1") is ps

    def test_get_missing_returns_none(self):
        snap = Snapshot()
        assert snap.get("nonexistent") is None

    def test_diff_detects_status_change(self):
        snap_old = Snapshot()
        snap_old.add(PipelineSnapshot("p1", "P", PipelineStatus.HEALTHY, 1.0))

        snap_new = Snapshot()
        snap_new.add(PipelineSnapshot("p1", "P", PipelineStatus.FAILING, 0.0))

        changes = snap_new.diff(snap_old)
        assert len(changes) == 1
        assert changes[0]["pipeline_id"] == "p1"
        assert changes[0]["previous_status"] == PipelineStatus.HEALTHY.value
        assert changes[0]["current_status"] == PipelineStatus.FAILING.value

    def test_diff_no_change_returns_empty(self):
        snap_a = Snapshot()
        snap_a.add(PipelineSnapshot("p1", "P", PipelineStatus.HEALTHY, 1.0))
        snap_b = Snapshot()
        snap_b.add(PipelineSnapshot("p1", "P", PipelineStatus.HEALTHY, 1.0))
        assert snap_a.diff(snap_b) == []


# ---------------------------------------------------------------------------
# SnapshotManager tests
# ---------------------------------------------------------------------------

class TestSnapshotManager:
    def test_capture_returns_snapshot(self, manager):
        snap = manager.capture()
        assert isinstance(snap, Snapshot)

    def test_capture_increments_history(self, manager):
        manager.capture()
        manager.capture()
        assert manager.history_size == 2

    def test_latest_after_capture(self, manager):
        snap = manager.capture()
        assert manager.latest() is snap

    def test_previous_returns_second_to_last(self, manager):
        first = manager.capture()
        manager.capture()
        assert manager.previous() is first

    def test_last_diff_empty_with_one_snapshot(self, manager):
        manager.capture()
        assert manager.last_diff() == []

    def test_all_snapshots_returns_list(self, manager):
        manager.capture()
        manager.capture()
        assert len(manager.all_snapshots()) == 2
