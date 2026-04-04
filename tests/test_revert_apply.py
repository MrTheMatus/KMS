"""Smoke tests for revert_apply: apply then revert, verify files and DB state."""

from __future__ import annotations

import sqlite3
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


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, env={"PYTHONPATH": str(cwd)}, capture_output=True, text=True, check=False,
    )


def _find_proposal_id(db_path: Path, item_path_contains: str) -> int:
    """Look up the proposal_id for the item whose path contains the given substring."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT p.id FROM proposals p JOIN items i ON i.id = p.item_id WHERE i.path LIKE ?",
        (f"%{item_path_contains}%",),
    ).fetchone()
    conn.close()
    assert row is not None, f"No proposal found for item matching '{item_path_contains}'"
    return int(row[0])


@pytest.fixture
def applied_repo(tmp_path: Path) -> tuple[Path, str, int]:
    """Set up a repo where scan+review+apply has already run for one file.

    Returns (cwd, cfg_path, proposal_id).
    """
    copy_kms_for_tests(tmp_path / "kms")
    vault = tmp_path / "vault"
    vault.mkdir(exist_ok=True)
    for d in ["00_Inbox", "10_Sources/web", "10_Sources/pdf", "00_Admin/reports",
              "20_Source-Notes", "30_Permanent-Notes"]:
        (vault / d).mkdir(parents=True, exist_ok=True)
    db = tmp_path / "kms" / "data" / "state.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    _write_config(tmp_path, vault, db)
    (vault / "00_Inbox" / "revert-test.txt").write_text("revert me", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text((ROOT / "pyproject.toml").read_text(), encoding="utf-8")

    py = sys.executable
    cfg = str(tmp_path / "kms" / "config" / "config.yaml")
    assert _run([py, "-m", "kms.scripts.scan_inbox", "--config", cfg], tmp_path).returncode == 0
    assert _run([py, "-m", "kms.scripts.make_review_queue", "--config", cfg], tmp_path).returncode == 0

    rq = vault / "00_Admin" / "review-queue.md"
    text = rq.read_text(encoding="utf-8")
    rq.write_text(text.replace("decision: pending", "decision: approve"), encoding="utf-8")

    r = _run([py, "-m", "kms.scripts.apply_decisions", "--config", cfg], tmp_path)
    assert r.returncode == 0, r.stderr + r.stdout

    pid = _find_proposal_id(db, "revert-test")
    return tmp_path, cfg, pid


def test_revert_restores_file_to_inbox(applied_repo: tuple[Path, str, int]) -> None:
    cwd, cfg, pid = applied_repo
    py = sys.executable

    assert (cwd / "vault" / "10_Sources" / "web" / "revert-test.txt").is_file()
    assert not (cwd / "vault" / "00_Inbox" / "revert-test.txt").is_file()

    r = _run([py, "-m", "kms.scripts.revert_apply", "--proposal-id", str(pid), "--config", cfg], cwd)
    assert r.returncode == 0, r.stderr + r.stdout

    assert (cwd / "vault" / "00_Inbox" / "revert-test.txt").is_file()
    assert not (cwd / "vault" / "10_Sources" / "web" / "revert-test.txt").is_file()


def test_revert_cleans_db_rows(applied_repo: tuple[Path, str, int]) -> None:
    cwd, cfg, pid = applied_repo
    py = sys.executable

    _run([py, "-m", "kms.scripts.revert_apply", "--proposal-id", str(pid), "--config", cfg], cwd)

    conn = sqlite3.connect(cwd / "kms" / "data" / "state.db")
    art = conn.execute("SELECT id FROM artifacts WHERE proposal_id = ?", (pid,)).fetchone()
    exe = conn.execute("SELECT id FROM executions WHERE proposal_id = ?", (pid,)).fetchone()
    item = conn.execute(
        "SELECT status FROM items WHERE id = (SELECT item_id FROM proposals WHERE id = ?)", (pid,)
    ).fetchone()
    audit_row = conn.execute(
        "SELECT action FROM audit_log WHERE action = 'revert_apply' AND entity_id = ?", (str(pid),)
    ).fetchone()
    conn.close()

    assert art is None, "artifact row should be deleted after revert"
    assert exe is None, "execution row should be deleted after revert"
    assert item is not None and item[0] == "new", "item status should be reset to 'new'"
    assert audit_row is not None, "revert should create an audit_log entry"


def test_revert_dry_run_does_not_move(applied_repo: tuple[Path, str, int]) -> None:
    cwd, cfg, pid = applied_repo
    py = sys.executable

    r = _run([py, "-m", "kms.scripts.revert_apply", "--proposal-id", str(pid), "--dry-run", "--config", cfg], cwd)
    assert r.returncode == 0, r.stderr + r.stdout

    assert (cwd / "vault" / "10_Sources" / "web" / "revert-test.txt").is_file()
    assert not (cwd / "vault" / "00_Inbox" / "revert-test.txt").is_file()


def test_revert_nonexistent_proposal_returns_error(applied_repo: tuple[Path, str, int]) -> None:
    cwd, cfg, _pid = applied_repo
    py = sys.executable

    r = _run([py, "-m", "kms.scripts.revert_apply", "--proposal-id", "9999", "--config", cfg], cwd)
    assert r.returncode == 2
