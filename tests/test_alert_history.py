"""Tests for siteping.alert_history."""

from datetime import datetime, timezone

import pytest

from siteping.alert_history import AlertHistory, AlertRecord


def _now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_record_returns_alert_record():
    ah = AlertHistory()
    rec = ah.record("https://example.com", _now(), "down", status_code=500)
    assert isinstance(rec, AlertRecord)
    assert rec.url == "https://example.com"
    assert rec.alert_type == "down"
    assert rec.status_code == 500
    assert rec.error is None


def test_record_with_error():
    ah = AlertHistory()
    rec = ah.record("https://example.com", _now(), "down", error="timeout")
    assert rec.error == "timeout"
    assert rec.status_code is None


def test_get_unknown_url_returns_empty():
    ah = AlertHistory()
    assert ah.get("https://unknown.com") == []


def test_latest_returns_most_recent():
    ah = AlertHistory()
    t1 = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2024, 6, 1, 11, 0, 0, tzinfo=timezone.utc)
    ah.record("https://example.com", t1, "down", status_code=503)
    ah.record("https://example.com", t2, "recovered", status_code=200)
    latest = ah.latest("https://example.com")
    assert latest is not None
    assert latest.alert_type == "recovered"
    assert latest.timestamp == t2


def test_latest_unknown_url_returns_none():
    ah = AlertHistory()
    assert ah.latest("https://ghost.com") is None


def test_max_per_url_enforced():
    ah = AlertHistory(max_per_url=3)
    url = "https://example.com"
    for i in range(5):
        ah.record(url, _now(), "down", status_code=500 + i)
    records = ah.get(url)
    assert len(records) == 3
    # oldest should have been evicted; last status_code is 504
    assert records[-1].status_code == 504


def test_all_urls_lists_tracked_urls():
    ah = AlertHistory()
    ah.record("https://a.com", _now(), "down")
    ah.record("https://b.com", _now(), "down")
    assert set(ah.all_urls()) == {"https://a.com", "https://b.com"}


def test_clear_removes_url():
    ah = AlertHistory()
    url = "https://example.com"
    ah.record(url, _now(), "down")
    ah.clear(url)
    assert ah.get(url) == []
    assert url not in ah.all_urls()


def test_invalid_max_per_url_raises():
    with pytest.raises(ValueError):
        AlertHistory(max_per_url=0)


def test_str_representation_down():
    rec = AlertRecord(
        url="https://example.com",
        timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        status_code=503,
        error=None,
        alert_type="down",
    )
    s = str(rec)
    assert "DOWN" in s
    assert "https://example.com" in s
    assert "503" in s


def test_str_representation_error():
    rec = AlertRecord(
        url="https://example.com",
        timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        status_code=None,
        error="connection refused",
        alert_type="down",
    )
    s = str(rec)
    assert "connection refused" in s
