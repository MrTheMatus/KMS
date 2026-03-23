"""Execution snapshot JSON."""

from __future__ import annotations

import json

from kms.app.execution_snapshot import build_apply_snapshot, parse_snapshot_json


def test_build_and_parse_roundtrip() -> None:
    snap = build_apply_snapshot(
        src_rel="00_Inbox/a.md",
        dest_rel="10_Sources/web/a.md",
        source_note_relpath="20_Source-Notes/src-2026-0001.md",
        created_source_note=True,
    )
    raw = json.dumps(snap)
    out = parse_snapshot_json(raw)
    assert out["moves"][0]["from"] == "00_Inbox/a.md"
    assert "20_Source-Notes/src-2026-0001.md" in out["created_paths"]
