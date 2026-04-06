"""Return full proposal detail as JSON — used by Obsidian plugin and CLI."""

from __future__ import annotations

import json
import sys

from kms.app.config import abs_path
from kms.app.db import connect, ensure_schema, fetch_all_dicts
from kms.app.paths import project_root
from kms.scripts._cli import build_parser, load_setup_logging


def main() -> int:
    p = build_parser("Show full detail for one or more proposals (JSON output).")
    p.add_argument("--proposal-id", type=int, default=None, help="Single proposal id")
    p.add_argument(
        "--item-path", type=str, default=None, help="Filter by item path (substring)"
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)

    db_path = abs_path(cfg, "database", "path")
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    where_parts: list[str] = []
    params: list = []

    if args.proposal_id is not None:
        where_parts.append("p.id = ?")
        params.append(args.proposal_id)
    if args.item_path:
        where_parts.append("i.path LIKE ?")
        params.append(f"%{args.item_path}%")

    where = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    rows = fetch_all_dicts(
        conn,
        f"""SELECT p.id AS proposal_id, p.lifecycle_status,
                   p.suggested_action, p.suggested_target,
                   p.suggested_metadata_json, p.reason, p.created_at,
                   i.id AS item_id, i.path AS item_path, i.kind, i.status AS item_status,
                   COALESCE(d.decision, 'pending') AS decision,
                   d.reviewer, d.review_note, d.override_target, d.decided_at,
                   a.id AS artifact_id, a.source_note_path, a.workspace_name,
                   a.anythingllm_doc_location,
                   COALESCE(a.index_status, '') AS index_status,
                   a.applied_at,
                   e.id AS execution_id, e.reverted_at
            FROM proposals p
            JOIN items i ON i.id = p.item_id
            LEFT JOIN decisions d ON d.proposal_id = p.id
            LEFT JOIN artifacts a ON a.proposal_id = p.id
            LEFT JOIN executions e ON e.proposal_id = p.id
            {where}
            ORDER BY p.id""",
        tuple(params),
    )
    conn.close()

    results = []
    for r in rows:
        # Parse triage metadata
        triage = {}
        try:
            meta = json.loads(r.get("suggested_metadata_json") or "{}")
            triage = meta.get("triage", {})
        except Exception:  # noqa: BLE001
            pass

        results.append(
            {
                "proposal_id": r["proposal_id"],
                "item_id": r["item_id"],
                "item_path": r["item_path"],
                "kind": r["kind"],
                "item_status": r["item_status"],
                "lifecycle_status": r.get("lifecycle_status"),
                "suggested_action": r["suggested_action"],
                "suggested_target": r["suggested_target"],
                "reason": r["reason"],
                "created_at": r.get("created_at"),
                # Decision
                "decision": r["decision"],
                "reviewer": r.get("reviewer") or "",
                "review_note": r.get("review_note") or "",
                "override_target": r.get("override_target"),
                "decided_at": r.get("decided_at"),
                # Triage
                "domain": triage.get("suggested_domain", ""),
                "topics": triage.get("suggested_topics", []),
                "confidence": triage.get("confidence", 0),
                "summary": (triage.get("summary") or "")[:500],
                # Artifact (post-apply)
                "artifact_id": r.get("artifact_id"),
                "source_note_path": r.get("source_note_path"),
                "index_status": r.get("index_status") or "",
                "applied_at": r.get("applied_at"),
                # Execution
                "execution_id": r.get("execution_id"),
                "reverted_at": r.get("reverted_at"),
                # Computed flags
                "can_revert": bool(r.get("execution_id") and not r.get("reverted_at")),
                "is_applied": bool(r.get("artifact_id")),
            }
        )

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2, default=str)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
