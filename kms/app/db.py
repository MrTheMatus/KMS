"""SQLite access: init schema, connections, audit."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kms.app.paths import ensure_dir


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    ensure_dir(db_path.parent)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def ensure_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    """Idempotent: create tables if missing."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
    )
    if cur.fetchone() is None:
        init_schema(conn, schema_path)
    _migrate_columns(conn)
    _ensure_executions_table(conn)
    # Denormalized lifecycle cache on proposals (cheap for small DBs)
    from kms.app.lifecycle import recompute_lifecycle

    recompute_lifecycle(conn)


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Add missing columns for forward-compatible local upgrades."""
    if not _has_column(conn, "decisions", "review_note"):
        conn.execute("ALTER TABLE decisions ADD COLUMN review_note TEXT")
    if not _has_column(conn, "proposals", "lifecycle_status"):
        conn.execute("ALTER TABLE proposals ADD COLUMN lifecycle_status TEXT")
    if not _has_column(conn, "artifacts", "index_status"):
        conn.execute(
            "ALTER TABLE artifacts ADD COLUMN index_status TEXT DEFAULT 'pending'"
        )
        conn.execute(
            """UPDATE artifacts SET index_status = 'ok'
               WHERE workspace_name IS NOT NULL AND TRIM(workspace_name) != ''
                 AND (index_status IS NULL OR index_status = 'pending')"""
        )
    if not _has_column(conn, "artifacts", "anythingllm_doc_location"):
        conn.execute("ALTER TABLE artifacts ADD COLUMN anythingllm_doc_location TEXT")
    conn.commit()


def _ensure_executions_table(conn: sqlite3.Connection) -> None:
    """Create executions table on existing DBs (new installs get it from schema.sql)."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='executions'"
    )
    if cur.fetchone() is not None:
        return
    conn.execute(
        """CREATE TABLE executions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          proposal_id INTEGER NOT NULL UNIQUE REFERENCES proposals(id) ON DELETE CASCADE,
          applied_at TEXT NOT NULL,
          reverted_at TEXT,
          snapshot_json TEXT NOT NULL,
          result_json TEXT
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_executions_proposal ON executions(proposal_id)"
    )
    conn.commit()


def audit(
    conn: sqlite3.Connection,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> None:
    conn.execute(
        """INSERT INTO audit_log (ts, action, entity_type, entity_id, payload_json, error_message)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            utc_now_iso(),
            action,
            entity_type,
            entity_id,
            json.dumps(payload, ensure_ascii=False) if payload else None,
            error_message,
        ),
    )
    conn.commit()


def fetch_all_dicts(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]
