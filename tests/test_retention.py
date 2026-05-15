"""Tests for siteping.retention."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from siteping.checker import CheckResult
from siteping.history import History, HistoryEntry
from siteping.retention import prune_history, run_retention


def _entry(url: str, age_days: float, up: bool = True) -> HistoryEntry:
    checked_at = datetime.now(tz=timezone.utc) - timedelta(days=age_days)
    result = CheckResult(url=url, up=up, status_code=200 if up else 0,
                         response_time=0.1, error=None)
    entry = HistoryEntry.__new__(HistoryEntry)
    entry.url = url
    entry.up = up
    entry.status_code = result.status_code
    entry.response_time = result.response_time
    entry.error = result.error
    entry.checked_at = checked_at
    return entry


def _history_with(entries: list[HistoryEntry]) -> History:
    h = History(max_entries=1000)
    for e in entries:
        url = e.url
        h._data.setdefault(url, []).append(e)
    return h


def test_prune_removes_old_entries():
    url = "https://example.com"
    h = _history_with([
        _entry(url, age_days=10),
        _entry(url, age_days=3),
        _entry(url, age_days=1),
    ])
    removed = prune_history(h, max_age_days=7)
    assert removed == {url: 1}
    assert len(h.get(url)) == 2


def test_prune_keeps_all_recent_entries():
    url = "https://example.com"
    h = _history_with([_entry(url, age_days=1), _entry(url, age_days=2)])
    removed = prune_history(h, max_age_days=7)
    assert removed == {}
    assert len(h.get(url)) == 2


def test_prune_removes_all_old_entries():
    url = "https://old.example.com"
    h = _history_with([_entry(url, age_days=30), _entry(url, age_days=20)])
    removed = prune_history(h, max_age_days=7)
    assert removed[url] == 2
    assert h.get(url) == []


def test_prune_multiple_urls():
    h = _history_with([
        _entry("https://a.com", age_days=10),
        _entry("https://a.com", age_days=1),
        _entry("https://b.com", age_days=2),
    ])
    removed = prune_history(h, max_age_days=7)
    assert removed == {"https://a.com": 1}


def test_prune_invalid_max_age_raises():
    h = History(max_entries=100)
    with pytest.raises(ValueError):
        prune_history(h, max_age_days=0)


def test_run_retention_no_config():
    config = MagicMock(spec=[])
    h = History(max_entries=100)
    result = run_retention(config, h)
    assert result == {}


def test_run_retention_with_config():
    url = "https://example.com"
    config = MagicMock(retention_days=7)
    h = _history_with([_entry(url, age_days=30)])
    result = run_retention(config, h)
    assert result[url] == 1
