"""Tests for pipewatch.core.enricher."""

from __future__ import annotations

import pytest

from pipewatch.core.enricher import EnrichmentRule, Enricher
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.reporter import PipelineSummary, Report


def _make_summary(name: str, meta: dict | None = None, tags: list[str] | None = None) -> PipelineSummary:
    p = Pipeline(name=name)
    if meta:
        for k, v in meta.items():
            p.add_metadata(k, v)
    if tags:
        for t in tags:
            p.tags.add(t)
    return PipelineSummary(pipeline=p, health_score=1.0)


def _make_report(*summaries: PipelineSummary) -> Report:
    return Report(
        pipelines=list(summaries),
        total=len(summaries),
        healthy=len(summaries),
        failing=0,
        unknown=0,
    )


@pytest.fixture
def enricher() -> Enricher:
    return Enricher()


class TestEnrichmentRule:
    def test_matches_metadata(self):
        rule = EnrichmentRule("env", "prod", "tier", "production")
        summary = _make_summary("p1", meta={"env": "prod"})
        assert rule.matches(summary) is True

    def test_no_match_wrong_value(self):
        rule = EnrichmentRule("env", "prod", "tier", "production")
        summary = _make_summary("p1", meta={"env": "staging"})
        assert rule.matches(summary) is False

    def test_matches_tag(self):
        rule = EnrichmentRule("tag", "finance", "domain", "finance")
        summary = _make_summary("p1", tags=["finance"])
        assert rule.matches(summary) is True

    def test_no_match_missing_tag(self):
        rule = EnrichmentRule("tag", "finance", "domain", "finance")
        summary = _make_summary("p1", tags=["marketing"])
        assert rule.matches(summary) is False

    def test_to_dict_keys(self):
        rule = EnrichmentRule("env", "prod", "tier", "production")
        d = rule.to_dict()
        assert set(d.keys()) == {"match_key", "match_value", "label_key", "label_value"}


class TestEnricher:
    def test_no_rules_returns_empty(self, enricher):
        report = _make_report(_make_summary("p1", meta={"env": "prod"}))
        assert enricher.enrich(report) == {}

    def test_matching_rule_returns_label(self, enricher):
        enricher.add_rule(EnrichmentRule("env", "prod", "tier", "production"))
        report = _make_report(_make_summary("p1", meta={"env": "prod"}))
        result = enricher.enrich(report)
        assert result["p1"]["tier"] == "production"

    def test_non_matching_pipeline_excluded(self, enricher):
        enricher.add_rule(EnrichmentRule("env", "prod", "tier", "production"))
        report = _make_report(
            _make_summary("p1", meta={"env": "prod"}),
            _make_summary("p2", meta={"env": "staging"}),
        )
        result = enricher.enrich(report)
        assert "p1" in result
        assert "p2" not in result

    def test_multiple_rules_merged(self, enricher):
        enricher.add_rule(EnrichmentRule("env", "prod", "tier", "production"))
        enricher.add_rule(EnrichmentRule("tag", "finance", "domain", "finance"))
        summary = _make_summary("p1", meta={"env": "prod"}, tags=["finance"])
        report = _make_report(summary)
        result = enricher.enrich(report)
        assert result["p1"]["tier"] == "production"
        assert result["p1"]["domain"] == "finance"

    def test_remove_rule(self, enricher):
        rule = EnrichmentRule("env", "prod", "tier", "production")
        enricher.add_rule(rule)
        enricher.remove_rule(rule)
        report = _make_report(_make_summary("p1", meta={"env": "prod"}))
        assert enricher.enrich(report) == {}

    def test_rules_property_returns_copy(self, enricher):
        rule = EnrichmentRule("env", "prod", "tier", "production")
        enricher.add_rule(rule)
        rules = enricher.rules
        rules.clear()
        assert len(enricher.rules) == 1
