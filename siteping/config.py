import os
from dataclasses import dataclass, field
from typing import List

import yaml


@dataclass
class SiteConfig:
    url: str
    timeout: int = 10
    expected_status: int = 200
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = self.url


@dataclass
class AppConfig:
    sites: List[SiteConfig] = field(default_factory=list)
    interval_seconds: int = 60
    alert_email: str = ""
    alert_webhook: str = ""


def load_config(path: str = "config.yaml") -> AppConfig:
    """Load and parse the YAML configuration file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError("Config file must be a YAML mapping")

    sites = [
        SiteConfig(
            url=site["url"],
            timeout=site.get("timeout", 10),
            expected_status=site.get("expected_status", 200),
            name=site.get("name", ""),
        )
        for site in raw.get("sites", [])
    ]

    return AppConfig(
        sites=sites,
        interval_seconds=raw.get("interval_seconds", 60),
        alert_email=raw.get("alert_email", ""),
        alert_webhook=raw.get("alert_webhook", ""),
    )
