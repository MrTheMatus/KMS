"""Tests for kms.gateway.server: auth, validation, happy-path, audit trail."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Generator
from unittest.mock import patch

import pytest
import yaml

from kms.app.db import connect, ensure_schema


@pytest.fixture
def _gateway_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Set up a temp DB, config, and token for the gateway app."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_Inbox").mkdir(parents=True)
    (vault / "00_Admin").mkdir(parents=True)
    db_path = tmp_path / "state.db"
    cfg = {
        "vault": {
            "root": str(vault),
            "admin_dir": "00_Admin",
            "inbox_dir": "00_Inbox",
            "sources_web": "10_Sources/web",
            "sources_pdf": "10_Sources/pdf",
            "source_notes": "20_Source-Notes",
            "permanent_notes": "30_Permanent-Notes",
            "archive_dir": "99_Archive",
        },
        "database": {"path": str(db_path)},
        "paths": {
            "review_queue_file": "00_Admin/review-queue.md",
            "daily_report_dir": "00_Admin/reports",
        },
        "templates": {"source_note": "kms/templates/source_note.md.j2"},
        "runtime": {"profile": "local"},
        "logging": {"level": "WARNING"},
        "anythingllm": {"enabled": False},
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    schema = Path(__file__).resolve().parents[1] / "kms" / "app" / "schema.sql"
    conn = connect(db_path)
    ensure_schema(conn, schema)
    conn.execute(
        "INSERT INTO items (path, kind, hash, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("00_Inbox/test.md", "markdown", "abc123", "new", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
    )
    conn.execute(
        "INSERT INTO proposals (item_id, suggested_action, suggested_target, reason, created_at) VALUES (?, ?, ?, ?, ?)",
        (1, "move_to_web", "10_Sources/web/test.md", "test", "2026-01-01T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("KMS_GATEWAY_TOKEN", "test-secret-token-1234")
    monkeypatch.setenv("KMS_CONFIG_PATH", str(cfg_path))

    return {"db_path": db_path, "cfg_path": cfg_path, "schema": schema}


@pytest.fixture
def client(_gateway_env: dict[str, Any]) -> Any:
    from kms.gateway.server import create_app

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _auth_header() -> dict[str, str]:
    return {"Authorization": "Bearer test-secret-token-1234"}


class TestHealth:
    def test_health_no_auth_required(self, client: Any) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.get_json()["ok"] is True


class TestAuth:
    def test_pending_without_token_returns_401(self, client: Any) -> None:
        r = client.get("/api/pending")
        assert r.status_code == 401

    def test_decisions_without_token_returns_401(self, client: Any) -> None:
        r = client.post("/api/decisions", json={"proposal_id": 1, "decision": "approve"})
        assert r.status_code == 401

    def test_wrong_token_returns_401(self, client: Any) -> None:
        r = client.get("/api/pending", headers={"Authorization": "Bearer wrong"})
        assert r.status_code == 401

    def test_query_param_token_works(self, client: Any) -> None:
        r = client.get("/api/pending?token=test-secret-token-1234")
        assert r.status_code == 200


class TestPending:
    def test_returns_pending_proposals(self, client: Any) -> None:
        r = client.get("/api/pending", headers=_auth_header())
        assert r.status_code == 200
        data = r.get_json()
        assert len(data["items"]) == 1
        assert data["items"][0]["proposal_id"] == 1


class TestDecisions:
    def test_approve_proposal(self, client: Any, _gateway_env: dict[str, Any]) -> None:
        r = client.post(
            "/api/decisions",
            json={"proposal_id": 1, "decision": "approve", "reviewer": "tester"},
            headers=_auth_header(),
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert data["decision"] == "approve"

        r2 = client.get("/api/pending", headers=_auth_header())
        assert len(r2.get_json()["items"]) == 0

    def test_invalid_decision_returns_400(self, client: Any) -> None:
        r = client.post(
            "/api/decisions",
            json={"proposal_id": 1, "decision": "invalid_value"},
            headers=_auth_header(),
        )
        assert r.status_code == 400

    def test_missing_proposal_id_returns_400(self, client: Any) -> None:
        r = client.post(
            "/api/decisions",
            json={"decision": "approve"},
            headers=_auth_header(),
        )
        assert r.status_code == 400

    def test_empty_body_returns_400(self, client: Any) -> None:
        r = client.post("/api/decisions", headers=_auth_header())
        assert r.status_code == 400

    def test_upsert_changes_decision(self, client: Any, _gateway_env: dict[str, Any]) -> None:
        client.post(
            "/api/decisions",
            json={"proposal_id": 1, "decision": "approve"},
            headers=_auth_header(),
        )
        client.post(
            "/api/decisions",
            json={"proposal_id": 1, "decision": "reject"},
            headers=_auth_header(),
        )
        conn = sqlite3.connect(_gateway_env["db_path"])
        row = conn.execute("SELECT decision FROM decisions WHERE proposal_id = 1").fetchone()
        conn.close()
        assert row[0] == "reject"


class TestAudit:
    def test_decision_creates_audit_entry(self, client: Any, _gateway_env: dict[str, Any]) -> None:
        client.post(
            "/api/decisions",
            json={"proposal_id": 1, "decision": "approve", "reviewer": "auditor"},
            headers=_auth_header(),
        )
        conn = sqlite3.connect(_gateway_env["db_path"])
        row = conn.execute(
            "SELECT action, entity_type, entity_id FROM audit_log WHERE action = 'gateway_decision'"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "gateway_decision"
        assert row[1] == "proposal"
        assert row[2] == "1"
