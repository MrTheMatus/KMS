"""Shared test helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copy_kms_for_tests(dest: Path) -> None:
    """Copy ``kms/`` without SQLite files so temp repos do not inherit a dev DB."""
    shutil.copytree(
        ROOT / "kms",
        dest,
        ignore=lambda _dir, names: {n for n in names if n.endswith(".db")},
    )
