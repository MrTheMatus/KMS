"""Structured snapshot for apply/revert (filesystem moves + created paths)."""

from __future__ import annotations

import json
from typing import Any


SNAPSHOT_VERSION = 1


def build_apply_snapshot(
    *,
    src_rel: str,
    dest_rel: str,
    source_note_relpath: str,
    created_source_note: bool,
) -> dict[str, Any]:
    """Minimal JSON stored in executions.snapshot_json for revert."""
    created: list[str] = []
    if created_source_note and source_note_relpath:
        created.append(source_note_relpath)
    return {
        "version": SNAPSHOT_VERSION,
        "moves": [{"from": src_rel, "to": dest_rel}],
        "created_paths": created,
        "source_note_relpath": source_note_relpath,
    }


def parse_snapshot_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        raise ValueError("empty snapshot")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid snapshot JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("snapshot must be a JSON object")
    return data
