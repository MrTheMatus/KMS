"""Print proposal lifecycle and index status (control plane read model)."""

from __future__ import annotations

import json
import sys

from kms.app.config import abs_path, vault_paths
from kms.app.db import connect, ensure_schema, fetch_all_dicts
from kms.app.paths import project_root
from kms.scripts._cli import build_parser, load_setup_logging


def main() -> int:
    p = build_parser("Show KMS control-plane status for proposals (lifecycle, paths, index).")
    p.add_argument(
        "--proposal-id",
        type=int,
        default=None,
        help="Filter to a single proposal id",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON lines",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    where = "WHERE p.id = ?" if args.proposal_id is not None else ""
    params: tuple = (args.proposal_id,) if args.proposal_id is not None else ()

    rows = fetch_all_dicts(
        conn,
        f"""SELECT p.id AS proposal_id, p.lifecycle_status,
                   p.suggested_action, p.suggested_target,
                   i.id AS item_id, i.path AS item_path, i.status AS item_status,
                   COALESCE(d.decision, 'pending') AS decision,
                   d.reviewer, d.review_note,
                   a.id AS artifact_id, a.source_note_path, a.workspace_name,
                   a.anythingllm_doc_location,
                   COALESCE(a.index_status, 'pending') AS index_status,
                   a.applied_at AS artifact_applied_at,
                   e.id AS execution_id
            FROM proposals p
            JOIN items i ON i.id = p.item_id
            LEFT JOIN decisions d ON d.proposal_id = p.id
            LEFT JOIN artifacts a ON a.proposal_id = p.id
            LEFT JOIN executions e ON e.proposal_id = p.id
            {where}
            ORDER BY p.id""",
        params,
    )
    conn.close()

    if not rows:
        print("No matching proposals.", file=sys.stderr)
        return 1 if args.proposal_id is not None else 0

    if args.json:
        for r in rows:
            print(json.dumps(r, default=str, ensure_ascii=False))
        return 0

    vault_root = vp["root"]
    print(f"# vault: {vault_root}")
    for r in rows:
        print(
            f"proposal={r['proposal_id']}\tlifecycle={r.get('lifecycle_status')}\t"
            f"decision={r['decision']}\titem={r['item_path']}\t"
            f"index={r.get('index_status')}\tworkspace={r.get('workspace_name')}\t"
            f"execution={r.get('execution_id')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
