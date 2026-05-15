"""Tests for siteping.history."""

import json
import os
from unittest.mock import MagicMock

import pytest

from siteping.checker import CheckResult
from siteping.history import History, HistoryEntry


def _make_result(url: str, ok: bool = True, status_code: int = 200) -> CheckResult:
    r = MagicMock(spec=CheckResult)
    r.url = url
    r.ok = ok
    r.status_code = status_code
    r.response_time = 0.123
    r.error = None if ok else "timeout"
    return r


def test_record_and_retrieve():
    h = History()
    result = _make_result("https://example.com")
    h.record(result)
    entries = h.get("https://example.com")
    assert len(entries) == 1
    assert entries[0].ok is True
    assert entries[0].url == "https://example.com"


def test_max_entries_respected():
    h = History(max_entries=3)
    url = "https://example.com"
    for _ in range(5):
        h.record(_make_result(url))
    assert len(h.get(url)) == 3


def test_get_unknown_url_returns_empty():
    h = History()
    assert h.get("https://nope.example") == []


def test_all_urls():
    h = History()
    h.record(_make_result("https://a.com"))
    h.record(_make_result("https://b.com"))
    assert set(h.all_urls()) == {"https://a.com", "https://b.com"}


def test_save_and_load(tmp_path):
    path = str(tmp_path / "hist.json")
    h = History()
    h.record(_make_result("https://example.com", ok=False, status_code=500))
    h.save(path)

    h2 = History()
    h2.load(path)
    entries = h2.get("https://example.com")
    assert len(entries) == 1
    assert entries[0].ok is False
    assert entries[0].status_code == 500


def test_load_missing_file_is_noop(tmp_path):
    h = History()
    h.load(str(tmp_path / "nonexistent.json"))  # should not raise
    assert h.all_urls() == []


def test_history_entry_from_result():
    result = _make_result("https://example.com")
    entry = HistoryEntry.from_result(result)
    assert entry.url == "https://example.com"
    assert entry.checked_at.endswith("Z")


def test_save_creates_valid_json(tmp_path):
    path = str(tmp_path / "hist.json")
    h = History()
    h.record(_make_result("https://x.com"))
    h.save(path)
    with open(path) as fh:
        data = json.load(fh)
    assert "https://x.com" in data
    assert isinstance(data["https://x.com"], list)
