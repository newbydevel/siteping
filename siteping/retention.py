"""Prune old history entries and state beyond a configurable retention window."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from siteping.history import History

if TYPE_CHECKING:
    from siteping.config import AppConfig


def prune_history(history: History, max_age_days: int) -> dict[str, int]:
    """Remove entries older than *max_age_days* from every URL bucket.

    Returns a mapping of url -> number of entries removed.
    """
    if max_age_days <= 0:
        raise ValueError("max_age_days must be a positive integer")

    cutoff: datetime = datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)
    removed: dict[str, int] = {}

    for url in history.all_urls():
        entries = history.get(url)
        kept = [e for e in entries if e.checked_at >= cutoff]
        dropped = len(entries) - len(kept)
        if dropped:
            history._data[url] = kept
            removed[url] = dropped

    return removed


def run_retention(config: "AppConfig", history: History) -> dict[str, int]:
    """Run pruning if retention is configured; return counts of removed entries."""
    max_age_days: int = getattr(config, "retention_days", 0)
    if not max_age_days:
        return {}
    return prune_history(history, max_age_days)
