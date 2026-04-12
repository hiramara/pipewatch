"""Tests for SuppressionWindow, SuppressionManager, and SuppressionFilter."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.suppression import SuppressionManager, SuppressionWindow
from pipewatch.core.suppression_filter import SuppressionFilter


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _window(
    pipeline: str = "pipe_a",
    offset_start: int = -60,
    offset_end: int = 60,
    reason: str = "maintenance",
) -> SuppressionWindow:
    now = _now()
    return SuppressionWindow(
        pipeline_name=pipeline,
        start=now + timedelta(seconds=offset_start),
        end=now + timedelta(seconds=offset_end),
        reason=reason,
    )


@pytest.fixture
def manager() -> SuppressionManager:
    return SuppressionManager()


class TestSuppressionWindow:
    def test_active_within_window(self):
        w = _window()
        assert w.is_active() is True

    def test_inactive_before_window(self):
        now = _now()
        w = SuppressionWindow("p", now + timedelta(hours=1), now + timedelta(hours=2))
        assert w.is_active() is False

    def test_inactive_after_window(self):
        now = _now()
        w = SuppressionWindow("p", now - timedelta(hours=2), now - timedelta(hours=1))
        assert w.is_active() is False

    def test_to_dict_keys(self):
        w = _window()
        d = w.to_dict()
        assert {"pipeline_name", "start", "end", "reason", "active"} <= d.keys()

    def test_repr_contains_status(self):
        w = _window()
        assert "active" in repr(w)


class TestSuppressionManager:
    def test_is_suppressed_with_active_window(self, manager):
        manager.add(_window("pipe_a"))
        assert manager.is_suppressed("pipe_a") is True

    def test_is_not_suppressed_without_window(self, manager):
        assert manager.is_suppressed("pipe_z") is False

    def test_is_not_suppressed_after_expiry(self, manager):
        now = _now()
        w = SuppressionWindow("pipe_b", now - timedelta(hours=2), now - timedelta(hours=1))
        manager.add(w)
        assert manager.is_suppressed("pipe_b") is False

    def test_remove_window(self, manager):
        w = _window("pipe_c")
        manager.add(w)
        removed = manager.remove("pipe_c", w.start)
        assert removed is True
        assert manager.is_suppressed("pipe_c") is False

    def test_active_windows_returns_only_active(self, manager):
        now = _now()
        active = _window("pipe_d")
        expired = SuppressionWindow("pipe_e", now - timedelta(hours=2), now - timedelta(hours=1))
        manager.add(active)
        manager.add(expired)
        assert active in manager.active_windows()
        assert expired not in manager.active_windows()

    def test_purge_expired_removes_old_windows(self, manager):
        now = _now()
        expired = SuppressionWindow("pipe_f", now - timedelta(hours=2), now - timedelta(hours=1))
        manager.add(expired)
        count = manager.purge_expired()
        assert count == 1
        assert manager.is_suppressed("pipe_f") is False


class TestSuppressionFilter:
    def _make_alert(self, pipeline: str = "pipe_a") -> Alert:
        return Alert(pipeline_name=pipeline, message="test", level=AlertLevel.WARNING)

    def test_passes_alert_when_not_suppressed(self, manager):
        inner = MagicMock()
        inner.name = "mock"
        sf = SuppressionFilter(inner, manager)
        alert = self._make_alert("pipe_x")
        sf.send(alert)
        inner.send.assert_called_once_with(alert)

    def test_suppresses_alert_when_window_active(self, manager):
        inner = MagicMock()
        inner.name = "mock"
        manager.add(_window("pipe_a"))
        sf = SuppressionFilter(inner, manager)
        alert = self._make_alert("pipe_a")
        sf.send(alert)
        inner.send.assert_not_called()
        assert alert in sf.suppressed

    def test_clear_suppressed(self, manager):
        inner = MagicMock()
        inner.name = "mock"
        manager.add(_window("pipe_a"))
        sf = SuppressionFilter(inner, manager)
        sf.send(self._make_alert("pipe_a"))
        sf.clear_suppressed()
        assert sf.suppressed == []

    def test_name_wraps_inner(self, manager):
        inner = MagicMock()
        inner.name = "LogChannel"
        sf = SuppressionFilter(inner, manager)
        assert "LogChannel" in sf.name
