"""Simple text-based dashboard summary for siteping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from siteping.history import History
from siteping.report import build_report


@dataclass
class DashboardRow:
    url: str
    status: str
    uptime_percent: float
    avg_response_ms: float
    last_status_code: int | None
    consecutive_failures: int

    def __str__(self) -> str:
        status_icon = "✅" if self.status == "up" else "❌"
        code_str = str(self.last_status_code) if self.last_status_code else "N/A"
        return (
            f"{status_icon} {self.url:<45} "
            f"uptime={self.uptime_percent:5.1f}%  "
            f"avg={self.avg_response_ms:7.1f}ms  "
            f"code={code_str}  "
            f"failures={self.consecutive_failures}"
        )


def build_dashboard(history: History) -> List[DashboardRow]:
    """Build a list of DashboardRow objects from current history."""
    rows: List[DashboardRow] = []
    for url in history.all_urls():
        report = build_report(url, history)
        entries = history.get(url)
        last_entry = entries[-1] if entries else None
        last_code = last_entry.status_code if last_entry else None
        current_status = last_entry.status if last_entry else "unknown"

        consecutive = 0
        for entry in reversed(entries):
            if entry.status == "down":
                consecutive += 1
            else:
                break

        rows.append(
            DashboardRow(
                url=url,
                status=current_status,
                uptime_percent=report["uptime_percent"],
                avg_response_ms=report["avg_response_ms"],
                last_status_code=last_code,
                consecutive_failures=consecutive,
            )
        )
    return rows


def render_dashboard(history: History) -> str:
    """Render the full dashboard as a printable string."""
    rows = build_dashboard(history)
    if not rows:
        return "No sites monitored yet."

    lines = [
        "=" * 80,
        " SitePing Dashboard",
        "=" * 80,
    ]
    for row in rows:
        lines.append(str(row))
    lines.append("=" * 80)
    return "\n".join(lines)
