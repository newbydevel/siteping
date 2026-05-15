"""Tests for siteping.alert_throttle."""

from datetime import datetime, timedelta

import pytest

from siteping.alert_throttle import ThrottleState, make_throttle

URL = "https://example.com"


def _now():
    return datetime(2024, 1, 15, 12, 0, 0)


def test_should_send_with_no_history():
    t = make_throttle(cooldown_minutes=30)
    assert t.should_send(URL, now=_now()) is True


def test_should_not_send_immediately_after_alert():
    t = make_throttle(cooldown_minutes=30)
    now = _now()
    t.record_alert(URL, now=now)
    assert t.should_send(URL, now=now) is False


def test_should_not_send_before_cooldown_expires():
    t = make_throttle(cooldown_minutes=30)
    now = _now()
    t.record_alert(URL, now=now)
    later = now + timedelta(minutes=29)
    assert t.should_send(URL, now=later) is False


def test_should_send_after_cooldown_expires():
    t = make_throttle(cooldown_minutes=30)
    now = _now()
    t.record_alert(URL, now=now)
    later = now + timedelta(minutes=30)
    assert t.should_send(URL, now=later) is True


def test_reset_clears_throttle():
    t = make_throttle(cooldown_minutes=30)
    now = _now()
    t.record_alert(URL, now=now)
    t.reset(URL)
    assert t.should_send(URL, now=now) is True


def test_reset_unknown_url_is_safe():
    t = make_throttle(cooldown_minutes=30)
    t.reset("https://unknown.example.com")  # should not raise


def test_time_until_next_when_ready():
    t = make_throttle(cooldown_minutes=30)
    assert t.time_until_next(URL, now=_now()) is None


def test_time_until_next_returns_remaining():
    t = make_throttle(cooldown_minutes=30)
    now = _now()
    t.record_alert(URL, now=now)
    later = now + timedelta(minutes=10)
    remaining = t.time_until_next(URL, now=later)
    assert remaining is not None
    assert remaining == timedelta(minutes=20)


def test_time_until_next_returns_none_when_expired():
    t = make_throttle(cooldown_minutes=30)
    now = _now()
    t.record_alert(URL, now=now)
    later = now + timedelta(minutes=31)
    assert t.time_until_next(URL, now=later) is None


def test_multiple_urls_are_independent():
    url_a = "https://a.example.com"
    url_b = "https://b.example.com"
    t = make_throttle(cooldown_minutes=30)
    now = _now()
    t.record_alert(url_a, now=now)
    assert t.should_send(url_a, now=now) is False
    assert t.should_send(url_b, now=now) is True
