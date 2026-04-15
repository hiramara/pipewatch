"""Pipeline compliance rules and evaluation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ComplianceRule:
    """A single compliance requirement for a pipeline."""

    name: str
    description: str
    required_metadata_keys: List[str] = field(default_factory=list)
    required_tags: List[str] = field(default_factory=list)
    require_owner: bool = False

    def evaluate(self, pipeline) -> "ComplianceViolation | None":
        """Return a violation if the pipeline fails this rule, else None."""
        reasons: List[str] = []

        meta = pipeline.metadata or {}
        for key in self.required_metadata_keys:
            if key not in meta:
                reasons.append(f"Missing required metadata key: '{key}'")

        pipeline_tags = {t.lower() for t in getattr(pipeline, "tags", [])}
        for tag in self.required_tags:
            if tag.lower() not in pipeline_tags:
                reasons.append(f"Missing required tag: '{tag}'")

        if self.require_owner and not getattr(pipeline, "owner", None):
            reasons.append("Pipeline has no assigned owner")

        if reasons:
            return ComplianceViolation(
                rule_name=self.name,
                pipeline_name=pipeline.name,
                reasons=reasons,
                evaluated_at=datetime.utcnow(),
            )
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required_metadata_keys": self.required_metadata_keys,
            "required_tags": self.required_tags,
            "require_owner": self.require_owner,
        }


@dataclass
class ComplianceViolation:
    """Records a compliance failure for a specific pipeline."""

    rule_name: str
    pipeline_name: str
    reasons: List[str]
    evaluated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "pipeline_name": self.pipeline_name,
            "reasons": list(self.reasons),
            "evaluated_at": self.evaluated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"<ComplianceViolation rule={self.rule_name!r} "
            f"pipeline={self.pipeline_name!r} reasons={len(self.reasons)}>"
        )
