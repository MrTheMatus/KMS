"""Sync decisions from review-queue.md and apply approved actions (Etap 2–3)."""

from __future__ import annotations

import logging
import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, create_batch, ensure_schema, fetch_all_dicts, update_batch_count, utc_now_iso
from kms.app.paths import ensure_dir, project_root
from kms.app.execution_snapshot import build_apply_snapshot
from kms.app.lifecycle import recompute_lifecycle
from kms.app.review_queue import parse_review_queue_markdown
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def _next_source_note_id(source_notes_dir: Path, year: int) -> str:
    prefix = f"src-{year}-"
    max_n = 0
    if source_notes_dir.is_dir():
        for p in source_notes_dir.glob("*.md"):
            m = re.match(rf"^{re.escape(prefix)}(\d{{4}})\.md$", p.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1:04d}"


def _extract_frontmatter_yaml(md_path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter delimited by leading '---' lines."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if len(lines) < 3:
        return None
    try:
        end_idx = lines[1:].index("---") + 1
    except ValueError:
        return None
    yaml_text = "\n".join(lines[1:end_idx]).strip()
    if not yaml_text:
        return {}
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _find_source_note_by_file_link(source_notes_dir: Path, file_link_rel: str) -> Path | None:
    """Return existing source note path if frontmatter.file_link matches."""
    if not source_notes_dir.is_dir():
        return None
    for p in source_notes_dir.glob("*.md"):
        fm = _extract_frontmatter_yaml(p)
        if not fm:
            continue
        if fm.get("file_link") == file_link_rel:
            return p
    return None


def _render_source_note(
    *,
    cfg: dict[str, Any],
    source_type: str,
    title: str,
    note_id: str,
    source_url: str | None,
    file_link_rel: str,
    captured_at: str,
    language: str,
) -> str:
    templates_dir = abs_path(cfg, "templates", "source_note").parent
    tpl_file = cfg["templates"]["source_note"]
    tpl_name = Path(tpl_file).name

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=()),
    )
    # Template uses Jinja's `tojson` filter.
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
    tpl = env.get_template(tpl_name)
    return tpl.render(
        id=note_id,
        source_type=source_type,
        title=title,
        source_url=source_url,
        file_link=file_link_rel,
        captured_at=captured_at,
        language=language,
        body="",
    )


def _create_source_note_for_file(
    *,
    cfg: dict[str, Any],
    vp: dict[str, Path],
    file_link_rel: str,
    source_type: str,
    title: str,
    language: str = "pl",
) -> Path:
    source_notes_dir = vp["source_notes"]
    year = date.today().year
    note_id = _next_source_note_id(source_notes_dir, year)
    captured_at = date.today().isoformat()

    body = _render_source_note(
        cfg=cfg,
        source_type=source_type,
        title=title,
        note_id=note_id,
        source_url=None,
        file_link_rel=file_link_rel,
        captured_at=captured_at,
        language=language,
    )

    source_notes_dir.mkdir(parents=True, exist_ok=True)
    out = source_notes_dir / f"{note_id}.md"
    if out.exists():
        raise FileExistsError(str(out))
    out.write_text(body, encoding="utf-8")
    return out


def main() -> int:
    p = build_parser(
        "Parse review-queue.md, upsert decisions, apply approved proposals (idempotent)."
    )
    add_dry_run(p)
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    rq_path = vp["review_queue"]

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    if not rq_path.is_file():
        _LOG.warning("No review queue file: %s", rq_path)
        conn.close()
        return 1

    content = rq_path.read_text(encoding="utf-8")
    try:
        blocks = parse_review_queue_markdown(content)
    except ValueError as e:
        audit(conn, "apply_decisions", "parse", str(rq_path), None, str(e))
        conn.commit()
        conn.close()
        _LOG.error("Parse error: %s", e)
        return 2

    now = utc_now_iso()
    valid_decisions = {"pending", "approve", "reject", "postpone"}
    for b in blocks:
        if b.decision not in valid_decisions:
            _LOG.warning("Invalid decision %s for proposal %s", b.decision, b.proposal_id)
            audit(
                conn,
                "apply_decisions",
                "decision",
                str(b.proposal_id),
                {"decision": b.decision},
                "invalid_decision",
            )
            continue
        if b.decision in {"approve", "reject"} and not b.reviewer.strip():
            _LOG.warning("Missing reviewer for proposal %s decision=%s", b.proposal_id, b.decision)
        conn.execute(
            """INSERT INTO decisions (proposal_id, decision, override_target, reviewer, review_note, decided_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(proposal_id) DO UPDATE SET
                 decision = excluded.decision,
                 override_target = excluded.override_target,
                 reviewer = excluded.reviewer,
                 review_note = excluded.review_note,
                 decided_at = excluded.decided_at""",
            (
                b.proposal_id,
                b.decision,
                b.override_target,
                b.reviewer or "",
                b.review_note or "",
                now,
            ),
        )
        _audit_suggestion_quality(conn, b.proposal_id, b.decision)
    conn.commit()

    if args.dry_run:
        pending = fetch_all_dicts(
            conn,
            """SELECT p.id AS proposal_id, p.item_id, p.suggested_action, p.suggested_target,
                      i.path AS item_path, d.decision, d.override_target
               FROM proposals p
               JOIN items i ON i.id = p.item_id
               JOIN decisions d ON d.proposal_id = p.id
               LEFT JOIN artifacts a ON a.proposal_id = p.id
               WHERE d.decision = 'approve' AND a.id IS NULL""",
        )
        for row in pending:
            _LOG.info(
                "dry-run: would apply proposal %s: %s -> %s",
                row["proposal_id"],
                row["item_path"],
                row.get("override_target") or row["suggested_target"],
            )
        conn.close()
        return 0

    approved = fetch_all_dicts(
        conn,
        """SELECT p.id AS proposal_id, p.item_id, p.suggested_action, p.suggested_target,
                  d.override_target,
                  i.path AS item_path
           FROM proposals p
           JOIN items i ON i.id = p.item_id
           JOIN decisions d ON d.proposal_id = p.id
           LEFT JOIN artifacts a ON a.proposal_id = p.id
           WHERE d.decision = 'approve' AND a.id IS NULL""",
    )

    batch_id = None
    if approved:
        ids = [str(r["proposal_id"]) for r in approved]
        batch_id = create_batch(
            conn, "apply_decisions",
            f"Apply {len(approved)} proposals: #{', #'.join(ids)}",
            len(approved),
        )

    exit_code = 0
    applied_count = 0
    for row in approved:
        ok = _apply_one(conn, cfg, vp, row, dry_run=False, batch_id=batch_id)
        if ok:
            applied_count += 1
        else:
            exit_code = 3

    if batch_id and applied_count != len(approved):
        update_batch_count(conn, batch_id, applied_count)

    recompute_lifecycle(conn)
    conn.close()
    return exit_code


def _apply_one(
    conn,
    cfg: dict[str, Any],
    vp: dict[str, Path],
    row: dict,
    *,
    dry_run: bool,
    batch_id: str | None = None,
) -> bool:
    proposal_id = int(row["proposal_id"])
    item_id = int(row["item_id"])
    action = row["suggested_action"]
    target_rel = row.get("override_target") or row["suggested_target"]
    src_rel = row["item_path"]
    vault = vp["root"]
    src = vault / src_rel
    dest = vault / (target_rel or "")
    dest_rel = dest.relative_to(vault).as_posix() if dest.is_relative_to(vault) else dest.as_posix()

    # Idempotency: if a previous run already moved the file but failed before inserting artifact,
    # `src` might be missing while `dest` already exists.
    if not src.is_file() and not dest.is_file():
        msg = f"missing source file: {src}"
        audit(
            conn,
            "apply_decisions",
            "proposal",
            str(proposal_id),
            {"item": item_id},
            msg,
        )
        conn.commit()
        _LOG.error("%s", msg)
        conn.execute(
            "UPDATE items SET status = 'failed', updated_at = ? WHERE id = ?",
            (utc_now_iso(), item_id),
        )
        conn.commit()
        return False

    try:
        ensure_dir(dest.parent)
        if src.is_file():
            if dest.exists():
                raise FileExistsError(str(dest))
            shutil.move(str(src), str(dest))

        if dry_run:
            _LOG.info(
                "dry-run: would apply proposal %s (%s) -> %s",
                proposal_id,
                action,
                dest_rel,
            )
            return True

        source_type = "pdf" if action == "move_to_pdf" else "web"
        source_note_path = _find_source_note_by_file_link(vp["source_notes"], dest_rel)
        created_source_note = False
        if source_note_path is None:
            title = Path(dest_rel).stem
            source_note_path = _create_source_note_for_file(
                cfg=cfg,
                vp=vp,
                file_link_rel=dest_rel,
                source_type=source_type,
                title=title,
            )
            created_source_note = True
        source_note_rel = source_note_path.relative_to(vault).as_posix()

        snapshot = build_apply_snapshot(
            src_rel=src_rel,
            dest_rel=dest_rel,
            source_note_relpath=source_note_rel,
            created_source_note=created_source_note,
        )
        now = utc_now_iso()
        conn.execute(
            "UPDATE items SET path = ?, status = 'applied', updated_at = ? WHERE id = ?",
            (dest_rel, now, item_id),
        )
        conn.execute(
            """INSERT INTO artifacts (proposal_id, item_id, source_note_path, workspace_name, applied_at, index_status)
               VALUES (?, ?, ?, NULL, ?, 'pending')""",
            (proposal_id, item_id, source_note_rel, now),
        )
        conn.execute(
            """INSERT INTO executions (proposal_id, applied_at, reverted_at, snapshot_json, result_json, batch_id)
               VALUES (?, ?, NULL, ?, ?, ?)""",
            (
                proposal_id,
                now,
                json.dumps(snapshot, ensure_ascii=False),
                json.dumps({"dest_item_path": dest_rel}, ensure_ascii=False),
                batch_id,
            ),
        )
        audit(
            conn,
            "apply_decisions",
            "proposal",
            str(proposal_id),
            {"moved": {"from": src_rel if src.is_file() else None, "to": dest_rel}, "source_note": source_note_rel},
            None,
            batch_id=batch_id,
        )
        conn.commit()
        _LOG.info("Applied proposal %s: %s -> %s", proposal_id, src_rel, dest_rel)
        return True
    except OSError as e:
        audit(
            conn,
            "apply_decisions",
            "proposal",
            str(proposal_id),
            {"item": item_id},
            str(e),
        )
        conn.commit()
        conn.execute(
            "UPDATE items SET status = 'failed', updated_at = ? WHERE id = ?",
            (utc_now_iso(), item_id),
        )
        conn.commit()
        _LOG.exception("Apply failed: %s", e)
        return False


def _audit_suggestion_quality(conn, proposal_id: int, human_decision: str) -> None:
    rows = fetch_all_dicts(
        conn,
        "SELECT suggested_metadata_json FROM proposals WHERE id = ?",
        (proposal_id,),
    )
    if not rows:
        return
    raw = rows[0].get("suggested_metadata_json")
    if not raw:
        return
    try:
        payload = json.loads(raw)
    except Exception:  # noqa: BLE001
        return
    triage = payload.get("triage")
    if not isinstance(triage, dict):
        return
    confidence = float(triage.get("confidence", 0.0))
    suggested_action = triage.get("suggested_permanent_note_action")
    accepted = human_decision == "approve"
    audit(
        conn,
        "triage_quality",
        "proposal",
        str(proposal_id),
        {
            "confidence": round(confidence, 4),
            "suggested_action": suggested_action,
            "human_decision": human_decision,
            "accepted": accepted,
        },
        None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
