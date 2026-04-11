"""Tests for CircuitBreakerManager."""
import pytest

from pipewatch.core.circuit_breaker import CircuitState
from pipewatch.core.circuit_breaker_manager import CircuitBreakerManager


@pytest.fixture
def manager():
    return CircuitBreakerManager(failure_threshold=3, recovery_timeout=60)


class TestCircuitBreakerManager:
    def test_is_open_returns_false_for_unknown_pipeline(self, manager):
        assert manager.is_open("unknown") is False

    def test_record_failure_creates_breaker(self, manager):
        manager.record_failure("pipe_x")
        assert manager.get("pipe_x") is not None

    def test_trips_after_threshold_failures(self, manager):
        for _ in range(3):
            manager.record_failure("pipe_x")
        assert manager.is_open("pipe_x") is True

    def test_record_success_closes_circuit(self, manager):
        manager.record_failure("pipe_x")
        manager.record_success("pipe_x")
        assert manager.is_open("pipe_x") is False

    def test_open_circuits_lists_tripped(self, manager):
        for _ in range(3):
            manager.record_failure("pipe_a")
        manager.record_failure("pipe_b")  # not yet tripped
        open_ids = [b.pipeline_id for b in manager.open_circuits()]
        assert "pipe_a" in open_ids
        assert "pipe_b" not in open_ids

    def test_reset_closes_open_circuit(self, manager):
        for _ in range(3):
            manager.record_failure("pipe_a")
        manager.reset("pipe_a")
        assert manager.is_open("pipe_a") is False

    def test_reset_nonexistent_is_noop(self, manager):
        manager.reset("nonexistent")  # should not raise

    def test_summary_returns_list_of_dicts(self, manager):
        manager.record_failure("pipe_a")
        manager.record_failure("pipe_b")
        result = manager.summary()
        assert isinstance(result, list)
        assert len(result) == 2
        assert all("pipeline_id" in d for d in result)

    def test_get_returns_none_for_missing(self, manager):
        assert manager.get("missing") is None

    def test_multiple_pipelines_independent(self, manager):
        for _ in range(3):
            manager.record_failure("pipe_a")
        assert manager.is_open("pipe_a") is True
        assert manager.is_open("pipe_b") is False
