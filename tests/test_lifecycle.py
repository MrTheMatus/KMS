"""Lifecycle status derivation."""

from __future__ import annotations

import pytest

from kms.app.lifecycle import (
    APPLIED,
    APPROVED,
    APPLY_FAILED,
    AWAITING_DECISION,
    INDEXED,
    INDEX_FAILED,
    POSTPONED,
    REJECTED,
    compute_lifecycle_row,
)


@pytest.mark.parametrize(
    "row,expected",
    [
        ({"decision": "pending"}, AWAITING_DECISION),
        ({"decision": "reject"}, REJECTED),
        ({"decision": "postpone"}, POSTPONED),
        ({"decision": "approve", "item_status": "failed", "artifact_id": None}, APPLY_FAILED),
        ({"decision": "approve", "item_status": "new", "artifact_id": None}, APPROVED),
        (
            {"decision": "approve", "artifact_id": 1, "index_status": "ok"},
            INDEXED,
        ),
        (
            {"decision": "approve", "artifact_id": 1, "index_status": "failed"},
            INDEX_FAILED,
        ),
        (
            {"decision": "approve", "artifact_id": 1, "index_status": "pending", "workspace_name": None},
            APPLIED,
        ),
        (
            {"decision": "approve", "artifact_id": 1, "index_status": "pending", "workspace_name": "ws"},
            INDEXED,
        ),
    ],
)
def test_compute_lifecycle_row(row: dict, expected: str) -> None:
    assert compute_lifecycle_row(row) == expected
