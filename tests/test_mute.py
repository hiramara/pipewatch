"""Tests for MuteRule and MuteManager."""

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.core.mute import MuteRule
from pipewatch.core.mute_manager import MuteManager


UTC = timezone.utc


# ---------------------------------------------------------------------------
# MuteRule
# ---------------------------------------------------------------------------

class TestMuteRule:
    def test_no_expiry_always_active(self):
        rule = MuteRule(pipeline_name="sales", reason="planned maintenance")
        assert rule.is_active() is True

    def test_future_expiry_is_active(self):
        rule = MuteRule(
            pipeline_name="sales",
            reason="",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert rule.is_active() is True

    def test_past_expiry_is_inactive(self):
        rule = MuteRule(
            pipeline_name="sales",
            reason="",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        assert rule.is_active() is False

    def test_to_dict_contains_keys(self):
        rule = MuteRule(pipeline_name="p1", reason="test")
        d = rule.to_dict()
        assert d["pipeline_name"] == "p1"
        assert d["reason"] == "test"
        assert d["expires_at"] is None
        assert d["active"] is True

    def test_repr_contains_pipeline_name(self):
        rule = MuteRule(pipeline_name="etl", reason="r")
        assert "etl" in repr(rule)


# ---------------------------------------------------------------------------
# MuteManager
# ---------------------------------------------------------------------------

@pytest.fixture
def manager() -> MuteManager:
    return MuteManager()


class TestMuteManager:
    def test_mute_creates_rule(self, manager):
        manager.mute("sales", "planned")
        assert manager.is_muted("sales") is True

    def test_unmuted_pipeline_not_muted(self, manager):
        assert manager.is_muted("unknown") is False

    def test_unmute_removes_rule(self, manager):
        manager.mute("sales", "x")
        removed = manager.unmute("sales")
        assert removed is True
        assert manager.is_muted("sales") is False

    def test_unmute_nonexistent_returns_false(self, manager):
        assert manager.unmute("ghost") is False

    def test_active_rules_excludes_expired(self, manager):
        manager.mute("a", "ok")
        manager.mute("b", "exp", expires_at=datetime.now(UTC) - timedelta(hours=1))
        active = manager.active_rules()
        names = [r.pipeline_name for r in active]
        assert "a" in names
        assert "b" not in names

    def test_purge_expired_removes_stale(self, manager):
        manager.mute("a", "ok")
        manager.mute("b", "exp", expires_at=datetime.now(UTC) - timedelta(hours=1))
        removed = manager.purge_expired()
        assert removed == 1
        assert len(manager) == 1

    def test_len(self, manager):
        manager.mute("x", "r")
        manager.mute("y", "r")
        assert len(manager) == 2
