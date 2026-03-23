"""Create proposals for new items and regenerate review-queue.md (Etap 2)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from kms.app.config import abs_path, load_config, vault_paths
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts, utc_now_iso
from kms.app.lifecycle import recompute_lifecycle
from kms.app.llm_triage import triage_against_permanent_notes
from kms.app.paths import project_root
from kms.app.review_queue import render_review_queue
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser("Generate proposals and 00_Admin/review-queue.md.")
    add_dry_run(p)
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    now = utc_now_iso()
    items = fetch_all_dicts(
        conn,
        "SELECT * FROM items WHERE status IN ('new', 'pending') ORDER BY id",
    )

    for it in items:
        existing = fetch_all_dicts(
            conn,
            "SELECT id FROM proposals WHERE item_id = ?",
            (it["id"],),
        )
        if not existing:
            action, target, reason = _suggest(it, vp)
            triage = triage_against_permanent_notes(
                _safe_read_text(vp["root"] / it["path"]),
                vp["permanent_notes"],
                provider=str(cfg.get("runtime", {}).get("llm_triage_provider", "heuristic")),
            )
            meta = {"original_path": it["path"], "triage": triage}
            conn.execute(
                """INSERT INTO proposals
                   (item_id, suggested_action, suggested_target, suggested_metadata_json, reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    it["id"],
                    action,
                    target,
                    json.dumps(meta, ensure_ascii=False),
                    reason,
                    now,
                ),
            )
    conn.commit()

    rows = fetch_all_dicts(
        conn,
        """SELECT p.id AS proposal_id, p.item_id, p.suggested_action, p.suggested_target,
                  p.suggested_metadata_json, p.reason, i.path, i.kind, i.status,
                  COALESCE(d.decision, 'pending') AS decision,
                  COALESCE(d.reviewer, '') AS reviewer,
                  COALESCE(d.review_note, '') AS review_note,
                  d.override_target
           FROM proposals p
           JOIN items i ON i.id = p.item_id
           LEFT JOIN decisions d ON d.proposal_id = p.id
           WHERE COALESCE(d.decision, 'pending') IN ('pending', 'postpone')
           ORDER BY p.id""",
    )

    blocks: list[dict] = []
    for row in rows:
        dec = str(row["decision"]).lower()
        rev = row["reviewer"] or ""
        body_md = _body_for_proposal(row, vp)
        blocks.append(
            {
                "proposal_id": row["proposal_id"],
                "item_id": row["item_id"],
                "decision": dec,
                "reviewer": rev,
                "override_target": row.get("override_target"),
                "review_note": row.get("review_note", ""),
                "body_md": body_md,
            }
        )

    title = "KMS Review queue"
    md = render_review_queue(title, blocks)

    rq_path = vp["review_queue"]
    rq_path.parent.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        _LOG.info("dry-run: would write %s", rq_path)
        print(md[:4000])
        conn.close()
        return 0

    rq_path.write_text(md, encoding="utf-8")
    confidences = [_triage(r).get("confidence", 0.0) for r in rows]
    avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0
    audit(
        conn,
        "make_review_queue",
        "file",
        str(rq_path),
        {"proposals": len(blocks), "avg_confidence": round(avg_conf, 4)},
        None,
    )
    conn.commit()
    recompute_lifecycle(conn)
    conn.close()
    _LOG.info("Wrote %s (%s blocks)", rq_path, len(blocks))
    print(str(rq_path))
    return 0


def _suggest(it: dict, vp: dict[str, Path]) -> tuple[str, str | None, str]:
    path = Path(it["path"])
    suf = path.suffix.lower()
    if suf == ".pdf":
        return (
            "move_to_pdf",
            str((vp["sources_pdf"] / path.name).relative_to(vp["root"])),
            "PDF: propose move to 10_Sources/pdf",
        )
    return (
        "move_to_web",
        str((vp["sources_web"] / path.name).relative_to(vp["root"])),
        "Non-PDF file: propose move to 10_Sources/web",
    )


def _body_for_proposal(row: dict, vp: dict[str, Path]) -> str:
    _ = vp
    source_path = row["path"]
    target_path = row["suggested_target"] or ""
    lines = [
        f"**Path:** `{row['path']}`",
        f"**Kind:** {row['kind']}",
        f"**Suggested action:** `{row['suggested_action']}`",
        f"**Target:** `{row['suggested_target']}`",
        f"**Reason:** {row['reason']}",
        f"**Triage confidence:** {_triage(row).get('confidence', 0):.2f}",
        f"**Permanent-note action:** `{_triage(row).get('suggested_permanent_note_action', 'manual-review')}`",
        f"**Suggested existing note:** `{_triage(row).get('suggested_existing_note_path')}`",
        f"**Summary:** {_triage(row).get('summary', '(none)')}",
        "",
        f"**Open source in Obsidian:** `[[{source_path}]]`",
        f"**Open proposed target path:** `[[{target_path}]]`",
        "",
        "**Decision checklist:**",
        "1) Read source note/source file",
        "2) Decide: approve / reject / postpone",
        "3) (Optional) set override_target",
        "4) Add short review_note for audit",
        "",
        "**Manual intervention notes (optional):**",
        "- Why this action is right/wrong",
        "- What to change before approve (e.g. override_target)",
        "",
        "Set `decision` in the YAML above to `approve`, `reject`, or `postpone`.",
    ]
    return "\n".join(lines)


def _triage(row: dict) -> dict:
    raw = row.get("suggested_metadata_json")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        return {}
    triage = data.get("triage")
    return triage if isinstance(triage, dict) else {}


def _safe_read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Binary file: {path.name}"
    except OSError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
