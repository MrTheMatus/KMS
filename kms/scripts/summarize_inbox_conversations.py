"""Synthesize all conversation notes in inbox into clean knowledge notes.

Targets markdown files in ``00_Inbox`` with frontmatter ``source_type: conversation``.
For each note:
- removes noisy artifacts (URLs/page markers/timestamps),
- synthesizes concise knowledge sections,
- rewrites body with a clean structure.

Optionally uses AnythingLLM workspace chat. If unavailable, falls back to local synthesis.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path

from kms.app.anythingllm_client import AnythingLLMClient, anythingllm_chat_text_response
from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging


STOPWORDS = {
    "oraz",
    "które",
    "który",
    "która",
    "jako",
    "przez",
    "tego",
    "też",
    "jest",
    "that",
    "this",
    "from",
    "with",
    "into",
    "have",
    "will",
    "were",
    "https",
    "http",
    "www",
    "page",
    "chatgpt",
    "conversation",
    "guide",
    "pm",
    "am",
}

META_NOISE = (
    "frontmatter topics",
    "słowa kluczowe",
    "oznacz decyzję w review-queue",
    "dla wartościowych fragmentów",
    "## streszczenie",
    "## kluczowe wnioski",
    "## technologie i tematy",
    "## co dalej",
)


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fm = text[: end + 5]
    body = text[end + 5 :].lstrip("\n")
    return fm, body


def _fm_value(fm: str, key: str) -> str:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, flags=re.M)
    if not m:
        return ""
    raw = m.group(1).strip()
    try:
        if raw.startswith('"') or raw.startswith("'"):
            return str(json.loads(raw.replace("'", '"')))
    except Exception:  # noqa: BLE001
        pass
    return raw.strip('"').strip("'")


def _strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _clean_noise(text: str) -> str:
    out = _strip_html_comments(text)
    out = re.sub(r"https?://\S+", "", out)
    out = re.sub(r"\bPage\s+\d+\s+of\s+\d+\b", "", out, flags=re.I)
    out = re.sub(r"\b\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s*[APMapm]*\b", "", out)
    out = re.sub(r"\f", "\n", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    # Drop previously generated meta/instruction lines if present.
    kept: list[str] = []
    for ln in out.splitlines():
        low = ln.strip().lower()
        if any(m in low for m in META_NOISE):
            continue
        if "pick=best scores:" in low or "unavailable/failed:" in low:
            continue
        kept.append(ln)
    out = "\n".join(kept)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _extract_keywords(text: str, top_k: int = 10) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9_+\-]{4,}", text.lower())
    words = [w for w in words if w not in STOPWORDS and not w.isdigit()]
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_k)]


def _extract_bullets(text: str, max_items: int = 6) -> list[str]:
    lines = [ln.strip(" -\t") for ln in text.splitlines()]
    out: list[str] = []
    seen: set[str] = set()
    for ln in lines:
        if not ln:
            continue
        low = ln.lower()
        if low.startswith("#"):
            continue
        if any(m in low for m in META_NOISE):
            continue
        if "pick=best scores:" in low or "unavailable/failed:" in low:
            continue
        if "http" in low or "page " in low:
            continue
        if re.search(r"\b\d{1,2}:\d{2}\b", low):
            continue
        if len(ln) < 30 or len(ln) > 220:
            continue
        key = re.sub(r"\s+", " ", low)
        if key in seen:
            continue
        seen.add(key)
        out.append(ln.rstrip("."))
        if len(out) >= max_items:
            return out

    # Fallback: sentence-based extraction if lines are too sparse.
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    out: list[str] = []
    for s in sentences:
        s = s.strip(" -\t")
        if len(s) < 40:
            continue
        if "http" in s.lower() or "page " in s.lower():
            continue
        if len(s) > 220:
            continue
        out.append(s.rstrip("."))
        if len(out) >= max_items:
            break
    return out


def _local_synthesis(*, title: str, body: str, topics: str) -> str:
    cleaned = _clean_noise(body)
    keywords = _extract_keywords(cleaned, top_k=8)
    bullets = _extract_bullets(cleaned, max_items=6)
    summary = (
        "Materiał dotyczy praktycznych aspektów inżynierskich i zawiera obserwacje, "
        "problemy oraz wskazówki możliwe do dalszego przeniesienia do notatek permanent."
    )
    if bullets:
        summary = " ".join(bullets[:2])[:500]
    lines = [
        "## Streszczenie",
        summary,
        "",
        "## Kluczowe wnioski",
    ]
    if bullets:
        lines.extend(f"- {b}" for b in bullets)
    else:
        lines.append("- Brak czytelnych zdań po czyszczeniu; wymagana ręczna rewizja.")
    lines.extend(
        [
            "",
            "## Technologie i tematy",
            f"- frontmatter topics: {topics or '(brak)'}",
            f"- słowa kluczowe: {', '.join(keywords) if keywords else '(brak)'}",
            "",
            "## Co dalej",
            "- Oznacz decyzję w review-queue (`approve` / `postpone` / `reject`).",
            "- Dla wartościowych fragmentów utwórz/rozszerz notatki permanent.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _llm_synthesis(cfg: dict, *, title: str, body: str, topics: str) -> str | None:
    api_cfg = cfg.get("anythingllm") or {}
    base = str(api_cfg.get("base_url", "http://localhost:3001")).rstrip("/")
    slug = str(api_cfg.get("workspace_slug", "my-workspace"))
    key_env = str(api_cfg.get("api_key_env", "ANYTHINGLLM_API_KEY"))
    api_key = os.getenv(key_env, "").strip()
    if not api_key:
        return None
    prompt = (
        "Zsyntetyzuj surową notatkę konwersacji do formy wiedzy. "
        "Usuń śmieci, linki i artefakty OCR/PDF. Odpowiedz po polsku, markdown, sekcje:\n"
        "## Streszczenie\n## Kluczowe wnioski (lista)\n## Technologie i tematy\n## Co dalej\n\n"
        f"Tytuł: {title}\n"
        f"Frontmatter topics: {topics}\n\n"
        "Treść wejściowa:\n"
        "```\n"
        f"{body[:24000]}\n"
        "```"
    )
    client = AnythingLLMClient(base_url=base, api_key=api_key, workspace_slug=slug)
    data = client.workspace_chat(
        prompt, mode="chat", session_id=f"kms-synth-{title[:32]}"
    )
    text = anythingllm_chat_text_response(data).strip()
    if not text or text.startswith("[AnythingLLM error:"):
        return None
    return text + ("\n" if not text.endswith("\n") else "")


def main() -> int:
    p = build_parser("Clean and synthesize conversation notes in inbox.")
    add_dry_run(p)
    p.add_argument(
        "--invoke-anythingllm",
        action="store_true",
        help="Use AnythingLLM synthesis first",
    )
    p.add_argument(
        "--max-files", type=int, default=0, help="Limit number of files (0 = all)"
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    vp = vault_paths(cfg)
    inbox = vp["inbox"]

    md_files = sorted(inbox.rglob("*.md"))
    targets: list[Path] = []
    for path in md_files:
        txt = path.read_text(encoding="utf-8")
        parsed = _split_frontmatter(txt)
        if not parsed:
            continue
        fm, _ = parsed
        if _fm_value(fm, "source_type").strip('"').strip("'") == "conversation":
            targets.append(path)
    if args.max_files > 0:
        targets = targets[: args.max_files]

    changed = failed = llm_used = 0
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8")
            parsed = _split_frontmatter(text)
            if not parsed:
                continue
            fm, body = parsed
            title = _fm_value(fm, "title") or path.stem
            topics = _fm_value(fm, "topics")
            synth: str | None = None
            if args.invoke_anythingllm and not args.dry_run:
                try:
                    synth = _llm_synthesis(cfg, title=title, body=body, topics=topics)
                    if synth:
                        llm_used += 1
                except Exception:  # noqa: BLE001
                    synth = None
            if synth is None:
                synth = _local_synthesis(title=title, body=body, topics=topics)
            new_body = f"# {title}\n\n{synth}"
            out_text = f"{fm}\n{new_body}"
            if args.dry_run:
                print(f"dry-run: would rewrite {path}")
                continue
            path.write_text(out_text, encoding="utf-8")
            changed += 1
        except Exception:  # noqa: BLE001
            failed += 1

    if not args.dry_run:
        try:
            db_path = abs_path(cfg, "database", "path")
            schema_path = project_root() / "kms" / "app" / "schema.sql"
            conn = connect(db_path)
            ensure_schema(conn, schema_path)
            audit(
                conn,
                "summarize_inbox_conversations",
                "run",
                None,
                {
                    "changed": changed,
                    "failed": failed,
                    "llm_used": llm_used,
                    "invoke_anythingllm": bool(args.invoke_anythingllm),
                },
            )
            conn.commit()
            conn.close()
        except Exception:  # noqa: BLE001
            pass

    print(
        json.dumps(
            {
                "changed": changed,
                "failed": failed,
                "llm_used": llm_used,
                "targets": len(targets),
            }
        )
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
