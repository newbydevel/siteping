"""Simple in-memory + file-backed state store for tracking previous check results."""
import json
import logging
import os
from pathlib import Path

from siteping.checker import CheckResult

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = ".siteping_state.json"


def _result_to_dict(r: CheckResult) -> dict:
    return {
        "url": r.url,
        "is_up": r.is_up,
        "status_code": r.status_code,
        "response_time": r.response_time,
        "error": r.error,
    }


def _dict_to_result(d: dict) -> CheckResult:
    return CheckResult(
        url=d["url"],
        is_up=d["is_up"],
        status_code=d.get("status_code"),
        response_time=d.get("response_time", 0.0),
        error=d.get("error"),
    )


def load_state(path: str = DEFAULT_STATE_FILE) -> dict[str, CheckResult]:
    """Load previous check results from a JSON file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        return {url: _dict_to_result(v) for url, v in data.items()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load state from %s: %s", path, exc)
        return {}


def save_state(
    results: dict[str, CheckResult],
    path: str = DEFAULT_STATE_FILE,
) -> None:
    """Persist current check results to a JSON file."""
    p = Path(path)
    try:
        data = {url: _result_to_dict(r) for url, r in results.items()}
        p.write_text(json.dumps(data, indent=2))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not save state to %s: %s", path, exc)
