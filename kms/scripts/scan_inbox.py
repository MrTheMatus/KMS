"""Scan 00_Inbox for new/changed files and upsert items in SQLite (Etap 2)."""

from __future__ import annotations

import logging
from pathlib import Path

from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts, utc_now_iso
from kms.app.hashing import sha256_file
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser("Scan vault inbox and register items in SQLite.")
    add_dry_run(p)
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    inbox = vp["inbox"]

    if args.dry_run:
        _LOG.info("dry-run: would scan %s", inbox)
        return 0

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    if not inbox.is_dir():
        audit(conn, "scan_inbox", "inbox", None, {"error": "missing_inbox"}, None)
        conn.close()
        _LOG.warning("Inbox does not exist: %s", inbox)
        return 1

    now = utc_now_iso()
    count_new = 0
    count_upd = 0
    dup_warn = 0

    for path in sorted(inbox.rglob("*")):
        # Ignore hidden files and generated/system reports (e.g. _topics_discovered.md).
        # These are not user content and should never enter the review/apply pipeline.
        if not path.is_file() or path.name.startswith(".") or path.name.startswith("_"):
            continue
        try:
            rel = path.relative_to(vp["root"])
        except ValueError:
            continue
        rel_s = rel.as_posix()
        h = sha256_file(path)
        others = fetch_all_dicts(
            conn,
            "SELECT path FROM items WHERE hash = ? AND path != ?",
            (h, rel_s),
        )
        if others:
            dup_warn += 1
            audit(
                conn,
                "scan_inbox",
                "duplicate_hash",
                rel_s,
                {"hash": h, "other_paths": [o["path"] for o in others]},
                None,
            )
        cur = conn.execute(
            "SELECT id, hash, status FROM items WHERE path = ?", (rel_s,)
        )
        row = cur.fetchone()
        if row is None:
            conn.execute(
                """INSERT INTO items (path, kind, hash, source_url, status, created_at, updated_at)
                   VALUES (?, ?, ?, NULL, 'new', ?, ?)""",
                (rel_s, _kind_from_name(path), h, now, now),
            )
            count_new += 1
        elif row["hash"] != h:
            conn.execute(
                "UPDATE items SET hash = ?, updated_at = ?, status = 'new' WHERE id = ?",
                (h, now, row["id"]),
            )
            count_upd += 1
    conn.commit()
    audit(
        conn,
        "scan_inbox",
        "run",
        None,
        {
            "new": count_new,
            "updated": count_upd,
            "duplicate_warnings": dup_warn,
            "inbox": str(inbox),
        },
        None,
    )
    conn.close()
    _LOG.info("scan_inbox done: new=%s updated=%s", count_new, count_upd)
    return 0


def _kind_from_name(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        return "pdf"
    if suf in {".md", ".markdown"}:
        return "markdown"
    return "file"


if __name__ == "__main__":
    raise SystemExit(main())
