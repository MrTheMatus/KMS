"""Opcjonalna warstwa nad ``llm_triage``: heurystyki merge/konflikt + markdown pod AnythingLLM.

Nie wywołuje LLM w Pythonie; nie mutuje vaultu. To samo indeksowanie leksykalne co
``triage_against_permanent_notes`` (``knowledge_index``), z dodatkową klasyfikacją dla reviewera.

Zob. ``kms-principles.md`` §9 — granica wobec „automatycznego merge” z architecture.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from kms.app.knowledge_index import (
    PermanentNote,
    find_best_matches,
    load_permanent_notes,
)
from kms.app.llm_triage import summarize_text


_STANCE_NEG = re.compile(
    r"\b(avoid|never|do not|don't|unsafe|leak|race|undefined|forbidden)\b",
    re.I,
)
_STANCE_POS = re.compile(
    r"\b(prefer|always|should|recommended|safe|modern|idiomatic)\b",
    re.I,
)


@dataclass
class MergeAdvisorResult:
    """Structured output for reviewers and LLM follow-up."""

    recommendation: str
    """One of: duplicate, conflict, merge_candidate, enrich_existing, independent."""

    confidence: float
    summary: str
    reasoning: str
    top_matches: list[dict[str, Any]] = field(default_factory=list)
    related_note_paths: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    conflict_signals: list[str] = field(default_factory=list)
    llm_prompt_markdown: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def _stance_balance(text: str) -> tuple[int, int]:
    neg = len(_STANCE_NEG.findall(text[:2000]))
    pos = len(_STANCE_POS.findall(text[:2000]))
    return neg, pos


def _read_note_text(_permanent_dir: Path, rel_or_abs: str) -> str:
    p = Path(rel_or_abs)
    if not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def analyze_incoming_vs_corpus(
    incoming_text: str,
    permanent_notes_dir: Path,
    *,
    top_k: int = 5,
) -> MergeAdvisorResult:
    """Heuristic analysis: duplicates, conflicts, merge vs new note.

    This does **not** call an LLM; it prepares ``llm_prompt_markdown`` for one.
    """
    notes = load_permanent_notes(permanent_notes_dir)
    matches = find_best_matches(incoming_text, notes, top_k=top_k)
    top_matches = [asdict(m) for m in matches]

    summary = summarize_text(incoming_text, max_chars=800)

    if not matches:
        return MergeAdvisorResult(
            recommendation="independent",
            confidence=0.5,
            summary=summary,
            reasoning="Brak sensownego pokrycia leksykalnego z notatkami kanonicznymi.",
            top_matches=[],
            suggested_actions=[
                "Potraktuj jako nową niezależną notatkę lub source note.",
                "Po zatwierdzeniu rozważ dodanie linków z warstwy permanent.",
            ],
            llm_prompt_markdown=_build_prompt_stub(
                incoming_text, notes, matches, "independent"
            ),
        )

    best = matches[0]
    second = matches[1] if len(matches) > 1 else None

    # Duplicate: very high overlap + same topic keywords in title
    if best.score >= 0.22 and _titles_similar(
        _title_from_path(best.note_path), incoming_text[:400]
    ):
        rec = "duplicate"
        conf = min(0.95, 0.55 + best.score)
        reason = (
            f"Bardzo wysokie pokrycie z «{best.title}» (score={best.score:.3f}). "
            "Prawdopodobny duplikat tematu lub wersja do scalenia ręcznego."
        )
        actions = [
            "Odrzuć duplikat lub scal treść ręcznie w istniejącej notatce.",
            f"Otwórz: `{best.note_path}` i porównaj akapity.",
        ]
    elif best.score >= 0.18 and second and second.score >= 0.14:
        t1 = _read_note_text(permanent_notes_dir, best.note_path)
        t2 = _read_note_text(permanent_notes_dir, second.note_path)
        n1, p1 = _stance_balance(t1)
        n2, p2 = _stance_balance(t2)
        inc_neg, inc_pos = _stance_balance(incoming_text)
        if _possible_conflict(inc_neg, inc_pos, n1, p1, n2, p2):
            rec = "conflict"
            conf = 0.62
            reason = (
                "Dwa silne dopasowania z różnym balansem „ostrzeżeń” vs „rekomendacji”. "
                "Możliwa sprzeczność merytoryczna — wymaga decyzji człowieka."
            )
            actions = [
                "Przeczytaj obie notatki kanoniczne i nowy tekst z inboxu.",
                "Zapisz jawny kompromis w jednej notatce lub oznacz wyjątek.",
            ]
        else:
            rec = "merge_candidate"
            conf = 0.68
            reason = (
                f"Średnie/wysokie pokrycie z «{best.title}»; drugi kandydat: «{second.title}». "
                "Rozważ rozszerzenie istniejącej sekcji zamiast nowego pliku."
            )
            actions = [
                f"Dodaj podsekcję do `{best.note_path}` lub połącz z `{second.note_path}`.",
                "Użyj linków Obsidian między powiązanymi idiomami.",
            ]
    elif best.score >= 0.12:
        rec = "enrich_existing"
        conf = 0.6 + best.score * 0.5
        reason = (
            f"Wykryto pokrycie z «{best.title}» (score={best.score:.3f}). "
            "Nowy materiał może wzbogacić istniejącą notatkę."
        )
        actions = [
            f"Otwórz `{best.note_path}` i dodaj brakujące idiomy / przykłady.",
            "Unikaj duplikacji nagłówków — scal w jedną sekcję.",
        ]
    else:
        rec = "independent"
        conf = 0.52
        reason = (
            "Słabe pokrycie — traktuj jako odrębny temat lub szkic pod przyszły merge."
        )
        actions = ["Utwórz nową permanent note lub zostaw w source layer do review."]

    conflict_signals: list[str] = []
    if rec == "conflict":
        conflict_signals.append("stance_mismatch_between_top_two_matches")

    result = MergeAdvisorResult(
        recommendation=rec,
        confidence=round(conf, 4),
        summary=summary,
        reasoning=reason,
        top_matches=top_matches,
        related_note_paths=[m.note_path for m in matches[:3]],
        suggested_actions=actions,
        conflict_signals=conflict_signals,
        llm_prompt_markdown=_build_prompt_stub(incoming_text, notes, matches, rec),
    )
    return result


def _title_from_path(note_path: str) -> str:
    stem = Path(note_path).stem.replace("-", " ")
    return stem


def _titles_similar(title: str, snippet: str) -> bool:
    tt = set(re.findall(r"[a-z0-9]{4,}", title.lower()))
    sn = set(re.findall(r"[a-z0-9]{4,}", snippet.lower()))
    if not tt:
        return False
    inter = len(tt & sn)
    return inter >= 2 or (inter >= 1 and len(tt) <= 3)


def _possible_conflict(
    in_neg: int,
    in_pos: int,
    n1: int,
    p1: int,
    n2: int,
    p2: int,
) -> bool:
    """Rough heuristic: incoming aligns with one note's warnings and other note's praise."""
    if n1 + p1 < 2 or n2 + p2 < 2:
        return False
    # Different quadrants
    if (n1 > p1 and p2 > n2) or (p1 > n1 and n2 > p2):
        return True
    if in_neg > in_pos + 1 and p1 > n1 and n2 > p2:
        return True
    if in_pos > in_neg + 1 and n1 > p1 and p2 > n2:
        return True
    return False


def _build_prompt_stub(
    incoming_text: str,
    notes: list[PermanentNote],
    matches: list[Any],
    rec: str,
) -> str:
    """Build a markdown block for pasting into Ollama / cloud chat."""
    lines = [
        "# KMS merge advisor — prompt (wklej do LLM)",
        "",
        "Jesteś asystentem KMS. Masz **nowy tekst z inboxu** i **istniejące notatki kanoniczne**.",
        "Odpowiedz po polsku, zwięźle, w sekcjach:",
        "",
        "1. **Streszczenie** (3–5 zdań) — o czym jest nowy tekst.",
        "2. **Duplikaty** — czy powiela istniejący materiał? Jakie ścieżki?",
        "3. **Konflikty** — czy są sprzeczne z zapisami w kanonie? Zacytuj fragmenty.",
        "4. **Rekomendacja** — jedna z: `merge_do_istniejącej` | `nowa_notatka` | `odrzuć_duplikat` | `scalenie_ręczne` | `wymaga_decyzji`.",
        "5. **Kroki** — lista numerowana co zrobić reviewerowi w Obsidian.",
        "",
        f"Heurystyczna wstępna klasyfikacja: **{rec}**.",
        "",
        "## Nowy tekst (inbox)",
        "```",
        incoming_text[:6000],
        "```",
        "",
        "## Top dopasowania (fragmenty)",
    ]
    path_by_str = {n.path.as_posix(): n for n in notes}
    for m in matches[:3]:
        n = path_by_str.get(m.note_path)
        if not n:
            continue
        excerpt = n.text[:1200] + ("…" if len(n.text) > 1200 else "")
        lines.append(f"### {m.title} (`{Path(m.note_path).name}`)")
        lines.append("```")
        lines.append(excerpt)
        lines.append("```")
        lines.append("")
    lines.append("---")
    lines.append("_Koniec promptu KMS merge advisor._")
    return "\n".join(lines)


def render_prompt_from_template(
    template_path: Path,
    *,
    incoming_text: str,
    result: MergeAdvisorResult,
    extra: dict[str, Any] | None = None,
) -> str:
    """Render Jinja2 template if available; else fall back to stub in result."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        return result.llm_prompt_markdown

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(enabled_extensions=("md.j2", "j2")),
    )
    tpl = env.get_template(template_path.name)
    ctx = {
        "incoming_text": incoming_text,
        "result": result,
        "result_dict": result.to_json_dict(),
        **(extra or {}),
    }
    return tpl.render(**ctx)
