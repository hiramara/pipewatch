"""Formatters for rendering pipeline reports to various output formats."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipewatch.core.reporter import Report


def _status_icon(status: str) -> str:
    icons = {
        "healthy": "\u2705",
        "degraded": "\u26a0\ufe0f",
        "critical": "\u274c",
        "unknown": "\u2753",
    }
    return icons.get(status.lower(), "\u2022")


def format_text(report: "Report") -> str:
    """Render a Report as a human-readable plain-text string."""
    lines: list[str] = []
    lines.append("=" * 50)
    lines.append(f"PipeWatch Report  [{report.generated_at}]")
    lines.append("=" * 50)
    lines.append(
        f"Pipelines  total={report.total_pipelines}  "
        f"healthy={report.healthy_count}  "
        f"degraded={report.degraded_count}  "
        f"critical={report.critical_count}"
    )
    lines.append("-" * 50)

    for summary in report.pipeline_summaries:
        icon = _status_icon(summary.status)
        score = f"{summary.health_score:.0f}%"
        lines.append(f"  {icon}  {summary.pipeline_name:<30} {summary.status:<10} {score}")
        if summary.active_alerts:
            for alert in summary.active_alerts:
                lines.append(f"       \u2514 [{alert.get('level', '?').upper()}] {alert.get('message', '')}")

    lines.append("=" * 50)
    return "\n".join(lines)


def format_json(report: "Report") -> str:
    """Render a Report as a JSON string."""
    import json

    return json.dumps(report.to_dict(), indent=2, default=str)


def format_csv(report: "Report") -> str:
    """Render pipeline summaries as CSV."""
    import csv
    import io

    output = io.StringIO()
    fieldnames = ["pipeline_name", "status", "health_score", "active_alert_count"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for summary in report.pipeline_summaries:
        writer.writerow(
            {
                "pipeline_name": summary.pipeline_name,
                "status": summary.status,
                "health_score": f"{summary.health_score:.2f}",
                "active_alert_count": len(summary.active_alerts),
            }
        )
    return output.getvalue()


FORMAT_HANDLERS = {
    "text": format_text,
    "json": format_json,
    "csv": format_csv,
}


def render(report: "Report", fmt: str = "text") -> str:
    """Dispatch to the appropriate formatter by name.

    Args:
        report: The Report object to render.
        fmt: One of 'text', 'json', or 'csv'.

    Returns:
        Formatted string representation of the report.

    Raises:
        ValueError: If *fmt* is not a recognised format name.
    """
    handler = FORMAT_HANDLERS.get(fmt.lower())
    if handler is None:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: {list(FORMAT_HANDLERS)}.")
    return handler(report)
