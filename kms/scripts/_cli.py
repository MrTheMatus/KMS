"""Shared CLI helpers: config, logging, argparse."""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

from kms.app.config import abs_path, load_config
from kms.app.paths import ensure_dir, project_root


def build_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.yaml (default: kms/config/config.yaml or config.example.yaml)",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="DEBUG logging")
    return p


def add_dry_run(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without mutating vault or database (where supported)",
    )


def setup_logging(cfg: dict[str, Any], verbose: bool) -> None:
    level = (
        logging.DEBUG
        if verbose
        else getattr(
            logging,
            str(cfg.get("logging", {}).get("level", "INFO")).upper(),
            logging.INFO,
        )
    )
    log_file = cfg.get("logging", {}).get("file")
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        path = abs_path(cfg, "logging", "file")
        ensure_dir(path.parent)
        max_bytes = int(cfg.get("logging", {}).get("max_bytes", 5_242_880))  # 5 MB
        backup_count = int(cfg.get("logging", {}).get("backup_count", 3))
        rotating = logging.handlers.RotatingFileHandler(
            path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handlers.append(rotating)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def load_setup_logging(args: argparse.Namespace) -> dict[str, Any]:
    cfg = load_config(args.config)
    setup_logging(cfg, args.verbose)

    # Validate config — print warnings, abort on errors
    from kms.app.config_validator import print_validation, validate_config

    issues = validate_config(cfg, project_root())
    has_errors = print_validation(issues)
    if has_errors:
        raise SystemExit("Config validation failed. Fix errors above and retry.")

    return cfg
