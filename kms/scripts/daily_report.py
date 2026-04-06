"""Daily text report: vault stats and recent files (Etap 1 / 3)."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from kms.app.config import abs_path, vault_paths
from kms.app.db import audit, connect, ensure_schema
from kms.app.paths import ensure_dir, project_root
from kms.scripts._cli import add_dry_run, build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)


def _count_md(root: Path) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for _ in root.rglob("*.md"))


def _recent_files(root: Path, since: datetime, limit: int = 20) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[tuple[float, Path]] = []
    for p in root.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if datetime.fromtimestamp(m, tz=timezone.utc) >= since:
                out.append((m, p))
    out.sort(key=lambda x: -x[0])
    return [p for _, p in out[:limit]]


def main() -> int:
    p = build_parser("Write a daily text report under vault 00_Admin/reports.")
    add_dry_run(p)
    p.add_argument(
        "--since",
        choices=("1d", "7d", "30d"),
        default="1d",
        help="Highlight files modified since this window (default: 1d)",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    dry_run = getattr(args, "dry_run", False)
    vp = vault_paths(cfg)
    vault_root = vp["root"]
    reports_dir = vp["reports"]
    ensure_dir(reports_dir)

    today = date.today().isoformat()
    out_path = reports_dir / f"daily-{today}.txt"

    delta = {"1d": 1, "7d": 7, "30d": 30}[args.since]
    since_dt = datetime.now(timezone.utc) - timedelta(days=delta)

    lines: list[str] = [
        f"KMS daily report {today}",
        f"Vault: {vault_root}",
        f"Profile: {cfg.get('runtime', {}).get('profile', 'local')}",
        "",
        "Counts (markdown files):",
        f"  Inbox: {_count_md(vp['inbox'])}",
        f"  Source notes: {_count_md(vp['source_notes'])}",
        f"  Vault total .md: {_count_md(vault_root)}",
        "",
        f"Recently touched (since ~{args.since}):",
    ]
    for rel_base, label in [
        (vp["inbox"], "inbox"),
        (vp["source_notes"], "source_notes"),
    ]:
        rec = _recent_files(rel_base, since_dt)
        lines.append(f"  [{label}]")
        for f in rec[:10]:
            try:
                rel = f.relative_to(vault_root)
            except ValueError:
                rel = f
            lines.append(f"    - {rel}")
        if not rec:
            lines.append("    (none)")

    body = "\n".join(lines) + "\n"
    if dry_run:
        _LOG.info("dry-run: would write %s", out_path)
        print(body)
        return 0
    out_path.write_text(body, encoding="utf-8")

    try:
        db_path = abs_path(cfg, "database", "path")
        schema_path = project_root() / "kms" / "app" / "schema.sql"
        conn = connect(db_path)
        ensure_schema(conn, schema_path)
        audit(
            conn,
            "daily_report",
            "report",
            today,
            {
                "path": str(out_path.relative_to(vault_root))
                if out_path.is_relative_to(vault_root)
                else str(out_path),
                "since": args.since,
            },
        )
        conn.close()
    except Exception:  # noqa: BLE001
        pass

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
