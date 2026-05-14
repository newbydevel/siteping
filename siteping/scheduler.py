import time
import logging
from datetime import datetime, timezone
from typing import Callable

from siteping.checker import CheckResult, check_url
from siteping.config import AppConfig, SiteConfig
from siteping.notifier import notify

logger = logging.getLogger(__name__)


def _should_alert(result: CheckResult, previous: dict[str, CheckResult]) -> bool:
    """Return True if we should send an alert for this result."""
    url = result.url
    prev = previous.get(url)

    # Alert on first failure or when status changes from up to down
    if not result.is_up:
        if prev is None or prev.is_up:
            return True
    return False


def run_checks(
    config: AppConfig,
    previous: dict[str, CheckResult],
    on_result: Callable[[CheckResult], None] | None = None,
) -> dict[str, CheckResult]:
    """Run all configured checks and send alerts as needed."""
    current: dict[str, CheckResult] = {}

    for site in config.sites:
        result = check_url(site)
        current[result.url] = result
        logger.info(str(result))

        if on_result:
            on_result(result)

        if _should_alert(result, previous):
            logger.warning("Alert triggered for %s", result.url)
            notify(result, config)

    return current


def start_loop(config: AppConfig) -> None:
    """Blocking loop that runs checks on the configured interval."""
    interval = config.interval_seconds
    logger.info(
        "Starting siteping — checking %d site(s) every %ds",
        len(config.sites),
        interval,
    )

    previous: dict[str, CheckResult] = {}

    while True:
        logger.debug("Running checks at %s", datetime.now(timezone.utc).isoformat())
        previous = run_checks(config, previous)
        time.sleep(interval)
