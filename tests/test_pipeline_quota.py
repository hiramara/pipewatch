"""Tests for pipeline quota tracking."""
from __future__ import annotations

import time

import pytest

from pipewatch.core.pipeline_quota import (
    QuotaBreach,
    QuotaEvaluator,
    QuotaRule,
    QuotaUsage,
)
from pipewatch.core.quota_config import QuotaConfig


# ---------------------------------------------------------------------------
# QuotaRule
# ---------------------------------------------------------------------------

class TestQuotaRule:
    def test_to_dict_keys(self):
        rule = QuotaRule(pipeline_name="sales", max_runs=10, max_records=5000)
        d = rule.to_dict()
        assert set(d.keys()) == {"pipeline_name", "max_runs", "max_records", "window_seconds"}

    def test_from_dict_roundtrip(self):
        rule = QuotaRule(pipeline_name="etl", max_runs=3, max_records=100, window_seconds=3600)
        assert QuotaRule.from_dict(rule.to_dict()) == rule

    def test_defaults(self):
        rule = QuotaRule(pipeline_name="x")
        assert rule.max_runs is None
        assert rule.max_records is None
        assert rule.window_seconds == 86400


# ---------------------------------------------------------------------------
# QuotaUsage
# ---------------------------------------------------------------------------

class TestQuotaUsage:
    def test_run_count_within_window(self):
        u = QuotaUsage(pipeline_name="p")
        now = time.time()
        u.record_run(now - 10)
        u.record_run(now - 5)
        assert u.runs_in_window(60) == 2

    def test_run_count_outside_window_excluded(self):
        u = QuotaUsage(pipeline_name="p")
        now = time.time()
        u.record_run(now - 200)   # outside 60-second window
        u.record_run(now - 10)
        assert u.runs_in_window(60) == 1

    def test_records_in_window(self):
        u = QuotaUsage(pipeline_name="p")
        now = time.time()
        u.record_records(100, now - 30)
        u.record_records(200, now - 5)
        assert u.records_in_window(60) == 300

    def test_records_outside_window_excluded(self):
        u = QuotaUsage(pipeline_name="p")
        now = time.time()
        u.record_records(999, now - 3600)
        u.record_records(50, now - 5)
        assert u.records_in_window(60) == 50


# ---------------------------------------------------------------------------
# QuotaEvaluator
# ---------------------------------------------------------------------------

@pytest.fixture
def evaluator():
    return QuotaEvaluator()


class TestQuotaEvaluator:
    def test_no_rule_returns_none(self, evaluator):
        assert evaluator.check("unknown") is None

    def test_no_breach_within_limits(self, evaluator):
        evaluator.add_rule(QuotaRule("pipe", max_runs=5, window_seconds=60))
        for _ in range(3):
            evaluator.record_run("pipe")
        assert evaluator.check("pipe") is None

    def test_run_limit_breach(self, evaluator):
        evaluator.add_rule(QuotaRule("pipe", max_runs=2, window_seconds=60))
        for _ in range(3):
            evaluator.record_run("pipe")
        breach = evaluator.check("pipe")
        assert breach is not None
        assert breach.run_limit_exceeded is True
        assert breach.record_limit_exceeded is False

    def test_record_limit_breach(self, evaluator):
        evaluator.add_rule(QuotaRule("pipe", max_records=100, window_seconds=60))
        evaluator.record_records("pipe", 150)
        breach = evaluator.check("pipe")
        assert breach is not None
        assert breach.record_limit_exceeded is True

    def test_check_all_returns_only_breaches(self, evaluator):
        evaluator.add_rule(QuotaRule("ok", max_runs=10, window_seconds=60))
        evaluator.add_rule(QuotaRule("bad", max_runs=1, window_seconds=60))
        evaluator.record_run("ok")
        evaluator.record_run("bad")
        evaluator.record_run("bad")
        breaches = evaluator.check_all()
        assert len(breaches) == 1
        assert breaches[0].pipeline_name == "bad"

    def test_breach_to_dict_keys(self, evaluator):
        evaluator.add_rule(QuotaRule("p", max_runs=1, window_seconds=60))
        evaluator.record_run("p")
        evaluator.record_run("p")
        breach = evaluator.check("p")
        d = breach.to_dict()
        assert "pipeline_name" in d
        assert "runs_used" in d
        assert "breached_at" in d


# ---------------------------------------------------------------------------
# QuotaConfig
# ---------------------------------------------------------------------------

class TestQuotaConfig:
    def test_add_and_get(self):
        cfg = QuotaConfig()
        rule = QuotaRule("etl", max_runs=5)
        cfg.add(rule)
        assert cfg.get("etl") == rule

    def test_len(self):
        cfg = QuotaConfig()
        cfg.add(QuotaRule("a", max_runs=1))
        cfg.add(QuotaRule("b", max_runs=2))
        assert len(cfg) == 2

    def test_remove(self):
        cfg = QuotaConfig()
        cfg.add(QuotaRule("x", max_runs=3))
        cfg.remove("x")
        assert cfg.get("x") is None

    def test_update_unknown_raises(self):
        cfg = QuotaConfig()
        with pytest.raises(KeyError):
            cfg.update(QuotaRule("ghost", max_runs=1))

    def test_from_dicts_roundtrip(self):
        rules = [
            QuotaRule("a", max_runs=10, window_seconds=3600),
            QuotaRule("b", max_records=500),
        ]
        cfg = QuotaConfig()
        for r in rules:
            cfg.add(r)
        restored = QuotaConfig.from_dicts(cfg.to_dicts())
        assert len(restored) == 2
        assert restored.get("a").max_runs == 10
