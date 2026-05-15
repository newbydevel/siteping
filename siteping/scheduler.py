"""Scheduler: runs checks on a fixed interval and dispatches alerts."""

from __future__ import annotations

import logging
import time
from typing import Dict

from siteping.checker import CheckResult, check_url
from siteping.config import AppConfig
from siteping.history import History
from siteping.notifier import send_email, send_webhook
from siteping.state import load_state, save_state

log = logging.getLogger(__name__)


def _should_alert(url: str, result: CheckResult, prev_state: Dict[str, bool]) -> bool:
    """Return True when we need to send an alert for this result."""
    was_up = prev_state.get(url, True)
    if not result.ok:
        # alert on first failure OR on continued failure every time
        return True
    if result.ok and not was_up:
        # recovery — alert once
        return True
    return False


def run_checks(config: AppConfig, state: Dict[str, bool], history: History) -> Dict[str, bool]:
    """Check every configured site, send alerts as needed, update state."""
    new_state: Dict[str, bool] = {}
    for site in config.sites:
        result = check_url(site.url, timeout=site.timeout, expected_status=site.expected_status)
        history.record(result)
        log.info("%s", result)

        if _should_alert(site.url, result, state):
            if config.email:
                send_email(result, config)
            if config.webhook:
                send_webhook(result, config)

        new_state[site.url] = result.ok

    return new_state


def start_loop(config: AppConfig, state_path: str = "siteping_state.json",
               history_path: str = "siteping_history.json") -> None:
    """Block forever, running checks every config.interval seconds."""
    history = History()
    history.load(history_path)

    while True:
        state = load_state(state_path)
        state = run_checks(config, state, history)
        save_state(state, state_path)
        history.save(history_path)
        log.debug("Sleeping %ds until next check cycle.", config.interval)
        time.sleep(config.interval)
