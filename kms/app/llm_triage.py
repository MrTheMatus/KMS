"""LLM-assisted triage with heuristic fallback.

Improvements:
- Auto-suggests domain and topics from content analysis
- Uses full text (not just 400 chars) for matching
- Richer reasoning with match_reason from knowledge_index
- Confidence calibration based on TF-IDF scores
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
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
    suggested_domain: str = ""
    suggested_topics: list[str] = field(default_factory=list)


# Domain detection patterns — map keywords to domain labels
_DOMAIN_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("cpp", re.compile(r"\b(c\+\+|cpp|constexpr|std::|raii|unique_ptr|shared_ptr|move semantics)\b", re.I)),
    ("angular", re.compile(r"\b(angular|ngmodule|rxjs|ngrx|component|directive|mat-)\b", re.I)),
    ("sql", re.compile(r"\b(sql|select|join|cursor|db2|postgresql|tablespace|inner join)\b", re.I)),
    ("electron-microscopy", re.compile(r"\b(tem|stem|electron dose|beam heating|radiolysis|nanothermometry|diffraction)\b", re.I)),
    ("devops", re.compile(r"\b(docker|kubernetes|systemd|nginx|ci/cd|jenkins|airflow|openshift)\b", re.I)),
    ("java", re.compile(r"\b(java|spring boot|hibernate|jvm|reflection|junit)\b", re.I)),
    ("typescript", re.compile(r"\b(typescript|promise|async|await|rxjs|observable)\b", re.I)),
    ("mainframe", re.compile(r"\b(z/os|mainframe|tuxedo|cobol|jcl|cics|db2 for z)\b", re.I)),
    ("career", re.compile(r"\b(career|rekrutacj|cv|portfolio|rozmowa kwalifikacyjna|gallup|strengths)\b", re.I)),
    ("python", re.compile(r"\b(python|pandas|airflow|numpy|matplotlib|pip)\b", re.I)),
]

# Topic extraction patterns — finer-grained than domain
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "performance": ["wydajność", "performance", "optymalizacja", "benchmark", "latency", "throughput"],
    "migration": ["migracja", "migration", "upgrade", "refactor", "modernizacja"],
    "debugging": ["debug", "błąd", "error", "troubleshoot", "fix", "diagnoz"],
    "architecture": ["architektura", "architecture", "pattern", "wzorzec", "microservice", "monolith"],
    "security": ["bezpieczeństwo", "security", "injection", "xss", "rodo", "gdpr", "compliance"],
    "testing": ["test", "e2e", "karma", "cypress", "junit", "pytest"],
    "data-science": ["pandas", "dataframe", "matplotlib", "analiza danych", "chemoinformatyka"],
    "grpc-rpc": ["grpc", "rpc", "protobuf", "connect", "websocket", "rest api"],
    "algorithms": ["algorytm", "algorithm", "sort", "linked list", "tree", "complexity"],
}


def _detect_domain(text: str) -> str:
    """Detect primary domain from text content."""
    scores: Counter = Counter()
    text_lower = text[:8000].lower()
    for domain, pattern in _DOMAIN_PATTERNS:
        hits = len(pattern.findall(text_lower))
        if hits:
            scores[domain] = hits
    if scores:
        return scores.most_common(1)[0][0]
    return ""


def _detect_topics(text: str, max_topics: int = 4) -> list[str]:
    """Detect relevant topics from text content."""
    text_lower = text[:8000].lower()
    found: list[tuple[str, int]] = []
    for topic, keywords in _TOPIC_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits >= 1:
            found.append((topic, hits))
    found.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in found[:max_topics]]


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

    ``top_k`` — number of matches in ``top_matches``.
    """
    _ = provider  # Reserved for anythingllm/cloud provider mode.
    notes = load_permanent_notes(permanent_notes_dir)
    matches = find_best_matches(source_text, notes, top_k=top_k)
    summary = summarize_text(source_text)
    domain = _detect_domain(source_text)
    topics = _detect_topics(source_text)

    if matches and matches[0].score >= 0.12:
        top = matches[0]
        # Use match_reason for richer explanation
        reason_detail = top.match_reason if hasattr(top, "match_reason") and top.match_reason else ""
        suggestion = TriageSuggestion(
            summary=summary,
            confidence=min(0.95, top.score + 0.35),
            suggested_permanent_note_action="update-existing",
            suggested_existing_note_path=top.note_path,
            reasoning=f"Silne pokrycie z «{top.title}» (score={top.score:.2f}). {reason_detail}",
            suggested_domain=top.domain or domain,
            suggested_topics=top.topics if top.topics else topics,
        )
    else:
        suggestion = TriageSuggestion(
            summary=summary,
            confidence=0.55 if matches else 0.45,
            suggested_permanent_note_action="create-new",
            suggested_existing_note_path=None,
            reasoning="Brak silnego pokrycia z notatkami kanonicznymi.",
            suggested_domain=domain,
            suggested_topics=topics,
        )
    payload = asdict(suggestion)
    payload["top_matches"] = [asdict(m) for m in matches]
    return payload
