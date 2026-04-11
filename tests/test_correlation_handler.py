"""Tests for CorrelationHandler."""
from unittest.mock import MagicMock

import pytest

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.correlation import CorrelationEngine
from pipewatch.core.correlation_handler import CorrelationHandler


def _alert(pipeline: str = "pipe_a") -> Alert:
    return Alert(
        pipeline_name=pipeline,
        check_name="row_count",
        level=AlertLevel.WARNING,
        message="test",
    )


@pytest.fixture
def mock_monitor():
    m = MagicMock()
    m.evaluate.return_value = []
    return m


@pytest.fixture
def handler(mock_monitor):
    return CorrelationHandler(mock_monitor)


class TestCorrelationHandler:
    def test_process_no_alerts_returns_empty(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = []
        result = handler.process()
        assert result == []

    def test_process_single_alert_creates_incident(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = [_alert()]
        incidents = handler.process()
        assert len(incidents) == 1

    def test_process_two_alerts_same_pipeline_one_incident(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = [_alert("pipe_a"), _alert("pipe_a")]
        incidents = handler.process()
        assert len(incidents) == 1
        assert len(incidents[0].alerts) == 2

    def test_process_two_pipelines_two_incidents(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = [_alert("pipe_a"), _alert("pipe_b")]
        incidents = handler.process()
        assert len(incidents) == 2

    def test_open_incidents_delegates_to_engine(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = [_alert()]
        handler.process()
        assert len(handler.open_incidents()) == 1

    def test_resolve_pipeline_delegates_to_engine(self, handler, mock_monitor):
        mock_monitor.evaluate.return_value = [_alert("pipe_a")]
        handler.process()
        count = handler.resolve_pipeline("pipe_a")
        assert count == 1
        assert handler.open_incidents() == []

    def test_custom_engine_used(self, mock_monitor):
        engine = CorrelationEngine(window_seconds=60)
        h = CorrelationHandler(mock_monitor, engine=engine)
        assert h.engine is engine

    def test_engine_property_returns_engine(self, handler):
        assert isinstance(handler.engine, CorrelationEngine)
