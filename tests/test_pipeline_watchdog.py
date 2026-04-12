"""Tests for PipelineWatchdog and StalenessRule."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.pipeline_watchdog import (
    PipelineWatchdog,
    StalenessRule,
    StalePipelineResult,
)


def _make_pipeline(name: str, last_updated: datetime) -> Pipeline:
    p = Pipeline(name=name)
    p.last_updated = last_updated
    return p


NOW = datetime(2024, 6, 1, 12, 0, 0)
RECENT = NOW - timedelta(seconds=60)
STALE = NOW - timedelta(seconds=600)


@pytest.fixture
def watchdog():
    return PipelineWatchdog(default_max_silence_seconds=300)


class TestStalenessRule:
    def test_not_stale_within_window(self):
        rule = StalenessRule("pipe", 300)
        assert not rule.is_stale(RECENT, now=NOW)

    def test_stale_outside_window(self):
        rule = StalenessRule("pipe", 300)
        assert rule.is_stale(STALE, now=NOW)

    def test_boundary_is_stale(self):
        rule = StalenessRule("pipe", 300)
        boundary = NOW - timedelta(seconds=301)
        assert rule.is_stale(boundary, now=NOW)

    def test_to_dict_roundtrip(self):
        rule = StalenessRule("my_pipe", 120)
        restored = StalenessRule.from_dict(rule.to_dict())
        assert restored.pipeline_name == rule.pipeline_name
        assert restored.max_silence_seconds == rule.max_silence_seconds


class TestPipelineWatchdog:
    def test_fresh_pipeline_not_stale(self, watchdog):
        p = _make_pipeline("fresh", RECENT)
        results = watchdog.evaluate([p], now=NOW)
        assert len(results) == 1
        assert not results[0].stale

    def test_stale_pipeline_flagged(self, watchdog):
        p = _make_pipeline("old", STALE)
        results = watchdog.evaluate([p], now=NOW)
        assert results[0].stale

    def test_custom_rule_overrides_default(self, watchdog):
        watchdog.add_rule(StalenessRule("custom", 1000))
        p = _make_pipeline("custom", STALE)  # 600s ago, within 1000s rule
        results = watchdog.evaluate([p], now=NOW)
        assert not results[0].stale

    def test_stale_only_filters_fresh(self, watchdog):
        pipelines = [
            _make_pipeline("fresh", RECENT),
            _make_pipeline("stale", STALE),
        ]
        stale = watchdog.stale_only(pipelines, now=NOW)
        assert len(stale) == 1
        assert stale[0].pipeline_name == "stale"

    def test_remove_rule_falls_back_to_default(self, watchdog):
        watchdog.add_rule(StalenessRule("pipe", 1000))
        watchdog.remove_rule("pipe")
        p = _make_pipeline("pipe", STALE)
        results = watchdog.evaluate([p], now=NOW)
        assert results[0].stale  # back to default 300s

    def test_result_to_dict_keys(self, watchdog):
        p = _make_pipeline("p", STALE)
        result = watchdog.evaluate([p], now=NOW)[0]
        d = result.to_dict()
        assert {"pipeline_name", "last_updated", "stale", "silence_seconds"} <= d.keys()
