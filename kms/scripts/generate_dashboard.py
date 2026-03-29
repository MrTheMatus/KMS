"""Generate 00_Admin/dashboard.md with pipeline stats for Obsidian."""

from __future__ import annotations

import logging
from pathlib import Path

from kms.app.config import abs_path, vault_paths
from kms.app.db import connect, ensure_schema, fetch_all_dicts, utc_now_iso
from kms.app.paths import project_root
from kms.scripts._cli import build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def main() -> int:
    p = build_parser("Generate KMS dashboard markdown for Obsidian.")
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    # --- Inbox stats ---
    inbox = vp["inbox"]
    inbox_files = 0
    inbox_by_kind: dict[str, int] = {}
    if inbox.is_dir():
        for f in inbox.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                inbox_files += 1
                suf = f.suffix.lower()
                kind = "pdf" if suf == ".pdf" else "markdown" if suf in (".md", ".markdown") else "other"
                inbox_by_kind[kind] = inbox_by_kind.get(kind, 0) + 1

    # --- Proposal stats ---
    proposal_stats = fetch_all_dicts(
        conn,
        """SELECT
             COALESCE(d.decision, 'pending') AS decision,
             COUNT(*) AS cnt
           FROM proposals p
           LEFT JOIN decisions d ON d.proposal_id = p.id
           GROUP BY decision""",
    )
    decision_counts = {r["decision"]: r["cnt"] for r in proposal_stats}
    total_proposals = sum(decision_counts.values())

    # --- Lifecycle stats ---
    lifecycle_stats = fetch_all_dicts(
        conn,
        "SELECT lifecycle_status, COUNT(*) AS cnt FROM proposals WHERE lifecycle_status IS NOT NULL GROUP BY lifecycle_status",
    )
    lifecycle_counts = {r["lifecycle_status"]: r["cnt"] for r in lifecycle_stats}

    # --- Index stats ---
    index_stats = fetch_all_dicts(
        conn,
        "SELECT index_status, COUNT(*) AS cnt FROM artifacts GROUP BY index_status",
    )
    index_counts = {r["index_status"]: r["cnt"] for r in index_stats}

    # --- Recent audit entries ---
    recent_audit = fetch_all_dicts(
        conn,
        "SELECT ts, action, entity_type, payload_json FROM audit_log ORDER BY ts DESC LIMIT 10",
    )

    # --- Domain breakdown ---
    domain_stats = _domain_breakdown(conn)

    conn.close()

    # --- Render ---
    now = utc_now_iso()[:16].replace("T", " ")
    pending = decision_counts.get("pending", 0)
    postpone = decision_counts.get("postpone", 0)
    approved = decision_counts.get("approve", 0)
    rejected = decision_counts.get("reject", 0)

    lines = [
        "# KMS Dashboard",
        "",
        f"> Ostatnia aktualizacja: {now}",
        "",
        "## Stan pipeline",
        "",
        "| Metryka | Wartość |",
        "|---------|--------|",
        f"| Pliki w Inbox | **{inbox_files}** |",
        f"| Propozycje pending | **{pending}** |",
        f"| Propozycje postpone | **{postpone}** |",
        f"| Approved (zastosowane) | **{approved}** |",
        f"| Rejected | **{rejected}** |",
        f"| Propozycje total | {total_proposals} |",
        "",
    ]

    # Index status (only if artifacts exist)
    if index_counts:
        lines.extend([
            "## Indeksowanie (AnythingLLM)",
            "",
            "| Status | Ilość |",
            "|--------|-------|",
        ])
        for status in ("ok", "pending", "failed"):
            cnt = index_counts.get(status, 0)
            if cnt:
                icon = {"ok": "OK", "pending": "Pending", "failed": "FAILED"}.get(status, status)
                lines.append(f"| {icon} | {cnt} |")
        lines.append("")

    # Inbox breakdown
    if inbox_by_kind:
        lines.extend([
            "## Inbox wg typu",
            "",
            "| Typ | Plików |",
            "|-----|--------|",
        ])
        for kind in sorted(inbox_by_kind, key=inbox_by_kind.get, reverse=True):
            lines.append(f"| {kind} | {inbox_by_kind[kind]} |")
        lines.append("")

    # Domain breakdown
    if domain_stats:
        lines.extend([
            "## Domeny (auto-detected)",
            "",
            "| Domena | Propozycji |",
            "|--------|-----------|",
        ])
        for domain, cnt in domain_stats[:10]:
            lines.append(f"| {domain} | {cnt} |")
        lines.append("")

    # Recent activity
    if recent_audit:
        lines.extend([
            "## Ostatnie akcje",
            "",
        ])
        for entry in recent_audit[:8]:
            ts = (entry["ts"] or "")[:16].replace("T", " ")
            action = entry["action"] or ""
            etype = entry["entity_type"] or ""
            lines.append(f"- `{ts}` — **{action}** ({etype})")
        lines.append("")

    # Quick actions (for PO reference)
    lines.extend([
        "## Szybkie akcje",
        "",
        "- **Ctrl+P** → `KMS: Refresh review queue` — skan inboxa + AI streszczenia",
        "- **Ctrl+P** → `KMS: Apply decisions` — zastosuj zatwierdzone propozycje",
        "- **Ctrl+P** → `KMS: Approve all pending` — zatwierdź wszystkie oczekujące",
        "- **Ctrl+P** → `KMS: Open review queue` — otwórz kolejkę",
        "",
        "---",
        f"*Wygenerowano automatycznie przez `generate_dashboard.py` — {now}*",
        "",
    ])

    md = "\n".join(lines)
    dashboard_path = vp["admin"] / "dashboard.md"
    dashboard_path.write_text(md, encoding="utf-8")
    _LOG.info("Dashboard written to %s", dashboard_path)
    print(str(dashboard_path))
    return 0


def _domain_breakdown(conn) -> list[tuple[str, int]]:
    """Extract domain counts from proposals metadata JSON."""
    import json

    rows = fetch_all_dicts(
        conn,
        "SELECT suggested_metadata_json FROM proposals WHERE suggested_metadata_json IS NOT NULL",
    )
    counts: dict[str, int] = {}
    for row in rows:
        try:
            data = json.loads(row["suggested_metadata_json"])
            triage = data.get("triage", {})
            domain = triage.get("suggested_domain", "")
            if domain:
                counts[domain] = counts.get(domain, 0) + 1
        except Exception:  # noqa: BLE001
            pass
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


if __name__ == "__main__":
    raise SystemExit(main())
