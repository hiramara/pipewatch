"""Configuration helper for building and managing AlertRouter rules."""

from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.core.alert import AlertLevel
from pipewatch.core.notifier import NotificationChannel
from pipewatch.core.routing import AlertRouter, RoutingRule


class RoutingConfig:
    """Fluent builder for an AlertRouter."""

    def __init__(self) -> None:
        self._router = AlertRouter()
        self._named: Dict[str, RoutingRule] = {}

    def add(
        self,
        name: str,
        channel: NotificationChannel,
        *,
        pipeline_name: Optional[str] = None,
        min_level: AlertLevel = AlertLevel.INFO,
        tags: Optional[List[str]] = None,
    ) -> "RoutingConfig":
        """Add a named routing rule. Raises ValueError on duplicate name."""
        if name in self._named:
            raise ValueError(f"Routing rule '{name}' already registered.")
        rule = RoutingRule(
            channel=channel,
            pipeline_name=pipeline_name,
            min_level=min_level,
            tags=tags or [],
        )
        self._named[name] = rule
        self._router.add_rule(rule)
        return self

    def remove(self, name: str) -> "RoutingConfig":
        """Remove a named routing rule. Raises KeyError if not found."""
        rule = self._named.pop(name)
        self._router.remove_rule(rule)
        return self

    def get(self, name: str) -> RoutingRule:
        """Return the rule registered under *name*."""
        return self._named[name]

    @property
    def router(self) -> AlertRouter:
        """Return the underlying AlertRouter."""
        return self._router

    @property
    def names(self) -> List[str]:
        return list(self._named.keys())

    def to_dicts(self) -> List[dict]:
        return [{"name": n, **r.to_dict()} for n, r in self._named.items()]
