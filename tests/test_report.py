"""Tests for siteping.report."""

from unittest.mock import MagicMock

from siteping.checker import CheckResult
from siteping.history import History
from siteping.report import _avg_response_time, _uptime_percent, build_report


def _make_result(url: str, ok: bool = True, rt: float = 0.2) -> MagicMock:
    r = MagicMock(spec=CheckResult)
    r.url = url
    r.ok = ok
    r.status_code = 200 if ok else 500
    r.response_time = rt
    r.error = None
    return r


def test_uptime_percent_all_up():
    h = History()
    url = "https://example.com"
    for _ in range(4):
        h.record(_make_result(url, ok=True))
    assert _uptime_percent(url, h) == 100.0


def test_uptime_percent_mixed():
    h = History()
    url = "https://example.com"
    h.record(_make_result(url, ok=True))
    h.record(_make_result(url, ok=False))
    assert _uptime_percent(url, h) == 50.0


def test_uptime_percent_no_history():
    h = History()
    assert _uptime_percent("https://nope.com", h) is None


def test_avg_response_time():
    h = History()
    url = "https://example.com"
    h.record(_make_result(url, rt=0.1))
    h.record(_make_result(url, rt=0.3))
    assert _avg_response_time(url, h) == 0.2


def test_avg_response_time_no_history():
    h = History()
    assert _avg_response_time("https://nope.com", h) is None


def test_build_report_no_history():
    h = History()
    report = build_report(h)
    assert "No history" in report


def test_build_report_contains_url():
    h = History()
    url = "https://example.com"
    h.record(_make_result(url, ok=True))
    report = build_report(h)
    assert url in report
    assert "UP" in report


def test_build_report_down_site():
    h = History()
    url = "https://broken.com"
    h.record(_make_result(url, ok=False))
    report = build_report(h)
    assert "DOWN" in report


def test_build_report_shows_uptime_and_avg():
    h = History()
    url = "https://example.com"
    for _ in range(3):
        h.record(_make_result(url, ok=True, rt=0.5))
    report = build_report(h)
    assert "100.0%" in report
    assert "0.5s" in report
