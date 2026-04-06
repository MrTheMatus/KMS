"""SQLite access: init schema, connections, audit."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kms.app.paths import ensure_dir


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(db_path: Path, *, timeout: float = 30.0) -> sqlite3.Connection:
    """Open the KMS SQLite database.

    Uses a non-zero busy timeout and WAL so concurrent CLI, gateway, and
    scripts wait briefly instead of failing with database is locked.
    """
    ensure_dir(db_path.parent)
    conn = sqlite3.connect(str(db_path), timeout=timeout)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    sql = schema_path.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def _lifecycle_needs_backfill(conn: sqlite3.Connection) -> bool:
    """True if any proposal is missing a derived lifecycle (needs recompute)."""
    row = conn.execute(
        "SELECT 1 FROM proposals WHERE lifecycle_status IS NULL LIMIT 1"
    ).fetchone()
    return row is not None


def ensure_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    """Idempotent: create tables if missing."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
    )
    if cur.fetchone() is None:
        init_schema(conn, schema_path)
    migrated = _migrate_columns(conn)
    _ensure_batches(conn)
    _ensure_executions_table(conn)
    # Denormalized lifecycle cache: only recompute after DDL changes or NULL rows.
    # Avoids write locks on every read-only script/gateway open during long jobs (e.g. retriage).
    if migrated or _lifecycle_needs_backfill(conn):
        from kms.app.lifecycle import recompute_lifecycle

        recompute_lifecycle(conn)


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _migrate_columns(conn: sqlite3.Connection) -> bool:
    """Add missing columns for forward-compatible local upgrades. Returns True if DB was mutated."""
    changed = False
    if not _has_column(conn, "decisions", "review_note"):
        conn.execute("ALTER TABLE decisions ADD COLUMN review_note TEXT")
        changed = True
    if not _has_column(conn, "proposals", "lifecycle_status"):
        conn.execute("ALTER TABLE proposals ADD COLUMN lifecycle_status TEXT")
        changed = True
    if not _has_column(conn, "artifacts", "index_status"):
        conn.execute(
            "ALTER TABLE artifacts ADD COLUMN index_status TEXT DEFAULT 'pending'"
        )
        conn.execute(
            """UPDATE artifacts SET index_status = 'ok'
               WHERE workspace_name IS NOT NULL AND TRIM(workspace_name) != ''
                 AND (index_status IS NULL OR index_status = 'pending')"""
        )
        changed = True
    if not _has_column(conn, "artifacts", "anythingllm_doc_location"):
        conn.execute("ALTER TABLE artifacts ADD COLUMN anythingllm_doc_location TEXT")
        changed = True
    conn.commit()
    return changed


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
          result_json TEXT,
          batch_id TEXT REFERENCES batches(id)
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_executions_proposal ON executions(proposal_id)"
    )
    conn.commit()


def _ensure_batches(conn: sqlite3.Connection) -> None:
    """Create batches table and add batch_id columns to existing tables."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='batches'"
    )
    if cur.fetchone() is None:
        conn.execute(
            """CREATE TABLE batches (
              id TEXT PRIMARY KEY,
              action TEXT NOT NULL,
              description TEXT,
              proposal_count INTEGER DEFAULT 0,
              created_at TEXT NOT NULL,
              reverted_at TEXT
            )"""
        )
    if not _has_column(conn, "audit_log", "batch_id"):
        conn.execute(
            "ALTER TABLE audit_log ADD COLUMN batch_id TEXT REFERENCES batches(id)"
        )
    if not _has_column(conn, "executions", "batch_id"):
        conn.execute(
            "ALTER TABLE executions ADD COLUMN batch_id TEXT REFERENCES batches(id)"
        )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_batch ON audit_log(batch_id)")
    conn.commit()


def create_batch(
    conn: sqlite3.Connection,
    action: str,
    description: str | None = None,
    proposal_count: int = 0,
) -> str:
    """Create a new batch group and return its UUID."""
    batch_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO batches (id, action, description, proposal_count, created_at) VALUES (?, ?, ?, ?, ?)",
        (batch_id, action, description, proposal_count, utc_now_iso()),
    )
    conn.commit()
    return batch_id


def update_batch_count(conn: sqlite3.Connection, batch_id: str, count: int) -> None:
    conn.execute(
        "UPDATE batches SET proposal_count = ? WHERE id = ?", (count, batch_id)
    )
    conn.commit()


def audit(
    conn: sqlite3.Connection,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
    error_message: str | None = None,
    batch_id: str | None = None,
) -> None:
    conn.execute(
        """INSERT INTO audit_log (ts, action, entity_type, entity_id, payload_json, error_message, batch_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            utc_now_iso(),
            action,
            entity_type,
            entity_id,
            json.dumps(payload, ensure_ascii=False) if payload else None,
            error_message,
            batch_id,
        ),
    )
    conn.commit()


def fetch_all_dicts(
    conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()
) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]
