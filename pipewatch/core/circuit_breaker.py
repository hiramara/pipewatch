"""Circuit breaker pattern for pipeline checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "closed"      # normal operation
    OPEN = "open"          # blocking calls after too many failures
    HALF_OPEN = "half_open"  # testing recovery


@dataclass
class CircuitBreaker:
    """Tracks consecutive failures for a pipeline and trips open after a threshold."""

    pipeline_id: str
    failure_threshold: int = 3
    recovery_timeout: int = 60  # seconds before moving to HALF_OPEN
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _failure_count: int = field(default=0, init=False, repr=False)
    _opened_at: Optional[datetime] = field(default=None, init=False, repr=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            elapsed = (datetime.utcnow() - self._opened_at).total_seconds()
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold and self._state == CircuitState.CLOSED:
            self._state = CircuitState.OPEN
            self._opened_at = datetime.utcnow()

    def record_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._opened_at = None
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = None

    def to_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "opened_at": self._opened_at.isoformat() if self._opened_at else None,
        }
