"""Tests for kms.app.db: schema, migrations, audit, helpers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from kms.app.db import (
    audit,
    connect,
    ensure_schema,
    fetch_all_dicts,
    init_schema,
    utc_now_iso,
)

SCHEMA = Path(__file__).resolve().parents[1] / "kms" / "app" / "schema.sql"


class TestConnect:
    def test_creates_db_file(self, tmp_path: Path) -> None:
        db = tmp_path / "sub" / "test.db"
        conn = connect(db)
        assert db.is_file()
        conn.close()

    def test_foreign_keys_enabled(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        r = conn.execute("PRAGMA foreign_keys").fetchone()
        assert r[0] == 1
        conn.close()


class TestSchema:
    def test_init_creates_all_tables(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        init_schema(conn, SCHEMA)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        expected = {"items", "proposals", "decisions", "artifacts", "executions", "audit_log"}
        assert expected.issubset(tables)
        conn.close()

    def test_ensure_schema_idempotent(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        ensure_schema(conn, SCHEMA)
        ensure_schema(conn, SCHEMA)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "items" in tables
        conn.close()


class TestMigrations:
    def test_migrate_adds_missing_columns(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("ALTER TABLE decisions RENAME TO decisions_old")
        conn.execute(
            """CREATE TABLE decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id INTEGER NOT NULL UNIQUE,
                decision TEXT NOT NULL,
                override_target TEXT,
                reviewer TEXT,
                decided_at TEXT NOT NULL
            )"""
        )
        conn.commit()
        ensure_schema(conn, SCHEMA)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(decisions)").fetchall()}
        assert "review_note" in cols
        conn.close()


class TestAudit:
    def test_audit_writes_row(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        ensure_schema(conn, SCHEMA)
        audit(conn, "test_action", "item", "42", {"key": "value"})
        rows = conn.execute("SELECT * FROM audit_log WHERE action = 'test_action'").fetchall()
        assert len(rows) == 1
        assert rows[0]["entity_type"] == "item"
        assert rows[0]["entity_id"] == "42"
        payload = json.loads(rows[0]["payload_json"])
        assert payload["key"] == "value"
        conn.close()

    def test_audit_with_error_message(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        ensure_schema(conn, SCHEMA)
        audit(conn, "fail_action", error_message="something broke")
        row = conn.execute("SELECT error_message FROM audit_log WHERE action = 'fail_action'").fetchone()
        assert row["error_message"] == "something broke"
        conn.close()

    def test_audit_none_payload(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        ensure_schema(conn, SCHEMA)
        audit(conn, "no_payload_action")
        row = conn.execute("SELECT payload_json FROM audit_log WHERE action = 'no_payload_action'").fetchone()
        assert row["payload_json"] is None
        conn.close()


class TestFetchAllDicts:
    def test_returns_list_of_dicts(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        ensure_schema(conn, SCHEMA)
        conn.execute(
            "INSERT INTO items (path, kind, hash, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("test.md", "markdown", "abc", "new", "2026-01-01", "2026-01-01"),
        )
        conn.commit()
        rows = fetch_all_dicts(conn, "SELECT * FROM items")
        assert isinstance(rows, list)
        assert len(rows) == 1
        assert isinstance(rows[0], dict)
        assert rows[0]["path"] == "test.md"
        conn.close()

    def test_empty_result(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "test.db")
        ensure_schema(conn, SCHEMA)
        rows = fetch_all_dicts(conn, "SELECT * FROM items")
        assert rows == []
        conn.close()


class TestUtcNowIso:
    def test_format(self) -> None:
        ts = utc_now_iso()
        assert "T" in ts
        assert ts.endswith("+00:00")
