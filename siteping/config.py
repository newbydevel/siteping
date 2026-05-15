"""Configuration loading for siteping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class SiteConfig:
    url: str
    interval: int = 60
    expected_status: int = 200
    timeout: float = 10.0

    def __post_init__(self) -> None:
        if self.interval <= 0:
            raise ValueError(f"interval must be positive, got {self.interval}")
        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive, got {self.timeout}")


@dataclass
class AppConfig:
    sites: List[SiteConfig] = field(default_factory=list)
    email: Optional[dict] = None
    webhook: Optional[dict] = None
    alert_after_failures: int = 1
    summary_interval: str = ""
    state_file: str = ".siteping_state.json"
    retention_days: int = 0  # 0 means no pruning


def load_config(path: str) -> AppConfig:
    """Load and validate configuration from a YAML file."""
    with open(path) as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError("Config file must be a YAML mapping")

    sites = [
        SiteConfig(
            url=s["url"],
            interval=s.get("interval", 60),
            expected_status=s.get("expected_status", 200),
            timeout=s.get("timeout", 10.0),
        )
        for s in raw.get("sites", [])
    ]

    return AppConfig(
        sites=sites,
        email=raw.get("email"),
        webhook=raw.get("webhook"),
        alert_after_failures=raw.get("alert_after_failures", 1),
        summary_interval=raw.get("summary_interval", ""),
        state_file=raw.get("state_file", ".siteping_state.json"),
        retention_days=raw.get("retention_days", 0),
    )
