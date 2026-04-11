"""Tests for pipewatch.core.retry."""

import pytest
from unittest.mock import MagicMock

from pipewatch.core.retry import RetryPolicy, RetryResult, RetryExecutor


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------

class TestRetryPolicy:
    def test_defaults(self):
        p = RetryPolicy()
        assert p.max_attempts == 3
        assert p.delay_seconds == 1.0
        assert p.backoff_factor == 2.0
        assert p.max_delay_seconds == 30.0

    def test_delay_for_first_attempt_is_zero(self):
        p = RetryPolicy(delay_seconds=2.0)
        assert p.delay_for(1) == 0.0

    def test_delay_for_second_attempt(self):
        p = RetryPolicy(delay_seconds=2.0, backoff_factor=2.0)
        assert p.delay_for(2) == 2.0

    def test_delay_for_third_attempt_with_backoff(self):
        p = RetryPolicy(delay_seconds=2.0, backoff_factor=2.0)
        assert p.delay_for(3) == 4.0

    def test_delay_capped_at_max(self):
        p = RetryPolicy(delay_seconds=10.0, backoff_factor=10.0, max_delay_seconds=15.0)
        assert p.delay_for(5) == 15.0

    def test_to_dict_keys(self):
        keys = RetryPolicy().to_dict().keys()
        assert {"max_attempts", "delay_seconds", "backoff_factor", "max_delay_seconds"} == set(keys)

    def test_from_dict_roundtrip(self):
        original = RetryPolicy(max_attempts=5, delay_seconds=0.5, backoff_factor=1.5, max_delay_seconds=20.0)
        restored = RetryPolicy.from_dict(original.to_dict())
        assert restored.max_attempts == 5
        assert restored.delay_seconds == 0.5
        assert restored.backoff_factor == 1.5


# ---------------------------------------------------------------------------
# RetryExecutor
# ---------------------------------------------------------------------------

@pytest.fixture
def no_delay_policy():
    return RetryPolicy(max_attempts=3, delay_seconds=0.0)


@pytest.fixture
def executor(no_delay_policy):
    return RetryExecutor(policy=no_delay_policy)


class TestRetryExecutor:
    def test_success_on_first_attempt(self, executor):
        result = executor.run(lambda: True, sleep_fn=lambda _: None)
        assert result.success is True
        assert result.attempts == 1

    def test_success_on_third_attempt(self, executor):
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            return call_count["n"] >= 3

        result = executor.run(flaky, sleep_fn=lambda _: None)
        assert result.success is True
        assert result.attempts == 3

    def test_all_attempts_fail(self, executor):
        result = executor.run(lambda: False, sleep_fn=lambda _: None)
        assert result.success is False
        assert result.attempts == 3

    def test_exception_captured(self, executor):
        def boom():
            raise ValueError("bad")

        result = executor.run(boom, sleep_fn=lambda _: None)
        assert result.success is False
        assert isinstance(result.last_exception, ValueError)

    def test_sleep_called_between_attempts(self):
        policy = RetryPolicy(max_attempts=3, delay_seconds=1.0, backoff_factor=1.0)
        ex = RetryExecutor(policy=policy)
        sleep_mock = MagicMock()
        ex.run(lambda: False, sleep_fn=sleep_mock)
        assert sleep_mock.call_count == 2  # attempts 2 and 3

    def test_to_dict_on_result(self, executor):
        result = executor.run(lambda: True, sleep_fn=lambda _: None)
        d = result.to_dict()
        assert d["success"] is True
        assert d["attempts"] == 1
        assert d["error"] is None

    def test_default_policy_used_when_none_given(self):
        ex = RetryExecutor()
        assert ex.policy.max_attempts == 3
