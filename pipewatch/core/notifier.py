"""Notifier module for dispatching alerts via configurable channels."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.core.alert import Alert, AlertLevel

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    def send(self, alert: Alert) -> bool:
        """Send an alert through this channel. Returns True on success."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable channel name."""
        ...


class LogChannel(NotificationChannel):
    """Notification channel that logs alerts using Python's logging module."""

    def __init__(self, level: int = logging.WARNING) -> None:
        self._level = level

    @property
    def name(self) -> str:
        return "log"

    def send(self, alert: Alert) -> bool:
        msg = f"[ALERT] {alert.level.value.upper()} | {alert.pipeline_id} | {alert.message}"
        logger.log(self._level, msg)
        return True


class StdoutChannel(NotificationChannel):
    """Notification channel that prints alerts to stdout."""

    @property
    def name(self) -> str:
        return "stdout"

    def send(self, alert: Alert) -> bool:
        icon = {AlertLevel.INFO: "ℹ", AlertLevel.WARNING: "⚠", AlertLevel.CRITICAL: "🔴"}.get(
            alert.level, "•"
        )
        print(f"{icon}  [{alert.level.value.upper()}] {alert.pipeline_id}: {alert.message}")
        return True


@dataclass
class Notifier:
    """Dispatches alerts to one or more notification channels."""

    channels: List[NotificationChannel] = field(default_factory=list)
    min_level: AlertLevel = AlertLevel.WARNING

    def add_channel(self, channel: NotificationChannel) -> None:
        """Register a notification channel."""
        self.channels.append(channel)

    def remove_channel(self, name: str) -> None:
        """Unregister a channel by name."""
        self.channels = [c for c in self.channels if c.name != name]

    def dispatch(self, alert: Alert) -> int:
        """Send alert to all channels if it meets min_level. Returns count of successes."""
        level_order = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.CRITICAL]
        if level_order.index(alert.level) < level_order.index(self.min_level):
            return 0
        successes = 0
        for channel in self.channels:
            try:
                if channel.send(alert):
                    successes += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Channel %s failed: %s", channel.name, exc)
        return successes

    def dispatch_many(self, alerts: List[Alert]) -> int:
        """Dispatch multiple alerts. Returns total success count."""
        return sum(self.dispatch(a) for a in alerts)
