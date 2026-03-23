"""Resolve project root and absolute paths for vault and KMS data."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Repository root: directory containing pyproject.toml."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    return here.parents[2]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
