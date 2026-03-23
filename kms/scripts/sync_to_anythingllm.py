"""Optional sync of approved artifacts to AnythingLLM (upload + embeddings)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from kms.app.anythingllm_client import AnythingLLMClient
from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts
from kms.app.lifecycle import recompute_lifecycle
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser("Sync applied files to AnythingLLM workspace embeddings.")
    add_dry_run(p)
    args = p.parse_args()
    cfg = load_setup_logging(args)
    api_cfg = cfg.get("anythingllm", {})
    if not api_cfg.get("enabled", False):
        _LOG.info("anythingllm.enabled=false, skipping sync.")
        return 0

    api_key = os.getenv(str(api_cfg.get("api_key_env", "ANYTHINGLLM_API_KEY")), "")
    if not api_key:
        _LOG.error("Missing API key env %s", api_cfg.get("api_key_env", "ANYTHINGLLM_API_KEY"))
        return 2

    client = AnythingLLMClient(
        base_url=str(api_cfg.get("base_url", "http://localhost:3001")),
        workspace_slug=str(api_cfg.get("workspace_slug", "my-workspace")),
        api_key=api_key,
    )

    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    rows = fetch_all_dicts(
        conn,
        """SELECT a.proposal_id, a.item_id, i.path
           FROM artifacts a
           JOIN items i ON i.id = a.item_id
           WHERE COALESCE(a.index_status, 'pending') IN ('pending', 'failed')""",
    )

    ok = 0
    failed = 0
    for row in rows:
        rel = row["path"]
        abs_file = (vp["root"] / rel).resolve()
        if not abs_file.is_file():
            failed += 1
            audit(conn, "anythingllm_sync", "proposal", str(row["proposal_id"]), {"path": rel}, "missing_file")
            continue
        try:
            if args.dry_run:
                _LOG.info("dry-run: would sync %s", abs_file)
                ok += 1
                continue
            up = client.upload_document_file(abs_file)
            doc_location = str((up.get("documents") or [{}])[0].get("location", ""))
            if doc_location:
                client.update_embeddings([doc_location])
            conn.execute(
                """UPDATE artifacts SET workspace_name = ?, index_status = 'ok',
                          anythingllm_doc_location = ?
                   WHERE proposal_id = ?""",
                (
                    str(api_cfg.get("workspace_slug", "my-workspace")),
                    doc_location or None,
                    int(row["proposal_id"]),
                ),
            )
            audit(
                conn,
                "anythingllm_sync",
                "proposal",
                str(row["proposal_id"]),
                {"path": rel, "doc_location": doc_location},
                None,
            )
            conn.commit()
            ok += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            conn.execute(
                "UPDATE artifacts SET index_status = 'failed' WHERE proposal_id = ?",
                (int(row["proposal_id"]),),
            )
            conn.commit()
            audit(conn, "anythingllm_sync", "proposal", str(row["proposal_id"]), {"path": rel}, str(exc))
            _LOG.error("Sync failed for %s: %s", rel, exc)

    recompute_lifecycle(conn)
    conn.close()
    _LOG.info("AnythingLLM sync done: ok=%s failed=%s", ok, failed)
    return 0 if failed == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())

