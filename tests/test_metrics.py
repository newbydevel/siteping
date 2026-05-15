"""Tests for siteping.metrics and siteping.metrics_reporter."""
from __future__ import annotations

import pytest

from siteping.metrics import MetricsStore
from siteping.metrics_reporter import render_metrics


def _store_with(*records):
    """records: list of (url, status_code, response_ms, up)"""
    store = MetricsStore()
    for url, status_code, response_ms, up in records:
        store.record(url, status_code, response_ms, up)
    return store


def test_record_increments_checks():
    store = MetricsStore()
    store.record("https://example.com", 200, 42.0, True)
    m = store.get("https://example.com")
    assert m is not None
    assert m.total_checks == 1
    assert m.total_failures == 0


def test_record_failure_increments_failures():
    store = MetricsStore()
    store.record("https://example.com", 500, 10.0, False)
    m = store.get("https://example.com")
    assert m.total_failures == 1
    assert m.consecutive_failures == 1


def test_consecutive_failures_reset_on_recovery():
    store = MetricsStore()
    store.record("https://x.com", 500, 5.0, False)
    store.record("https://x.com", 500, 5.0, False)
    store.record("https://x.com", 200, 5.0, True)
    m = store.get("https://x.com")
    assert m.consecutive_failures == 0
    assert m.total_failures == 2


def test_uptime_percent_all_up():
    store = _store_with(
        ("https://a.com", 200, 10.0, True),
        ("https://a.com", 200, 10.0, True),
    )
    assert store.get("https://a.com").uptime_percent == 100.0


def test_uptime_percent_mixed():
    store = _store_with(
        ("https://b.com", 200, 10.0, True),
        ("https://b.com", 500, 10.0, False),
    )
    assert store.get("https://b.com").uptime_percent == 50.0


def test_uptime_percent_no_checks():
    store = MetricsStore()
    store._sites["https://c.com"] = __import__("siteping.metrics", fromlist=["SiteMetrics"]).SiteMetrics(url="https://c.com")
    assert store.get("https://c.com").uptime_percent == 100.0


def test_all_sites_returns_all():
    store = _store_with(
        ("https://a.com", 200, 5.0, True),
        ("https://b.com", 200, 5.0, True),
    )
    urls = {m.url for m in store.all_sites()}
    assert urls == {"https://a.com", "https://b.com"}


def test_get_unknown_url_returns_none():
    store = MetricsStore()
    assert store.get("https://unknown.com") is None


def test_render_metrics_empty():
    store = MetricsStore()
    output = render_metrics(store)
    assert "No metrics" in output


def test_render_metrics_contains_url():
    store = _store_with(("https://example.com", 200, 55.3, True))
    output = render_metrics(store)
    assert "https://example.com" in output
    assert "100.0" in output


def test_render_metrics_shows_monitor_uptime():
    store = MetricsStore()
    store.record("https://z.com", 200, 1.0, True)
    output = render_metrics(store)
    assert "Monitor uptime" in output
