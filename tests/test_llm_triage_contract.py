from __future__ import annotations

from pathlib import Path

from kms.app.llm_triage import triage_against_permanent_notes


def test_llm_triage_contract_has_required_fields(tmp_path: Path) -> None:
    perm = tmp_path / "30_Permanent-Notes"
    perm.mkdir(parents=True, exist_ok=True)
    (perm / "pv-costs.md").write_text("# PV costs\nGrid storage tariff details and costs.", encoding="utf-8")

    payload = triage_against_permanent_notes(
        "This source describes tariff and grid storage costs for PV systems.",
        perm,
    )
    assert isinstance(payload["summary"], str)
    assert isinstance(payload["confidence"], float)
    assert payload["suggested_permanent_note_action"] in {"create-new", "update-existing"}
    assert "top_matches" in payload

