"""PDF -> Markdown conversion with converter fallback chain or best-of scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ConverterPick = Literal["chain", "best"]


@dataclass
class ConversionResult:
    markdown: str
    converter: str
    warnings: list[str]
    scores: dict[str, float] = field(default_factory=dict)


def score_transcript_markdown(md: str) -> float:
    """Heuristic score for chat-like transcripts: dialogue structure, uniqueness, text density."""
    if not md or not md.strip():
        return -1e9
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]
    if not lines:
        return -1e9
    n = len(lines)

    speaker_line = re.compile(
        r"^(you|user|assistant|chatgpt|system)\b"
        r"|^(ty|użytkownik|asystent)\b"
        r"|^#\s*(you|chatgpt|assistant|user)\b",
        re.I,
    )
    # "Name: message" with some substance
    colon_utterance = re.compile(r"^.{1,80}:\s+\S{8,}")

    dialogue_like = 0
    for ln in lines:
        if ln.startswith("## Page "):
            continue
        if speaker_line.search(ln):
            dialogue_like += 1
        elif colon_utterance.match(ln):
            dialogue_like += 1

    unique_ratio = len(set(lines)) / max(n, 1)
    page_headers = sum(1 for ln in lines if ln.startswith("## Page "))
    page_penalty = page_headers * 1.5

    alnum = sum(1 for c in md if c.isalnum())
    alnum_ratio = alnum / max(len(md), 1)

    # Length matters for real transcripts; dampen with sqrt to avoid favouring only noise
    length_factor = min(n, 500) ** 0.35

    score = (
        dialogue_like * 4.0
        + unique_ratio * 12.0
        + alnum_ratio * 20.0
        + length_factor
        - page_penalty
    )
    return score


def _try_markitdown(pdf_path: Path, warnings: list[str]) -> str | None:
    try:
        from markitdown import MarkItDown  # type: ignore

        mdi = MarkItDown()
        res = mdi.convert(str(pdf_path))
        md = getattr(res, "text_content", None) or ""
        if md and str(md).strip():
            return str(md).strip()
        warnings.append("markitdown returned empty markdown")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"markitdown unavailable/failed: {exc}")
    return None


def _try_docling(pdf_path: Path, warnings: list[str]) -> str | None:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore

        conv = DocumentConverter()
        res = conv.convert(str(pdf_path))
        md = res.document.export_to_markdown()
        if md and md.strip():
            return md.strip()
        warnings.append("docling returned empty markdown")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"docling unavailable/failed: {exc}")
    return None


def _try_pymupdf4llm(pdf_path: Path, warnings: list[str]) -> str | None:
    try:
        import pymupdf4llm  # type: ignore

        md = pymupdf4llm.to_markdown(str(pdf_path))
        if md and md.strip():
            return md.strip()
        warnings.append("pymupdf4llm returned empty markdown")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"pymupdf4llm unavailable/failed: {exc}")
    return None


def _try_pypdf(pdf_path: Path, warnings: list[str]) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        parts: list[str] = [f"# {pdf_path.stem}", ""]
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            parts.append(f"## Page {i}")
            parts.append("")
            parts.append(text.strip() if text.strip() else "_(no text extracted)_")
            parts.append("")
        return "\n".join(parts).strip()
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"pypdf unavailable/failed: {exc}")
    return None


def _candidates_for_pdf(pdf_path: Path, warnings: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name, fn in (
        ("markitdown", _try_markitdown),
        ("docling", _try_docling),
        ("pymupdf4llm", _try_pymupdf4llm),
        ("pypdf", _try_pypdf),
    ):
        md = fn(pdf_path, warnings)
        if md:
            out.append((name, md + "\n" if not md.endswith("\n") else md))
    return out


def convert_pdf_to_markdown(
    pdf_path: Path,
    *,
    pick: ConverterPick = "chain",
) -> ConversionResult:
    """Convert PDF to markdown.

    ``pick="chain"``: first successful backend in order markitdown → docling → pymupdf4llm → pypdf.

    ``pick="best"``: run all backends that succeed, choose highest
    :func:`score_transcript_markdown` (for chat exports with messy layout).
    """
    if not pdf_path.is_file():
        raise FileNotFoundError(str(pdf_path))

    warnings: list[str] = []

    if pick == "best":
        candidates = _candidates_for_pdf(pdf_path, warnings)
        if not candidates:
            raise RuntimeError(f"Failed to convert PDF {pdf_path}")
        scores = {name: score_transcript_markdown(md) for name, md in candidates}
        best_name, best_md = max(candidates, key=lambda x: scores[x[0]])
        summary = ", ".join(f"{n}={scores[n]:.1f}" for n, _ in candidates)
        warnings.append(f"pick=best scores: {summary}; selected={best_name}")
        return ConversionResult(
            markdown=best_md if best_md.endswith("\n") else best_md + "\n",
            converter=best_name,
            warnings=warnings,
            scores=scores,
        )

    # chain
    for name, fn in (
        ("markitdown", _try_markitdown),
        ("docling", _try_docling),
        ("pymupdf4llm", _try_pymupdf4llm),
        ("pypdf", _try_pypdf),
    ):
        md = fn(pdf_path, warnings)
        if md:
            body = md + "\n" if not md.endswith("\n") else md
            return ConversionResult(markdown=body, converter=name, warnings=warnings)
    raise RuntimeError(f"Failed to convert PDF {pdf_path}")
