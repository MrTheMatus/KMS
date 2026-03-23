"""Proposal lifecycle status: single source of truth derived from decisions, artifacts, executions, items."""

from __future__ import annotations

from typing import Any

from kms.app.db import fetch_all_dicts

# Canonical lifecycle values (persisted on proposals.lifecycle_status)
AWAITING_DECISION = "awaiting_decision"
APPROVED = "approved"
REJECTED = "rejected"
POSTPONED = "postponed"
APPLIED = "applied"
INDEXED = "indexed"
INDEX_FAILED = "index_failed"
APPLY_FAILED = "apply_failed"

ALL_STATUSES: tuple[str, ...] = (
    AWAITING_DECISION,
    APPROVED,
    REJECTED,
    POSTPONED,
    APPLIED,
    INDEXED,
    INDEX_FAILED,
    APPLY_FAILED,
)


def compute_lifecycle_row(row: dict[str, Any]) -> str:
    """Derive lifecycle from one joined row (proposal + decision + item + artifact + execution).

    Expected keys: decision (or None), item_status,
    artifact_id (optional), index_status (optional), workspace_name (optional).
    """
    decision = (row.get("decision") or "pending").lower().strip()
    item_status = (row.get("item_status") or "new").lower()
    artifact_id = row.get("artifact_id")
    index_status = (row.get("index_status") or "pending").lower()

    if decision == "reject":
        return REJECTED
    if decision == "postpone":
        return POSTPONED
    if decision == "pending":
        return AWAITING_DECISION

    # decision == approve
    if artifact_id is None:
        if item_status == "failed":
            return APPLY_FAILED
        return APPROVED

    # Has artifact
    if index_status == "ok":
        return INDEXED
    if index_status == "failed":
        return INDEX_FAILED
    if index_status == "skipped":
        return APPLIED
    # pending — check legacy: workspace_name set but no index_status migration
    if row.get("workspace_name"):
        return INDEXED
    return APPLIED


def recompute_lifecycle(conn: Any, proposal_id: int | None = None) -> int:
    """Recompute and UPDATE proposals.lifecycle_status. Returns number of rows updated."""
    where = "WHERE p.id = ?" if proposal_id is not None else ""
    params: tuple[Any, ...] = (proposal_id,) if proposal_id is not None else ()

    rows = fetch_all_dicts(
        conn,
        f"""SELECT p.id AS proposal_id, p.item_id,
                   COALESCE(d.decision, 'pending') AS decision,
                   i.status AS item_status,
                   a.id AS artifact_id,
                   COALESCE(a.index_status, 'pending') AS index_status,
                   a.workspace_name AS workspace_name
            FROM proposals p
            JOIN items i ON i.id = p.item_id
            LEFT JOIN decisions d ON d.proposal_id = p.id
            LEFT JOIN artifacts a ON a.proposal_id = p.id
            {where}""",
        params,
    )

    n = 0
    for row in rows:
        status = compute_lifecycle_row(
            {
                "decision": row["decision"],
                "item_status": row["item_status"],
                "artifact_id": row["artifact_id"],
                "index_status": row["index_status"],
                "workspace_name": row["workspace_name"],
            }
        )
        conn.execute(
            "UPDATE proposals SET lifecycle_status = ? WHERE id = ?",
            (status, row["proposal_id"]),
        )
        n += 1
    conn.commit()
    return n
