"""Tests for pipewatch.core.scheduler."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.monitor import Monitor
from pipewatch.core.notifier import Notifier
from pipewatch.core.scheduler import Scheduler, SchedulerConfig


@pytest.fixture()
def mock_monitor() -> MagicMock:
    m = MagicMock(spec=Monitor)
    m.evaluate.return_value = [
        Alert(pipeline_id="p1", message="test", level=AlertLevel.WARNING)
    ]
    return m


@pytest.fixture()
def mock_notifier() -> MagicMock:
    n = MagicMock(spec=Notifier)
    n.dispatch_many.return_value = 1
    return n


@pytest.fixture()
def scheduler(mock_monitor: MagicMock, mock_notifier: MagicMock) -> Scheduler:
    cfg = SchedulerConfig(interval_seconds=0.05, run_immediately=False, max_iterations=2)
    return Scheduler(monitor=mock_monitor, notifier=mock_notifier, config=cfg)


class TestSchedulerConfig:
    def test_defaults(self) -> None:
        cfg = SchedulerConfig()
        assert cfg.interval_seconds == 60.0
        assert cfg.run_immediately is True
        assert cfg.max_iterations is None


class TestScheduler:
    def test_initialization(self, scheduler: Scheduler) -> None:
        assert scheduler.iteration_count == 0
        assert not scheduler.is_running

    def test_run_once_increments_iteration(self, scheduler: Scheduler) -> None:
        scheduler.run_once()
        assert scheduler.iteration_count == 1

    def test_run_once_calls_monitor_evaluate(self, scheduler: Scheduler, mock_monitor: MagicMock) -> None:
        scheduler.run_once()
        mock_monitor.evaluate.assert_called_once()

    def test_run_once_calls_notifier_dispatch_many(self, scheduler: Scheduler, mock_notifier: MagicMock) -> None:
        scheduler.run_once()
        mock_notifier.dispatch_many.assert_called_once()

    def test_on_cycle_callback_invoked(self, mock_monitor: MagicMock, mock_notifier: MagicMock) -> None:
        callback = MagicMock()
        cfg = SchedulerConfig(run_immediately=False)
        s = Scheduler(monitor=mock_monitor, notifier=mock_notifier, config=cfg, on_cycle=callback)
        s.run_once()
        callback.assert_called_once_with(1)

    def test_start_sets_is_running(self, scheduler: Scheduler) -> None:
        scheduler.start()
        assert scheduler.is_running
        scheduler.stop()

    def test_start_twice_raises(self, scheduler: Scheduler) -> None:
        scheduler.start()
        with pytest.raises(RuntimeError, match="already running"):
            scheduler.start()
        scheduler.stop()

    def test_stop_clears_running(self, scheduler: Scheduler) -> None:
        scheduler.start()
        scheduler.stop(timeout=2.0)
        assert not scheduler.is_running

    def test_max_iterations_respected(self, mock_monitor: MagicMock, mock_notifier: MagicMock) -> None:
        cfg = SchedulerConfig(interval_seconds=0.01, run_immediately=True, max_iterations=2)
        s = Scheduler(monitor=mock_monitor, notifier=mock_notifier, config=cfg)
        s.start()
        time.sleep(0.3)
        s.stop(timeout=2.0)
        assert s.iteration_count <= 3  # run_immediately + up to max_iterations loop ticks
