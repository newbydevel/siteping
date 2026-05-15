"""Collect and expose runtime metrics for siteping."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class SiteMetrics:
    url: str
    total_checks: int = 0
    total_failures: int = 0
    consecutive_failures: int = 0
    last_checked: datetime | None = None
    last_status_code: int | None = None
    last_response_ms: float | None = None

    @property
    def uptime_percent(self) -> float:
        if self.total_checks == 0:
            return 100.0
        return round(100.0 * (self.total_checks - self.total_failures) / self.total_checks, 2)

    def __str__(self) -> str:
        return (
            f"{self.url} | checks={self.total_checks} failures={self.total_failures} "
            f"uptime={self.uptime_percent}% last_status={self.last_status_code}"
        )


@dataclass
class MetricsStore:
    _sites: Dict[str, SiteMetrics] = field(default_factory=dict)
    _started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record(self, url: str, status_code: int | None, response_ms: float | None, up: bool) -> None:
        if url not in self._sites:
            self._sites[url] = SiteMetrics(url=url)
        m = self._sites[url]
        m.total_checks += 1
        m.last_checked = datetime.now(timezone.utc)
        m.last_status_code = status_code
        m.last_response_ms = response_ms
        if not up:
            m.total_failures += 1
            m.consecutive_failures += 1
        else:
            m.consecutive_failures = 0

    def get(self, url: str) -> SiteMetrics | None:
        return self._sites.get(url)

    def all_sites(self) -> List[SiteMetrics]:
        return list(self._sites.values())

    @property
    def uptime_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self._started_at).total_seconds()


_global_store = MetricsStore()


def get_store() -> MetricsStore:
    return _global_store


def reset_store() -> None:
    global _global_store
    _global_store = MetricsStore()
