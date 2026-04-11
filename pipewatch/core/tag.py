"""Tag-based filtering and grouping for pipelines."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Set


@dataclass
class TagSet:
    """An immutable-ish set of string tags attached to a pipeline."""

    _tags: Set[str] = field(default_factory=set)

    def add(self, *tags: str) -> None:
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError(f"Tags must be non-empty strings, got: {tag!r}")
            self._tags.add(tag.strip().lower())

    def remove(self, tag: str) -> None:
        self._tags.discard(tag.strip().lower())

    def has(self, tag: str) -> bool:
        return tag.strip().lower() in self._tags

    def matches_any(self, tags: Iterable[str]) -> bool:
        return any(self.has(t) for t in tags)

    def matches_all(self, tags: Iterable[str]) -> bool:
        return all(self.has(t) for t in tags)

    def to_list(self) -> list[str]:
        return sorted(self._tags)

    @classmethod
    def from_list(cls, tags: Iterable[str]) -> "TagSet":
        ts = cls()
        ts.add(*tags)
        return ts

    def __repr__(self) -> str:
        return f"TagSet({self.to_list()})"

    def __len__(self) -> int:
        return len(self._tags)

    def __iter__(self):
        return iter(sorted(self._tags))
