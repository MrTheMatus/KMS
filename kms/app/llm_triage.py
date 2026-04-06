"""LLM-assisted triage with heuristic fallback.

Improvements over v1:
- Extensive domain patterns (English + Polish keywords)
- Rich topic vocabulary with Polish inflection-aware matching
- Optional LLM-based classification for higher accuracy
- Full text (not just 400 chars) for matching
- Richer reasoning with match_reason from knowledge_index
- Confidence calibration based on TF-IDF scores
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from kms.app.knowledge_index import find_best_matches, load_permanent_notes

if TYPE_CHECKING:
    from kms.app.llm_client import LLMClient

_LOG = logging.getLogger(__name__)


@dataclass
class TriageSuggestion:
    summary: str
    confidence: float
    suggested_permanent_note_action: str
    suggested_existing_note_path: str | None
    reasoning: str
    suggested_domain: str = ""
    suggested_topics: list[str] = field(default_factory=list)


# ── Domain detection patterns ───────────────────────────────────────
# Each tuple: (domain_label, compiled_regex)
# Patterns are case-insensitive, include English + Polish keywords.

_DOMAIN_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "cpp",
        re.compile(
            r"(?:c\+\+|cpp\b|constexpr|std::|raii|unique_ptr|shared_ptr|move.?semantics"
            r"|template\s*<|destruktor|wirtualn[aey]|wskaźnik|nullptr|noexcept|vtable"
            r"|polimorfizm|dziedziczen|klasa\s+bazow|operator\s+new|operator\s+delete"
            r"|reinterpret_cast|static_cast|dynamic_cast|const_cast|sizeof\s*\("
            r"|#include\s*<|namespace\s+\w|cmake|makefile|gcc|clang|g\+\+|msvc"
            r"|stl\b|vector\s*<|map\s*<|deque|queue|stack|iterator"
            r"|pamięci|zarządzanie\s+pamięcią|wycieki?\s+pamięci|smart.?pointer"
            r"|goto\b|longjmp|setjmp|volatile|mutable|extern\s+\"C\")",
            re.I,
        ),
    ),
    (
        "angular",
        re.compile(
            r"(?:angular(?:js)?|ngmodule|ng-|@component|@directive|@injectable|@pipe"
            r"|rxjs|ngrx|observable|subscribe|behaviorsubject|mat-|matdialog"
            r"|standalone.?component|signal[s]?\b|zoneless|change.?detection"
            r"|template.?driven|reactive.?form|router.?outlet|lazy.?load"
            r"|angular\.json|ng\s+serve|ng\s+build|ng\s+generate"
            r"|komponent|dyrektywa|serwis|moduł.*angular|scss|styleurl)",
            re.I,
        ),
    ),
    (
        "sql",
        re.compile(
            r"(?:\bsql\b|select\s+\w|insert\s+into|update\s+\w+\s+set|delete\s+from"
            r"|inner\s+join|left\s+join|right\s+join|cross\s+join|group\s+by|order\s+by"
            r"|having\b|where\s+\w|create\s+table|alter\s+table|drop\s+table"
            r"|cursor\b|stored\s+proc|trigger\b|index\s+on|tablespace"
            r"|postgresql|mysql|oracle\s+db|sqlite|mariadb|db2\b|mssql"
            r"|transakcj|zapytani[ae]|baza\s+danych|relacyjn|normalizacj"
            r"|optymalizacj.*zapyta|explain\s+plan|execution\s+plan)",
            re.I,
        ),
    ),
    (
        "electron-microscopy",
        re.compile(
            r"(?:\btem\b|stem\b|electron\s+(?:dose|beam|microscop|diffraction)"
            r"|beam.?heating|radiolysis|nanothermometr|cryo.?tem|cryo.?em"
            r"|mikroskop.*elektron|wiązk[aię].*elektron|dyfrakc|transmisy"
            r"|próbk[aię]|preparatyk|dawka.*elektron|dawkami\s+elektron"
            r"|skaningow|eels\b|eds\b|haadf|saed|fib\b"
            r"|faz[aęoy]|przemiany?\s+fazow|krystalograf|amorficzn"
            r"|nanostruktur|nanomateriał|cienk[aie]\s+warstw)",
            re.I,
        ),
    ),
    (
        "devops",
        re.compile(
            r"(?:docker|kubernetes|k8s|systemd|nginx|ci/cd|jenkins|airflow"
            r"|openshift|terraform|ansible|helm|gitlab.?ci|github.?actions"
            r"|pipeline|deploy|kontener|wdrożeni|infrastruktur"
            r"|load.?balanc|reverse.?proxy|monitoring|prometheus|grafana"
            r"|logowanie.*serwer|linux|bash|shell|cron|ssh|ssl/tls"
            r"|dns\b|vpc\b|subnet|firewall|aws|gcp|azure(?!\s+devops))",
            re.I,
        ),
    ),
    (
        "java",
        re.compile(
            r"(?:\bjava\b(?!script)|spring\s*boot|hibernate|jvm\b|jdk\b"
            r"|maven|gradle|junit|mockito|lombok|@autowired|@bean"
            r"|@controller|@service|@repository|servlet|tomcat|jakarta"
            r"|collections\b|stream\(\)|optional\.|lambda.*java"
            r"|interfejs.*java|klasa.*abstract|enum\s+\w+\s*\{)",
            re.I,
        ),
    ),
    (
        "typescript",
        re.compile(
            r"(?:typescript|\.ts\b|interface\s+\w+\s*\{|type\s+\w+\s*="
            r"|generic[s]?\b|enum\b.*typescript|promise<|async\s+function"
            r"|decorator|tsconfig|tsc\b|strict.?mode.*ts"
            r"|union\s+type|intersection|mapped\s+type|conditional\s+type"
            r"|readonly\b|partial<|required<|pick<|omit<)",
            re.I,
        ),
    ),
    (
        "react",
        re.compile(
            r"(?:react(?:\.js)?|jsx|tsx|usestate|useeffect|usecontext|usememo"
            r"|usecallback|useref|usereducer|next\.?js|gatsby|redux"
            r"|react.?router|react.?query|komponent.*react|hook[isy]?\b)",
            re.I,
        ),
    ),
    (
        "mainframe",
        re.compile(
            r"(?:z/os|mainframe|tuxedo|cobol|jcl|cics|db2\s+for\s+z"
            r"|ebcdic|vsam|ims\b|mvs\b|tso\b|ispf|rexx|racf"
            r"|sysplex|lpar|coupling\s+facility)",
            re.I,
        ),
    ),
    (
        "career",
        re.compile(
            r"(?:career|kariera|rekrutacj|cv\b|portfolio|rozmow[aęy]\s+kwalifikacy"
            r"|gallup|strengths|negocjacj|awans|podwyżk|wynagrodzeni"
            r"|kompetencj|rozwój\s+zawodow|ścieżk[aię]\s+kariery"
            r"|lider|leadership|mentor|management|zarządzani"
            r"|feedback|ocena\s+pracown|onboarding|offboarding"
            r"|praca\s+zdalna|remote\s+work|freelanc|kontrakt\s+b2b"
            r"|soft\s*skill|umiejętności\s+miękk|komunikacj[aię]"
            r"|product\s+owner|scrum\s+master|agile\s+coach)",
            re.I,
        ),
    ),
    (
        "python",
        re.compile(
            r"(?:\bpython\b|pandas|numpy|matplotlib|pip\b|pipenv|poetry"
            r"|django|flask|fastapi|sqlalchemy|pydantic|pytest|mypy"
            r"|virtualenv|venv|\.py\b|import\s+\w+|from\s+\w+\s+import"
            r"|dekorator|generator|iterator.*python|list\s+comprehension"
            r"|f-string|walrus|dataclass)",
            re.I,
        ),
    ),
    (
        "networking",
        re.compile(
            r"(?:tcp/ip|udp\b|http[s]?\b|websocket|grpc|rest\s*api"
            r"|protobuf|graphql|oauth|jwt\b|cors\b|ssl|tls"
            r"|protokół|sieciow|routing|load.?balanc"
            r"|mikroserwis|microservice|api\s+gateway|service\s+mesh)",
            re.I,
        ),
    ),
    (
        "research",
        re.compile(
            r"(?:badani[ae]|research|eksperyment|hipotez|metodologi"
            r"|analiz[aęy]\s+(?:danych|wyników|statystyczn)|publikacj"
            r"|artykuł\s+naukow|paper\b|doi\b|abstract\b|peer.?review"
            r"|plan\s+badawcz|wynik[ió]\s+bada|laboratori"
            r"|nauk[aię]|naukow|akademi)",
            re.I,
        ),
    ),
    (
        "rust",
        re.compile(
            r"(?:\brust\b|cargo\b|rustc|ownership|borrow.?checker"
            r"|lifetime|trait\b|impl\b|enum\s*\{|match\s*\{|unwrap\(\)"
            r"|option<|result<|tokio|async-std|wasm)",
            re.I,
        ),
    ),
    (
        "dotnet",
        re.compile(
            r"(?:\.net|c#|csharp|asp\.net|blazor|entity\s+framework"
            r"|nuget|mstest|xunit|linq|wpf|maui|xamarin"
            r"|@model|razor|signalr)",
            re.I,
        ),
    ),
    (
        "go",
        re.compile(
            r"(?:\bgo\b(?:lang)?|goroutine|channel\b|defer\b|func\s+\w+"
            r"|package\s+main|go\s+mod|go\s+build|interface\s*\{\})",
            re.I,
        ),
    ),
]

# ── Topic extraction keywords ───────────────────────────────────────
# Each topic has a list of keywords (English + Polish).

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "performance": [
        "wydajność",
        "performance",
        "optymalizacja",
        "optimization",
        "benchmark",
        "latency",
        "throughput",
        "cache",
        "profil",
        "bottleneck",
        "szybkość",
        "opóźnieni",
        "pamięć",
        "memory",
        "cpu",
        "gpu",
    ],
    "migration": [
        "migracja",
        "migration",
        "upgrade",
        "refactor",
        "modernizacja",
        "legacy",
        "przepisywani",
        "konwersja",
        "portowani",
        "backward.?compat",
    ],
    "debugging": [
        "debug",
        "błąd",
        "error",
        "troubleshoot",
        "fix",
        "diagnoz",
        "stack.?trace",
        "exception",
        "crash",
        "segfault",
        "core.?dump",
        "logowani",
        "breakpoint",
        "inspect",
    ],
    "architecture": [
        "architektura",
        "architecture",
        "pattern",
        "wzorzec",
        "microservice",
        "monolith",
        "clean.?arch",
        "hexagonal",
        "cqrs",
        "event.?sourc",
        "domain.?driven",
        "ddd",
        "solid",
        "dependency.?inject",
        "ioc",
        "warstwa",
        "layer",
        "moduł",
        "component",
    ],
    "security": [
        "bezpieczeństwo",
        "security",
        "injection",
        "xss",
        "csrf",
        "rodo",
        "gdpr",
        "compliance",
        "auth",
        "uwierzytelni",
        "autoryzacj",
        "szyfrowanie",
        "encryption",
        "vulnerability",
        "penetr",
    ],
    "testing": [
        "test",
        "e2e",
        "karma",
        "cypress",
        "junit",
        "pytest",
        "mock",
        "stub",
        "tdd",
        "bdd",
        "coverage",
        "assertion",
        "spec",
        "integracyjn",
        "jednostkow",
        "automatyczn.*test",
    ],
    "data-science": [
        "pandas",
        "dataframe",
        "matplotlib",
        "analiza danych",
        "chemoinformatyka",
        "machine.?learning",
        "deep.?learning",
        "neural",
        "model.*train",
        "dataset",
        "feature",
        "regression",
        "classification",
    ],
    "networking": [
        "grpc",
        "rpc",
        "protobuf",
        "connect",
        "websocket",
        "rest.?api",
        "graphql",
        "http",
        "tcp",
        "protokół",
        "endpoint",
        "api",
    ],
    "algorithms": [
        "algorytm",
        "algorithm",
        "sort",
        "linked.?list",
        "tree",
        "complexity",
        "big.?o",
        "rekurencj",
        "dynamic.?program",
        "graph",
        "binary.?search",
        "hash.?map",
    ],
    "management": [
        "zarządzani",
        "management",
        "projekt",
        "sprint",
        "backlog",
        "scrum",
        "kanban",
        "agile",
        "waterfall",
        "deadline",
        "estymacj",
        "planowani",
        "priorytet",
        "stakeholder",
        "roadmap",
    ],
    "research": [
        "badani",
        "research",
        "eksperyment",
        "hipotez",
        "metodologi",
        "analiz.*wyników",
        "publikacj",
        "naukow",
        "laboratori",
        "obserwacj",
        "próbk",
        "pomiar",
    ],
    "career": [
        "kariera",
        "career",
        "rekrutacj",
        "rozmowa.*kwalifikac",
        "negocjacj",
        "awans",
        "podwyżk",
        "kompetencj",
        "cv",
        "portfolio",
        "mentor",
        "lider",
        "leadership",
        "onboarding",
    ],
    "frontend": [
        "frontend",
        "css",
        "scss",
        "html",
        "dom",
        "responsive",
        "layout",
        "flexbox",
        "grid",
        "animation",
        "ux",
        "ui",
        "stylowani",
        "interfejs.*użytkownik",
    ],
    "backend": [
        "backend",
        "serwer",
        "server",
        "baza.*danych",
        "database",
        "orm",
        "endpoint",
        "middleware",
        "cache.*serwer",
        "kolejk",
        "queue",
        "worker",
        "cron",
    ],
}


def _detect_domain(text: str) -> str:
    """Detect primary domain from text content using regex patterns."""
    scores: Counter = Counter()
    text_lower = text[:12000].lower()
    for domain, pattern in _DOMAIN_PATTERNS:
        hits = len(pattern.findall(text_lower))
        if hits:
            scores[domain] = hits
    if scores:
        return scores.most_common(1)[0][0]
    return ""


def _detect_topics(text: str, max_topics: int = 4) -> list[str]:
    """Detect relevant topics from text content."""
    text_lower = text[:12000].lower()
    found: list[tuple[str, int]] = []
    for topic, keywords in _TOPIC_KEYWORDS.items():
        hits = sum(1 for kw in keywords if re.search(kw, text_lower))
        if hits >= 1:
            found.append((topic, hits))
    found.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in found[:max_topics]]


# ── LLM-based classification ───────────────────────────────────────

_CLASSIFY_SYSTEM = (
    "Jesteś klasyfikatorem notatek technicznych. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em. "
    "Żadnego dodatkowego tekstu, komentarzy ani markdown."
)

# ── Contradiction detection ───────────────────────────────────────

_CONTRADICTION_SYSTEM = (
    "Jesteś weryfikatorem spójności bazy wiedzy inżyniera. "
    "Odpowiadaj WYŁĄCZNIE poprawnym JSON-em. "
    "Żadnego dodatkowego tekstu, komentarzy ani markdown."
)

_CONTRADICTION_PROMPT = """\
Porównaj NOWĄ NOTATKĘ z ISTNIEJĄCĄ NOTATKĄ z bazy wiedzy.
Czy nowa notatka PRZECZY lub JEST SPRZECZNA z istniejącą?

Szukaj:
- Sprzecznych twierdzeń technicznych (np. "X jest pass-by-reference" vs "X jest pass-by-value")
- Sprzecznych rekomendacji (np. "używaj X" vs "nie używaj X")
- Wzajemnie wykluczających się faktów

NIE zgłaszaj jako sprzeczność:
- Uzupełniających się informacji
- Informacji o różnych wersjach/kontekstach (np. Python 2 vs Python 3)
- Różnego poziomu szczegółowości

Zwróć JSON: {{"contradiction": true/false, "severity": "none"|"low"|"high", \
"explanation": "krótkie wyjaśnienie po polsku (1-2 zdania)"}}

ISTNIEJĄCA NOTATKA (tytuł: {existing_title}):
{existing_content}

NOWA NOTATKA (tytuł: {new_title}):
{new_content}"""

_CLASSIFY_PROMPT = """\
Przeanalizuj poniższą notatkę i zwróć JSON z dwoma polami:
- "domain": jedna etykieta domeny (np. cpp, angular, sql, python, java, typescript, \
devops, electron-microscopy, career, react, mainframe, networking, research, rust, \
dotnet, go — lub inna krótka etykieta jeśli żadna nie pasuje)
- "topics": lista do 4 tematów (np. performance, migration, debugging, architecture, \
security, testing, management, research, career, frontend, backend, algorithms, \
data-science, networking — lub inne krótkie etykiety)

Zwróć TYLKO JSON: {{"domain": "...", "topics": ["...", "..."]}}

Tytuł: {title}
Treść (fragment):
{content}"""


def check_contradiction(
    client: LLMClient,
    new_text: str,
    existing_text: str,
    *,
    new_title: str = "",
    existing_title: str = "",
) -> dict:
    """Check if new note contradicts existing knowledge.

    Returns dict with keys: contradiction (bool), severity (str), explanation (str).
    """
    prompt = _CONTRADICTION_PROMPT.format(
        existing_title=existing_title or "(bez tytułu)",
        existing_content=existing_text[:2000],
        new_title=new_title or "(bez tytułu)",
        new_content=new_text[:2000],
    )
    try:
        raw = client.generate(prompt, system=_CONTRADICTION_SYSTEM).strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return {
            "contradiction": bool(data.get("contradiction", False)),
            "severity": str(data.get("severity", "none")).lower(),
            "explanation": str(data.get("explanation", "")),
        }
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("Contradiction check failed: %s", exc)
        return {"contradiction": False, "severity": "none", "explanation": ""}


def llm_classify(
    client: LLMClient, text: str, title: str = ""
) -> tuple[str, list[str]]:
    """Use LLM to classify domain and topics.  Returns (domain, topics)."""
    prompt = _CLASSIFY_PROMPT.format(title=title, content=text[:3000])
    try:
        raw = client.generate(prompt, system=_CLASSIFY_SYSTEM).strip()
        # Strip markdown fences if model wraps response
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        domain = str(data.get("domain", "")).strip().lower()
        topics = data.get("topics", [])
        if isinstance(topics, list):
            topics = [str(t).strip().lower() for t in topics if t][:4]
        else:
            topics = []
        return domain, topics
    except Exception as exc:  # noqa: BLE001
        _LOG.debug("LLM classify failed: %s", exc)
        return "", []


# ── Heuristic summary ──────────────────────────────────────────────


def summarize_text(text: str, max_chars: int = 400) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1] + "…"


# ── Main triage function ───────────────────────────────────────────


def triage_against_permanent_notes(
    source_text: str,
    permanent_notes_dir: Path,
    *,
    provider: str = "heuristic",
    top_k: int = 3,
    llm_client: LLMClient | None = None,
    title: str = "",
) -> dict[str, Any]:
    """Return serialisable triage suggestion payload.

    ``top_k`` — number of matches in ``top_matches``.
    ``llm_client`` — optional; when provided, LLM is used for domain/topic classification
                      with heuristic as fallback.
    """
    _ = provider  # Reserved for future provider modes.
    notes = load_permanent_notes(permanent_notes_dir)
    matches = find_best_matches(source_text, notes, top_k=top_k)
    summary = summarize_text(source_text)

    # Domain / topics — LLM first (if available), then heuristic
    domain = ""
    topics: list[str] = []
    if llm_client is not None:
        domain, topics = llm_classify(llm_client, source_text, title=title)

    if not domain:
        domain = _detect_domain(source_text)
    if not topics:
        topics = _detect_topics(source_text)

    # Contradiction check — only when LLM available and strong match exists
    contradiction: dict = {}
    if llm_client is not None and matches and matches[0].score >= 0.12:
        top_match = matches[0]
        # Read the existing note content for comparison
        existing_path = Path(top_match.note_path)
        if existing_path.is_file():
            try:
                existing_text = existing_path.read_text(encoding="utf-8")
                contradiction = check_contradiction(
                    llm_client,
                    source_text,
                    existing_text,
                    new_title=title,
                    existing_title=top_match.title,
                )
                if contradiction.get("contradiction"):
                    _LOG.warning(
                        "Contradiction detected vs «%s» (%s): %s",
                        top_match.title,
                        contradiction.get("severity"),
                        contradiction.get("explanation"),
                    )
            except OSError:
                pass

    if matches and matches[0].score >= 0.12:
        top = matches[0]
        reason_detail = (
            top.match_reason
            if hasattr(top, "match_reason") and top.match_reason
            else ""
        )

        # If contradiction found, override action to flag for human review
        if (
            contradiction.get("contradiction")
            and contradiction.get("severity") == "high"
        ):
            perm_action = "review-contradiction"
            reasoning = (
                f"⚠ SPRZECZNOŚĆ z «{top.title}» (score={top.score:.2f}): "
                f"{contradiction.get('explanation', '')}. {reason_detail}"
            )
        else:
            perm_action = "update-existing"
            reasoning = f"Silne pokrycie z «{top.title}» (score={top.score:.2f}). {reason_detail}"

        suggestion = TriageSuggestion(
            summary=summary,
            confidence=min(0.95, top.score + 0.35),
            suggested_permanent_note_action=perm_action,
            suggested_existing_note_path=top.note_path,
            reasoning=reasoning,
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
    if contradiction:
        payload["contradiction"] = contradiction
    return payload
