"""Parse and render review-queue.md (YAML blocks between HTML markers)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

BEGIN = "<!-- kms:begin -->"
END = "<!-- kms:end -->"


@dataclass
class ParsedBlock:
    proposal_id: int
    item_id: int
    decision: str
    reviewer: str
    override_target: str | None
    review_note: str
    raw_body: str


def _extract_yaml_from_fence(text: str) -> tuple[dict[str, Any], str]:
    """Return (yaml_dict, markdown body after closing fence)."""
    text = text.strip()
    lines = text.splitlines()
    if not lines:
        return {}, ""
    if not lines[0].strip().startswith("```"):
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("YAML block must be a mapping")
        return data, ""
    yaml_lines: list[str] = []
    i = 1
    while i < len(lines) and lines[i].strip() != "```":
        yaml_lines.append(lines[i])
        i += 1
    if i >= len(lines) or lines[i].strip() != "```":
        raise ValueError("Unclosed ``` fence in kms block")
    body = "\n".join(lines[i + 1 :]).strip()
    data = yaml.safe_load("\n".join(yaml_lines)) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML block must be a mapping")
    return data, body


def parse_review_queue_markdown(content: str) -> list[ParsedBlock]:
    """Extract proposal blocks from full file content."""
    out: list[ParsedBlock] = []
    pos = 0
    while True:
        start = content.find(BEGIN, pos)
        if start < 0:
            break
        end = content.find(END, start + len(BEGIN))
        if end < 0:
            raise ValueError("Unclosed kms block: missing <!-- kms:end -->")
        block_text = content[start + len(BEGIN) : end].strip()
        pos = end + len(END)
        data, body = _extract_yaml_from_fence(block_text)
        pid = int(data["proposal_id"])
        iid = int(data["item_id"])
        decision = str(data.get("decision", "pending")).lower().strip()
        reviewer = str(data.get("reviewer", "") or "")
        override = data.get("override_target")
        override_target = str(override) if override else None
        review_note = str(data.get("review_note", "") or "")
        out.append(
            ParsedBlock(
                proposal_id=pid,
                item_id=iid,
                decision=decision,
                reviewer=reviewer,
                override_target=override_target,
                review_note=review_note,
                raw_body=body,
            )
        )
    return out


def render_review_queue(
    title: str,
    blocks: list[dict[str, Any]],
) -> str:
    """blocks: proposal dicts with keys proposal_id, item_id, path, kind, suggested_action, suggested_target, reason, decision, reviewer, override_target, body_md"""
    lines: list[str] = [f"# {title}", ""]
    for idx, b in enumerate(blocks):
        lines.append(BEGIN)
        lines.append("```kms-review")
        lines.append(
            yaml.dump(
                {
                    "proposal_id": b["proposal_id"],
                    "item_id": b["item_id"],
                    "decision": b.get("decision", "pending"),
                    "reviewer": b.get("reviewer", ""),
                    "override_target": b.get("override_target"),
                    "review_note": b.get("review_note", ""),
                },
                allow_unicode=True,
                default_flow_style=False,
            ).strip()
        )
        lines.append("```")
        lines.append("")
        lines.append(str(b.get("body_md", "")).strip())
        lines.append("")
        lines.append(END)
        lines.append("")
        # Thick separator between proposals
        if idx < len(blocks) - 1:
            lines.append("***")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
