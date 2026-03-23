"""Load YAML config with optional .env overrides for paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import yaml

from kms.app.paths import project_root


def _merge_env(cfg: dict[str, Any]) -> dict[str, Any]:
    root = os.environ.get("KMS_VAULT_ROOT")
    if root:
        cfg.setdefault("vault", {})["root"] = root
    db = os.environ.get("KMS_DATABASE_PATH")
    if db:
        cfg.setdefault("database", {})["path"] = db
    return cfg


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    root = project_root()
    path = config_path or (root / "kms" / "config" / "config.yaml")
    if not path.is_file():
        example = root / "kms" / "config" / "config.example.yaml"
        if example.is_file():
            path = example
        else:
            raise FileNotFoundError(
                f"Config not found: {config_path or 'kms/config/config.yaml'}"
            )
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a mapping")
    cfg: dict[str, Any] = dict(raw)
    _merge_env(cfg)
    return cfg


def abs_path(cfg: Mapping[str, Any], *keys: str) -> Path:
    """Resolve path from nested cfg keys relative to project root."""
    root = project_root()
    node: Any = cfg
    for k in keys:
        if not isinstance(node, Mapping) or k not in node:
            raise KeyError(".".join(keys))
        node = node[k]
    if not isinstance(node, str):
        raise TypeError(f"Expected string path at {'.'.join(keys)}")
    p = Path(node)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def vault_paths(cfg: Mapping[str, Any]) -> dict[str, Path]:
    v = cfg["vault"]
    base = abs_path(cfg, "vault", "root")
    return {
        "root": base,
        "admin": base / v["admin_dir"],
        "inbox": base / v["inbox_dir"],
        "sources_web": base / v["sources_web"],
        "sources_pdf": base / v["sources_pdf"],
        "source_notes": base / v["source_notes"],
        "permanent_notes": base / v.get("permanent_notes", "30_Permanent-Notes"),
        "archive": base / v["archive_dir"],
        "review_queue": base / cfg["paths"]["review_queue_file"],
        "reports": base / cfg["paths"]["daily_report_dir"],
    }
