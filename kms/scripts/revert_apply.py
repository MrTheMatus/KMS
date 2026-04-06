"""Revert applied proposals: single proposal or entire batch."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from kms.app.anythingllm_client import AnythingLLMClient
from kms.app.config import abs_path, vault_paths
from kms.app.db import (
    audit,
    connect,
    create_batch,
    ensure_schema,
    fetch_all_dicts,
    utc_now_iso,
)
from kms.app.execution_snapshot import parse_snapshot_json
from kms.app.lifecycle import recompute_lifecycle
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser(
        "Revert applied proposals: single (--proposal-id) or entire batch (--batch-id)."
    )
    add_dry_run(p)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--proposal-id",
        type=int,
        default=None,
        help="Single proposal id to revert",
    )
    g.add_argument(
        "--batch-id",
        type=str,
        default=None,
        help="Batch UUID — revert all proposals applied in that batch",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    vault = vp["root"]

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    if args.batch_id:
        return _revert_batch(conn, cfg, vp, vault, args.batch_id, dry_run=args.dry_run)
    else:
        code = _revert_one(conn, cfg, vp, vault, args.proposal_id, dry_run=args.dry_run)
        recompute_lifecycle(conn)
        conn.close()
        return code


def _revert_batch(conn, cfg, vp, vault, batch_id: str, *, dry_run: bool) -> int:
    """Revert all proposals belonging to a batch."""
    # Validate batch exists
    batches = fetch_all_dicts(conn, "SELECT * FROM batches WHERE id = ?", (batch_id,))
    if not batches:
        _LOG.error("Batch %s not found", batch_id)
        conn.close()
        return 2
    batch = batches[0]
    if batch.get("reverted_at"):
        _LOG.error("Batch %s already reverted at %s", batch_id, batch["reverted_at"])
        conn.close()
        return 2

    # Find all executions in this batch
    execs = fetch_all_dicts(
        conn,
        "SELECT proposal_id FROM executions WHERE batch_id = ? AND reverted_at IS NULL",
        (batch_id,),
    )
    if not execs:
        _LOG.error("No active executions found for batch %s", batch_id)
        conn.close()
        return 2

    pids = [e["proposal_id"] for e in execs]
    _LOG.info("Batch %s: reverting %d proposals: %s", batch_id[:8], len(pids), pids)

    if dry_run:
        for pid in pids:
            _LOG.info("dry-run: would revert proposal %s", pid)
        conn.close()
        return 0

    # Create a revert batch for audit trail
    revert_batch_id = create_batch(
        conn,
        "revert_batch",
        f"Revert batch {batch_id[:8]} ({len(pids)} proposals)",
        len(pids),
    )

    failed = 0
    for pid in pids:
        code = _revert_one(
            conn, cfg, vp, vault, pid, dry_run=False, revert_batch_id=revert_batch_id
        )
        if code != 0:
            _LOG.error("Failed to revert proposal %s (continuing with remaining)", pid)
            failed += 1

    # Mark original batch as reverted
    conn.execute(
        "UPDATE batches SET reverted_at = ? WHERE id = ?",
        (utc_now_iso(), batch_id),
    )
    conn.commit()

    recompute_lifecycle(conn)
    conn.close()

    reverted = len(pids) - failed
    _LOG.info("Batch revert complete: %d/%d proposals reverted", reverted, len(pids))
    return 3 if failed else 0


def _revert_one(
    conn, cfg, vp, vault, pid: int, *, dry_run: bool, revert_batch_id: str | None = None
) -> int:
    """Revert a single proposal. Returns 0 on success."""
    rows = fetch_all_dicts(
        conn,
        """SELECT e.id AS execution_id, e.snapshot_json,
                  a.id AS artifact_id, a.workspace_name, a.index_status,
                  a.anythingllm_doc_location
           FROM executions e
           JOIN artifacts a ON a.proposal_id = e.proposal_id
           WHERE e.proposal_id = ?""",
        (pid,),
    )
    if not rows:
        _LOG.error("No execution+artifact for proposal_id=%s (nothing to revert)", pid)
        return 2

    row = rows[0]
    try:
        snap = parse_snapshot_json(row["snapshot_json"])
    except (ValueError, OSError) as e:
        _LOG.error("Invalid snapshot: %s", e)
        return 2

    moves = snap.get("moves") or []
    if not moves:
        _LOG.error("Snapshot has no moves")
        return 2
    m0 = moves[0]
    src_rel = str(m0.get("from", ""))
    dest_rel = str(m0.get("to", ""))
    created_paths = list(snap.get("created_paths") or [])

    dest = vault / dest_rel
    src = vault / src_rel

    if dry_run:
        _LOG.info(
            "dry-run: would revert proposal %s: move %s -> %s, delete %s, drop artifact",
            pid,
            dest_rel,
            src_rel,
            created_paths,
        )
        return 0

    # Remove from AnythingLLM workspace index (best-effort).
    api_cfg = cfg.get("anythingllm", {})
    index_ok = str(row.get("index_status", "")).lower() == "ok"
    doc_loc = (row.get("anythingllm_doc_location") or "").strip()
    if index_ok and api_cfg.get("enabled") and doc_loc:
        api_key = os.getenv(str(api_cfg.get("api_key_env", "ANYTHINGLLM_API_KEY")), "")
        if api_key:
            client = AnythingLLMClient(
                base_url=str(api_cfg.get("base_url", "http://localhost:3001")),
                workspace_slug=str(api_cfg.get("workspace_slug", "my-workspace")),
                api_key=api_key,
            )
            try:
                client.remove_embeddings([doc_loc])
                audit(
                    conn,
                    "revert_apply",
                    "proposal",
                    str(pid),
                    {"anythingllm_removed": True, "doc_location": doc_loc},
                    None,
                    batch_id=revert_batch_id,
                )
            except Exception as exc:  # noqa: BLE001
                _LOG.warning(
                    "AnythingLLM remove_embeddings failed (continuing revert): %s", exc
                )
                audit(
                    conn,
                    "revert_apply",
                    "proposal",
                    str(pid),
                    {"anythingllm_remove_failed": True, "doc_location": doc_loc},
                    str(exc),
                    batch_id=revert_batch_id,
                )
        else:
            audit(
                conn,
                "revert_apply",
                "proposal",
                str(pid),
                {"anythingllm_manual": True, "reason": "missing API key env"},
                None,
                batch_id=revert_batch_id,
            )
    elif index_ok and not doc_loc:
        audit(
            conn,
            "revert_apply",
            "proposal",
            str(pid),
            {"anythingllm_manual": True, "reason": "no doc_location on artifact"},
            None,
            batch_id=revert_batch_id,
        )

    for rel in created_paths:
        pth = vault / rel
        if pth.is_file():
            pth.unlink()
            _LOG.info("Removed created file %s", rel)

    if dest.is_file():
        _ensure_parent(src)
        if src.exists():
            _LOG.error("Revert blocked: source path already exists: %s", src)
            return 3
        shutil.move(str(dest), str(src))
        _LOG.info("Moved %s -> %s", dest_rel, src_rel)
    elif not src.is_file():
        _LOG.warning("Neither dest nor src file present; continuing DB cleanup")

    conn.execute("DELETE FROM artifacts WHERE proposal_id = ?", (pid,))
    conn.execute("DELETE FROM executions WHERE proposal_id = ?", (pid,))
    conn.execute(
        "UPDATE items SET path = ?, status = 'new', updated_at = ? WHERE id = (SELECT item_id FROM proposals WHERE id = ?)",
        (src_rel, utc_now_iso(), pid),
    )
    audit(
        conn,
        "revert_apply",
        "proposal",
        str(pid),
        {
            "reverted": {"from": dest_rel, "to": src_rel},
            "created_removed": created_paths,
        },
        None,
        batch_id=revert_batch_id,
    )
    conn.commit()
    _LOG.info("Reverted proposal %s", pid)
    return 0


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
