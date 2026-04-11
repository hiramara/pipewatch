"""Mute rules for suppressing alerts on known noisy pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class MuteRule:
    """Suppresses alerts for a pipeline within an optional time window."""

    pipeline_name: str
    reason: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def is_active(self, at: Optional[datetime] = None) -> bool:
        """Return True if the rule is currently active."""
        now = at or datetime.now(timezone.utc)
        if self.expires_at is None:
            return True
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "pipeline_name": self.pipeline_name,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.is_active(),
        }

    def __repr__(self) -> str:
        expiry = self.expires_at.isoformat() if self.expires_at else "never"
        return (
            f"MuteRule(pipeline={self.pipeline_name!r}, "
            f"reason={self.reason!r}, expires={expiry})"
        )
