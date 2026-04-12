"""Tests for PipelineAnnotator."""

from __future__ import annotations

import pytest

from pipewatch.core.pipeline_annotator import Annotation, PipelineAnnotator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def annotator() -> PipelineAnnotator:
    return PipelineAnnotator()


# ---------------------------------------------------------------------------
# Annotation dataclass
# ---------------------------------------------------------------------------


class TestAnnotation:
    def test_to_dict_keys(self):
        a = Annotation(pipeline_name="etl", text="looks good", author="alice")
        d = a.to_dict()
        assert set(d) == {"pipeline_name", "text", "author", "created_at"}

    def test_to_dict_values(self):
        a = Annotation(pipeline_name="etl", text="looks good", author="alice")
        d = a.to_dict()
        assert d["pipeline_name"] == "etl"
        assert d["text"] == "looks good"
        assert d["author"] == "alice"

    def test_repr_contains_pipeline(self):
        a = Annotation(pipeline_name="etl", text="note", author="bob")
        assert "etl" in repr(a)
        assert "bob" in repr(a)


# ---------------------------------------------------------------------------
# PipelineAnnotator
# ---------------------------------------------------------------------------


class TestPipelineAnnotator:
    def test_annotate_returns_annotation(self, annotator):
        note = annotator.annotate("pipe_a", "first note")
        assert isinstance(note, Annotation)
        assert note.pipeline_name == "pipe_a"

    def test_get_empty_returns_empty_list(self, annotator):
        assert annotator.get("unknown") == []

    def test_get_returns_all_notes_in_order(self, annotator):
        annotator.annotate("pipe_a", "note 1")
        annotator.annotate("pipe_a", "note 2")
        notes = annotator.get("pipe_a")
        assert len(notes) == 2
        assert notes[0].text == "note 1"
        assert notes[1].text == "note 2"

    def test_empty_text_raises(self, annotator):
        with pytest.raises(ValueError, match="empty"):
            annotator.annotate("pipe_a", "   ")

    def test_remove_by_index(self, annotator):
        annotator.annotate("pipe_a", "keep")
        annotator.annotate("pipe_a", "remove me")
        annotator.remove("pipe_a", 1)
        notes = annotator.get("pipe_a")
        assert len(notes) == 1
        assert notes[0].text == "keep"

    def test_remove_invalid_index_raises(self, annotator):
        annotator.annotate("pipe_a", "only note")
        with pytest.raises(IndexError):
            annotator.remove("pipe_a", 5)

    def test_clear_removes_all(self, annotator):
        annotator.annotate("pipe_a", "note")
        annotator.clear("pipe_a")
        assert annotator.get("pipe_a") == []

    def test_all_pipeline_names(self, annotator):
        annotator.annotate("pipe_a", "note")
        annotator.annotate("pipe_b", "note")
        names = annotator.all_pipeline_names()
        assert set(names) == {"pipe_a", "pipe_b"}

    def test_all_pipeline_names_excludes_cleared(self, annotator):
        annotator.annotate("pipe_a", "note")
        annotator.clear("pipe_a")
        assert "pipe_a" not in annotator.all_pipeline_names()

    def test_latest_returns_most_recent(self, annotator):
        annotator.annotate("pipe_a", "first")
        annotator.annotate("pipe_a", "second")
        latest = annotator.latest("pipe_a")
        assert latest is not None
        assert latest.text == "second"

    def test_latest_returns_none_when_empty(self, annotator):
        assert annotator.latest("unknown") is None

    def test_author_defaults_to_system(self, annotator):
        note = annotator.annotate("pipe_a", "auto note")
        assert note.author == "system"

    def test_custom_author_stored(self, annotator):
        note = annotator.annotate("pipe_a", "manual note", author="ops-team")
        assert note.author == "ops-team"
