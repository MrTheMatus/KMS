"""Smoke tests for scripts/ingest_conversations.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {**dict(__import__("os").environ), "PYTHONPATH": str(cwd)}
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ingest_conversations.py"), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def test_ingest_dry_run_skips_huge(tmp_path: Path) -> None:
    src = tmp_path / "in"
    src.mkdir()
    shutil.copy(
        ROOT / "example-vault" / "10_Sources" / "pdf" / "minimal-demo.pdf",
        src / "small.pdf",
    )
    (src / "huge.pdf").write_bytes(b"x" * (2 * 1024 * 1024))
    out = tmp_path / "out"
    r = _run(
        [
            "--source-dir",
            str(src),
            "--target-dir",
            str(out),
            "--max-size-mb",
            "1",
            "--dry-run",
        ],
        tmp_path,
    )
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["skipped"] >= 1
    assert data["ok"] >= 1


def test_ingest_converts_minimal_pdf(tmp_path: Path) -> None:
    src = tmp_path / "in"
    src.mkdir()
    shutil.copy(
        ROOT / "example-vault" / "10_Sources" / "pdf" / "minimal-demo.pdf",
        src / "demo.pdf",
    )
    out = tmp_path / "out"
    r = _run(
        [
            "--source-dir",
            str(src),
            "--target-dir",
            str(out),
            "--converter-pick",
            "best",
        ],
        tmp_path,
    )
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["failed"] == 0
    assert data["ok"] >= 1
    mds = [p for p in out.glob("*.md") if not p.name.startswith("_")]
    assert len(mds) == 1
    text = mds[0].read_text(encoding="utf-8")
    assert "source-note" in text
    assert "conversation" in text
    assert "pick=best scores:" in text
    report = out / "_topics_discovered.md"
    assert report.is_file()
