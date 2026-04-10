"""Tests for pipewatch.core.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.notifier import LogChannel, Notifier, StdoutChannel


@pytest.fixture()
def warning_alert() -> Alert:
    return Alert(pipeline_id="pipe-1", message="Lag exceeded threshold", level=AlertLevel.WARNING)


@pytest.fixture()
def critical_alert() -> Alert:
    return Alert(pipeline_id="pipe-2", message="Pipeline down", level=AlertLevel.CRITICAL)


@pytest.fixture()
def info_alert() -> Alert:
    return Alert(pipeline_id="pipe-3", message="Pipeline started", level=AlertLevel.INFO)


@pytest.fixture()
def notifier() -> Notifier:
    n = Notifier()
    n.add_channel(StdoutChannel())
    return n


class TestNotifier:
    def test_initialization_empty(self) -> None:
        n = Notifier()
        assert n.channels == []
        assert n.min_level == AlertLevel.WARNING

    def test_add_channel(self, notifier: Notifier) -> None:
        assert len(notifier.channels) == 1
        notifier.add_channel(LogChannel())
        assert len(notifier.channels) == 2

    def test_remove_channel(self, notifier: Notifier) -> None:
        notifier.remove_channel("stdout")
        assert len(notifier.channels) == 0

    def test_remove_nonexistent_channel_is_noop(self, notifier: Notifier) -> None:
        notifier.remove_channel("email")
        assert len(notifier.channels) == 1

    def test_dispatch_returns_success_count(self, notifier: Notifier, warning_alert: Alert) -> None:
        result = notifier.dispatch(warning_alert)
        assert result == 1

    def test_dispatch_below_min_level_skipped(self, notifier: Notifier, info_alert: Alert) -> None:
        notifier.min_level = AlertLevel.WARNING
        result = notifier.dispatch(info_alert)
        assert result == 0

    def test_dispatch_critical_always_sent(self, notifier: Notifier, critical_alert: Alert) -> None:
        notifier.min_level = AlertLevel.WARNING
        result = notifier.dispatch(critical_alert)
        assert result == 1

    def test_dispatch_many(self, notifier: Notifier, warning_alert: Alert, critical_alert: Alert) -> None:
        result = notifier.dispatch_many([warning_alert, critical_alert])
        assert result == 2

    def test_channel_exception_is_handled(self, warning_alert: Alert) -> None:
        bad_channel = MagicMock()
        bad_channel.name = "bad"
        bad_channel.send.side_effect = RuntimeError("network error")
        n = Notifier(channels=[bad_channel])
        result = n.dispatch(warning_alert)
        assert result == 0


class TestStdoutChannel:
    def test_name(self) -> None:
        assert StdoutChannel().name == "stdout"

    def test_send_returns_true(self, warning_alert: Alert, capsys: pytest.CaptureFixture) -> None:
        ch = StdoutChannel()
        assert ch.send(warning_alert) is True
        captured = capsys.readouterr()
        assert "pipe-1" in captured.out


class TestLogChannel:
    def test_name(self) -> None:
        assert LogChannel().name == "log"

    def test_send_returns_true(self, critical_alert: Alert) -> None:
        ch = LogChannel()
        with patch("pipewatch.core.notifier.logger") as mock_log:
            result = ch.send(critical_alert)
        assert result is True
        mock_log.log.assert_called_once()
