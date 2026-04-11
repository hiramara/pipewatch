"""Per-pipeline retry configuration registry."""

from __future__ import annotations

from typing import Dict, Optional

from pipewatch.core.retry import RetryPolicy


class RetryConfig:
    """Stores RetryPolicy objects keyed by pipeline name.

    A default policy is used for pipelines that have no explicit entry.
    """

    def __init__(self, default_policy: Optional[RetryPolicy] = None) -> None:
        self._default = default_policy or RetryPolicy()
        self._policies: Dict[str, RetryPolicy] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def set(self, pipeline_name: str, policy: RetryPolicy) -> None:
        """Register a policy for a specific pipeline."""
        if not pipeline_name:
            raise ValueError("pipeline_name must be a non-empty string")
        self._policies[pipeline_name] = policy

    def remove(self, pipeline_name: str) -> None:
        """Remove any custom policy for *pipeline_name* (falls back to default)."""
        self._policies.pop(pipeline_name, None)

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def get(self, pipeline_name: str) -> RetryPolicy:
        """Return the policy for *pipeline_name*, or the default policy."""
        return self._policies.get(pipeline_name, self._default)

    @property
    def default(self) -> RetryPolicy:
        return self._default

    def pipeline_names(self) -> list:
        """Return list of pipeline names with explicit policies."""
        return list(self._policies.keys())

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "default": self._default.to_dict(),
            "pipelines": {
                name: policy.to_dict()
                for name, policy in self._policies.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RetryConfig":
        default = RetryPolicy.from_dict(data.get("default", {}))
        cfg = cls(default_policy=default)
        for name, policy_data in data.get("pipelines", {}).items():
            cfg.set(name, RetryPolicy.from_dict(policy_data))
        return cfg

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetryConfig(default={self._default!r}, "
            f"pipelines={list(self._policies.keys())})"
        )
