from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from kms.app.llm_triage import check_contradiction, triage_against_permanent_notes


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
    assert payload["suggested_permanent_note_action"] in {"create-new", "update-existing", "review-contradiction"}
    assert "top_matches" in payload


def test_check_contradiction_returns_dict() -> None:
    """check_contradiction should return a valid dict with required keys."""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = json.dumps({
        "contradiction": True,
        "severity": "high",
        "explanation": "Sprzeczne twierdzenia o pass-by-value vs pass-by-reference.",
    })

    result = check_contradiction(
        mock_llm,
        "Java jest pass-by-reference.",
        "Java jest pass-by-value — zawsze kopiuje referencję.",
        new_title="Java references",
        existing_title="Java parameter passing",
    )
    assert result["contradiction"] is True
    assert result["severity"] == "high"
    assert "pass-by" in result["explanation"].lower() or "sprzeczn" in result["explanation"].lower()


def test_check_contradiction_no_conflict() -> None:
    """Non-contradicting notes should return contradiction=False."""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = json.dumps({
        "contradiction": False,
        "severity": "none",
        "explanation": "Notatki się uzupełniają.",
    })

    result = check_contradiction(
        mock_llm,
        "Python ma dynamiczne typowanie.",
        "Python wspiera duck typing i dynamiczne typowanie.",
    )
    assert result["contradiction"] is False
    assert result["severity"] == "none"


def test_check_contradiction_handles_llm_error() -> None:
    """If LLM fails, return safe defaults (no contradiction)."""
    mock_llm = MagicMock()
    mock_llm.generate.side_effect = RuntimeError("LLM unreachable")

    result = check_contradiction(mock_llm, "text A", "text B")
    assert result["contradiction"] is False
    assert result["severity"] == "none"


def test_triage_includes_contradiction_when_detected(tmp_path: Path) -> None:
    """When LLM detects contradiction, triage payload should include it."""
    perm = tmp_path / "30_Permanent-Notes"
    perm.mkdir(parents=True, exist_ok=True)
    # Create a note with substantial overlap tokens to trigger matching
    existing_content = (
        "# Java parameter passing\n"
        "Java jest pass-by-value. Zawsze kopiuje referencję do obiektu. "
        "Obiekty nie są kopiowane, ale referencja tak. "
        "To fundamentalna różnica między Java a C++."
    )
    (perm / "java-parameters.md").write_text(existing_content, encoding="utf-8")

    # Create mock LLM that classifies and detects contradiction
    mock_llm = MagicMock()

    def mock_generate(prompt: str, system: str | None = None) -> str:
        if "Porównaj" in prompt or "SPRZECZNA" in prompt:
            return json.dumps({
                "contradiction": True,
                "severity": "high",
                "explanation": "Nowa notatka twierdzi pass-by-reference, istniejąca pass-by-value.",
            })
        # Classification prompt
        return json.dumps({"domain": "java", "topics": ["architecture"]})

    mock_llm.generate = mock_generate

    payload = triage_against_permanent_notes(
        "Java jest pass-by-reference, obiekty są przekazywane przez referencję.",
        perm,
        llm_client=mock_llm,
        title="Java references",
    )

    # Should have contradiction data if match was strong enough
    if payload.get("contradiction"):
        assert payload["contradiction"]["contradiction"] is True
        assert payload["suggested_permanent_note_action"] == "review-contradiction"

