"""Tests for WatchdogConfig."""

import pytest

from pipewatch.core.watchdog_config import WatchdogConfig
from pipewatch.core.pipeline_watchdog import PipelineWatchdog


@pytest.fixture
def config():
    return WatchdogConfig(default_max_silence_seconds=300)


class TestWatchdogConfig:
    def test_add_and_get(self, config):
        config.add("pipe_a", 120)
        rule = config.get("pipe_a")
        assert rule is not None
        assert rule.max_silence_seconds == 120

    def test_add_duplicate_raises(self, config):
        config.add("pipe_a", 120)
        with pytest.raises(ValueError, match="already exists"):
            config.add("pipe_a", 200)

    def test_update_replaces_rule(self, config):
        config.add("pipe_a", 120)
        config.update("pipe_a", 600)
        assert config.get("pipe_a").max_silence_seconds == 600

    def test_remove_existing(self, config):
        config.add("pipe_a", 120)
        config.remove("pipe_a")
        assert config.get("pipe_a") is None

    def test_remove_nonexistent_raises(self, config):
        with pytest.raises(KeyError):
            config.remove("ghost")

    def test_len(self, config):
        config.add("a", 60)
        config.add("b", 90)
        assert len(config) == 2

    def test_iter(self, config):
        config.add("a", 60)
        config.add("b", 90)
        names = {r.pipeline_name for r in config}
        assert names == {"a", "b"}

    def test_build_watchdog_returns_watchdog(self, config):
        config.add("pipe_a", 120)
        wd = config.build_watchdog()
        assert isinstance(wd, PipelineWatchdog)

    def test_build_watchdog_has_rule(self, config):
        config.add("pipe_a", 120)
        wd = config.build_watchdog()
        # rule should be registered; custom rule overrides default
        assert wd._rules.get("pipe_a") is not None
        assert wd._rules["pipe_a"].max_silence_seconds == 120
