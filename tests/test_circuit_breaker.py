"""Tests for CircuitBreaker."""
from datetime import datetime, timedelta

import pytest

from pipewatch.core.circuit_breaker import CircuitBreaker, CircuitState


@pytest.fixture
def breaker():
    return CircuitBreaker(pipeline_id="pipe_a", failure_threshold=3, recovery_timeout=60)


class TestCircuitBreaker:
    def test_initial_state_is_closed(self, breaker):
        assert breaker.state == CircuitState.CLOSED

    def test_failures_below_threshold_stay_closed(self, breaker):
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

    def test_trips_open_at_threshold(self, breaker):
        for _ in range(3):
            breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    def test_is_open_returns_true_when_open(self, breaker):
        for _ in range(3):
            breaker.record_failure()
        assert breaker.is_open() is True

    def test_is_open_returns_false_when_closed(self, breaker):
        assert breaker.is_open() is False

    def test_success_resets_closed_circuit(self, breaker):
        breaker.record_failure()
        breaker.record_success()
        assert breaker._failure_count == 0

    def test_half_open_after_recovery_timeout(self, breaker):
        for _ in range(3):
            breaker.record_failure()
        # Simulate timeout by backdating opened_at
        breaker._opened_at = datetime.utcnow() - timedelta(seconds=61)
        assert breaker.state == CircuitState.HALF_OPEN

    def test_success_in_half_open_closes_circuit(self, breaker):
        for _ in range(3):
            breaker.record_failure()
        breaker._opened_at = datetime.utcnow() - timedelta(seconds=61)
        _ = breaker.state  # trigger transition to HALF_OPEN
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0

    def test_reset_clears_all_state(self, breaker):
        for _ in range(3):
            breaker.record_failure()
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0

    def test_to_dict_keys(self, breaker):
        d = breaker.to_dict()
        assert "pipeline_id" in d
        assert "state" in d
        assert "failure_count" in d
        assert d["opened_at"] is None
