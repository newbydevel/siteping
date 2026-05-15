"""Tests for siteping.summary_scheduler."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from siteping.summary_scheduler import SummaryScheduler


def _now():
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_invalid_interval():
    with pytest.raises(ValueError):
        SummaryScheduler(interval_minutes=0)


def test_is_due_initially():
    sched = SummaryScheduler(interval_minutes=60)
    assert sched.is_due(_now()) is True


def test_is_not_due_immediately_after_send():
    sched = SummaryScheduler(interval_minutes=60)
    config = MagicMock()
    history = MagicMock()
    now = _now()
    with patch("siteping.summary_scheduler.send_summary") as mock_send:
        mock_send.return_value = MagicMock()
        sched.maybe_send(config, history, now=now)
    assert sched.is_due(now) is False


def test_is_due_after_interval_elapsed():
    sched = SummaryScheduler(interval_minutes=30)
    config = MagicMock()
    history = MagicMock()
    now = _now()
    with patch("siteping.summary_scheduler.send_summary") as mock_send:
        mock_send.return_value = MagicMock()
        sched.maybe_send(config, history, now=now)
    later = now + timedelta(minutes=31)
    assert sched.is_due(later) is True


def test_maybe_send_returns_true_when_due():
    sched = SummaryScheduler(interval_minutes=60)
    config = MagicMock()
    history = MagicMock()
    with patch("siteping.summary_scheduler.send_summary") as mock_send:
        mock_send.return_value = MagicMock()
        sent = sched.maybe_send(config, history, now=_now())
    assert sent is True


def test_maybe_send_returns_false_when_not_due():
    sched = SummaryScheduler(interval_minutes=60)
    config = MagicMock()
    history = MagicMock()
    now = _now()
    with patch("siteping.summary_scheduler.send_summary") as mock_send:
        mock_send.return_value = MagicMock()
        sched.maybe_send(config, history, now=now)
        sent = sched.maybe_send(config, history, now=now)
    assert sent is False
