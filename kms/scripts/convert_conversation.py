"""Convert a raw conversation (chat, WhatsApp, Discord, paste) into a knowledge source-note.

The note lands in ``00_Inbox/`` with ``source_type: conversation`` and goes through
the standard ``scan_inbox → make_review_queue → apply`` HITL pipeline.

Optional: ``--invoke-anythingllm`` sends the rendered prompt to AnythingLLM
``POST /api/v1/workspace/{slug}/chat`` — model is configured in workspace UI.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from kms.app.anythingllm_client import AnythingLLMClient, anythingllm_chat_text_response
from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def _slug_from_title(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9ąćęłńóśźż\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:60].strip("-") or "conversation"


def _build_prompt(template_path: Path, conversation_text: str, title: str | None) -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(enabled_extensions=()),
    )
    tpl = env.get_template(template_path.name)
    return tpl.render(conversation_text=conversation_text, title=title or "")


def _build_source_note(
    *,
    note_id: str,
    title: str,
    captured_at: str,
    body: str,
) -> str:
    fm_lines = [
        "---",
        f"id: {json.dumps(note_id, ensure_ascii=False)}",
        "type: source-note",
        'source_type: "conversation"',
        f"title: {json.dumps(title, ensure_ascii=False)}",
        "source_url: null",
        "file_link: null",
        f"captured_at: {json.dumps(captured_at, ensure_ascii=False)}",
        'language: "pl"',
        "topics: []",
        "status: inbox",
        "project: null",
        "confidence: low",
        "owner: null",
        "reviewer: null",
        "domain: null",
        "last_reviewed_at: null",
        "sensitivity: internal",
        "---",
        "",
        f"# {title}",
        "",
        body,
    ]
    return "\n".join(fm_lines) + "\n"


def _next_conv_id(inbox: Path) -> str:
    prefix = f"conv-{date.today().year}-"
    max_n = 0
    if inbox.is_dir():
        for p in inbox.glob("conv-*.md"):
            m = re.match(rf"^{re.escape(prefix)}(\d{{4}})\.md$", p.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1:04d}"


def _process_single(
    *,
    cfg: dict,
    inbox: Path,
    tpl_path: Path,
    input_path: Path,
    title: str,
    invoke_anythingllm: bool,
    dry_run: bool,
    dry_run_seq: int | None = None,
) -> tuple[int, str | None]:
    """Returns (exit_code, out_path or None).

    ``dry_run_seq`` — when set with ``dry_run``, use synthetic id so batch dry-run output differs per file.
    """
    conversation_text = input_path.read_text(encoding="utf-8")
    if not conversation_text.strip():
        _LOG.error("Input file is empty: %s", input_path)
        return 1, None

    prompt_md = _build_prompt(tpl_path, conversation_text, title)
    if invoke_anythingllm and not dry_run:
        body = _call_anythingllm(cfg, prompt_md)
    else:
        body = prompt_md

    if dry_run and dry_run_seq is not None:
        note_id = f"conv-dry-{date.today().year}-{dry_run_seq:04d}"
    else:
        note_id = _next_conv_id(inbox)
    captured = date.today().isoformat()
    note_content = _build_source_note(
        note_id=note_id,
        title=title,
        captured_at=captured,
        body=body,
    )

    if dry_run:
        print(f"dry-run: would write {inbox / f'{note_id}.md'}")
        print(note_content)
        return 0, None

    inbox.mkdir(parents=True, exist_ok=True)
    out_path = inbox / f"{note_id}.md"
    out_path.write_text(note_content, encoding="utf-8")
    _LOG.info("Created %s", out_path)

    try:
        db_path = abs_path(cfg, "database", "path")
        schema_path = project_root() / "kms" / "app" / "schema.sql"
        conn = connect(db_path)
        ensure_schema(conn, schema_path)
        audit(conn, "convert_conversation", "source_note", note_id, {
            "input_file": str(input_path),
            "title": title,
            "invoke_anythingllm": invoke_anythingllm,
        })
        conn.commit()
        conn.close()
    except Exception:  # noqa: BLE001
        _LOG.warning("Audit write failed (non-fatal)", exc_info=True)

    print(str(out_path))
    return 0, str(out_path)


def main() -> int:
    p = build_parser("Convert a raw conversation into a knowledge source-note in inbox.")
    add_dry_run(p)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", type=Path, default=None, help="Single conversation text file")
    src.add_argument(
        "--batch-dir",
        type=Path,
        default=None,
        help="Directory of *.txt / *.md conversation files (one note per file)",
    )
    p.add_argument("--title", default=None, help="Note title for --input only (default: timestamp)")
    p.add_argument(
        "--invoke-anythingllm",
        action="store_true",
        help="Send prompt to AnythingLLM and use reply as note body",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    vp = vault_paths(cfg)
    inbox = vp["inbox"]

    tpl_path = (project_root() / "kms" / "templates" / "conversation_extract.md.j2").resolve()
    if not tpl_path.is_file():
        _LOG.error("Template not found: %s", tpl_path)
        return 1

    if args.batch_dir is not None:
        bdir = Path(args.batch_dir).resolve()
        if not bdir.is_dir():
            _LOG.error("batch-dir not found: %s", bdir)
            return 1
        files = sorted(
            p for p in bdir.iterdir()
            if p.is_file() and p.suffix.lower() in {".txt", ".md"}
        )
        if not files:
            _LOG.warning("No .txt or .md files in %s", bdir)
            return 1
        err = 0
        for i, fp in enumerate(files, start=1):
            title = fp.stem.replace("_", " ").strip() or fp.name
            code, _ = _process_single(
                cfg=cfg,
                inbox=inbox,
                tpl_path=tpl_path,
                input_path=fp,
                title=title,
                invoke_anythingllm=args.invoke_anythingllm,
                dry_run=args.dry_run,
                dry_run_seq=i if args.dry_run else None,
            )
            err = err or code
        return err

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        _LOG.error("Input file not found: %s", input_path)
        return 1

    title = args.title or f"Rozmowa {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    code, _ = _process_single(
        cfg=cfg,
        inbox=inbox,
        tpl_path=tpl_path,
        input_path=input_path,
        title=title,
        invoke_anythingllm=args.invoke_anythingllm,
        dry_run=args.dry_run,
    )
    return code


def _call_anythingllm(cfg: dict, prompt: str) -> str:
    api_cfg = cfg.get("anythingllm") or {}
    base = str(api_cfg.get("base_url", "http://localhost:3001")).rstrip("/")
    slug = str(api_cfg.get("workspace_slug", "my-workspace"))
    key_env = str(api_cfg.get("api_key_env", "ANYTHINGLLM_API_KEY"))
    api_key = os.getenv(key_env, "").strip()
    if not api_key:
        _LOG.warning("AnythingLLM API key not set (%s), falling back to raw prompt", key_env)
        return prompt

    client = AnythingLLMClient(base_url=base, api_key=api_key, workspace_slug=slug)
    try:
        data = client.workspace_chat(
            prompt,
            mode="chat",
            session_id=f"kms-conv-{date.today().isoformat()}",
        )
        return anythingllm_chat_text_response(data)
    except RuntimeError as exc:
        _LOG.error("AnythingLLM chat failed: %s", exc)
        return f"[AnythingLLM error: {exc}]\n\n{prompt}"


if __name__ == "__main__":
    raise SystemExit(main())
