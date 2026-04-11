"""Tests for pipewatch.core.dependency.DependencyGraph."""

import pytest

from pipewatch.core.dependency import DependencyGraph


@pytest.fixture
def graph() -> DependencyGraph:
    return DependencyGraph()


class TestDependencyGraph:
    def test_add_and_downstreams(self, graph):
        graph.add_dependency("raw", "clean")
        assert "clean" in graph.downstreams_of("raw")

    def test_upstreams_of(self, graph):
        graph.add_dependency("raw", "clean")
        graph.add_dependency("meta", "clean")
        ups = graph.upstreams_of("clean")
        assert "raw" in ups
        assert "meta" in ups

    def test_remove_dependency(self, graph):
        graph.add_dependency("raw", "clean")
        graph.remove_dependency("raw", "clean")
        assert graph.downstreams_of("raw") == []

    def test_remove_nonexistent_does_not_raise(self, graph):
        graph.remove_dependency("ghost", "nobody")  # should not raise

    def test_self_dependency_raises(self, graph):
        with pytest.raises(ValueError, match="cannot depend on itself"):
            graph.add_dependency("pipe", "pipe")

    def test_all_downstreams_transitive(self, graph):
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("c", "d")
        result = graph.all_downstreams_of("a")
        assert set(result) == {"b", "c", "d"}

    def test_all_downstreams_empty_for_leaf(self, graph):
        graph.add_dependency("a", "b")
        assert graph.all_downstreams_of("b") == []

    def test_no_cycle_detected(self, graph):
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        assert graph.has_cycle() is False

    def test_cycle_detected(self, graph):
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("c", "a")  # creates cycle
        assert graph.has_cycle() is True

    def test_to_dict(self, graph):
        graph.add_dependency("raw", "clean")
        graph.add_dependency("raw", "archive")
        d = graph.to_dict()
        assert "raw" in d
        assert sorted(d["raw"]) == ["archive", "clean"]

    def test_to_dict_empty(self, graph):
        assert graph.to_dict() == {}

    def test_multiple_upstreams_multiple_downstreams(self, graph):
        graph.add_dependency("src1", "transform")
        graph.add_dependency("src2", "transform")
        graph.add_dependency("transform", "load")
        assert set(graph.upstreams_of("transform")) == {"src1", "src2"}
        assert graph.downstreams_of("transform") == ["load"]
