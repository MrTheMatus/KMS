"""Minimal HTTP gateway: list pending proposals, submit decisions (Tailscale/VPN only).

Run: KMS_GATEWAY_TOKEN=secret PYTHONPATH=. python -m kms.gateway.server
Apply file moves still via `kms.scripts.apply_decisions` on the host.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

from kms.app.config import abs_path, load_config
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts, utc_now_iso
from kms.app.paths import project_root

_LOG = logging.getLogger(__name__)


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO)
    token = os.environ.get("KMS_GATEWAY_TOKEN", "").strip()
    if not token:
        _LOG.warning("KMS_GATEWAY_TOKEN unset — refusing to bind (set a strong token).")
        sys.exit(1)

    cfg_path = os.environ.get("KMS_CONFIG_PATH")
    cfg = load_config(Path(cfg_path).expanduser() if cfg_path else None)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")

    app = Flask(__name__)

    def _auth() -> bool:
        got = request.headers.get("Authorization", "")
        if got.startswith("Bearer "):
            return got.removeprefix("Bearer ").strip() == token
        return request.args.get("token") == token

    @app.get("/health")
    def health() -> Any:
        return jsonify({"ok": True})

    @app.get("/api/pending")
    def pending() -> Any:
        if not _auth():
            return jsonify({"error": "unauthorized"}), 401
        conn = connect(db_path)
        ensure_schema(conn, schema_path)
        rows = fetch_all_dicts(
            conn,
            """SELECT p.id AS proposal_id, p.item_id, p.suggested_action, p.suggested_target,
                      p.reason, i.path AS item_path,
                      COALESCE(d.decision, 'pending') AS decision
               FROM proposals p
               JOIN items i ON i.id = p.item_id
               LEFT JOIN decisions d ON d.proposal_id = p.id
               WHERE COALESCE(d.decision, 'pending') = 'pending'
               ORDER BY p.id""",
        )
        conn.close()
        return jsonify({"items": rows})

    @app.post("/api/decisions")
    def decisions() -> Any:
        if not _auth():
            return jsonify({"error": "unauthorized"}), 401
        data = request.get_json(silent=True) or {}
        pid = data.get("proposal_id")
        decision = str(data.get("decision", "")).lower().strip()
        reviewer = str(data.get("reviewer", "") or "")
        override = data.get("override_target")
        override_target = str(override) if override else None
        if pid is None or decision not in ("approve", "reject", "postpone", "pending"):
            return jsonify({"error": "invalid body"}), 400
        now = utc_now_iso()
        conn = connect(db_path)
        ensure_schema(conn, schema_path)
        conn.execute(
            """INSERT INTO decisions (proposal_id, decision, override_target, reviewer, decided_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(proposal_id) DO UPDATE SET
                 decision = excluded.decision,
                 override_target = excluded.override_target,
                 reviewer = excluded.reviewer,
                 decided_at = excluded.decided_at""",
            (int(pid), decision, override_target, reviewer, now),
        )
        conn.commit()
        audit(
            conn,
            "gateway_decision",
            "proposal",
            str(pid),
            {
                "decision": decision,
                "reviewer": reviewer or None,
                "override_target": override_target,
                "source": "gateway",
            },
        )
        conn.close()
        return jsonify({"ok": True, "proposal_id": int(pid), "decision": decision})

    return app


def main() -> None:
    app = create_app()
    host = os.environ.get("KMS_GATEWAY_HOST", "127.0.0.1")
    port = int(os.environ.get("KMS_GATEWAY_PORT", "8765"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
