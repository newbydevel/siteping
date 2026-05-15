"""Periodic summary report generation and delivery."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from siteping.config import AppConfig
from siteping.history import History
from siteping.notifier import send_email, send_webhook
from siteping.report import build_report


@dataclass
class SummaryResult:
    sent_email: bool = False
    sent_webhook: bool = False
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.error:
            return f"Summary failed: {self.error}"
        channels = []
        if self.sent_email:
            channels.append("email")
        if self.sent_webhook:
            channels.append("webhook")
        return f"Summary sent via: {', '.join(channels) or 'none'}"


def _format_summary(report: dict, generated_at: datetime) -> str:
    """Format a report dict into a human-readable summary string."""
    ts = generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [f"Siteping Summary Report — {ts}", ""]
    for url, stats in report.items():
        uptime = stats.get("uptime_percent", 0.0)
        avg_ms = stats.get("avg_response_ms")
        avg_str = f"{avg_ms:.0f}ms" if avg_ms is not None else "n/a"
        lines.append(f"  {url}")
        lines.append(f"    Uptime : {uptime:.1f}%")
        lines.append(f"    Avg RT : {avg_str}")
    return "\n".join(lines)


def send_summary(config: AppConfig, history: History) -> SummaryResult:
    """Build a summary from history and dispatch it via configured channels."""
    result = SummaryResult()
    try:
        report = build_report(history)
        now = datetime.now(tz=timezone.utc)
        body = _format_summary(report, now)
        subject = f"Siteping Summary — {now.strftime('%Y-%m-%d')}"

        if config.email:
            nr = send_email(subject, body, config)
            result.sent_email = nr.success

        if config.webhook:
            payload = {"type": "summary", "report": report,
                       "generated_at": now.isoformat()}
            nr = send_webhook(payload, config)
            result.sent_webhook = nr.success

    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)

    return result
