"""Thin remote gateway — approve/reject/postpone + status.

Zero external dependencies (stdlib only). Designed to run behind VPN/Tailscale.

Endpoints:
  GET  /api/pending          List pending proposals (id, path, domain, summary)
  GET  /api/status           Last apply batch + proposal counts
  POST /api/decisions        Set decisions: [{"proposal_id": 1, "decision": "approve"}, ...]
  GET  /api/health           Liveness check

Auth: Bearer token from KMS_GATEWAY_TOKEN env var (required).
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from kms.app.config import abs_path, load_config
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts, utc_now_iso
from kms.app.paths import project_root

_LOG = logging.getLogger(__name__)

_VALID_DECISIONS = {"approve", "reject", "postpone"}


class _GatewayHandler(BaseHTTPRequestHandler):
    """Minimal JSON API handler."""

    server: GatewayServer  # type: ignore[override]

    # ── Auth ──────────────────────────────────────────────

    def _check_auth(self) -> bool:
        token = self.server.token
        if not token:
            self._json_error(HTTPStatus.INTERNAL_SERVER_ERROR, "KMS_GATEWAY_TOKEN not set")
            return False
        auth = self.headers.get("Authorization", "")
        if auth != f"Bearer {token}":
            self._json_error(HTTPStatus.UNAUTHORIZED, "Invalid or missing token")
            return False
        return True

    # ── Routing ───────────────────────────────────────────

    def do_GET(self) -> None:
        if not self._check_auth():
            return
        if self.path == "/api/pending":
            self._handle_pending()
        elif self.path == "/api/status":
            self._handle_status()
        elif self.path == "/api/health":
            self._json_response({"ok": True, "version": "0.3.1"})
        else:
            self._json_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        if not self._check_auth():
            return
        if self.path == "/api/decisions":
            self._handle_set_decisions()
        else:
            self._json_error(HTTPStatus.NOT_FOUND, "Not found")

    # ── Handlers ──────────────────────────────────────────

    def _handle_pending(self) -> None:
        """Return pending proposals with key metadata."""
        conn = self._get_conn()
        rows = fetch_all_dicts(
            conn,
            """SELECT p.id AS proposal_id, i.path, p.suggested_action,
                      p.suggested_target, p.suggested_metadata_json, p.reason,
                      d.decision, d.review_note
               FROM proposals p
               JOIN items i ON i.id = p.item_id
               JOIN decisions d ON d.proposal_id = p.id
               WHERE d.decision = 'pending'
               ORDER BY p.id""",
        )
        # Parse metadata for domain/topics/summary
        result = []
        for r in rows:
            meta = _parse_meta(r.get("suggested_metadata_json"))
            result.append({
                "proposal_id": r["proposal_id"],
                "path": r["path"],
                "action": r["suggested_action"],
                "target": r["suggested_target"],
                "domain": meta.get("domain"),
                "topics": meta.get("topics", []),
                "summary": meta.get("summary", ""),
                "review_note": r["review_note"],
            })
        conn.close()
        self._json_response(result)

    def _handle_status(self) -> None:
        """Return proposal counts + last apply batch."""
        conn = self._get_conn()
        counts = {}
        for row in fetch_all_dicts(
            conn,
            "SELECT d.decision, COUNT(*) AS cnt FROM decisions d GROUP BY d.decision",
        ):
            counts[row["decision"]] = row["cnt"]

        last_batch = fetch_all_dicts(
            conn,
            """SELECT id, action, description, proposal_count, created_at, reverted_at
               FROM batches ORDER BY created_at DESC LIMIT 1""",
        )
        conn.close()

        self._json_response({
            "counts": counts,
            "total": sum(counts.values()),
            "last_batch": last_batch[0] if last_batch else None,
        })

    def _handle_set_decisions(self) -> None:
        """Accept JSON array of {proposal_id, decision, review_note?}."""
        body = self._read_body()
        if body is None:
            return

        if not isinstance(body, list):
            self._json_error(HTTPStatus.BAD_REQUEST, "Expected JSON array")
            return

        conn = self._get_conn()
        updated = 0
        errors: list[str] = []

        for entry in body:
            pid = entry.get("proposal_id")
            decision = entry.get("decision", "").strip().lower()
            note = entry.get("review_note")

            if not pid or decision not in _VALID_DECISIONS:
                errors.append(f"Invalid entry: proposal_id={pid}, decision={decision}")
                continue

            # Verify proposal exists and is pending
            existing = fetch_all_dicts(
                conn,
                "SELECT d.decision FROM decisions d WHERE d.proposal_id = ?",
                (pid,),
            )
            if not existing:
                errors.append(f"Proposal {pid} not found")
                continue
            if existing[0]["decision"] != "pending":
                errors.append(f"Proposal {pid} is already {existing[0]['decision']}")
                continue

            conn.execute(
                "UPDATE decisions SET decision = ?, decided_at = ?, reviewer = 'gateway' WHERE proposal_id = ?",
                (decision, utc_now_iso(), pid),
            )
            if note is not None:
                conn.execute(
                    "UPDATE decisions SET review_note = ? WHERE proposal_id = ?",
                    (note, pid),
                )
            audit(
                conn,
                action=f"gateway_decision_{decision}",
                entity_type="proposal",
                entity_id=str(pid),
                payload={"decision": decision, "review_note": note},
            )
            updated += 1

        conn.commit()
        conn.close()

        self._json_response({
            "updated": updated,
            "errors": errors,
        }, status=HTTPStatus.OK if not errors else HTTPStatus.MULTI_STATUS)

    # ── Helpers ───────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        conn = connect(self.server.db_path)
        ensure_schema(conn, self.server.schema_path)
        return conn

    def _read_body(self) -> Any | None:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._json_error(HTTPStatus.BAD_REQUEST, "Empty body")
            return None
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError) as e:
            self._json_error(HTTPStatus.BAD_REQUEST, f"Invalid JSON: {e}")
            return None

    def _json_response(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, status: HTTPStatus, message: str) -> None:
        self._json_response({"error": message}, status=status)

    def log_message(self, fmt: str, *args: Any) -> None:
        _LOG.info(fmt, *args)


class GatewayServer(HTTPServer):
    """HTTPServer subclass carrying config for handlers."""

    def __init__(
        self,
        address: tuple[str, int],
        db_path: Path,
        schema_path: Path,
        token: str,
    ) -> None:
        super().__init__(address, _GatewayHandler)
        self.db_path = db_path
        self.schema_path = schema_path
        self.token = token


def _parse_meta(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="KMS thin remote gateway (decisions only)")
    p.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=8780, help="Port (default: 8780)")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    token = os.environ.get("KMS_GATEWAY_TOKEN", "")
    if not token:
        _LOG.error("KMS_GATEWAY_TOKEN environment variable is required")
        return 1

    cfg = load_config()
    db_path = abs_path(cfg, "database", "path")
    schema_path = project_root() / "kms" / "app" / "schema.sql"

    server = GatewayServer((args.host, args.port), db_path, schema_path, token)
    _LOG.info("KMS Gateway listening on %s:%d (token: %s...)", args.host, args.port, token[:4])
    _LOG.info("Endpoints: GET /api/pending, GET /api/status, POST /api/decisions, GET /api/health")
    _LOG.info("Auth: Authorization: Bearer <KMS_GATEWAY_TOKEN>")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _LOG.info("Shutting down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
