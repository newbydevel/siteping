import smtplib
import json
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional

from siteping.checker import CheckResult
from siteping.config import AppConfig


@dataclass
class NotifyResult:
    success: bool
    method: str
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            return f"[{self.method}] notification sent"
        return f"[{self.method}] notification failed: {self.error}"


def _build_message(result: CheckResult) -> str:
    status = "UP" if result.is_up else "DOWN"
    lines = [
        f"Site status: {status}",
        f"URL: {result.url}",
        f"Status code: {result.status_code or 'N/A'}",
    ]
    if result.error:
        lines.append(f"Error: {result.error}")
    if result.response_time_ms is not None:
        lines.append(f"Response time: {result.response_time_ms:.1f}ms")
    return "\n".join(lines)


def send_email(result: CheckResult, config: AppConfig) -> NotifyResult:
    if not config.email:
        return NotifyResult(success=False, method="email", error="email config missing")

    cfg = config.email
    subject = f"[siteping] {'UP' if result.is_up else 'DOWN'}: {result.url}"
    body = _build_message(result)

    msg = MIMEMultipart()
    msg["From"] = cfg.from_address
    msg["To"] = ", ".join(cfg.to_addresses)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
            if cfg.use_tls:
                server.starttls()
            if cfg.username and cfg.password:
                server.login(cfg.username, cfg.password)
            server.sendmail(cfg.from_address, cfg.to_addresses, msg.as_string())
        return NotifyResult(success=True, method="email")
    except Exception as exc:
        return NotifyResult(success=False, method="email", error=str(exc))


def send_webhook(result: CheckResult, config: AppConfig) -> NotifyResult:
    if not config.webhook:
        return NotifyResult(success=False, method="webhook", error="webhook config missing")

    payload = {
        "url": result.url,
        "is_up": result.is_up,
        "status_code": result.status_code,
        "response_time_ms": result.response_time_ms,
        "error": result.error,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        config.webhook.url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
        return NotifyResult(success=True, method="webhook")
    except urllib.error.URLError as exc:
        return NotifyResult(success=False, method="webhook", error=str(exc))


def notify(result: CheckResult, config: AppConfig) -> list[NotifyResult]:
    results = []
    if config.email:
        results.append(send_email(result, config))
    if config.webhook:
        results.append(send_webhook(result, config))
    return results
