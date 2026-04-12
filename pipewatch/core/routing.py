"""Alert routing: direct alerts to specific channels based on rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.notifier import NotificationChannel


@dataclass
class RoutingRule:
    """Maps a condition to a target notification channel."""

    channel: NotificationChannel
    pipeline_name: Optional[str] = None  # None means match all
    min_level: AlertLevel = AlertLevel.INFO
    tags: List[str] = field(default_factory=list)

    def matches(self, alert: Alert) -> bool:
        """Return True if *alert* satisfies this rule's conditions."""
        if alert.level.value < self.min_level.value:
            return False
        if self.pipeline_name and alert.pipeline_name != self.pipeline_name:
            return False
        if self.tags:
            alert_tags = set(alert.metadata.get("tags", []))
            if not set(self.tags).intersection(alert_tags):
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "channel": self.channel.name,
            "pipeline_name": self.pipeline_name,
            "min_level": self.min_level.name,
            "tags": list(self.tags),
        }


class AlertRouter:
    """Routes alerts to matching channels based on registered rules."""

    def __init__(self) -> None:
        self._rules: List[RoutingRule] = []
        self._routed: List[tuple] = []  # (alert, channel_name) history

    def add_rule(self, rule: RoutingRule) -> None:
        """Register a routing rule."""
        self._rules.append(rule)

    def remove_rule(self, rule: RoutingRule) -> None:
        """Unregister a routing rule (no-op if absent)."""
        self._rules = [r for r in self._rules if r is not rule]

    def route(self, alert: Alert) -> List[str]:
        """Send *alert* to every matching channel. Return list of channel names used."""
        sent_to: List[str] = []
        for rule in self._rules:
            if rule.matches(alert):
                rule.channel.send(alert)
                sent_to.append(rule.channel.name)
                self._routed.append((alert, rule.channel.name))
        return sent_to

    def route_all(self, alerts: List[Alert]) -> dict:
        """Route multiple alerts. Return mapping of alert id -> channel names."""
        return {alert.id: self.route(alert) for alert in alerts}

    @property
    def rules(self) -> List[RoutingRule]:
        return list(self._rules)

    @property
    def history(self) -> List[tuple]:
        """Return (alert, channel_name) pairs for all routed alerts."""
        return list(self._routed)
