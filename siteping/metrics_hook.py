"""Hook that integrates MetricsStore into the scheduler check loop."""
from __future__ import annotations

from siteping.checker import CheckResult
from siteping.metrics import MetricsStore, get_store


def record_check_result(result: CheckResult, store: MetricsStore | None = None) -> None:
    """Record a CheckResult into the metrics store."""
    store = store or get_store()
    store.record(
        url=result.url,
        status_code=result.status_code,
        response_ms=result.response_ms,
        up=result.up,
    )
