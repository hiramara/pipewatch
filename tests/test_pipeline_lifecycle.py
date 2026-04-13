"""Tests for PipelineLifecycle and LifecycleEvent."""

import pytest
from pipewatch.core.pipeline import PipelineStatus
from pipewatch.core.pipeline_lifecycle import LifecycleEvent, PipelineLifecycle


@pytest.fixture
def lc():
    return PipelineLifecycle("sales_etl")


class TestLifecycleEvent:
    def test_to_dict_keys(self):
        event = LifecycleEvent(
            pipeline_name="p",
            from_status=None,
            to_status=PipelineStatus.HEALTHY,
        )
        keys = set(event.to_dict())
        assert keys == {"pipeline_name", "from_status", "to_status", "timestamp", "note"}

    def test_to_dict_from_none(self):
        event = LifecycleEvent("p", None, PipelineStatus.HEALTHY)
        assert event.to_dict()["from_status"] is None

    def test_repr_contains_name_and_statuses(self):
        event = LifecycleEvent("p", PipelineStatus.HEALTHY, PipelineStatus.FAILING)
        r = repr(event)
        assert "p" in r
        assert "healthy" in r
        assert "failing" in r


class TestPipelineLifecycle:
    def test_initial_state(self, lc):
        assert lc.current_status is None
        assert lc.transition_count() == 0

    def test_first_record_creates_event(self, lc):
        event = lc.record(PipelineStatus.HEALTHY)
        assert event is not None
        assert event.from_status is None
        assert event.to_status == PipelineStatus.HEALTHY

    def test_same_status_returns_none(self, lc):
        lc.record(PipelineStatus.HEALTHY)
        event = lc.record(PipelineStatus.HEALTHY)
        assert event is None
        assert lc.transition_count() == 1

    def test_status_change_creates_event(self, lc):
        lc.record(PipelineStatus.HEALTHY)
        event = lc.record(PipelineStatus.FAILING)
        assert event is not None
        assert event.from_status == PipelineStatus.HEALTHY
        assert event.to_status == PipelineStatus.FAILING

    def test_events_list_is_copy(self, lc):
        lc.record(PipelineStatus.HEALTHY)
        events = lc.events
        events.clear()
        assert lc.transition_count() == 1

    def test_last_transition_returns_most_recent(self, lc):
        lc.record(PipelineStatus.HEALTHY)
        lc.record(PipelineStatus.FAILING)
        assert lc.last_transition().to_status == PipelineStatus.FAILING

    def test_note_stored_in_event(self, lc):
        event = lc.record(PipelineStatus.HEALTHY, note="initial run")
        assert event.note == "initial run"
