import pytest
import responses
import requests

from siteping.checker import check_url, CheckResult


@responses.activate
def test_check_url_up():
    responses.add(responses.GET, "https://example.com", status=200, body="OK")
    result = check_url("https://example.com")

    assert isinstance(result, CheckResult)
    assert result.is_up is True
    assert result.status_code == 200
    assert result.error is None
    assert result.response_time_ms >= 0
    assert result.url == "https://example.com"


@responses.activate
def test_check_url_unexpected_status():
    responses.add(responses.GET, "https://example.com", status=503)
    result = check_url("https://example.com", expected_status=200)

    assert result.is_up is False
    assert result.status_code == 503
    assert "503" in result.error


@responses.activate
def test_check_url_timeout():
    responses.add(
        responses.GET,
        "https://example.com",
        body=requests.exceptions.Timeout(),
    )
    result = check_url("https://example.com", timeout=5)

    assert result.is_up is False
    assert result.status_code is None
    assert result.error == "timeout"


@responses.activate
def test_check_url_connection_error():
    responses.add(
        responses.GET,
        "https://example.com",
        body=requests.exceptions.ConnectionError("refused"),
    )
    result = check_url("https://example.com")

    assert result.is_up is False
    assert result.status_code is None
    assert result.error is not None


def test_check_result_str_up():
    r = CheckResult(url="https://example.com", status_code=200, response_time_ms=42.5, is_up=True)
    assert "[UP]" in str(r)
    assert "200" in str(r)


def test_check_result_str_down():
    r = CheckResult(url="https://example.com", status_code=None, response_time_ms=10.0, is_up=False, error="timeout")
    assert "[DOWN]" in str(r)
    assert "timeout" in str(r)
