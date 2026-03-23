"""Verify vault ↔ SQLite consistency: detect drift between filesystem and DB state."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from kms.app.config import abs_path, vault_paths
from kms.app.db import connect, ensure_schema, fetch_all_dicts
from kms.app.hashing import sha256_file
from kms.app.paths import project_root
from kms.scripts._cli import build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser("Check vault ↔ SQLite consistency: missing files, hash mismatches, orphan DB rows.")
    p.add_argument("--json", action="store_true", help="Output results as JSON")
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    vault_root = vp["root"]

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    items = fetch_all_dicts(conn, "SELECT id, path, hash, status FROM items")

    missing_files: list[dict] = []
    hash_mismatches: list[dict] = []
    orphan_files: list[str] = []

    db_paths: set[str] = set()
    for item in items:
        rel = item["path"]
        db_paths.add(rel)
        full = vault_root / rel
        if not full.is_file():
            if item["status"] not in ("applied", "failed"):
                missing_files.append({"id": item["id"], "path": rel, "status": item["status"]})
        else:
            current_hash = sha256_file(full)
            if item["hash"] and current_hash != item["hash"]:
                hash_mismatches.append({
                    "id": item["id"],
                    "path": rel,
                    "db_hash": item["hash"][:12] + "…",
                    "file_hash": current_hash[:12] + "…",
                })

    inbox = vp["inbox"]
    if inbox.is_dir():
        for f in sorted(inbox.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                try:
                    rel = f.relative_to(vault_root).as_posix()
                except ValueError:
                    continue
                if rel not in db_paths:
                    orphan_files.append(rel)

    conn.close()

    ok = not missing_files and not hash_mismatches and not orphan_files

    if args.json:
        print(json.dumps({
            "ok": ok,
            "missing_files": missing_files,
            "hash_mismatches": hash_mismatches,
            "orphan_inbox_files": orphan_files,
        }, indent=2, ensure_ascii=False))
    else:
        if ok:
            print("Integrity check passed: vault and SQLite are consistent.")
        else:
            if missing_files:
                print(f"Missing files ({len(missing_files)}):")
                for m in missing_files:
                    print(f"  [{m['status']}] {m['path']} (item {m['id']})")
            if hash_mismatches:
                print(f"Hash mismatches ({len(hash_mismatches)}):")
                for h in hash_mismatches:
                    print(f"  {h['path']} — DB: {h['db_hash']}, file: {h['file_hash']}")
            if orphan_files:
                print(f"Inbox files not in DB ({len(orphan_files)}):")
                for o in orphan_files:
                    print(f"  {o}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
