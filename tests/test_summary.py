"""Tests for siteping.summary."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from siteping.checker import CheckResult
from siteping.history import History
from siteping.summary import SummaryResult, _format_summary, send_summary
from datetime import datetime, timezone


def _make_config(email=True, webhook=False):
    cfg = MagicMock()
    cfg.email = MagicMock() if email else None
    cfg.webhook = MagicMock() if webhook else None
    return cfg


def _populated_history() -> History:
    h = History(max_entries=10)
    r = CheckResult(url="https://example.com", status_code=200,
                    response_time_ms=120.0, is_up=True, error=None)
    h.record(r)
    return h


def test_summary_result_str_success():
    sr = SummaryResult(sent_email=True, sent_webhook=True)
    assert "email" in str(sr)
    assert "webhook" in str(sr)


def test_summary_result_str_error():
    sr = SummaryResult(error="boom")
    assert "failed" in str(sr).lower()


def test_format_summary_contains_url():
    report = {"https://example.com": {"uptime_percent": 100.0, "avg_response_ms": 95.5}}
    now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    text = _format_summary(report, now)
    assert "https://example.com" in text
    assert "100.0%" in text
    assert "96ms" in text  # rounded
    assert "2024-01-15" in text


def test_format_summary_no_avg():
    report = {"https://a.com": {"uptime_percent": 50.0, "avg_response_ms": None}}
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    text = _format_summary(report, now)
    assert "n/a" in text


@patch("siteping.summary.send_email")
def test_send_summary_email(mock_email):
    mock_email.return_value = MagicMock(success=True)
    config = _make_config(email=True, webhook=False)
    history = _populated_history()
    result = send_summary(config, history)
    assert result.sent_email is True
    assert result.sent_webhook is False
    mock_email.assert_called_once()


@patch("siteping.summary.send_webhook")
def test_send_summary_webhook(mock_hook):
    mock_hook.return_value = MagicMock(success=True)
    config = _make_config(email=False, webhook=True)
    history = _populated_history()
    result = send_summary(config, history)
    assert result.sent_webhook is True
    assert result.sent_email is False


@patch("siteping.summary.build_report", side_effect=RuntimeError("db gone"))
def test_send_summary_captures_exception(mock_report):
    config = _make_config()
    history = History()
    result = send_summary(config, history)
    assert result.error is not None
    assert "db gone" in result.error
