"""Tests for kms.app.hashing: SHA-256 file hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path

from kms.app.hashing import sha256_file


def test_sha256_matches_known(tmp_path: Path) -> None:
    p = tmp_path / "sample.txt"
    content = b"hello kms"
    p.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert sha256_file(p) == expected


def test_sha256_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.txt"
    p.write_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert sha256_file(p) == expected


def test_sha256_deterministic(tmp_path: Path) -> None:
    p = tmp_path / "det.txt"
    p.write_text("deterministic content", encoding="utf-8")
    h1 = sha256_file(p)
    h2 = sha256_file(p)
    assert h1 == h2
