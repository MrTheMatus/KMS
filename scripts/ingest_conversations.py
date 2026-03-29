#!/usr/bin/env python3
"""Batch: PDFs (e.g. chat exports) -> Markdown source-notes in vault inbox.

Uses ``kms.app.pdf_converter.convert_pdf_to_markdown`` (markitdown → … → pypdf).

Use ``--converter-pick best`` to run every available backend and keep the transcript
that scores best for chat-like layout (recommended for ChatGPT PDF exports).

Example::

    python scripts/ingest_conversations.py \\
        --source-dir conversations/ \\
        --target-dir example-vault/00_Inbox/conversations/

Then: ``python -m kms.scripts.scan_inbox`` and review-queue as usual.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kms.app.config import abs_path, load_config
from kms.app.db import audit, connect, ensure_schema
from kms.app.pdf_converter import ConverterPick, convert_pdf_to_markdown
from kms.app.paths import project_root

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_LOG = logging.getLogger(__name__)


def _slug_from_stem(stem: str) -> str:
    s = stem.lower()
    s = re.sub(r"[^a-z0-9ąćęłńóśźż]+", "-", s, flags=re.I)
    return s.strip("-") or "document"


TOPIC_RULES: dict[str, tuple[str, ...]] = {
    "java": ("java", "spring", "aop", "mapstruct", "lombok", "jvm"),
    "typescript": ("typescript", "ts", "tsconfig"),
    "angular": ("angular", "rxjs", "ngrx", "component", "template"),
    "cpp": ("c++", "cpp", "constexpr", "raii", "std::"),
    "sql": ("sql", "db2", "query", "join", "cursor"),
    "debugging": ("debug", "trace", "stack", "profil", "incident"),
    "performance": ("performance", "latency", "benchmark", "cache"),
    "system-design": ("architecture", "microservice", "pipeline", "event-driven"),
    "govtech": ("govtech", "urzęd", "publiczn", "compliance", "audit"),
    "tem": ("tem", "electron microscopy", "beam", "radiolysis", "diffraction"),
}

BASELINE_TOPICS = {
    "principles",
    "cpp",
    "system-design",
    "performance",
    "sql",
    "debugging",
    "domain",
    "cross-domain",
    "govtech",
}


def _extract_topics(*, title: str, markdown: str) -> list[str]:
    hay = f"{title}\n{markdown[:20000]}".lower()
    out: list[str] = []
    for topic, needles in TOPIC_RULES.items():
        if any(n.lower() in hay for n in needles):
            out.append(topic)
    return sorted(set(out))


def _wrap_source_note(
    *,
    note_id: str,
    title: str,
    body: str,
    source_file: str,
    topics: list[str],
) -> str:
    j = lambda x: json.dumps(x, ensure_ascii=False)
    lines = [
        "---",
        f"id: {j(note_id)}",
        "type: source-note",
        'source_type: "conversation"',
        f"title: {j(title)}",
        "source_url: null",
        "file_link: null",
        f"captured_from_pdf: {j(source_file)}",
        'language: "pl"',
        f"topics: {json.dumps(topics, ensure_ascii=False)}",
        "status: inbox",
        "project: null",
        'confidence: "low"',
        "owner: null",
        "reviewer: null",
        "domain: null",
        "last_reviewed_at: null",
        "sensitivity: internal",
        "---",
    ]
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(body.rstrip())
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Ingest PDF conversation exports into inbox as Markdown.")
    p.add_argument(
        "--source-dir",
        type=Path,
        default=ROOT / "conversations",
        help="Directory containing .pdf files (default: ./conversations)",
    )
    p.add_argument(
        "--target-dir",
        type=Path,
        default=ROOT / "example-vault" / "00_Inbox" / "conversations",
        help="Inbox subdirectory for generated .md (default: example-vault/00_Inbox/conversations)",
    )
    p.add_argument(
        "--max-size-mb",
        type=float,
        default=0.0,
        help="Skip PDFs larger than this; <=0 disables limit (default: disabled)",
    )
    p.add_argument(
        "--converter-pick",
        type=str,
        choices=("chain", "best"),
        default="chain",
        help='chain: first successful converter; best: score all candidates (better for chat PDFs)',
    )
    p.add_argument("--dry-run", action="store_true", help="Print actions only; do not write files")
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional config.yaml for audit_log only",
    )
    args = p.parse_args()

    src = args.source_dir.resolve()
    dst = args.target_dir.resolve()
    max_bytes = int(args.max_size_mb * 1024 * 1024)

    if not src.is_dir():
        _LOG.error("Source dir not found: %s", src)
        return 1

    pdfs = sorted(src.glob("*.pdf"))
    if not pdfs:
        _LOG.info("No PDF files in %s", src)
        return 0

    ok = skip = fail = 0
    details: list[dict[str, str | int]] = []
    topic_counts: Counter[str] = Counter()

    for pdf in pdfs:
        try:
            size = pdf.stat().st_size
        except OSError as exc:
            fail += 1
            details.append({"file": pdf.name, "result": "error", "reason": str(exc)})
            continue

        if args.max_size_mb > 0 and size > max_bytes:
            skip += 1
            details.append({
                "file": pdf.name,
                "result": "skip",
                "reason": f"size {size} > max {max_bytes}",
            })
            _LOG.warning("SKIP %s (%.1f MB > %.1f MB)", pdf.name, size / 1e6, args.max_size_mb)
            continue

        slug = _slug_from_stem(pdf.stem)
        note_id = f"conv-pdf-{slug[:48]}"
        out_md = dst / f"{slug}.md"
        title = pdf.stem.replace("_", " ").strip()

        if args.dry_run:
            _LOG.info("dry-run: would convert %s -> %s", pdf.name, out_md)
            ok += 1
            details.append({"file": pdf.name, "result": "dry_run", "out": str(out_md)})
            continue

        try:
            result = convert_pdf_to_markdown(
                pdf,
                pick=cast(ConverterPick, args.converter_pick),
            )
            body = result.markdown
            topics = _extract_topics(title=title, markdown=body)
            topic_counts.update(topics)
            if result.warnings:
                body = (
                    "<!-- conversion warnings:\n"
                    + "\n".join(f"  - {w}" for w in result.warnings)
                    + "\n-->\n\n"
                    + body
                )
            wrapped = _wrap_source_note(
                note_id=note_id,
                title=title,
                body=body,
                source_file=pdf.name,
                topics=topics,
            )
            dst.mkdir(parents=True, exist_ok=True)
            out_md.write_text(wrapped, encoding="utf-8")
            ok += 1
            _LOG.info("OK %s -> %s (%s)", pdf.name, out_md.name, result.converter)
            details.append({
                "file": pdf.name,
                "result": "ok",
                "converter": result.converter,
                "topics": ",".join(topics),
            })
        except Exception as exc:  # noqa: BLE001
            fail += 1
            _LOG.error("FAIL %s: %s", pdf.name, exc)
            details.append({"file": pdf.name, "result": "error", "reason": str(exc)})

    report = {
        "ok": ok,
        "skipped": skip,
        "failed": fail,
        "details": details,
        "topics_found": dict(topic_counts),
        "new_topics": sorted(t for t in topic_counts if t not in BASELINE_TOPICS),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not args.dry_run:
        dst.mkdir(parents=True, exist_ok=True)
        report_md = dst / "_topics_discovered.md"
        lines = [
            "# Topics discovered from conversations PDFs",
            "",
            f"- Processed OK: {ok}",
            f"- Skipped: {skip}",
            f"- Failed: {fail}",
            "",
            "## Topic counts",
        ]
        if topic_counts:
            for k, v in topic_counts.most_common():
                lines.append(f"- `{k}`: {v}")
        else:
            lines.append("- (none)")
        lines.append("")
        lines.append("## New topics (outside current baseline)")
        new_topics = sorted(t for t in topic_counts if t not in BASELINE_TOPICS)
        if new_topics:
            lines.extend([f"- `{t}`" for t in new_topics])
        else:
            lines.append("- (none)")
        lines.append("")
        report_md.write_text("\n".join(lines), encoding="utf-8")

    if args.config and not args.dry_run:
        try:
            cfg = load_config(args.config)
            db_path = abs_path(cfg, "database", "path")
            schema_path = project_root() / "kms" / "app" / "schema.sql"
            conn = connect(db_path)
            ensure_schema(conn, schema_path)
            audit(conn, "ingest_conversations", "run", None, {
                "ok": ok,
                "skipped": skip,
                "failed": fail,
                "source_dir": str(src),
                "target_dir": str(dst),
                "topics_found": dict(topic_counts),
            })
            conn.commit()
            conn.close()
        except Exception:  # noqa: BLE001
            _LOG.warning("audit_log skipped (no DB or config)", exc_info=True)

    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
