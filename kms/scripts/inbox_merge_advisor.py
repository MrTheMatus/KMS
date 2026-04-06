"""Deep merge / conflict / duplicate suggestions for inbox items vs permanent notes.

Runs **after** ``scan_inbox`` + ``make_review_queue`` (or on demand per proposal).
Does not mutate vault; prints prompt + JSON for reviewer.

Optional: ``--invoke-anythingllm`` sends the rendered prompt to AnythingLLM
``POST /api/v1/workspace/{slug}/chat`` — **model jest ustawiany w UI workspace** (nie w KMS).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from kms.app.anythingllm_client import AnythingLLMClient, anythingllm_chat_text_response
from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema, fetch_all_dicts
from kms.app.merge_advisor import (
    analyze_incoming_vs_corpus,
    render_prompt_from_template,
)
from kms.app.paths import project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser(
        "Merge advisor: conflict/duplicate/merge hints vs permanent notes + LLM prompt."
    )
    add_dry_run(p)
    p.add_argument(
        "--proposal-id",
        type=int,
        default=None,
        help="Single proposal id (default: all pending/postponed with pending decision)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON per proposal",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write full markdown report to this file",
    )
    p.add_argument(
        "--invoke-anythingllm",
        action="store_true",
        help="Send prompt via AnythingLLM API (/workspace/{slug}/chat); model from workspace UI",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    permanent = vp["permanent_notes"]

    ma_cfg = cfg.get("merge_advisor") or {}
    tpl_rel = str(
        ma_cfg.get("prompt_template", "kms/templates/merge_advisor_prompt.md.j2")
    )
    tpl_path = (project_root() / tpl_rel).resolve()
    if not tpl_path.is_file():
        tpl_path = (
            project_root() / "kms" / "templates" / "merge_advisor_prompt.md.j2"
        ).resolve()

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    where = "AND p.id = ?" if args.proposal_id is not None else ""
    params: tuple[Any, ...] = (
        (args.proposal_id,) if args.proposal_id is not None else ()
    )

    rows = fetch_all_dicts(
        conn,
        f"""SELECT p.id AS proposal_id, i.path AS item_path, i.kind
            FROM proposals p
            JOIN items i ON i.id = p.item_id
            LEFT JOIN decisions d ON d.proposal_id = p.id
            WHERE COALESCE(d.decision, 'pending') IN ('pending', 'postpone')
            {where}
            ORDER BY p.id""",
        params,
    )

    if not rows:
        _LOG.warning("No matching proposals.")
        conn.close()
        return 1

    chunks: list[str] = []
    out_objects: list[dict[str, Any]] = []

    for row in rows:
        rel = row["item_path"]
        src = vp["root"] / rel
        text = ""
        if src.is_file():
            try:
                text = src.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = f"[binary or non-UTF8: {rel}]"
        else:
            text = f"[missing file: {rel}]"

        result = analyze_incoming_vs_corpus(text, permanent)
        try:
            prompt_md = render_prompt_from_template(
                tpl_path,
                incoming_text=text,
                result=result,
                extra={"proposal_id": row["proposal_id"], "item_path": rel},
            )
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("Template render failed, using stub: %s", exc)
            prompt_md = result.llm_prompt_markdown

        llm_reply = ""
        if args.invoke_anythingllm and not args.dry_run:
            llm_reply = _call_anythingllm_chat(
                cfg, ma_cfg, prompt_md, int(row["proposal_id"])
            )

        obj = {
            "proposal_id": row["proposal_id"],
            "item_path": rel,
            "kind": row.get("kind"),
            "recommendation": result.recommendation,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "related_note_paths": result.related_note_paths,
            "suggested_actions": result.suggested_actions,
            "conflict_signals": result.conflict_signals,
            "anythingllm_reply": llm_reply or None,
        }
        out_objects.append({**obj, "llm_prompt_markdown": prompt_md})

        if args.json:
            print(json.dumps(obj, ensure_ascii=False, indent=2))
        else:
            chunks.append(
                f"## Proposal {row['proposal_id']} — `{rel}`\n\n"
                f"- **Rekomendacja:** `{result.recommendation}` (pewność {result.confidence})\n"
                f"- **Uzasadnienie:** {result.reasoning}\n"
                f"- **Powiązane:** {', '.join(result.related_note_paths[:3]) or '(brak)'}\n\n"
                f"### Sugerowane akcje\n"
                + "\n".join(f"- {a}" for a in result.suggested_actions)
                + "\n\n### Prompt (AnythingLLM)\n\n"
                + prompt_md
                + ("\n\n### Odpowiedź AnythingLLM\n\n" + llm_reply if llm_reply else "")
                + "\n\n---\n"
            )

        if not args.dry_run:
            audit(
                conn,
                "inbox_merge_advisor",
                "proposal",
                str(row["proposal_id"]),
                {
                    "recommendation": result.recommendation,
                    "confidence": result.confidence,
                    "invoke_anythingllm": bool(args.invoke_anythingllm),
                },
            )

    if not args.dry_run:
        conn.commit()
    conn.close()

    report = "\n".join(chunks) if chunks else ""
    if args.out and not args.dry_run:
        args.out.write_text(
            report or json.dumps(out_objects, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        _LOG.info("Wrote %s", args.out)
    elif not args.json and report:
        print(report)

    return 0


def _call_anythingllm_chat(
    cfg: dict[str, Any],
    ma_cfg: dict[str, Any],
    prompt: str,
    proposal_id: int,
) -> str:
    api_cfg = cfg.get("anythingllm") or {}
    base = str(api_cfg.get("base_url", "http://localhost:3001")).rstrip("/")
    slug = str(api_cfg.get("workspace_slug", "my-workspace"))
    key_env = str(api_cfg.get("api_key_env", "ANYTHINGLLM_API_KEY"))
    api_key = os.getenv(key_env, "").strip()
    if not api_key:
        return f"[anythingllm: ustaw zmienną środowiskową {key_env}]"

    mode = str(ma_cfg.get("anythingllm_chat_mode", "chat"))
    session_id = f"kms-merge-advisor-{proposal_id}"

    client = AnythingLLMClient(base_url=base, api_key=api_key, workspace_slug=slug)
    try:
        data = client.workspace_chat(
            prompt,
            mode=mode,
            session_id=session_id,
            reset=False,
        )
        return anythingllm_chat_text_response(data)
    except RuntimeError as exc:
        _LOG.error("AnythingLLM chat failed: %s", exc)
        return f"[anythingllm error: {exc}]"


if __name__ == "__main__":
    raise SystemExit(main())
