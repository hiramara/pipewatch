"""Wraps a notifier and suppresses alerts that exceed the rate limit."""

from __future__ import annotations

from typing import List

from pipewatch.core.alert import Alert
from pipewatch.core.notifier import NotificationChannel
from pipewatch.core.rate_limiter import RateLimiter


class RateLimitFilter:
    """Decorator around a NotificationChannel that applies rate limiting."""

    def __init__(self, channel: NotificationChannel, limiter: RateLimiter) -> None:
        self._channel = channel
        self._limiter = limiter
        self._suppressed: List[Alert] = []

    @property
    def suppressed(self) -> List[Alert]:
        """Alerts that were blocked by the rate limiter."""
        return list(self._suppressed)

    def send(self, alert: Alert) -> bool:
        """Send the alert if within rate limit; otherwise suppress it.

        Returns True if the alert was forwarded, False if suppressed.
        """
        pipeline_name = alert.pipeline_name
        if self._limiter.is_allowed(pipeline_name):
            self._channel.send(alert)
            return True
        self._suppressed.append(alert)
        return False

    def clear_suppressed(self) -> None:
        """Clear the list of suppressed alerts."""
        self._suppressed.clear()

    def reset_pipeline(self, pipeline_name: str) -> None:
        """Reset rate-limit window for a pipeline and clear its suppressions."""
        self._limiter.reset(pipeline_name)
        self._suppressed = [
            a for a in self._suppressed if a.pipeline_name != pipeline_name
        ]
