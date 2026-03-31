"""Search proposals in KMS database — used by Obsidian plugin and CLI."""

from __future__ import annotations

import json
import logging
import sys

from kms.app.config import abs_path
from kms.app.db import connect, ensure_schema, fetch_all_dicts
from kms.app.paths import project_root
from kms.scripts._cli import build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser("Search KMS proposals by text, domain or topic.")
    p.add_argument("--query", "-q", required=True, help="Search query (free text)")
    p.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    p.add_argument("--limit", type=int, default=30, help="Max results (default: 30)")
    p.add_argument(
        "--pending-only",
        action="store_true",
        help="Show only pending+postpone proposals (default: all)",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)

    db_path = abs_path(cfg, "database", "path")
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    like = f"%{args.query}%"

    decision_filter = ""
    if args.pending_only:
        decision_filter = "AND COALESCE(d.decision, 'pending') IN ('pending', 'postpone')"

    sql = f"""
        SELECT p.id AS proposal_id, p.item_id,
               p.suggested_metadata_json, p.reason,
               i.path AS item_path, i.kind,
               COALESCE(d.decision, 'pending') AS decision,
               COALESCE(d.review_note, '') AS review_note
        FROM proposals p
        JOIN items i ON i.id = p.item_id
        LEFT JOIN decisions d ON d.proposal_id = p.id
        WHERE (
            i.path LIKE ?
            OR p.reason LIKE ?
            OR p.suggested_metadata_json LIKE ?
            OR COALESCE(d.review_note, '') LIKE ?
        )
        {decision_filter}
        ORDER BY p.id DESC
        LIMIT ?
    """
    rows = fetch_all_dicts(conn, sql, (like, like, like, like, args.limit))

    results = []
    for row in rows:
        meta: dict = {}
        try:
            meta = json.loads(row["suggested_metadata_json"] or "{}")
        except Exception:  # noqa: BLE001
            pass
        triage = meta.get("triage", {})
        results.append(
            {
                "proposal_id": row["proposal_id"],
                "item_path": row["item_path"],
                "domain": triage.get("suggested_domain", ""),
                "topics": triage.get("suggested_topics", []),
                "summary": (triage.get("summary") or "")[:300],
                "decision": row["decision"],
                "confidence": triage.get("confidence", 0),
                "review_note": row.get("review_note", ""),
            }
        )

    conn.close()

    if args.format == "json":
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        print()  # trailing newline
    else:
        if not results:
            print("No matching proposals found.")
            return 0
        for r in results:
            domain = r["domain"] or "?"
            topics = ", ".join(r["topics"]) if r["topics"] else "-"
            print(f"#{r['proposal_id']}  [{domain}]  {r['item_path']}")
            print(f"  topics: {topics}  | confidence: {r['confidence']:.2f}  | decision: {r['decision']}")
            if r["summary"]:
                print(f"  {r['summary'][:120]}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
