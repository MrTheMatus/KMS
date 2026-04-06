"""Verify vault ↔ SQLite consistency: detect drift between filesystem and DB state.

Modes:
  (default)        Check vault/DB consistency only
  --self-check     Full environment check: deps, config, vault structure, DB, plugin
"""

from __future__ import annotations

import importlib
import json
import logging

from kms.app.config import abs_path, vault_paths
from kms.app.db import connect, ensure_schema, fetch_all_dicts
from kms.app.hashing import sha256_file
from kms.app.paths import project_root
from kms.scripts._cli import build_parser, load_setup_logging

_LOG = logging.getLogger(__name__)

_REQUIRED_DEPS = ["yaml", "jinja2", "pypdf"]
_VAULT_DIRS = [
    "admin_dir",
    "inbox",
    "sources_web",
    "sources_pdf",
    "source_notes",
    "permanent_notes",
    "archive",
]


def _check_deps() -> list[dict]:
    """Check that required Python packages are importable."""
    issues = []
    for mod in _REQUIRED_DEPS:
        try:
            importlib.import_module(mod)
        except ImportError:
            issues.append({"check": "dependency", "module": mod, "status": "missing"})
    return issues


def _check_vault_structure(vp: dict) -> list[dict]:
    """Check that expected vault directories exist."""
    issues = []
    for key in _VAULT_DIRS:
        if key not in vp:
            continue
        d = vp[key]
        if not d.is_dir():
            issues.append(
                {"check": "vault_dir", "path": str(d), "key": key, "status": "missing"}
            )
    return issues


def _check_plugin(vp: dict) -> list[dict]:
    """Check that plugin essential files exist."""
    issues = []
    plugin_dir = vp["root"] / ".obsidian" / "plugins" / "kms-review"
    for fname in ("main.js", "manifest.json", "styles.css"):
        fpath = plugin_dir / fname
        if not fpath.is_file():
            issues.append({"check": "plugin", "file": fname, "status": "missing"})
    if (plugin_dir / "manifest.json").is_file():
        try:
            manifest = json.loads((plugin_dir / "manifest.json").read_text())
            if "version" not in manifest:
                issues.append(
                    {"check": "plugin", "file": "manifest.json", "status": "no_version"}
                )
        except (json.JSONDecodeError, OSError):
            issues.append(
                {"check": "plugin", "file": "manifest.json", "status": "parse_error"}
            )
    return issues


def _check_config(cfg: dict) -> list[dict]:
    """Basic config sanity checks."""
    issues = []
    if not cfg.get("vault", {}).get("root"):
        issues.append({"check": "config", "field": "vault.root", "status": "missing"})
    if not cfg.get("database", {}).get("path"):
        issues.append(
            {"check": "config", "field": "database.path", "status": "missing"}
        )
    return issues


def _check_db_consistency(conn, vault_root, vp) -> tuple[list, list, list]:
    """Check vault ↔ DB drift: missing files, hash mismatches, orphan inbox files."""
    items = fetch_all_dicts(conn, "SELECT id, path, hash, status FROM items")

    missing_files: list[dict] = []
    hash_mismatches: list[dict] = []
    orphan_files: list[str] = []

    db_paths: set[str] = set()
    for item in items:
        rel = item["path"]
        db_paths.add(rel)
        full = vault_root / rel
        if not full.is_file():
            if item["status"] not in ("applied", "failed"):
                missing_files.append(
                    {"id": item["id"], "path": rel, "status": item["status"]}
                )
        else:
            current_hash = sha256_file(full)
            if item["hash"] and current_hash != item["hash"]:
                hash_mismatches.append(
                    {
                        "id": item["id"],
                        "path": rel,
                        "db_hash": item["hash"][:12] + "\u2026",
                        "file_hash": current_hash[:12] + "\u2026",
                    }
                )

    inbox = vp["inbox"]
    if inbox.is_dir():
        for f in sorted(inbox.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                try:
                    rel = f.relative_to(vault_root).as_posix()
                except ValueError:
                    continue
                if rel not in db_paths:
                    orphan_files.append(rel)

    return missing_files, hash_mismatches, orphan_files


def main() -> int:
    p = build_parser(
        "Check vault \u2194 SQLite consistency: missing files, hash mismatches, orphan DB rows."
    )
    p.add_argument("--json", action="store_true", help="Output results as JSON")
    p.add_argument(
        "--self-check",
        action="store_true",
        help="Full environment check (deps, config, vault, DB, plugin)",
    )
    args = p.parse_args()
    cfg = load_setup_logging(args)
    schema_path = project_root() / "kms" / "app" / "schema.sql"
    db_path = abs_path(cfg, "database", "path")
    vp = vault_paths(cfg)
    vault_root = vp["root"]

    conn = connect(db_path)
    ensure_schema(conn, schema_path)

    # --- Core DB consistency check (always runs) ---
    missing_files, hash_mismatches, orphan_files = _check_db_consistency(
        conn, vault_root, vp
    )
    conn.close()

    db_ok = not missing_files and not hash_mismatches and not orphan_files

    # --- Extended self-check (optional) ---
    env_issues: list[dict] = []
    if args.self_check:
        env_issues.extend(_check_deps())
        env_issues.extend(_check_config(cfg))
        env_issues.extend(_check_vault_structure(vp))
        env_issues.extend(_check_plugin(vp))

    all_ok = db_ok and not env_issues

    if args.json:
        result = {
            "ok": all_ok,
            "missing_files": missing_files,
            "hash_mismatches": hash_mismatches,
            "orphan_inbox_files": orphan_files,
        }
        if args.self_check:
            result["environment_issues"] = env_issues
            result["self_check"] = not env_issues
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if args.self_check:
            if env_issues:
                print(f"Environment issues ({len(env_issues)}):")
                for iss in env_issues:
                    print(
                        f"  [{iss['check']}] {iss.get('module') or iss.get('field') or iss.get('path') or iss.get('file')}: {iss['status']}"
                    )
            else:
                print(
                    "Environment check passed: deps, config, vault structure, plugin OK."
                )
            print()

        if db_ok:
            print("Integrity check passed: vault and SQLite are consistent.")
        else:
            if missing_files:
                print(f"Missing files ({len(missing_files)}):")
                for m in missing_files:
                    print(f"  [{m['status']}] {m['path']} (item {m['id']})")
            if hash_mismatches:
                print(f"Hash mismatches ({len(hash_mismatches)}):")
                for h in hash_mismatches:
                    print(
                        f"  {h['path']} \u2014 DB: {h['db_hash']}, file: {h['file_hash']}"
                    )
            if orphan_files:
                print(f"Inbox files not in DB ({len(orphan_files)}):")
                for o in orphan_files:
                    print(f"  {o}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
