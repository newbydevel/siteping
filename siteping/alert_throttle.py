"""Alert throttling to prevent notification spam.

Tracks when alerts were last sent per URL and suppresses
repeated notifications within a configurable cooldown window.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class ThrottleState:
    last_alerted: Dict[str, datetime] = field(default_factory=dict)
    cooldown_minutes: int = 30

    def should_send(self, url: str, now: Optional[datetime] = None) -> bool:
        """Return True if enough time has passed since the last alert for url."""
        if now is None:
            now = datetime.utcnow()
        last = self.last_alerted.get(url)
        if last is None:
            return True
        return (now - last) >= timedelta(minutes=self.cooldown_minutes)

    def record_alert(self, url: str, now: Optional[datetime] = None) -> None:
        """Mark that an alert was just sent for url."""
        if now is None:
            now = datetime.utcnow()
        self.last_alerted[url] = now

    def reset(self, url: str) -> None:
        """Clear throttle state for url (e.g. when site recovers)."""
        self.last_alerted.pop(url, None)

    def time_until_next(self, url: str, now: Optional[datetime] = None) -> Optional[timedelta]:
        """Return how long until the next alert is allowed, or None if ready."""
        if now is None:
            now = datetime.utcnow()
        last = self.last_alerted.get(url)
        if last is None:
            return None
        elapsed = now - last
        cooldown = timedelta(minutes=self.cooldown_minutes)
        if elapsed >= cooldown:
            return None
        return cooldown - elapsed


def make_throttle(cooldown_minutes: int = 30) -> ThrottleState:
    """Create a new ThrottleState with the given cooldown."""
    return ThrottleState(cooldown_minutes=cooldown_minutes)
