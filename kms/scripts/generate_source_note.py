"""Generate a new source note from template (Etap 1)."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from kms.app.config import abs_path
from kms.app.db import audit, connect, ensure_schema
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging


def _next_id(source_notes_dir: Path, year: int) -> str:
    prefix = f"src-{year}-"
    max_n = 0
    if source_notes_dir.is_dir():
        for p in source_notes_dir.glob("*.md"):
            m = re.match(rf"^{re.escape(prefix)}(\d{{4}})\.md$", p.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1:04d}"


def main() -> int:
    p = build_parser("Generate a source note markdown file from template.")
    add_dry_run(p)
    p.add_argument("--title", required=True, help="Note title")
    p.add_argument(
        "--source-type",
        default="web",
        choices=["web", "pdf", "conversation", "other"],
        help="source_type frontmatter",
    )
    p.add_argument("--source-url", default="", help="URL if web capture")
    p.add_argument("--file-link", default="", help="Relative vault path to binary/PDF")
    p.add_argument("--language", default="pl")
    p.add_argument("--id", dest="note_id", default=None, help="Override id (default: auto)")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: 20_Source-Notes/<id>.md)",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    from kms.app.config import vault_paths

    vp = vault_paths(cfg)
    source_notes = vp["source_notes"]
    templates_dir = abs_path(cfg, "templates", "source_note").parent
    # templates.source_note points to file; loader needs directory
    tpl_file = cfg["templates"]["source_note"]
    tpl_name = Path(tpl_file).name

    year = date.today().year
    note_id = args.note_id or _next_id(source_notes, year)
    captured = date.today().isoformat()

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=()),
    )
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
    tpl = env.get_template(tpl_name)
    body = tpl.render(
        id=note_id,
        source_type=args.source_type,
        title=args.title,
        source_url=args.source_url or None,
        file_link=args.file_link or None,
        captured_at=captured,
        language=args.language,
        body="",
    )

    out = args.output
    if out is None:
        out = source_notes / f"{note_id}.md"
    else:
        out = Path(out).resolve()

    if out.exists():
        print(f"Refusing to overwrite existing file: {out}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"dry-run: would write {out}")
        print(body)
        return 0

    source_notes.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")

    try:
        db_path = abs_path(cfg, "database", "path")
        schema_path = project_root() / "kms" / "app" / "schema.sql"
        conn = connect(db_path)
        ensure_schema(conn, schema_path)
        audit(conn, "generate_source_note", "source_note", note_id, {
            "path": str(out.relative_to(vp["root"])) if out.is_relative_to(vp["root"]) else str(out),
            "title": args.title,
            "source_type": args.source_type,
        })
        conn.close()
    except Exception:  # noqa: BLE001
        pass

    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
