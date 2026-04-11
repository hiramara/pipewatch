"""Manages circuit breakers across all registered pipelines."""
from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.core.circuit_breaker import CircuitBreaker, CircuitState


class CircuitBreakerManager:
    """Registry and coordinator for per-pipeline circuit breakers."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._breakers: Dict[str, CircuitBreaker] = {}

    def _get_or_create(self, pipeline_id: str) -> CircuitBreaker:
        if pipeline_id not in self._breakers:
            self._breakers[pipeline_id] = CircuitBreaker(
                pipeline_id=pipeline_id,
                failure_threshold=self._failure_threshold,
                recovery_timeout=self._recovery_timeout,
            )
        return self._breakers[pipeline_id]

    def record_failure(self, pipeline_id: str) -> CircuitBreaker:
        breaker = self._get_or_create(pipeline_id)
        breaker.record_failure()
        return breaker

    def record_success(self, pipeline_id: str) -> CircuitBreaker:
        breaker = self._get_or_create(pipeline_id)
        breaker.record_success()
        return breaker

    def is_open(self, pipeline_id: str) -> bool:
        if pipeline_id not in self._breakers:
            return False
        return self._breakers[pipeline_id].is_open()

    def reset(self, pipeline_id: str) -> None:
        if pipeline_id in self._breakers:
            self._breakers[pipeline_id].reset()

    def open_circuits(self) -> List[CircuitBreaker]:
        return [b for b in self._breakers.values() if b.state == CircuitState.OPEN]

    def get(self, pipeline_id: str) -> Optional[CircuitBreaker]:
        return self._breakers.get(pipeline_id)

    def summary(self) -> List[dict]:
        return [b.to_dict() for b in self._breakers.values()]
