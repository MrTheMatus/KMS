from __future__ import annotations

from pathlib import Path

from kms.app.pdf_converter import convert_pdf_to_markdown


def test_convert_minimal_pdf_smoke() -> None:
    pdf = Path("example-vault/10_Sources/pdf/minimal-demo.pdf").resolve()
    result = convert_pdf_to_markdown(pdf)
    assert result.markdown.strip()
    assert result.converter in {"markitdown", "docling", "pymupdf4llm", "pypdf"}


def test_convert_minimal_pdf_pick_best() -> None:
    pdf = Path("example-vault/10_Sources/pdf/minimal-demo.pdf").resolve()
    result = convert_pdf_to_markdown(pdf, pick="best")
    assert result.markdown.strip()
    assert result.converter in {"markitdown", "docling", "pymupdf4llm", "pypdf"}
    assert result.scores
    assert result.converter in result.scores
    assert any("pick=best scores:" in w for w in result.warnings)

