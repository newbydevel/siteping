"""Generate a plain-text summary report from History."""

from __future__ import annotations

from typing import Optional

from siteping.history import History


def _uptime_percent(url: str, history: History) -> Optional[float]:
    entries = history.get(url)
    if not entries:
        return None
    ok_count = sum(1 for e in entries if e.ok)
    return round(ok_count / len(entries) * 100, 1)


def _avg_response_time(url: str, history: History) -> Optional[float]:
    entries = [e for e in history.get(url) if e.response_time is not None]
    if not entries:
        return None
    return round(sum(e.response_time for e in entries) / len(entries), 3)


def build_report(history: History) -> str:
    """Return a human-readable uptime summary for all tracked URLs."""
    urls = history.all_urls()
    if not urls:
        return "No history recorded yet."

    lines = ["=== SitePing Report ===", ""]
    for url in sorted(urls):
        entries = history.get(url)
        uptime = _uptime_percent(url, history)
        avg_rt = _avg_response_time(url, history)
        last = entries[-1] if entries else None
        status_str = "UP" if (last and last.ok) else "DOWN"

        lines.append(f"  {url}")
        lines.append(f"    Status      : {status_str}")
        lines.append(f"    Uptime      : {uptime}% ({len(entries)} checks)")
        if avg_rt is not None:
            lines.append(f"    Avg resp    : {avg_rt}s")
        if last:
            lines.append(f"    Last check  : {last.checked_at}")
        lines.append("")

    return "\n".join(lines)
