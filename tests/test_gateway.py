"""Tests for the thin remote gateway."""

from __future__ import annotations

import json
import threading
import urllib.request
from pathlib import Path

import pytest

from kms.app.db import connect, ensure_schema, utc_now_iso
from kms.gateway.server import GatewayServer

SCHEMA = Path(__file__).resolve().parent.parent / "kms" / "app" / "schema.sql"
TOKEN = "test-token-12345"


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """Create a temporary DB with schema and seed data."""
    p = tmp_path / "state.db"
    conn = connect(p)
    ensure_schema(conn, SCHEMA)

    now = utc_now_iso()
    # Insert 3 items + proposals + decisions (2 pending, 1 approved)
    for i, (path, decision) in enumerate(
        [
            ("00_Inbox/file-a.md", "pending"),
            ("00_Inbox/file-b.md", "pending"),
            ("00_Inbox/file-c.md", "approve"),
        ],
        start=1,
    ):
        conn.execute(
            "INSERT INTO items (id, path, kind, hash, status, created_at, updated_at) VALUES (?, ?, 'file', 'abc', 'new', ?, ?)",
            (i, path, now, now),
        )
        meta = json.dumps(
            {"domain": "testing", "topics": ["unit-test"], "summary": f"Test file {i}"}
        )
        conn.execute(
            "INSERT INTO proposals (id, item_id, suggested_action, suggested_target, suggested_metadata_json, created_at) VALUES (?, ?, 'move', '10_Sources/', ?, ?)",
            (i, i, meta, now),
        )
        conn.execute(
            "INSERT INTO decisions (proposal_id, decision, decided_at) VALUES (?, ?, ?)",
            (i, decision, now if decision != "pending" else None),
        )
    conn.commit()
    conn.close()
    return p


@pytest.fixture()
def gateway(db_path: Path):
    """Start gateway on a random port, yield base URL, stop on cleanup."""
    server = GatewayServer(("127.0.0.1", 0), db_path, SCHEMA, TOKEN)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def _request(
    url: str, method: str = "GET", data: dict | list | None = None, token: str = TOKEN
) -> tuple[int, dict]:
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


class TestGatewayAuth:
    def test_no_token_returns_401(self, gateway: str) -> None:
        req = urllib.request.Request(f"{gateway}/api/status")
        # No auth header
        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have raised HTTPError")
        except urllib.error.HTTPError as e:
            assert e.code == 401

    def test_wrong_token_returns_401(self, gateway: str) -> None:
        status, body = _request(f"{gateway}/api/status", token="wrong-token")
        assert status == 401

    def test_valid_token_returns_200(self, gateway: str) -> None:
        status, body = _request(f"{gateway}/api/health")
        assert status == 200
        assert body["ok"] is True

    def test_health_is_public(self, gateway: str) -> None:
        """Health endpoint works without auth (liveness probe)."""
        req = urllib.request.Request(f"{gateway}/api/health")
        resp = urllib.request.urlopen(req)
        assert resp.status == 200
        body = json.loads(resp.read())
        assert body["ok"] is True


class TestGatewayPending:
    def test_returns_pending_proposals(self, gateway: str) -> None:
        status, body = _request(f"{gateway}/api/pending")
        assert status == 200
        assert len(body) == 2  # 2 pending, 1 approved (excluded)
        ids = {p["proposal_id"] for p in body}
        assert ids == {1, 2}

    def test_pending_includes_metadata(self, gateway: str) -> None:
        status, body = _request(f"{gateway}/api/pending")
        p = body[0]
        assert "domain" in p
        assert "topics" in p
        assert "summary" in p
        assert p["domain"] == "testing"


class TestGatewayStatus:
    def test_returns_counts(self, gateway: str) -> None:
        status, body = _request(f"{gateway}/api/status")
        assert status == 200
        assert body["counts"]["pending"] == 2
        assert body["counts"]["approve"] == 1
        assert body["total"] == 3


class TestGatewayDecisions:
    def test_approve_single(self, gateway: str, db_path: Path) -> None:
        status, body = _request(
            f"{gateway}/api/decisions",
            method="POST",
            data=[{"proposal_id": 1, "decision": "approve"}],
        )
        assert status == 200
        assert body["updated"] == 1
        assert body["errors"] == []

        # Verify in DB
        conn = connect(db_path)
        rows = conn.execute(
            "SELECT decision FROM decisions WHERE proposal_id = 1"
        ).fetchall()
        assert rows[0][0] == "approve"
        conn.close()

    def test_reject_with_note(self, gateway: str, db_path: Path) -> None:
        status, body = _request(
            f"{gateway}/api/decisions",
            method="POST",
            data=[
                {
                    "proposal_id": 2,
                    "decision": "reject",
                    "review_note": "Duplicate content",
                }
            ],
        )
        assert status == 200
        assert body["updated"] == 1

        conn = connect(db_path)
        rows = conn.execute(
            "SELECT decision, review_note, reviewer FROM decisions WHERE proposal_id = 2"
        ).fetchall()
        assert rows[0][0] == "reject"
        assert rows[0][1] == "Duplicate content"
        assert rows[0][2] == "gateway"
        conn.close()

    def test_cannot_change_non_pending(self, gateway: str) -> None:
        status, body = _request(
            f"{gateway}/api/decisions",
            method="POST",
            data=[{"proposal_id": 3, "decision": "reject"}],
        )
        assert body["updated"] == 0
        assert len(body["errors"]) == 1
        assert "already approve" in body["errors"][0]

    def test_invalid_decision_value(self, gateway: str) -> None:
        status, body = _request(
            f"{gateway}/api/decisions",
            method="POST",
            data=[{"proposal_id": 1, "decision": "delete"}],
        )
        assert body["updated"] == 0
        assert len(body["errors"]) == 1

    def test_nonexistent_proposal(self, gateway: str) -> None:
        status, body = _request(
            f"{gateway}/api/decisions",
            method="POST",
            data=[{"proposal_id": 999, "decision": "approve"}],
        )
        assert body["updated"] == 0
        assert "not found" in body["errors"][0].lower()

    def test_batch_decisions(self, gateway: str) -> None:
        status, body = _request(
            f"{gateway}/api/decisions",
            method="POST",
            data=[
                {"proposal_id": 1, "decision": "approve"},
                {"proposal_id": 2, "decision": "reject"},
            ],
        )
        assert status == 200
        assert body["updated"] == 2

    def test_audit_log_created(self, gateway: str, db_path: Path) -> None:
        _request(
            f"{gateway}/api/decisions",
            method="POST",
            data=[{"proposal_id": 1, "decision": "approve"}],
        )
        conn = connect(db_path)
        logs = conn.execute(
            "SELECT action, entity_id FROM audit_log WHERE action LIKE 'gateway_%'"
        ).fetchall()
        assert len(logs) >= 1
        assert logs[0][0] == "gateway_decision_approve"
        assert logs[0][1] == "1"
        conn.close()


class TestGateway404:
    def test_unknown_path(self, gateway: str) -> None:
        status, body = _request(f"{gateway}/api/unknown")
        assert status == 404
