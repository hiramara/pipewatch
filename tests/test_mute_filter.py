"""Tests for MuteFilter."""

from unittest.mock import MagicMock

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.mute_filter import MuteFilter
from pipewatch.core.mute_manager import MuteManager
from pipewatch.core.notifier import Notifier


def _make_alert(pipeline: str, level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        pipeline_name=pipeline,
        message=f"{pipeline} alert",
        level=level,
    )


@pytest.fixture
def manager() -> MuteManager:
    return MuteManager()


@pytest.fixture
def mock_notifier() -> MagicMock:
    return MagicMock(spec=Notifier)


@pytest.fixture
def mute_filter(mock_notifier, manager) -> MuteFilter:
    return MuteFilter(notifier=mock_notifier, mute_manager=manager)


class TestMuteFilter:
    def test_non_muted_alert_is_forwarded(self, mute_filter, mock_notifier):
        alert = _make_alert("sales")
        mute_filter.send([alert])
        mock_notifier.send.assert_called_once()
        forwarded = mock_notifier.send.call_args[0][0]
        assert alert in forwarded

    def test_muted_alert_is_suppressed(self, mute_filter, mock_notifier, manager):
        manager.mute("sales", "maintenance")
        alert = _make_alert("sales")
        mute_filter.send([alert])
        mock_notifier.send.assert_not_called()
        assert alert in mute_filter.suppressed

    def test_mixed_alerts_only_forwards_unmuted(self, mute_filter, mock_notifier, manager):
        manager.mute("muted_pipe", "reason")
        a1 = _make_alert("ok_pipe")
        a2 = _make_alert("muted_pipe")
        mute_filter.send([a1, a2])
        forwarded = mock_notifier.send.call_args[0][0]
        assert a1 in forwarded
        assert a2 not in forwarded

    def test_suppressed_accumulates(self, mute_filter, manager):
        manager.mute("p", "r")
        mute_filter.send([_make_alert("p")])
        mute_filter.send([_make_alert("p")])
        assert len(mute_filter.suppressed) == 2

    def test_clear_suppressed(self, mute_filter, manager):
        manager.mute("p", "r")
        mute_filter.send([_make_alert("p")])
        mute_filter.clear_suppressed()
        assert mute_filter.suppressed == []

    def test_no_alerts_does_not_call_notifier(self, mute_filter, mock_notifier):
        mute_filter.send([])
        mock_notifier.send.assert_not_called()
