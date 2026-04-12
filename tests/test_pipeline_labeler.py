"""Tests for PipelineLabeler and LabelSet."""
import pytest
from pipewatch.core.pipeline_labeler import LabelSet, PipelineLabeler


class TestLabelSet:
    def test_set_and_get(self):
        ls = LabelSet()
        ls.set("env", "production")
        assert ls.get("env") == "production"

    def test_keys_are_lowercased(self):
        ls = LabelSet()
        ls.set("ENV", "prod")
        assert ls.has("env")
        assert not ls.has("ENV")

    def test_values_are_stripped(self):
        ls = LabelSet()
        ls.set("team", "  data  ")
        assert ls.get("team") == "data"

    def test_remove_existing(self):
        ls = LabelSet()
        ls.set("env", "staging")
        ls.remove("env")
        assert not ls.has("env")

    def test_remove_nonexistent_does_not_raise(self):
        ls = LabelSet()
        ls.remove("missing")  # should not raise

    def test_matches_case_insensitive(self):
        ls = LabelSet()
        ls.set("region", "us-east")
        assert ls.matches("region", "US-EAST")

    def test_matches_returns_false_when_absent(self):
        ls = LabelSet()
        assert not ls.matches("region", "us-east")

    def test_to_dict(self):
        ls = LabelSet()
        ls.set("env", "prod")
        ls.set("team", "data")
        d = ls.to_dict()
        assert d == {"env": "prod", "team": "data"}

    def test_keys_returns_frozenset(self):
        ls = LabelSet()
        ls.set("a", "1")
        ls.set("b", "2")
        assert ls.keys() == frozenset({"a", "b"})


class TestPipelineLabeler:
    def test_set_and_retrieve(self):
        labeler = PipelineLabeler()
        labeler.set_label("pipe_a", "env", "prod")
        assert labeler.labels_for("pipe_a").get("env") == "prod"

    def test_unknown_pipeline_returns_empty_labelset(self):
        labeler = PipelineLabeler()
        ls = labeler.labels_for("unknown")
        assert ls.to_dict() == {}

    def test_remove_label(self):
        labeler = PipelineLabeler()
        labeler.set_label("pipe_a", "env", "dev")
        labeler.remove_label("pipe_a", "env")
        assert not labeler.labels_for("pipe_a").has("env")

    def test_pipelines_with(self):
        labeler = PipelineLabeler()
        labeler.set_label("pipe_a", "team", "data")
        labeler.set_label("pipe_b", "team", "data")
        labeler.set_label("pipe_c", "team", "ops")
        result = set(labeler.pipelines_with("team", "data"))
        assert result == {"pipe_a", "pipe_b"}

    def test_all_labels_excludes_empty(self):
        labeler = PipelineLabeler()
        labeler.labels_for("empty_pipe")  # create but don't set
        labeler.set_label("pipe_a", "env", "prod")
        assert "empty_pipe" not in labeler.all_labels()
        assert "pipe_a" in labeler.all_labels()
