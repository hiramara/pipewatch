"""Retry policy and execution tracking for pipeline checks."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class RetryPolicy:
    """Defines how retries should be attempted for a failing check."""

    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    max_delay_seconds: float = 30.0

    def delay_for(self, attempt: int) -> float:
        """Return the delay in seconds before the given attempt (1-indexed)."""
        if attempt <= 1:
            return 0.0
        raw = self.delay_seconds * (self.backoff_factor ** (attempt - 2))
        return min(raw, self.max_delay_seconds)

    def to_dict(self) -> dict:
        return {
            "max_attempts": self.max_attempts,
            "delay_seconds": self.delay_seconds,
            "backoff_factor": self.backoff_factor,
            "max_delay_seconds": self.max_delay_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RetryPolicy":
        return cls(
            max_attempts=data.get("max_attempts", 3),
            delay_seconds=data.get("delay_seconds", 1.0),
            backoff_factor=data.get("backoff_factor", 2.0),
            max_delay_seconds=data.get("max_delay_seconds", 30.0),
        )


@dataclass
class RetryResult:
    """Outcome of a retried execution."""

    success: bool
    attempts: int
    last_exception: Optional[Exception] = field(default=None, repr=False)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "attempts": self.attempts,
            "error": str(self.last_exception) if self.last_exception else None,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
        }


class RetryExecutor:
    """Executes a callable with retry logic defined by a RetryPolicy."""

    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self._policy = policy or RetryPolicy()

    @property
    def policy(self) -> RetryPolicy:
        return self._policy

    def run(self, fn: Callable[[], bool], sleep_fn: Callable[[float], None] = time.sleep) -> RetryResult:
        """Run *fn* up to policy.max_attempts times, returning a RetryResult."""
        start = time.monotonic()
        last_exc: Optional[Exception] = None

        for attempt in range(1, self._policy.max_attempts + 1):
            delay = self._policy.delay_for(attempt)
            if delay > 0:
                sleep_fn(delay)
            try:
                result = fn()
                if result:
                    return RetryResult(
                        success=True,
                        attempts=attempt,
                        elapsed_seconds=time.monotonic() - start,
                    )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc

        return RetryResult(
            success=False,
            attempts=self._policy.max_attempts,
            last_exception=last_exc,
            elapsed_seconds=time.monotonic() - start,
        )
