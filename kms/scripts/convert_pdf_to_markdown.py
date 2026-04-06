"""Convert PDF files in inbox to markdown files in sources_web."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema
from kms.app.pdf_converter import ConverterPick, convert_pdf_to_markdown
from kms.app.paths import ensure_dir, project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser("Convert PDF files to markdown using converter fallback chain.")
    add_dry_run(p)
    p.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Optional single PDF path (absolute or relative to vault root).",
    )
    p.add_argument(
        "--converter-pick",
        type=str,
        choices=("chain", "best"),
        default="chain",
        help="chain: first success; best: pick highest transcript score (chat PDFs).",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    vp = vault_paths(cfg)
    inbox = vp["inbox"]
    out_dir = vp["sources_web"]
    ensure_dir(out_dir)

    pdf_files: list[Path] = []
    if args.input is not None:
        candidate = args.input
        if not candidate.is_absolute():
            candidate = (vp["root"] / candidate).resolve()
        pdf_files = [candidate]
    else:
        pdf_files = sorted([p for p in inbox.rglob("*.pdf") if p.is_file()])

    if not pdf_files:
        _LOG.info("No PDFs found to convert.")
        return 0

    converted = 0
    failed = 0
    for pdf in pdf_files:
        out_md = out_dir / f"{pdf.stem}.md"
        try:
            result = convert_pdf_to_markdown(
                pdf,
                pick=cast(ConverterPick, args.converter_pick),
            )
            if args.dry_run:
                _LOG.info(
                    "dry-run: would convert %s -> %s (converter=%s warnings=%s)",
                    pdf,
                    out_md,
                    result.converter,
                    len(result.warnings),
                )
                converted += 1
                continue
            out_md.write_text(result.markdown, encoding="utf-8")
            converted += 1
            _LOG.info("Converted %s -> %s (%s)", pdf, out_md, result.converter)
            for w in result.warnings:
                _LOG.warning("%s: %s", pdf.name, w)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            _LOG.error("PDF conversion failed for %s: %s", pdf, exc)

    try:
        db_path = abs_path(cfg, "database", "path")
        schema_path = project_root() / "kms" / "app" / "schema.sql"
        conn = connect(db_path)
        ensure_schema(conn, schema_path)
        audit(
            conn,
            "convert_pdf_to_markdown",
            "run",
            None,
            {
                "converted": converted,
                "failed": failed,
                "dry_run": args.dry_run,
            },
        )
        conn.close()
    except Exception:  # noqa: BLE001
        pass

    _LOG.info("PDF conversion done: converted=%s failed=%s", converted, failed)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
