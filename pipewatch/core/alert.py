"""Alert module for pipewatch — defines alert levels and alert dispatch logic."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents a single alert triggered by a pipeline or check."""

    pipeline_id: str
    message: str
    level: AlertLevel = AlertLevel.WARNING
    check_name: Optional[str] = None
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False

    def resolve(self) -> None:
        """Mark this alert as resolved."""
        self.resolved = True

    def to_dict(self) -> dict:
        """Serialize the alert to a dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "message": self.message,
            "level": self.level.value,
            "check_name": self.check_name,
            "triggered_at": self.triggered_at.isoformat(),
            "resolved": self.resolved,
        }

    def __repr__(self) -> str:
        status = "RESOLVED" if self.resolved else "ACTIVE"
        return (
            f"<Alert [{self.level.value.upper()}] pipeline={self.pipeline_id!r} "
            f"message={self.message!r} status={status}>"
        )


class AlertManager:
    """Collects and manages alerts for monitored pipelines."""

    def __init__(self) -> None:
        self._alerts: list[Alert] = []

    def trigger(self, alert: Alert) -> None:
        """Register a new alert."""
        self._alerts.append(alert)

    def resolve_all(self, pipeline_id: str) -> int:
        """Resolve all active alerts for a given pipeline. Returns count resolved."""
        count = 0
        for alert in self._alerts:
            if alert.pipeline_id == pipeline_id and not alert.resolved:
                alert.resolve()
                count += 1
        return count

    def active_alerts(self, pipeline_id: Optional[str] = None) -> list[Alert]:
        """Return all unresolved alerts, optionally filtered by pipeline."""
        return [
            a for a in self._alerts
            if not a.resolved and (pipeline_id is None or a.pipeline_id == pipeline_id)
        ]

    def all_alerts(self) -> list[Alert]:
        """Return every alert regardless of resolved status."""
        return list(self._alerts)

    def summary(self) -> dict:
        """Return a high-level count summary of alerts by level."""
        counts: dict[str, int] = {level.value: 0 for level in AlertLevel}
        for alert in self.active_alerts():
            counts[alert.level.value] += 1
        return counts
