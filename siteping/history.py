"""Simple check history tracking — stores recent results per URL."""

from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Deque, Dict, List, Optional

from siteping.checker import CheckResult

DEFAULT_HISTORY_FILE = "siteping_history.json"
DEFAULT_MAX_ENTRIES = 50


@dataclass
class HistoryEntry:
    url: str
    ok: bool
    status_code: Optional[int]
    response_time: Optional[float]
    error: Optional[str]
    checked_at: str  # ISO-8601

    @staticmethod
    def from_result(result: CheckResult) -> "HistoryEntry":
        return HistoryEntry(
            url=result.url,
            ok=result.ok,
            status_code=result.status_code,
            response_time=result.response_time,
            error=result.error,
            checked_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        )


class History:
    """In-memory ring-buffer of check results, with JSON persistence."""

    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        self.max_entries = max_entries
        self._store: Dict[str, Deque[HistoryEntry]] = {}

    def record(self, result: CheckResult) -> None:
        entry = HistoryEntry.from_result(result)
        if result.url not in self._store:
            self._store[result.url] = deque(maxlen=self.max_entries)
        self._store[result.url].append(entry)

    def get(self, url: str) -> List[HistoryEntry]:
        return list(self._store.get(url, []))

    def all_urls(self) -> List[str]:
        return list(self._store.keys())

    def save(self, path: str = DEFAULT_HISTORY_FILE) -> None:
        data = {
            url: [asdict(e) for e in entries]
            for url, entries in self._store.items()
        }
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2)

    def load(self, path: str = DEFAULT_HISTORY_FILE) -> None:
        if not os.path.exists(path):
            return
        with open(path) as fh:
            data = json.load(fh)
        for url, entries in data.items():
            self._store[url] = deque(
                (HistoryEntry(**e) for e in entries), maxlen=self.max_entries
            )
