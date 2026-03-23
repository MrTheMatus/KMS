"""PDF -> Markdown conversion with converter fallback chain."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConversionResult:
    markdown: str
    converter: str
    warnings: list[str]


def convert_pdf_to_markdown(pdf_path: Path) -> ConversionResult:
    """Try converters in order: docling -> pymupdf4llm -> pypdf text fallback."""
    warnings: list[str] = []
    if not pdf_path.is_file():
        raise FileNotFoundError(str(pdf_path))

    # 1) docling
    try:
        from docling.document_converter import DocumentConverter  # type: ignore

        conv = DocumentConverter()
        res = conv.convert(str(pdf_path))
        md = res.document.export_to_markdown()
        if md and md.strip():
            return ConversionResult(markdown=md.strip() + "\n", converter="docling", warnings=warnings)
        warnings.append("docling returned empty markdown")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"docling unavailable/failed: {exc}")

    # 2) pymupdf4llm
    try:
        import pymupdf4llm  # type: ignore

        md = pymupdf4llm.to_markdown(str(pdf_path))
        if md and md.strip():
            return ConversionResult(markdown=md.strip() + "\n", converter="pymupdf4llm", warnings=warnings)
        warnings.append("pymupdf4llm returned empty markdown")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"pymupdf4llm unavailable/failed: {exc}")

    # 3) pypdf basic text extraction
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
        md = "\n".join(parts).strip() + "\n"
        return ConversionResult(markdown=md, converter="pypdf", warnings=warnings)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"pypdf unavailable/failed: {exc}")
        raise RuntimeError(f"Failed to convert PDF {pdf_path}") from exc

