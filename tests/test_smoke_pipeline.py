"""Smoke: scan → review → apply on a temporary vault (requires full package)."""

from __future__ import annotations

import sqlite3
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.conftest import copy_kms_for_tests

ROOT = Path(__file__).resolve().parents[1]


def _write_config(tmp: Path, vault: Path, db: Path) -> Path:
    cfg = {
        "vault": {
            "root": str(vault.relative_to(tmp)),
            "admin_dir": "00_Admin",
            "inbox_dir": "00_Inbox",
            "sources_web": "10_Sources/web",
            "sources_pdf": "10_Sources/pdf",
            "source_notes": "20_Source-Notes",
            "archive_dir": "99_Archive",
        },
        "database": {"path": str(db.relative_to(tmp))},
        "paths": {
            "review_queue_file": "00_Admin/review-queue.md",
            "daily_report_dir": "00_Admin/reports",
        },
        "templates": {
            "source_note": "kms/templates/source_note.md.j2",
            "review_queue": "kms/templates/review_queue.md.j2",
        },
        "runtime": {"profile": "local"},
        "logging": {"level": "WARNING", "file": "kms/logs/kms.log"},
        "backup": {"include_sqlite": True, "dest": "kms/backups"},
    }
    cfg_dir = tmp / "kms" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    p = cfg_dir / "config.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = {"PYTHONPATH": str(cwd)}
    if env:
        e.update(env)
    return subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True, check=False)


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    """Mirror kms/ and example-vault under tmp."""
    copy_kms_for_tests(tmp_path / "kms")
    shutil.copytree(ROOT / "example-vault", tmp_path / "vault")
    (tmp_path / "vault" / "10_Sources" / "web").mkdir(parents=True, exist_ok=True)
    (tmp_path / "vault" / "10_Sources" / "pdf").mkdir(parents=True, exist_ok=True)
    (tmp_path / "vault" / "00_Admin" / "reports").mkdir(parents=True, exist_ok=True)
    db = tmp_path / "kms" / "data" / "state.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    _write_config(tmp_path, tmp_path / "vault", db)
    inbox = tmp_path / "vault" / "00_Inbox"
    for child in list(inbox.iterdir()):
        if child.is_dir():
            shutil.rmtree(child)
        elif child.is_file():
            child.unlink()
    (inbox / "note.txt").write_text("hello kms", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text((ROOT / "pyproject.toml").read_text(), encoding="utf-8")
    return tmp_path


def test_scan_make_apply_dry_run(mini_repo: Path) -> None:
    cwd = mini_repo
    py = sys.executable
    r = _run(
        [py, "-m", "kms.scripts.scan_inbox", "--config", str(cwd / "kms" / "config" / "config.yaml")],
        cwd,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    r2 = _run(
        [py, "-m", "kms.scripts.make_review_queue", "--config", str(cwd / "kms" / "config" / "config.yaml")],
        cwd,
    )
    assert r2.returncode == 0, r2.stderr + r2.stdout
    rq = cwd / "vault" / "00_Admin" / "review-queue.md"
    assert rq.is_file()
    text = rq.read_text(encoding="utf-8")
    text = text.replace("decision: pending", "decision: approve", 1)
    rq.write_text(text, encoding="utf-8")
    r3 = _run(
        [
            py,
            "-m",
            "kms.scripts.apply_decisions",
            "--dry-run",
            "--config",
            str(cwd / "kms" / "config" / "config.yaml"),
        ],
        cwd,
    )
    assert r3.returncode == 0, r3.stderr + r3.stdout
    assert (cwd / "vault" / "00_Inbox" / "note.txt").is_file()


def test_apply_twice_idempotent(mini_repo: Path) -> None:
    """Apply moves files; second apply exits 0 without duplicating work."""
    cwd = mini_repo
    py = sys.executable
    cfg = str(cwd / "kms" / "config" / "config.yaml")
    assert _run([py, "-m", "kms.scripts.scan_inbox", "--config", cfg], cwd).returncode == 0
    assert _run([py, "-m", "kms.scripts.make_review_queue", "--config", cfg], cwd).returncode == 0
    rq = cwd / "vault" / "00_Admin" / "review-queue.md"
    text = rq.read_text(encoding="utf-8")
    rq.write_text(text.replace("decision: pending", "decision: approve"), encoding="utf-8")
    r1 = _run([py, "-m", "kms.scripts.apply_decisions", "--config", cfg], cwd)
    assert r1.returncode == 0, r1.stderr + r1.stdout
    assert (cwd / "vault" / "10_Sources" / "web" / "note.txt").is_file()
    r2 = _run([py, "-m", "kms.scripts.apply_decisions", "--config", cfg], cwd)
    assert r2.returncode == 0, r2.stderr + r2.stdout


def test_apply_missing_source_marks_failed(mini_repo: Path) -> None:
    cwd = mini_repo
    py = sys.executable
    cfg = str(cwd / "kms" / "config" / "config.yaml")
    assert _run([py, "-m", "kms.scripts.scan_inbox", "--config", cfg], cwd).returncode == 0
    assert _run([py, "-m", "kms.scripts.make_review_queue", "--config", cfg], cwd).returncode == 0

    rq = cwd / "vault" / "00_Admin" / "review-queue.md"
    text = rq.read_text(encoding="utf-8")
    rq.write_text(text.replace("decision: pending", "decision: approve"), encoding="utf-8")

    source = cwd / "vault" / "00_Inbox" / "note.txt"
    source.unlink()
    r = _run([py, "-m", "kms.scripts.apply_decisions", "--config", cfg], cwd)
    assert r.returncode == 3, r.stderr + r.stdout

    conn = sqlite3.connect(cwd / "kms" / "data" / "state.db")
    status = conn.execute("SELECT status FROM items WHERE path = ?", ("00_Inbox/note.txt",)).fetchone()
    audit_err = conn.execute(
        "SELECT error_message FROM audit_log WHERE action = 'apply_decisions' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert status is not None and status[0] == "failed"
    assert audit_err is not None and "missing source file" in (audit_err[0] or "")


def test_apply_target_collision_marks_failed(mini_repo: Path) -> None:
    cwd = mini_repo
    py = sys.executable
    cfg = str(cwd / "kms" / "config" / "config.yaml")
    assert _run([py, "-m", "kms.scripts.scan_inbox", "--config", cfg], cwd).returncode == 0
    assert _run([py, "-m", "kms.scripts.make_review_queue", "--config", cfg], cwd).returncode == 0

    target = cwd / "vault" / "10_Sources" / "web" / "note.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("already exists", encoding="utf-8")

    rq = cwd / "vault" / "00_Admin" / "review-queue.md"
    text = rq.read_text(encoding="utf-8")
    rq.write_text(text.replace("decision: pending", "decision: approve"), encoding="utf-8")
    r = _run([py, "-m", "kms.scripts.apply_decisions", "--config", cfg], cwd)
    assert r.returncode == 3, r.stderr + r.stdout

    conn = sqlite3.connect(cwd / "kms" / "data" / "state.db")
    status = conn.execute("SELECT status FROM items WHERE path = ?", ("00_Inbox/note.txt",)).fetchone()
    audit_err = conn.execute(
        "SELECT error_message FROM audit_log WHERE action = 'apply_decisions' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert status is not None and status[0] == "failed"
    assert audit_err is not None and "note.txt" in (audit_err[0] or "")
