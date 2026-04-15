"""Tests for pipeline compliance rules, config, and evaluator."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.core.pipeline_compliance import ComplianceRule, ComplianceViolation
from pipewatch.core.compliance_config import ComplianceConfig
from pipewatch.core.compliance_evaluator import ComplianceEvaluator, ComplianceReport


def _make_pipeline(name="pipe", metadata=None, tags=None, owner=None):
    p = MagicMock()
    p.name = name
    p.metadata = metadata or {}
    p.tags = tags or []
    p.owner = owner
    return p


# ---------------------------------------------------------------------------
# ComplianceRule
# ---------------------------------------------------------------------------

class TestComplianceRule:
    def test_no_requirements_passes(self):
        rule = ComplianceRule(name="empty", description="no reqs")
        pipeline = _make_pipeline()
        assert rule.evaluate(pipeline) is None

    def test_missing_metadata_key_creates_violation(self):
        rule = ComplianceRule(
            name="meta", description="", required_metadata_keys=["team"]
        )
        pipeline = _make_pipeline(metadata={})
        v = rule.evaluate(pipeline)
        assert v is not None
        assert "team" in v.reasons[0]

    def test_present_metadata_key_passes(self):
        rule = ComplianceRule(
            name="meta", description="", required_metadata_keys=["team"]
        )
        pipeline = _make_pipeline(metadata={"team": "data-eng"})
        assert rule.evaluate(pipeline) is None

    def test_missing_tag_creates_violation(self):
        rule = ComplianceRule(name="tag", description="", required_tags=["production"])
        pipeline = _make_pipeline(tags=["staging"])
        v = rule.evaluate(pipeline)
        assert v is not None
        assert any("production" in r for r in v.reasons)

    def test_tag_check_is_case_insensitive(self):
        rule = ComplianceRule(name="tag", description="", required_tags=["production"])
        pipeline = _make_pipeline(tags=["Production"])
        assert rule.evaluate(pipeline) is None

    def test_require_owner_no_owner_creates_violation(self):
        rule = ComplianceRule(name="owner", description="", require_owner=True)
        pipeline = _make_pipeline(owner=None)
        v = rule.evaluate(pipeline)
        assert v is not None
        assert any("owner" in r.lower() for r in v.reasons)

    def test_require_owner_with_owner_passes(self):
        rule = ComplianceRule(name="owner", description="", require_owner=True)
        pipeline = _make_pipeline(owner="alice")
        assert rule.evaluate(pipeline) is None

    def test_to_dict_contains_expected_keys(self):
        rule = ComplianceRule(name="r", description="d", require_owner=True)
        d = rule.to_dict()
        assert set(d.keys()) == {
            "name", "description", "required_metadata_keys",
            "required_tags", "require_owner",
        }


class TestComplianceViolation:
    def test_to_dict_keys(self):
        rule = ComplianceRule(
            name="r", description="", required_metadata_keys=["env"]
        )
        v = rule.evaluate(_make_pipeline())
        d = v.to_dict()
        assert "rule_name" in d and "pipeline_name" in d and "reasons" in d

    def test_repr_contains_rule_and_pipeline(self):
        v = ComplianceViolation(rule_name="r", pipeline_name="p", reasons=["x"])
        assert "r" in repr(v) and "p" in repr(v)


# ---------------------------------------------------------------------------
# ComplianceConfig
# ---------------------------------------------------------------------------

class TestComplianceConfig:
    def test_add_and_get(self):
        cfg = ComplianceConfig()
        rule = ComplianceRule(name="r1", description="")
        cfg.add(rule)
        assert cfg.get("r1") is rule

    def test_add_duplicate_raises(self):
        cfg = ComplianceConfig()
        cfg.add(ComplianceRule(name="dup", description=""))
        with pytest.raises(ValueError):
            cfg.add(ComplianceRule(name="dup", description=""))

    def test_remove(self):
        cfg = ComplianceConfig()
        cfg.add(ComplianceRule(name="r", description=""))
        cfg.remove("r")
        assert "r" not in cfg

    def test_remove_missing_raises(self):
        cfg = ComplianceConfig()
        with pytest.raises(KeyError):
            cfg.remove("ghost")

    def test_len(self):
        cfg = ComplianceConfig()
        cfg.add(ComplianceRule(name="a", description=""))
        cfg.add(ComplianceRule(name="b", description=""))
        assert len(cfg) == 2


# ---------------------------------------------------------------------------
# ComplianceEvaluator
# ---------------------------------------------------------------------------

class TestComplianceEvaluator:
    def _monitor(self, pipelines):
        m = MagicMock()
        m.pipelines = {p.name: p for p in pipelines}
        return m

    def test_no_violations_report_is_compliant(self):
        cfg = ComplianceConfig()
        evaluator = ComplianceEvaluator(cfg)
        monitor = self._monitor([_make_pipeline()])
        report = evaluator.evaluate(monitor)
        assert report.compliant

    def test_violation_detected(self):
        cfg = ComplianceConfig()
        cfg.add(ComplianceRule(name="r", description="", required_metadata_keys=["env"]))
        evaluator = ComplianceEvaluator(cfg)
        monitor = self._monitor([_make_pipeline(name="p1", metadata={})])
        report = evaluator.evaluate(monitor)
        assert not report.compliant
        assert len(report.violations) == 1

    def test_by_pipeline_groups_correctly(self):
        cfg = ComplianceConfig()
        cfg.add(ComplianceRule(name="r", description="", required_metadata_keys=["env"]))
        evaluator = ComplianceEvaluator(cfg)
        pipelines = [
            _make_pipeline(name="p1", metadata={}),
            _make_pipeline(name="p2", metadata={"env": "prod"}),
        ]
        report = evaluator.evaluate(self._monitor(pipelines))
        grouped = report.by_pipeline()
        assert "p1" in grouped
        assert "p2" not in grouped

    def test_to_dicts_returns_list_of_dicts(self):
        cfg = ComplianceConfig()
        cfg.add(ComplianceRule(name="r", description="", require_owner=True))
        evaluator = ComplianceEvaluator(cfg)
        monitor = self._monitor([_make_pipeline(name="p", owner=None)])
        report = evaluator.evaluate(monitor)
        dicts = report.to_dicts()
        assert isinstance(dicts, list)
        assert dicts[0]["pipeline_name"] == "p"
