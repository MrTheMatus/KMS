"""List batch operations as JSON — used by Obsidian plugin and CLI."""

from __future__ import annotations

import json
import sys

from kms.app.config import abs_path
from kms.app.db import connect, ensure_schema, fetch_all_dicts
from kms.app.paths import project_root
from kms.scripts._cli import build_parser, load_setup_logging


def main() -> int:
    p = build_parser("List batch operations (JSON output).")
    p.add_argument("--active-only", action="store_true", help="Show only non-reverted batches")
    p.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    args = p.parse_args()
    cfg = load_setup_logging(args)

    db_path = abs_path(cfg, "database", "path")
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    where = "WHERE reverted_at IS NULL" if args.active_only else ""
    rows = fetch_all_dicts(
        conn,
        f"SELECT * FROM batches {where} ORDER BY created_at DESC LIMIT ?",
        (args.limit,),
    )
    conn.close()

    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2, default=str)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
