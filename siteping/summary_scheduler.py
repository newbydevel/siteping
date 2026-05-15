"""Tracks whether a periodic summary is due and triggers delivery."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from siteping.config import AppConfig
from siteping.history import History
from siteping.summary import send_summary

logger = logging.getLogger(__name__)


class SummaryScheduler:
    """Fires a summary at a fixed interval (in minutes)."""

    def __init__(self, interval_minutes: int = 60) -> None:
        if interval_minutes < 1:
            raise ValueError("interval_minutes must be >= 1")
        self.interval: timedelta = timedelta(minutes=interval_minutes)
        self._last_sent: Optional[datetime] = None

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Return True if enough time has elapsed since the last summary."""
        if now is None:
            now = datetime.now(tz=timezone.utc)
        if self._last_sent is None:
            return True
        return (now - self._last_sent) >= self.interval

    def time_until_next(self, now: Optional[datetime] = None) -> timedelta:
        """Return how long until the next summary is due.

        Returns timedelta(0) if a summary is already due.
        """
        if now is None:
            now = datetime.now(tz=timezone.utc)
        if self._last_sent is None:
            return timedelta(0)
        elapsed = now - self._last_sent
        remaining = self.interval - elapsed
        return remaining if remaining > timedelta(0) else timedelta(0)

    def maybe_send(self, config: AppConfig, history: History,
                   now: Optional[datetime] = None) -> bool:
        """Send a summary if one is due. Returns True if a summary was sent."""
        if now is None:
            now = datetime.now(tz=timezone.utc)
        if not self.is_due(now):
            return False
        result = send_summary(config, history)
        self._last_sent = now
        logger.info("Summary dispatched: %s", result)
        return True
