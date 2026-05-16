"""Tracks a log of past alerts sent for each URL."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class AlertRecord:
    url: str
    timestamp: datetime
    status_code: Optional[int]
    error: Optional[str]
    alert_type: str  # 'down' | 'recovered' | 'summary'

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if self.error:
            detail = f"error={self.error}"
        else:
            detail = f"status={self.status_code}"
        return f"[{ts}] {self.alert_type.upper()} {self.url} ({detail})"


class AlertHistory:
    def __init__(self, max_per_url: int = 50) -> None:
        if max_per_url < 1:
            raise ValueError("max_per_url must be at least 1")
        self._max = max_per_url
        self._records: Dict[str, List[AlertRecord]] = {}

    def record(
        self,
        url: str,
        timestamp: datetime,
        alert_type: str,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
    ) -> AlertRecord:
        entry = AlertRecord(
            url=url,
            timestamp=timestamp,
            status_code=status_code,
            error=error,
            alert_type=alert_type,
        )
        bucket = self._records.setdefault(url, [])
        bucket.append(entry)
        if len(bucket) > self._max:
            bucket.pop(0)
        return entry

    def get(self, url: str) -> List[AlertRecord]:
        return list(self._records.get(url, []))

    def all_urls(self) -> List[str]:
        return list(self._records.keys())

    def latest(self, url: str) -> Optional[AlertRecord]:
        records = self._records.get(url)
        return records[-1] if records else None

    def clear(self, url: str) -> None:
        self._records.pop(url, None)
