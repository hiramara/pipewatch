"""Pipeline dependency tracking — defines upstream/downstream relationships."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class DependencyGraph:
    """Tracks directed upstream → downstream dependencies between pipelines."""

    _edges: Dict[str, Set[str]] = field(default_factory=dict)  # upstream -> set of downstreams

    def add_dependency(self, upstream: str, downstream: str) -> None:
        """Register that *downstream* depends on *upstream*."""
        if upstream == downstream:
            raise ValueError(f"Pipeline '{upstream}' cannot depend on itself.")
        self._edges.setdefault(upstream, set()).add(downstream)

    def remove_dependency(self, upstream: str, downstream: str) -> None:
        """Remove a dependency edge. Silently ignores unknown edges."""
        if upstream in self._edges:
            self._edges[upstream].discard(downstream)
            if not self._edges[upstream]:
                del self._edges[upstream]

    def upstreams_of(self, pipeline: str) -> List[str]:
        """Return all pipelines that *pipeline* directly depends on."""
        return [
            up for up, downs in self._edges.items() if pipeline in downs
        ]

    def downstreams_of(self, pipeline: str) -> List[str]:
        """Return all pipelines that directly depend on *pipeline*."""
        return list(self._edges.get(pipeline, []))

    def all_downstreams_of(self, pipeline: str) -> List[str]:
        """Return the transitive closure of downstream dependents (BFS)."""
        visited: Set[str] = set()
        queue = list(self._edges.get(pipeline, []))
        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                queue.extend(self._edges.get(node, []))
        return list(visited)

    def has_cycle(self) -> bool:
        """Return True if the graph contains a cycle (DFS-based)."""
        visited: Set[str] = set()
        in_stack: Set[str] = set()

        def _dfs(node: str) -> bool:
            visited.add(node)
            in_stack.add(node)
            for neighbour in self._edges.get(node, []):
                if neighbour not in visited:
                    if _dfs(neighbour):
                        return True
                elif neighbour in in_stack:
                    return True
            in_stack.discard(node)
            return False

        all_nodes = set(self._edges.keys()) | {
            d for downs in self._edges.values() for d in downs
        }
        for node in all_nodes:
            if node not in visited:
                if _dfs(node):
                    return True
        return False

    def to_dict(self) -> Dict[str, List[str]]:
        """Serialise the graph to a plain dict for reporting/storage."""
        return {up: sorted(downs) for up, downs in self._edges.items()}
