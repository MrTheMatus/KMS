"""Index and compare permanent notes (canonical knowledge layer).

Improvements over the original Jaccard-only approach:
- TF-IDF weighting so common words ("code", "function") matter less
- Bigram matching to catch multi-word concepts ("smart pointers", "move semantics")
- YAML frontmatter extraction for domain/topics metadata
- Title-boosted scoring (title matches are 3x more relevant)
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PermanentNote:
    path: Path
    title: str
    text: str
    tokens: set[str]
    domain: str = ""
    topics: list[str] = field(default_factory=list)
    title_tokens: set[str] = field(default_factory=set)
    bigrams: set[str] = field(default_factory=set)
    token_counts: Counter = field(default_factory=Counter)


@dataclass
class NoteMatch:
    note_path: str
    title: str
    score: float
    domain: str = ""
    topics: list[str] = field(default_factory=list)
    match_reason: str = ""


_TOKEN_RE = re.compile(r"[A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+")

# Common stopwords that add noise to matching
_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "from",
        "are",
        "was",
        "but",
        "not",
        "you",
        "all",
        "can",
        "had",
        "her",
        "one",
        "our",
        "out",
        "has",
        "have",
        "been",
        "will",
        "they",
        "its",
        "also",
        "use",
        "jak",
        "jest",
        "nie",
        "przy",
        "dla",
        "lub",
        "ale",
        "czy",
        "pod",
        "nad",
        "bez",
        "kod",
        "code",
        "jest",
        "może",
        "oraz",
        "tego",
        "które",
        "jest",
        "gdzie",
        "jako",
        "tylko",
        "jednak",
        "więc",
    }
)


def _tokenize(text: str) -> set[str]:
    """Tokenize text, filtering stopwords and short tokens."""
    return {
        t.lower()
        for t in _TOKEN_RE.findall(text)
        if len(t) > 2 and t.lower() not in _STOPWORDS
    }


def _tokenize_counted(text: str) -> Counter:
    """Tokenize with frequency counts for TF computation."""
    tokens = [
        t.lower()
        for t in _TOKEN_RE.findall(text)
        if len(t) > 2 and t.lower() not in _STOPWORDS
    ]
    return Counter(tokens)


def _bigrams(text: str) -> set[str]:
    """Extract word bigrams for multi-word concept matching."""
    words = [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 2]
    return {f"{words[i]}_{words[i + 1]}" for i in range(len(words) - 1)}


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _extract_frontmatter(text: str) -> dict[str, str]:
    """Extract domain and topics from YAML frontmatter if present."""
    result: dict[str, str] = {}
    if not text.lstrip().startswith("---"):
        return result
    lines = text.split("\n")
    in_fm = False
    for line in lines:
        if line.strip() == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if in_fm:
            if line.startswith("domain:"):
                val = line.split(":", 1)[1].strip().strip('"').strip("'")
                if val and val != "null":
                    result["domain"] = val
            elif line.startswith("topics:"):
                val = line.split(":", 1)[1].strip()
                if val.startswith("["):
                    topics = re.findall(r'"([^"]+)"', val)
                    if topics:
                        result["topics"] = ",".join(topics)
    return result


def load_permanent_notes(permanent_dir: Path) -> list[PermanentNote]:
    if not permanent_dir.is_dir():
        return []
    out: list[PermanentNote] = []
    for p in sorted(permanent_dir.rglob("*.md")):
        txt = p.read_text(encoding="utf-8")
        title = _extract_title(txt, p.stem)
        fm = _extract_frontmatter(txt)
        topics_list = fm.get("topics", "").split(",") if fm.get("topics") else []
        out.append(
            PermanentNote(
                path=p,
                title=title,
                text=txt,
                tokens=_tokenize(txt),
                domain=fm.get("domain", ""),
                topics=topics_list,
                title_tokens=_tokenize(title),
                bigrams=_bigrams(txt),
                token_counts=_tokenize_counted(txt),
            )
        )
    return out


def _compute_idf(notes: list[PermanentNote]) -> dict[str, float]:
    """Compute inverse document frequency across corpus."""
    n_docs = len(notes)
    if n_docs == 0:
        return {}
    doc_freq: Counter = Counter()
    for note in notes:
        doc_freq.update(note.tokens)
    return {
        token: math.log((n_docs + 1) / (df + 1)) + 1.0 for token, df in doc_freq.items()
    }


def find_best_matches(
    source_text: str, notes: list[PermanentNote], *, top_k: int = 3
) -> list[NoteMatch]:
    source_tokens = _tokenize(source_text)
    source_bigrams = _bigrams(source_text)
    if not source_tokens or not notes:
        return []

    idf = _compute_idf(notes)

    ranked: list[NoteMatch] = []
    for n in notes:
        # TF-IDF weighted overlap (replaces raw Jaccard)
        common_tokens = source_tokens & n.tokens
        if not common_tokens:
            continue

        # Weighted score: sum of IDF for shared tokens / sum of IDF for union
        shared_weight = sum(idf.get(t, 1.0) for t in common_tokens)
        union_weight = sum(idf.get(t, 1.0) for t in (source_tokens | n.tokens))
        tfidf_score = shared_weight / union_weight if union_weight else 0

        # Title boost: matching title tokens are 3x more valuable
        title_overlap = source_tokens & n.title_tokens
        title_boost = len(title_overlap) * 0.03 if title_overlap else 0

        # Bigram bonus: multi-word concepts matching
        common_bigrams = source_bigrams & n.bigrams
        bigram_bonus = min(len(common_bigrams) * 0.01, 0.1)

        score = tfidf_score + title_boost + bigram_bonus

        # Build match reason for reviewer
        reasons = []
        if title_overlap:
            reasons.append(f"tytuł: {', '.join(sorted(title_overlap)[:5])}")
        top_shared = sorted(common_tokens, key=lambda t: idf.get(t, 0), reverse=True)[
            :5
        ]
        reasons.append(f"tokeny: {', '.join(top_shared)}")
        if common_bigrams:
            reasons.append(f"bigramy: {', '.join(sorted(common_bigrams)[:3])}")

        ranked.append(
            NoteMatch(
                note_path=n.path.as_posix(),
                title=n.title,
                score=round(score, 4),
                domain=n.domain,
                topics=n.topics,
                match_reason="; ".join(reasons),
            )
        )
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:top_k]
