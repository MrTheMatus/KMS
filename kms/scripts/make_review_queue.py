"""Create proposals for new items and regenerate review-queue.md (Etap 2).

Supports:
  --ai-summary    Generate AI summaries via unified LLM client
  --retriage      Re-run domain/topic classification for ALL existing proposals
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts, utc_now_iso
from kms.app.lifecycle import recompute_lifecycle
from kms.app.llm_client import LLMClient, create_llm_client
from kms.app.llm_triage import triage_against_permanent_notes
from kms.app.paths import project_root
from kms.app.review_queue import render_review_queue
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)

_SUMMARY_SYSTEM = (
    "Jesteś asystentem bazy wiedzy inżyniera. Piszesz zwięzłe streszczenia "
    "notatek technicznych (3-5 zdań po polsku). Skupiasz się na: głównym temacie, "
    "kluczowych wnioskach/technikach i przydatności praktycznej. "
    "Nie powtarzasz metadanych YAML ani ścieżek plików. "
    "BEZWZGLĘDNIE odpowiadaj TYLKO po polsku. Nigdy nie używaj chińskiego ani żadnego innego języka azjatyckiego."
)

_SUMMARY_PROMPT = (
    "Napisz zwięzłe streszczenie poniższej notatki (3-5 zdań po polsku).\n\n"
    "Tytuł: {title}\n"
    "Treść:\n```\n{content}\n```"
)


def main() -> int:
    p = build_parser("Generate proposals and 00_Admin/review-queue.md.")
    add_dry_run(p)
    p.add_argument(
        "--ai-summary",
        action="store_true",
        help="Use LLM to generate concise AI summaries for each proposal",
    )
    p.add_argument(
        "--retriage",
        action="store_true",
        help="Re-run domain/topic classification for ALL existing proposals (uses LLM if available)",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    # ── Create unified LLM client (used for summaries, retriage, and new proposals) ──
    llm: LLMClient | None = None
    use_ai = getattr(args, "ai_summary", False) or getattr(args, "retriage", False)
    if use_ai and not args.dry_run:
        llm = create_llm_client(cfg)
        if llm and llm.is_available():
            _LOG.info("LLM client ready: %s", llm)
        elif llm:
            _LOG.warning("LLM endpoint not reachable (%s) — falling back to heuristic", llm.base_url)
            llm = None
        else:
            _LOG.warning("No LLM configured — falling back to heuristic")

    # ── Retriage: re-classify ALL proposals ──
    if getattr(args, "retriage", False) and not args.dry_run:
        _retriage_all(conn, vp, llm)

    # ── Create proposals for NEW items ──
    now = utc_now_iso()
    items = fetch_all_dicts(
        conn,
        "SELECT * FROM items WHERE status IN ('new', 'pending') ORDER BY id",
    )

    new_count = 0
    for it in items:
        existing = fetch_all_dicts(
            conn,
            "SELECT id FROM proposals WHERE item_id = ?",
            (it["id"],),
        )
        if not existing:
            action, target, reason = _suggest(it, vp)
            source_text = _safe_read_text(vp["root"] / it["path"])
            title = Path(it["path"]).stem.replace("_", " ").replace("-", " ")
            triage = triage_against_permanent_notes(
                source_text,
                vp["permanent_notes"],
                provider=str(cfg.get("runtime", {}).get("llm_triage_provider", "heuristic")),
                llm_client=llm,
                title=title,
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
            new_count += 1
    if new_count:
        _LOG.info("Created %d new proposals", new_count)
    conn.commit()

    # ── Build review-queue.md ──
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

    ai_summaries_count = 0
    ai_backend = f"llm/{llm.model}" if llm else "none"

    blocks: list[dict] = []
    for row in rows:
        dec = str(row["decision"]).lower()
        rev = row["reviewer"] or ""

        # Generate AI summary if available
        ai_summary = None
        if llm and getattr(args, "ai_summary", False):
            _LOG.info("Generating AI summary %d/%d: %s", len(blocks) + 1, len(rows), row["path"])
            ai_summary = _generate_summary(llm, row, vp)
            if ai_summary:
                ai_summaries_count += 1

        body_md = _body_for_proposal(row, vp, ai_summary=ai_summary)
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
        {
            "proposals": len(blocks),
            "avg_confidence": round(avg_conf, 4),
            "ai_summaries": ai_summaries_count,
            "ai_backend": ai_backend,
        },
        None,
    )
    conn.commit()
    recompute_lifecycle(conn)
    conn.close()
    _LOG.info("Wrote %s (%s blocks, %s AI summaries via %s)", rq_path, len(blocks), ai_summaries_count, ai_backend)
    print(str(rq_path))
    return 0


# ── Retriage ────────────────────────────────────────────────────────


def _retriage_all(
    conn,
    vp: dict[str, Path],
    llm: LLMClient | None,
) -> None:
    """Re-run triage (domain/topic classification) for every proposal and update DB."""
    rows = fetch_all_dicts(
        conn,
        "SELECT p.id, p.suggested_metadata_json, i.path FROM proposals p JOIN items i ON i.id = p.item_id",
    )
    _LOG.info("Retriage: updating %d proposals…", len(rows))
    updated = 0
    for idx, row in enumerate(rows):
        source_text = _safe_read_text(vp["root"] / row["path"])
        if not source_text:
            continue

        title = Path(row["path"]).stem.replace("_", " ").replace("-", " ")
        new_triage = triage_against_permanent_notes(
            source_text,
            vp["permanent_notes"],
            llm_client=llm,
            title=title,
        )

        # Merge into existing metadata (preserve original_path etc.)
        try:
            meta = json.loads(row["suggested_metadata_json"] or "{}")
        except Exception:  # noqa: BLE001
            meta = {}
        meta["triage"] = new_triage
        meta.setdefault("original_path", row["path"])

        conn.execute(
            "UPDATE proposals SET suggested_metadata_json = ? WHERE id = ?",
            (json.dumps(meta, ensure_ascii=False), row["id"]),
        )
        updated += 1

        if (idx + 1) % 20 == 0:
            _LOG.info("Retriage progress: %d/%d", idx + 1, len(rows))
            conn.commit()

    conn.commit()
    _LOG.info("Retriage complete: %d/%d proposals updated", updated, len(rows))


# ── Helpers ─────────────────────────────────────────────────────────


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


def _generate_summary(
    client: LLMClient,
    row: dict,
    vp: dict[str, Path],
) -> str | None:
    """Generate a concise AI summary for a proposal."""
    source_path = vp["root"] / row["path"]
    content = _safe_read_text(source_path)
    if not content or len(content) < 50:
        return None

    title = Path(row["path"]).stem.replace("_", " ").replace("-", " ")
    prompt = _SUMMARY_PROMPT.format(title=title, content=content[:4000])

    try:
        text = client.generate(prompt, system=_SUMMARY_SYSTEM).strip()

        if text and len(text) > 20:
            # Strip non-Latin scripts that Qwen sometimes injects (CJK, Cyrillic, Thai, etc.)
            text = re.sub(r'[\u0400-\u04ff\u0500-\u052f]+', '', text)  # Cyrillic
            text = re.sub(r'[\u0e00-\u0e7f]+', '', text)  # Thai
            text = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+', '', text)  # CJK
            # Clean up leftover artifacts (double spaces, trailing colons, etc.)
            text = re.sub(r'\s{2,}', ' ', text).strip()
            text = re.sub(r'[：:]\s*$', '.', text)
            if len(text) > 20:
                return text
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("AI summary failed for proposal %s: %s", row["proposal_id"], exc)
    return None


def _body_for_proposal(row: dict, vp: dict[str, Path], *, ai_summary: str | None = None) -> str:
    _ = vp
    triage_data = _triage(row)
    domain = triage_data.get("suggested_domain", "")
    topics = triage_data.get("suggested_topics", [])
    topics_str = ", ".join(topics) if topics else "(brak)"
    match_reason = ""
    top_matches = triage_data.get("top_matches", [])
    if top_matches and isinstance(top_matches[0], dict):
        match_reason = top_matches[0].get("match_reason", "")

    # Use AI summary if available, otherwise fall back to triage summary
    summary_text = ai_summary or triage_data.get("summary", "(none)")
    summary_label = "Streszczenie (AI)" if ai_summary else "Summary"

    lines = [
        f"**Path:** `{row['path']}`",
        f"**Kind:** {row['kind']}",
        f"**Suggested action:** `{row['suggested_action']}`",
        f"**Target:** `{row['suggested_target']}`",
        f"**Reason:** {row['reason']}",
        f"**Triage confidence:** {triage_data.get('confidence', 0):.2f}",
        f"**Permanent-note action:** `{triage_data.get('suggested_permanent_note_action', 'manual-review')}`",
        f"**Suggested existing note:** `{triage_data.get('suggested_existing_note_path')}`",
        f"**Suggested domain:** `{domain or '(auto-detect failed)'}`",
        f"**Suggested topics:** {topics_str}",
        f"**Match reason:** {match_reason}" if match_reason else "",
        "",
        f"**{summary_label}:** {summary_text}",
        "",
        f"**Open source in Obsidian:** [[{row['path']}]]",
        f"**Open proposed target path:** [[{row['suggested_target'] or ''}]]",
    ]
    return "\n".join(ln for ln in lines if ln is not None)


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
