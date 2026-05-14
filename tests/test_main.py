import sys
from unittest.mock import MagicMock, patch

import pytest

from siteping.__main__ import main


def test_main_missing_config(tmp_path):
    result = main(["-c", str(tmp_path / "nonexistent.yaml")])
    assert result == 1


def test_main_invalid_config(tmp_path):
    bad_config = tmp_path / "config.yaml"
    bad_config.write_text("not: valid: yaml: [")

    result = main(["-c", str(bad_config)])
    assert result == 1


def test_main_runs_loop_then_keyboard_interrupt(tmp_path):
    good_config = tmp_path / "config.yaml"
    good_config.write_text(
        "interval_seconds: 30\n"
        "sites:\n"
        "  - url: https://example.com\n"
        "    expected_status: 200\n"
        "    timeout: 10\n"
    )

    with patch("siteping.__main__.start_loop", side_effect=KeyboardInterrupt):
        result = main(["-c", str(good_config)])

    assert result == 0


def test_main_verbose_flag_accepted(tmp_path):
    good_config = tmp_path / "config.yaml"
    good_config.write_text(
        "interval_seconds: 30\n"
        "sites:\n"
        "  - url: https://example.com\n"
        "    expected_status: 200\n"
        "    timeout: 10\n"
    )

    with patch("siteping.__main__.start_loop", side_effect=KeyboardInterrupt):
        result = main(["-c", str(good_config), "--verbose"])

    assert result == 0
