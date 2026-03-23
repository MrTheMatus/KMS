"""Index and compare permanent notes (canonical knowledge layer)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class PermanentNote:
    path: Path
    title: str
    text: str
    tokens: set[str]


@dataclass
class NoteMatch:
    note_path: str
    title: str
    score: float


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 2}


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def load_permanent_notes(permanent_dir: Path) -> list[PermanentNote]:
    if not permanent_dir.is_dir():
        return []
    out: list[PermanentNote] = []
    for p in sorted(permanent_dir.rglob("*.md")):
        txt = p.read_text(encoding="utf-8")
        title = _extract_title(txt, p.stem)
        out.append(PermanentNote(path=p, title=title, text=txt, tokens=_tokenize(txt)))
    return out


def find_best_matches(
    source_text: str, notes: list[PermanentNote], *, top_k: int = 3
) -> list[NoteMatch]:
    source_tokens = _tokenize(source_text)
    if not source_tokens or not notes:
        return []
    ranked: list[NoteMatch] = []
    for n in notes:
        inter = len(source_tokens.intersection(n.tokens))
        union = len(source_tokens.union(n.tokens)) or 1
        score = inter / union
        if score > 0:
            ranked.append(
                NoteMatch(note_path=n.path.as_posix(), title=n.title, score=round(score, 4))
            )
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:top_k]

