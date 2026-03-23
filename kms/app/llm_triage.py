"""LLM-assisted triage with heuristic fallback."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from kms.app.knowledge_index import find_best_matches, load_permanent_notes


@dataclass
class TriageSuggestion:
    summary: str
    confidence: float
    suggested_permanent_note_action: str
    suggested_existing_note_path: str | None
    reasoning: str


def summarize_text(text: str, max_chars: int = 400) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1] + "…"


def triage_against_permanent_notes(
    source_text: str,
    permanent_notes_dir: Path,
    *,
    provider: str = "heuristic",
    top_k: int = 3,
) -> dict[str, Any]:
    """Return serializable triage suggestion payload.

    ``top_k`` — liczba dopasowań w ``top_matches`` (np. ``merge_advisor`` używa większego ``top_k``).
    """
    _ = provider  # Reserved for anythingllm/cloud provider mode.
    notes = load_permanent_notes(permanent_notes_dir)
    matches = find_best_matches(source_text, notes, top_k=top_k)
    summary = summarize_text(source_text)
    if matches and matches[0].score >= 0.12:
        top = matches[0]
        suggestion = TriageSuggestion(
            summary=summary,
            confidence=min(0.95, top.score + 0.35),
            suggested_permanent_note_action="update-existing",
            suggested_existing_note_path=top.note_path,
            reasoning=f"High lexical overlap with '{top.title}' ({top.score:.2f}).",
        )
    else:
        suggestion = TriageSuggestion(
            summary=summary,
            confidence=0.55 if matches else 0.45,
            suggested_permanent_note_action="create-new",
            suggested_existing_note_path=None,
            reasoning="No strong overlap with canonical notes.",
        )
    payload = asdict(suggestion)
    payload["top_matches"] = [asdict(m) for m in matches]
    return payload

