"""Manages a collection of MuteRules and checks whether a pipeline is muted."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.core.mute import MuteRule


class MuteManager:
    """Registry of mute rules keyed by pipeline name."""

    def __init__(self) -> None:
        self._rules: Dict[str, MuteRule] = {}

    def mute(
        self,
        pipeline_name: str,
        reason: str,
        expires_at: Optional[datetime] = None,
    ) -> MuteRule:
        """Add or replace a mute rule for *pipeline_name*."""
        rule = MuteRule(
            pipeline_name=pipeline_name,
            reason=reason,
            expires_at=expires_at,
        )
        self._rules[pipeline_name] = rule
        return rule

    def unmute(self, pipeline_name: str) -> bool:
        """Remove an existing rule. Returns True if a rule was removed."""
        return self._rules.pop(pipeline_name, None) is not None

    def is_muted(self, pipeline_name: str, at: Optional[datetime] = None) -> bool:
        """Return True if *pipeline_name* has an active mute rule."""
        rule = self._rules.get(pipeline_name)
        if rule is None:
            return False
        return rule.is_active(at=at)

    def active_rules(self, at: Optional[datetime] = None) -> List[MuteRule]:
        """Return all currently active rules."""
        now = at or datetime.now(timezone.utc)
        return [r for r in self._rules.values() if r.is_active(at=now)]

    def purge_expired(self, at: Optional[datetime] = None) -> int:
        """Remove expired rules. Returns the number of rules removed."""
        now = at or datetime.now(timezone.utc)
        expired = [
            name
            for name, rule in self._rules.items()
            if not rule.is_active(at=now)
        ]
        for name in expired:
            del self._rules[name]
        return len(expired)

    def all_rules(self) -> List[MuteRule]:
        return list(self._rules.values())

    def __len__(self) -> int:
        return len(self._rules)
