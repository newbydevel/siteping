import time
import requests
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_TIMEOUT = 10
DEFAULT_EXPECTED_STATUS = 200


@dataclass
class CheckResult:
    url: str
    status_code: Optional[int]
    response_time_ms: float
    is_up: bool
    error: Optional[str] = None
    checked_at: float = field(default_factory=time.time)

    def __str__(self) -> str:
        if self.is_up:
            return f"[UP] {self.url} — {self.status_code} in {self.response_time_ms:.0f}ms"
        return f"[DOWN] {self.url} — {self.error or self.status_code}"


def check_url(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    expected_status: int = DEFAULT_EXPECTED_STATUS,
) -> CheckResult:
    """Perform a single HTTP GET check against a URL."""
    start = time.monotonic()
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed = (time.monotonic() - start) * 1000
        is_up = response.status_code == expected_status
        return CheckResult(
            url=url,
            status_code=response.status_code,
            response_time_ms=elapsed,
            is_up=is_up,
            error=None if is_up else f"unexpected status {response.status_code}",
        )
    except requests.exceptions.Timeout:
        elapsed = (time.monotonic() - start) * 1000
        return CheckResult(
            url=url,
            status_code=None,
            response_time_ms=elapsed,
            is_up=False,
            error="timeout",
        )
    except requests.exceptions.RequestException as exc:
        elapsed = (time.monotonic() - start) * 1000
        return CheckResult(
            url=url,
            status_code=None,
            response_time_ms=elapsed,
            is_up=False,
            error=str(exc),
        )
