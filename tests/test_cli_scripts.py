"""CLI smoke tests for scripts not covered by other test files:
verify_integrity, daily_report, generate_source_note."""

from __future__ import annotations

import subprocess
import sqlite3
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
            "permanent_notes": "30_Permanent-Notes",
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


@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    copy_kms_for_tests(tmp_path / "kms")
    vault = tmp_path / "vault"
    vault.mkdir()
    for d in ["00_Inbox", "10_Sources/web", "10_Sources/pdf", "00_Admin/reports",
              "20_Source-Notes", "30_Permanent-Notes"]:
        (vault / d).mkdir(parents=True, exist_ok=True)
    db = tmp_path / "kms" / "data" / "state.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    _write_config(tmp_path, vault, db)
    (tmp_path / "pyproject.toml").write_text((ROOT / "pyproject.toml").read_text(), encoding="utf-8")
    return tmp_path


# --------------- verify_integrity ---------------

class TestVerifyIntegrity:
    def test_clean_state_returns_0(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.verify_integrity", "--config", cfg], mini_repo)
        assert r.returncode == 0
        assert "consistent" in r.stdout.lower() or "passed" in r.stdout.lower()

    def test_orphan_inbox_file_returns_1(self, mini_repo: Path) -> None:
        (mini_repo / "vault" / "00_Inbox" / "orphan.txt").write_text("no db entry", encoding="utf-8")
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.verify_integrity", "--config", cfg], mini_repo)
        assert r.returncode == 1
        assert "orphan" in r.stdout.lower() or "not in db" in r.stdout.lower()

    def test_json_output(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.verify_integrity", "--json", "--config", cfg], mini_repo)
        assert r.returncode == 0
        import json
        data = json.loads(r.stdout)
        assert data["ok"] is True


# --------------- daily_report ---------------

class TestDailyReport:
    def test_dry_run_prints_report(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.daily_report", "--dry-run", "--config", cfg], mini_repo)
        assert r.returncode == 0
        assert "KMS daily report" in r.stdout

    def test_writes_report_file(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.daily_report", "--config", cfg], mini_repo)
        assert r.returncode == 0
        reports = list((mini_repo / "vault" / "00_Admin" / "reports").glob("daily-*.txt"))
        assert len(reports) >= 1

    def test_creates_audit_entry(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        _run([sys.executable, "-m", "kms.scripts.daily_report", "--config", cfg], mini_repo)
        conn = sqlite3.connect(mini_repo / "kms" / "data" / "state.db")
        row = conn.execute("SELECT action FROM audit_log WHERE action = 'daily_report'").fetchone()
        conn.close()
        assert row is not None


# --------------- generate_source_note ---------------

class TestGenerateSourceNote:
    def test_dry_run_does_not_create_file(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([
            sys.executable, "-m", "kms.scripts.generate_source_note",
            "--title", "Dry Run Test", "--dry-run", "--config", cfg,
        ], mini_repo)
        assert r.returncode == 0
        assert "dry-run" in r.stdout.lower()
        notes = list((mini_repo / "vault" / "20_Source-Notes").glob("*.md"))
        assert len(notes) == 0

    def test_creates_source_note_file(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([
            sys.executable, "-m", "kms.scripts.generate_source_note",
            "--title", "Real Note", "--source-type", "web", "--config", cfg,
        ], mini_repo)
        assert r.returncode == 0
        notes = list((mini_repo / "vault" / "20_Source-Notes").glob("src-*.md"))
        assert len(notes) == 1
        content = notes[0].read_text(encoding="utf-8")
        assert "Real Note" in content

    def test_refuses_overwrite(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        _run([
            sys.executable, "-m", "kms.scripts.generate_source_note",
            "--title", "First", "--id", "src-2026-0001", "--config", cfg,
        ], mini_repo)
        r2 = _run([
            sys.executable, "-m", "kms.scripts.generate_source_note",
            "--title", "Duplicate", "--id", "src-2026-0001", "--config", cfg,
        ], mini_repo)
        assert r2.returncode == 2

    def test_creates_audit_entry(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        _run([
            sys.executable, "-m", "kms.scripts.generate_source_note",
            "--title", "Audit Test", "--config", cfg,
        ], mini_repo)
        conn = sqlite3.connect(mini_repo / "kms" / "data" / "state.db")
        row = conn.execute("SELECT action FROM audit_log WHERE action = 'generate_source_note'").fetchone()
        conn.close()
        assert row is not None


# --------------- generate_dashboard ---------------

class TestGenerateDashboard:
    def test_creates_dashboard_file(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.generate_dashboard", "--config", cfg], mini_repo)
        assert r.returncode == 0, r.stderr + r.stdout
        dashboard = mini_repo / "vault" / "00_Admin" / "dashboard.md"
        assert dashboard.is_file()
        content = dashboard.read_text(encoding="utf-8")
        assert "Dashboard" in content
        assert "pipeline" in content.lower() or "metryka" in content.lower()

    def test_dashboard_shows_inbox_count(self, mini_repo: Path) -> None:
        (mini_repo / "vault" / "00_Inbox" / "file1.md").write_text("test", encoding="utf-8")
        (mini_repo / "vault" / "00_Inbox" / "file2.pdf").write_bytes(b"%PDF-1.4 test")
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.generate_dashboard", "--config", cfg], mini_repo)
        assert r.returncode == 0, r.stderr + r.stdout
        content = (mini_repo / "vault" / "00_Admin" / "dashboard.md").read_text(encoding="utf-8")
        assert "2" in content


# --------------- status ---------------

class TestStatus:
    def test_empty_db_returns_0(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.status", "--config", cfg], mini_repo)
        assert r.returncode == 0

    def test_json_output_parseable(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        py = sys.executable
        _run([py, "-m", "kms.scripts.scan_inbox", "--config", cfg], mini_repo)
        (mini_repo / "vault" / "00_Inbox" / "test.txt").write_text("content", encoding="utf-8")
        _run([py, "-m", "kms.scripts.scan_inbox", "--config", cfg], mini_repo)
        _run([py, "-m", "kms.scripts.make_review_queue", "--config", cfg], mini_repo)
        r = _run([py, "-m", "kms.scripts.status", "--json", "--config", cfg], mini_repo)
        assert r.returncode == 0
        import json
        for line in r.stdout.strip().splitlines():
            data = json.loads(line)
            assert "proposal_id" in data

    def test_filter_by_proposal_id(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([sys.executable, "-m", "kms.scripts.status", "--proposal-id", "999", "--config", cfg], mini_repo)
        assert r.returncode == 1


# --------------- convert_conversation ---------------

_SAMPLE_CONVERSATION = """\
Alice: Próbowałeś kiedyś debugować race condition?
Bob: Tak, ostatnio miałem taki case — dwa joby co 5 minut, nakładające się transakcje.
Alice: I jak znalazłeś przyczynę?
Bob: Śledzenie po thread ID w logach, grep po PID. Klasyczne metody.
Alice: No właśnie, logging strategy jest kluczowy.
"""


class TestConvertConversation:
    def test_dry_run_does_not_create_file(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        conv_file = mini_repo / "sample_conv.txt"
        conv_file.write_text(_SAMPLE_CONVERSATION, encoding="utf-8")
        r = _run([
            sys.executable, "-m", "kms.scripts.convert_conversation",
            "--input", str(conv_file), "--title", "Dry Run Conv", "--dry-run", "--config", cfg,
        ], mini_repo)
        assert r.returncode == 0
        assert "dry-run" in r.stdout.lower()
        notes = list((mini_repo / "vault" / "00_Inbox").glob("conv-*.md"))
        assert len(notes) == 0

    def test_creates_inbox_note(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        conv_file = mini_repo / "sample_conv.txt"
        conv_file.write_text(_SAMPLE_CONVERSATION, encoding="utf-8")
        r = _run([
            sys.executable, "-m", "kms.scripts.convert_conversation",
            "--input", str(conv_file), "--title", "Debug Chat", "--config", cfg,
        ], mini_repo)
        assert r.returncode == 0
        notes = list((mini_repo / "vault" / "00_Inbox").glob("conv-*.md"))
        assert len(notes) == 1
        content = notes[0].read_text(encoding="utf-8")
        assert "source_type" in content
        assert "conversation" in content
        assert "Debug Chat" in content

    def test_creates_audit_entry(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        conv_file = mini_repo / "sample_conv.txt"
        conv_file.write_text(_SAMPLE_CONVERSATION, encoding="utf-8")
        _run([
            sys.executable, "-m", "kms.scripts.convert_conversation",
            "--input", str(conv_file), "--config", cfg,
        ], mini_repo)
        conn = sqlite3.connect(mini_repo / "kms" / "data" / "state.db")
        row = conn.execute("SELECT action FROM audit_log WHERE action = 'convert_conversation'").fetchone()
        conn.close()
        assert row is not None

    def test_missing_input_returns_1(self, mini_repo: Path) -> None:
        cfg = str(mini_repo / "kms" / "config" / "config.yaml")
        r = _run([
            sys.executable, "-m", "kms.scripts.convert_conversation",
            "--input", str(mini_repo / "nonexistent.txt"), "--config", cfg,
        ], mini_repo)
        assert r.returncode == 1
