"""Revert a successful apply for one proposal: restore files from execution snapshot, remove artifact/execution rows."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from kms.app.anythingllm_client import AnythingLLMClient
from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts, utc_now_iso
from kms.app.execution_snapshot import parse_snapshot_json
from kms.app.lifecycle import recompute_lifecycle
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser(
        "Revert apply for one proposal: move file back, remove created source note, drop artifact/execution."
    )
    add_dry_run(p)
    p.add_argument(
        "--proposal-id",
        type=int,
        required=True,
        help="Proposal id to revert (must have an execution snapshot from apply)",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    vault = vp["root"]

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    pid = args.proposal_id
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
        conn.close()
        return 2

    row = rows[0]
    try:
        snap = parse_snapshot_json(row["snapshot_json"])
    except (ValueError, OSError) as e:
        _LOG.error("Invalid snapshot: %s", e)
        conn.close()
        return 2

    moves = snap.get("moves") or []
    if not moves:
        _LOG.error("Snapshot has no moves")
        conn.close()
        return 2
    m0 = moves[0]
    src_rel = str(m0.get("from", ""))
    dest_rel = str(m0.get("to", ""))
    created_paths = list(snap.get("created_paths") or [])

    dest = vault / dest_rel
    src = vault / src_rel

    if args.dry_run:
        _LOG.info(
            "dry-run: would revert proposal %s: move %s -> %s, delete %s, drop artifact",
            pid,
            dest_rel,
            src_rel,
            created_paths,
        )
        if str(row.get("index_status", "")).lower() == "ok":
            loc = row.get("anythingllm_doc_location") or ""
            if loc and cfg.get("anythingllm", {}).get("enabled"):
                _LOG.info("dry-run: would call AnythingLLM remove_embeddings for location=%s", loc)
            else:
                _LOG.info(
                    "dry-run: indexed but no stored doc location — may need manual removal in AnythingLLM UI"
                )
        conn.close()
        return 0

    # Remove from AnythingLLM workspace index when we have the stored location (best-effort).
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
                )
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("AnythingLLM remove_embeddings failed (continuing revert): %s", exc)
                audit(
                    conn,
                    "revert_apply",
                    "proposal",
                    str(pid),
                    {"anythingllm_remove_failed": True, "doc_location": doc_loc},
                    str(exc),
                )
        else:
            audit(
                conn,
                "revert_apply",
                "proposal",
                str(pid),
                {
                    "anythingllm_manual": True,
                    "reason": "missing API key env",
                },
                None,
            )
    elif index_ok and not doc_loc:
        audit(
            conn,
            "revert_apply",
            "proposal",
            str(pid),
            {
                "anythingllm_manual": True,
                "reason": "no anythingllm_doc_location on artifact (sync before this column existed)",
            },
            None,
        )

    for rel in created_paths:
        pth = vault / rel
        if pth.is_file():
            pth.unlink()
            _LOG.info("Removed created file %s", rel)

    if dest.is_file():
        ensure_parent(src)
        if src.exists():
            _LOG.error("Revert blocked: source path already exists: %s", src)
            conn.close()
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
        {"reverted": {"from": dest_rel, "to": src_rel}, "created_removed": created_paths},
        None,
    )
    conn.commit()
    recompute_lifecycle(conn)
    conn.close()
    _LOG.info("Reverted proposal %s", pid)
    return 0


def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
