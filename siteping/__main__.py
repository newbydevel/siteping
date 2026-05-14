import argparse
import logging
import sys

from siteping.config import load_config
from siteping.scheduler import start_loop


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="siteping",
        description="Lightweight uptime monitor",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.error("Config file not found: %s", args.config)
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load config: %s", exc)
        return 1

    try:
        start_loop(config)
    except KeyboardInterrupt:
        logger.info("Shutting down.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
