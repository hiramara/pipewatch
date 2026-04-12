"""Attach and manage user-defined labels on pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, Optional


@dataclass
class LabelSet:
    """An immutable-like collection of key/value label pairs for a pipeline."""

    _labels: Dict[str, str] = field(default_factory=dict, repr=False)

    def set(self, key: str, value: str) -> None:
        """Add or overwrite a label."""
        self._labels[key.strip().lower()] = value.strip()

    def remove(self, key: str) -> None:
        """Remove a label by key; silently ignores missing keys."""
        self._labels.pop(key.strip().lower(), None)

    def get(self, key: str) -> Optional[str]:
        """Return the value for *key*, or ``None`` if absent."""
        return self._labels.get(key.strip().lower())

    def has(self, key: str) -> bool:
        return key.strip().lower() in self._labels

    def matches(self, key: str, value: str) -> bool:
        """Return True when the stored value equals *value* (case-insensitive)."""
        stored = self.get(key)
        return stored is not None and stored.lower() == value.strip().lower()

    def keys(self) -> FrozenSet[str]:
        return frozenset(self._labels.keys())

    def to_dict(self) -> Dict[str, str]:
        return dict(self._labels)

    def __repr__(self) -> str:  # pragma: no cover
        return f"LabelSet({self._labels!r})"


class PipelineLabeler:
    """Manage :class:`LabelSet` instances keyed by pipeline name."""

    def __init__(self) -> None:
        self._store: Dict[str, LabelSet] = {}

    def _get_or_create(self, pipeline_name: str) -> LabelSet:
        if pipeline_name not in self._store:
            self._store[pipeline_name] = LabelSet()
        return self._store[pipeline_name]

    def set_label(self, pipeline_name: str, key: str, value: str) -> None:
        """Set *key*/*value* label on *pipeline_name*."""
        self._get_or_create(pipeline_name).set(key, value)

    def remove_label(self, pipeline_name: str, key: str) -> None:
        """Remove *key* from *pipeline_name*'s labels."""
        if pipeline_name in self._store:
            self._store[pipeline_name].remove(key)

    def labels_for(self, pipeline_name: str) -> LabelSet:
        """Return the :class:`LabelSet` for *pipeline_name* (empty if unknown)."""
        return self._get_or_create(pipeline_name)

    def pipelines_with(self, key: str, value: str) -> Iterable[str]:
        """Yield pipeline names whose label *key* equals *value*."""
        for name, ls in self._store.items():
            if ls.matches(key, value):
                yield name

    def all_labels(self) -> Dict[str, Dict[str, str]]:
        """Return a mapping of pipeline name → label dict."""
        return {name: ls.to_dict() for name, ls in self._store.items() if ls._labels}
