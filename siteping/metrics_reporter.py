"""Format and output metrics as a plain-text report."""
from __future__ import annotations

from typing import List

from siteping.metrics import MetricsStore, SiteMetrics

_HEADER = "{:<45} {:>8} {:>9} {:>10} {:>12}".format(
    "URL", "Checks", "Failures", "Uptime %", "Last ms"
)
_SEP = "-" * 90


def _format_row(m: SiteMetrics) -> str:
    last_ms = f"{m.last_response_ms:.1f}" if m.last_response_ms is not None else "N/A"
    return "{:<45} {:>8} {:>9} {:>9}% {:>12}".format(
        m.url[:45],
        m.total_checks,
        m.total_failures,
        m.uptime_percent,
        last_ms,
    )


def render_metrics(store: MetricsStore) -> str:
    sites = store.all_sites()
    if not sites:
        return "No metrics collected yet."
    lines: List[str] = [_HEADER, _SEP]
    for m in sorted(sites, key=lambda s: s.url):
        lines.append(_format_row(m))
    lines.append(_SEP)
    lines.append(f"Monitor uptime: {store.uptime_seconds:.0f}s")
    return "\n".join(lines)


def print_metrics(store: MetricsStore | None = None) -> None:
    from siteping.metrics import get_store
    store = store or get_store()
    print(render_metrics(store))
