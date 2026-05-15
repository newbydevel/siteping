"""Tests for siteping.metrics_hook."""
from __future__ import annotations

from siteping.checker import CheckResult
from siteping.metrics import MetricsStore
from siteping.metrics_hook import record_check_result


def _result(url="https://example.com", up=True, status_code=200, response_ms=30.0, error=None):
    return CheckResult(
        url=url,
        up=up,
        status_code=status_code,
        response_ms=response_ms,
        error=error,
    )


def test_hook_records_successful_check():
    store = MetricsStore()
    record_check_result(_result(up=True, status_code=200, response_ms=25.0), store=store)
    m = store.get("https://example.com")
    assert m is not None
    assert m.total_checks == 1
    assert m.total_failures == 0
    assert m.last_response_ms == 25.0
    assert m.last_status_code == 200


def test_hook_records_failed_check():
    store = MetricsStore()
    record_check_result(_result(up=False, status_code=503, response_ms=100.0), store=store)
    m = store.get("https://example.com")
    assert m.total_failures == 1
    assert m.consecutive_failures == 1


def test_hook_records_error_check_no_status():
    store = MetricsStore()
    record_check_result(_result(up=False, status_code=None, response_ms=None, error="timeout"), store=store)
    m = store.get("https://example.com")
    assert m.total_failures == 1
    assert m.last_status_code is None
    assert m.last_response_ms is None


def test_hook_multiple_urls():
    store = MetricsStore()
    record_check_result(_result(url="https://a.com", up=True), store=store)
    record_check_result(_result(url="https://b.com", up=False), store=store)
    assert store.get("https://a.com").total_checks == 1
    assert store.get("https://b.com").total_failures == 1


def test_hook_uses_global_store_by_default():
    from siteping.metrics import reset_store, get_store
    reset_store()
    record_check_result(_result())
    m = get_store().get("https://example.com")
    assert m is not None
    assert m.total_checks == 1
    reset_store()
