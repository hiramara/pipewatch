"""Pipeline alert correlation — groups related alerts into incidents."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pipewatch.core.alert import Alert, AlertLevel


@dataclass
class Incident:
    """A group of correlated alerts treated as a single incident."""

    incident_id: str = field(default_factory=lambda: str(uuid4()))
    alerts: List[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False

    @property
    def level(self) -> AlertLevel:
        """Highest severity level among constituent alerts."""
        if not self.alerts:
            return AlertLevel.INFO
        return max(a.level for a in self.alerts, key=lambda lvl: lvl.value)

    @property
    def pipeline_names(self) -> List[str]:
        return list({a.pipeline_name for a in self.alerts})

    def resolve(self) -> None:
        self.resolved = True
        for alert in self.alerts:
            if not alert.resolved:
                alert.resolve()

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "resolved": self.resolved,
            "level": self.level.value,
            "pipeline_names": self.pipeline_names,
            "alert_count": len(self.alerts),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        status = "resolved" if self.resolved else "active"
        return f"<Incident {self.incident_id[:8]} [{status}] alerts={len(self.alerts)}>"


class CorrelationEngine:
    """Groups incoming alerts into incidents based on shared pipeline or check name."""

    def __init__(self, window_seconds: int = 300) -> None:
        self._window_seconds = window_seconds
        self._incidents: List[Incident] = []

    def ingest(self, alert: Alert) -> Incident:
        """Add *alert* to an existing open incident or create a new one."""
        incident = self._find_open(alert)
        if incident is None:
            incident = Incident(alerts=[alert])
            self._incidents.append(incident)
        else:
            incident.alerts.append(alert)
        return incident

    def _find_open(self, alert: Alert) -> Optional[Incident]:
        now = datetime.utcnow()
        for inc in self._incidents:
            if inc.resolved:
                continue
            age = (now - inc.created_at).total_seconds()
            if age > self._window_seconds:
                continue
            if alert.pipeline_name in inc.pipeline_names:
                return inc
        return None

    def open_incidents(self) -> List[Incident]:
        return [i for i in self._incidents if not i.resolved]

    def all_incidents(self) -> List[Incident]:
        return list(self._incidents)

    def resolve_for_pipeline(self, pipeline_name: str) -> int:
        """Resolve every open incident that involves *pipeline_name*."""
        count = 0
        for inc in self.open_incidents():
            if pipeline_name in inc.pipeline_names:
                inc.resolve()
                count += 1
        return count
