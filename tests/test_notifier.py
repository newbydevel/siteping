import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from typing import Optional

from siteping.checker import CheckResult
from siteping.notifier import send_email, send_webhook, notify, NotifyResult


@dataclass
class FakeEmailConfig:
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    use_tls: bool = True
    from_address: str = "alerts@example.com"
    to_addresses: list = field(default_factory=lambda: ["admin@example.com"])
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class FakeWebhookConfig:
    url: str = "https://hooks.example.com/notify"


@dataclass
class FakeAppConfig:
    email: Optional[FakeEmailConfig] = None
    webhook: Optional[FakeWebhookConfig] = None


DOWN_RESULT = CheckResult(url="https://example.com", is_up=False, status_code=500, error=None, response_time_ms=120.0)
UP_RESULT = CheckResult(url="https://example.com", is_up=True, status_code=200, error=None, response_time_ms=85.0)


def test_send_email_success():
    config = FakeAppConfig(email=FakeEmailConfig())
    with patch("smtplib.SMTP") as mock_smtp:
        instance = mock_smtp.return_value.__enter__.return_value
        result = send_email(DOWN_RESULT, config)
    assert result.success is True
    assert result.method == "email"
    instance.sendmail.assert_called_once()


def test_send_email_no_config():
    config = FakeAppConfig(email=None)
    result = send_email(DOWN_RESULT, config)
    assert result.success is False
    assert "missing" in result.error


def test_send_email_smtp_error():
    config = FakeAppConfig(email=FakeEmailConfig())
    with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        result = send_email(DOWN_RESULT, config)
    assert result.success is False
    assert result.error is not None


def test_send_webhook_success():
    config = FakeAppConfig(webhook=FakeWebhookConfig())
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = send_webhook(UP_RESULT, config)
    assert result.success is True
    assert result.method == "webhook"


def test_send_webhook_no_config():
    config = FakeAppConfig(webhook=None)
    result = send_webhook(UP_RESULT, config)
    assert result.success is False


def test_send_webhook_request_error():
    import urllib.error
    config = FakeAppConfig(webhook=FakeWebhookConfig())
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = send_webhook(DOWN_RESULT, config)
    assert result.success is False
    assert "timeout" in result.error


def test_notify_calls_both():
    config = FakeAppConfig(email=FakeEmailConfig(), webhook=FakeWebhookConfig())
    with patch("siteping.notifier.send_email", return_value=NotifyResult(True, "email")) as me, \
         patch("siteping.notifier.send_webhook", return_value=NotifyResult(True, "webhook")) as mw:
        results = notify(DOWN_RESULT, config)
    assert len(results) == 2
    me.assert_called_once()
    mw.assert_called_once()


def test_notify_result_str():
    ok = NotifyResult(success=True, method="email")
    fail = NotifyResult(success=False, method="webhook", error="connection refused")
    assert "sent" in str(ok)
    assert "failed" in str(fail)
