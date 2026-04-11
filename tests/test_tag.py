"""Tests for TagSet."""
import pytest
from pipewatch.core.tag import TagSet


class TestTagSet:
    def test_add_and_has(self):
        ts = TagSet()
        ts.add("finance", "daily")
        assert ts.has("finance")
        assert ts.has("daily")
        assert not ts.has("weekly")

    def test_tags_lowercased_and_stripped(self):
        ts = TagSet()
        ts.add("  Finance  ", "DAILY")
        assert ts.has("finance")
        assert ts.has("daily")

    def test_remove(self):
        ts = TagSet()
        ts.add("finance")
        ts.remove("finance")
        assert not ts.has("finance")

    def test_remove_nonexistent_does_not_raise(self):
        ts = TagSet()
        ts.remove("ghost")  # should not raise

    def test_invalid_tag_raises(self):
        ts = TagSet()
        with pytest.raises(ValueError):
            ts.add("")
        with pytest.raises(ValueError):
            ts.add("  ")

    def test_matches_any(self):
        ts = TagSet.from_list(["a", "b"])
        assert ts.matches_any(["b", "c"])
        assert not ts.matches_any(["x", "y"])

    def test_matches_all(self):
        ts = TagSet.from_list(["a", "b", "c"])
        assert ts.matches_all(["a", "b"])
        assert not ts.matches_all(["a", "z"])

    def test_to_list_sorted(self):
        ts = TagSet.from_list(["zebra", "apple", "mango"])
        assert ts.to_list() == ["apple", "mango", "zebra"]

    def test_len(self):
        ts = TagSet.from_list(["x", "y"])
        assert len(ts) == 2

    def test_iter(self):
        ts = TagSet.from_list(["b", "a"])
        assert list(ts) == ["a", "b"]

    def test_repr(self):
        ts = TagSet.from_list(["prod"])
        assert "prod" in repr(ts)
