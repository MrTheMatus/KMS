"""Tests for kms.app.merge_advisor heuristics and prompt rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from kms.app.merge_advisor import analyze_incoming_vs_corpus, render_prompt_from_template


@pytest.fixture
def cpp_corpus() -> Path:
    return Path(__file__).resolve().parents[1] / "example-vault" / "30_Permanent-Notes" / "cpp-corpus"


def test_analyze_independent_when_no_overlap(cpp_corpus: Path) -> None:
    r = analyze_incoming_vs_corpus("xyzabc nonsense token zzzqqq", cpp_corpus)
    assert r.recommendation == "independent"
    assert r.confidence < 0.55


def test_analyze_raii_overlap(cpp_corpus: Path) -> None:
    text = """
    RAII means resource acquisition is initialization. Destructor frees FILE handle.
    Use lock_guard for mutex RAII. See also scope exit patterns.
    """
    r = analyze_incoming_vs_corpus(text, cpp_corpus)
    assert r.recommendation in ("duplicate", "enrich_existing", "merge_candidate", "conflict", "independent")
    assert r.top_matches
    assert any("raii" in (m.get("title") or "").lower() or "raii" in (m.get("note_path") or "").lower() for m in r.top_matches)


def test_render_prompt_contains_sections(cpp_corpus: Path, tmp_path: Path) -> None:
    r = analyze_incoming_vs_corpus("std::unique_ptr ownership", cpp_corpus)
    tpl = Path(__file__).resolve().parents[1] / "kms" / "templates" / "merge_advisor_prompt.md.j2"
    out = render_prompt_from_template(tpl, incoming_text="hello", result=r)
    assert "KMS" in out
    assert "Streszczenie" in out or "streszczenie" in out.lower()


def test_analyze_returns_prompt_stub(cpp_corpus: Path) -> None:
    r = analyze_incoming_vs_corpus("optional std::optional", cpp_corpus)
    assert len(r.llm_prompt_markdown) > 100
    assert "inbox" in r.llm_prompt_markdown.lower() or "Nowy tekst" in r.llm_prompt_markdown
