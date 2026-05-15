"""Tests for siteping.dashboard."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from siteping.checker import CheckResult
from siteping.history import History, HistoryEntry
from siteping.dashboard import DashboardRow, build_dashboard, render_dashboard


def _make_entry(url: str, status: str, code: int | None = 200, ms: float = 120.0) -> HistoryEntry:
    result = CheckResult(
        url=url,
        status=status,
        status_code=code,
        response_time_ms=ms,
        error=None,
    )
    return HistoryEntry.from_result(result)


def _history_with(*entries_by_url: tuple) -> History:
    """Build a History pre-populated with (url, entry) pairs."""
    h = History(max_entries=50)
    for url, entry in entries_by_url:
        h._data[url] = h._data.get(url, []) + [entry]
    return h


def test_build_dashboard_empty():
    h = History(max_entries=50)
    rows = build_dashboard(h)
    assert rows == []


def test_build_dashboard_single_up_site():
    url = "https://example.com"
    entry = _make_entry(url, "up", code=200, ms=80.0)
    h = _history_with((url, entry))
    rows = build_dashboard(h)
    assert len(rows) == 1
    row = rows[0]
    assert row.url == url
    assert row.status == "up"
    assert row.last_status_code == 200
    assert row.consecutive_failures == 0
    assert row.uptime_percent == 100.0
    assert row.avg_response_ms == pytest.approx(80.0)


def test_build_dashboard_consecutive_failures():
    url = "https://broken.com"
    entries = [
        _make_entry(url, "up"),
        _make_entry(url, "down", code=500),
        _make_entry(url, "down", code=500),
    ]
    h = History(max_entries=50)
    h._data[url] = entries
    rows = build_dashboard(h)
    assert rows[0].consecutive_failures == 2
    assert rows[0].status == "down"


def test_dashboard_row_str_up():
    row = DashboardRow(
        url="https://example.com",
        status="up",
        uptime_percent=99.5,
        avg_response_ms=45.3,
        last_status_code=200,
        consecutive_failures=0,
    )
    text = str(row)
    assert "✅" in text
    assert "99.5%" in text
    assert "200" in text


def test_dashboard_row_str_down():
    row = DashboardRow(
        url="https://down.com",
        status="down",
        uptime_percent=50.0,
        avg_response_ms=0.0,
        last_status_code=None,
        consecutive_failures=3,
    )
    text = str(row)
    assert "❌" in text
    assert "N/A" in text
    assert "failures=3" in text


def test_render_dashboard_no_sites():
    h = History(max_entries=50)
    output = render_dashboard(h)
    assert "No sites monitored" in output


def test_render_dashboard_includes_header():
    url = "https://example.com"
    entry = _make_entry(url, "up")
    h = History(max_entries=50)
    h._data[url] = [entry]
    output = render_dashboard(h)
    assert "SitePing Dashboard" in output
    assert url in output
