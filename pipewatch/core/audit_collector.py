"""Collects audit events from monitor evaluation results."""

from typing import Optional
from pipewatch.core.audit import AuditLog, AuditEvent, AuditEventType
from pipewatch.core.monitor import Monitor
from pipewatch.core.pipeline import PipelineStatus


class AuditCollector:
    """Observes a Monitor and writes structured audit events to an AuditLog."""

    def __init__(self, log: Optional[AuditLog] = None) -> None:
        self._log = log or AuditLog()
        self._last_statuses: dict = {}

    @property
    def log(self) -> AuditLog:
        return self._log

    def observe(self, monitor: Monitor, actor: Optional[str] = None) -> None:
        """Snapshot current pipeline states and record any changes."""
        for pipeline_id, pipeline in monitor.pipelines.items():
            current_status = pipeline.status
            previous_status = self._last_statuses.get(pipeline_id)

            if previous_status is None:
                self._log.record(
                    AuditEvent(
                        event_type=AuditEventType.PIPELINE_REGISTERED,
                        pipeline_id=pipeline_id,
                        details={"initial_status": current_status.value},
                        actor=actor,
                    )
                )
            elif previous_status != current_status:
                self._log.record(
                    AuditEvent(
                        event_type=AuditEventType.STATUS_CHANGE,
                        pipeline_id=pipeline_id,
                        details={
                            "from": previous_status.value,
                            "to": current_status.value,
                        },
                        actor=actor,
                    )
                )

            self._last_statuses[pipeline_id] = current_status

    def record_alert_raised(self, pipeline_id: str, alert_id: str, level: str, actor: Optional[str] = None) -> None:
        self._log.record(
            AuditEvent(
                event_type=AuditEventType.ALERT_RAISED,
                pipeline_id=pipeline_id,
                details={"alert_id": alert_id, "level": level},
                actor=actor,
            )
        )

    def record_alert_resolved(self, pipeline_id: str, alert_id: str, actor: Optional[str] = None) -> None:
        self._log.record(
            AuditEvent(
                event_type=AuditEventType.ALERT_RESOLVED,
                pipeline_id=pipeline_id,
                details={"alert_id": alert_id},
                actor=actor,
            )
        )
