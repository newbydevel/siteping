from unittest.mock import MagicMock, patch

import pytest

from siteping.checker import CheckResult
from siteping.scheduler import _should_alert, run_checks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(url: str, is_up: bool, status: int = 200) -> CheckResult:
    return CheckResult(
        url=url,
        is_up=is_up,
        status_code=status if is_up else None,
        response_time=0.1,
        error=None if is_up else "timeout",
    )


# ---------------------------------------------------------------------------
# _should_alert
# ---------------------------------------------------------------------------

def test_should_alert_first_failure():
    result = _result("https://example.com", is_up=False)
    assert _should_alert(result, {}) is True


def test_should_alert_repeated_failure():
    url = "https://example.com"
    prev = {url: _result(url, is_up=False)}
    result = _result(url, is_up=False)
    # Already alerted — don't spam
    assert _should_alert(result, prev) is False


def test_should_not_alert_when_up():
    result = _result("https://example.com", is_up=True)
    assert _should_alert(result, {}) is False


def test_should_alert_transition_up_to_down():
    url = "https://example.com"
    prev = {url: _result(url, is_up=True)}
    result = _result(url, is_up=False)
    assert _should_alert(result, prev) is True


def test_should_not_alert_stable_up():
    url = "https://example.com"
    prev = {url: _result(url, is_up=True)}
    result = _result(url, is_up=True)
    assert _should_alert(result, prev) is False


# ---------------------------------------------------------------------------
# run_checks
# ---------------------------------------------------------------------------

def test_run_checks_returns_current_results():
    fake_site = MagicMock()
    fake_site.url = "https://example.com"

    fake_config = MagicMock()
    fake_config.sites = [fake_site]

    fake_result = _result("https://example.com", is_up=True)

    with patch("siteping.scheduler.check_url", return_value=fake_result) as mock_check, \
         patch("siteping.scheduler.notify") as mock_notify:
        current = run_checks(fake_config, {})

    assert "https://example.com" in current
    assert current["https://example.com"].is_up is True
    mock_notify.assert_not_called()


def test_run_checks_calls_notify_on_failure():
    fake_site = MagicMock()
    fake_site.url = "https://broken.com"

    fake_config = MagicMock()
    fake_config.sites = [fake_site]

    fake_result = _result("https://broken.com", is_up=False)

    with patch("siteping.scheduler.check_url", return_value=fake_result), \
         patch("siteping.scheduler.notify") as mock_notify:
        run_checks(fake_config, {})

    mock_notify.assert_called_once_with(fake_result, fake_config)


def test_run_checks_calls_on_result_callback():
    fake_site = MagicMock()
    fake_site.url = "https://example.com"

    fake_config = MagicMock()
    fake_config.sites = [fake_site]

    fake_result = _result("https://example.com", is_up=True)
    collected = []

    with patch("siteping.scheduler.check_url", return_value=fake_result), \
         patch("siteping.scheduler.notify"):
        run_checks(fake_config, {}, on_result=collected.append)

    assert collected == [fake_result]
