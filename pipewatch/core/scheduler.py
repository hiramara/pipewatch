"""Scheduler for periodically evaluating monitors and dispatching alerts."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from pipewatch.core.monitor import Monitor
from pipewatch.core.notifier import Notifier

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the Scheduler."""

    interval_seconds: float = 60.0
    run_immediately: bool = True
    max_iterations: Optional[int] = None  # None means run indefinitely


class Scheduler:
    """Periodically evaluates a Monitor and dispatches resulting alerts."""

    def __init__(
        self,
        monitor: Monitor,
        notifier: Notifier,
        config: Optional[SchedulerConfig] = None,
        on_cycle: Optional[Callable[[int], None]] = None,
    ) -> None:
        self.monitor = monitor
        self.notifier = notifier
        self.config = config or SchedulerConfig()
        self.on_cycle = on_cycle
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._iteration_count: int = 0

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def iteration_count(self) -> int:
        return self._iteration_count

    def _run_cycle(self) -> None:
        """Execute a single evaluation + notification cycle."""
        alerts = self.monitor.evaluate()
        dispatched = self.notifier.dispatch_many(alerts)
        self._iteration_count += 1
        logger.debug(
            "Cycle %d: %d alerts evaluated, %d dispatched.",
            self._iteration_count,
            len(alerts),
            dispatched,
        )
        if self.on_cycle:
            self.on_cycle(self._iteration_count)

    def _loop(self) -> None:
        if self.config.run_immediately:
            self._run_cycle()
        while not self._stop_event.is_set():
            max_iter = self.config.max_iterations
            if max_iter is not None and self._iteration_count >= max_iter:
                break
            self._stop_event.wait(timeout=self.config.interval_seconds)
            if self._stop_event.is_set():
                break
            self._run_cycle()

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self.is_running:
            raise RuntimeError("Scheduler is already running.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="pipewatch-scheduler")
        self._thread.start()
        logger.info("Scheduler started (interval=%.1fs).", self.config.interval_seconds)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the scheduler to stop and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("Scheduler stopped after %d iterations.", self._iteration_count)

    def run_once(self) -> None:
        """Execute a single cycle synchronously (useful for testing/CLI)."""
        self._run_cycle()
