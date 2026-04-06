"""Full vault re-embed for AnythingLLM — use after changing embedding model/chunking.

Unlike ``sync_to_anythingllm`` (incremental, DB-driven), this script:
 1. scans vault folders on disk (30_Permanent-Notes, 20_Source-Notes, 10_Sources)
 2. uploads every markdown file to AnythingLLM
 3. embeds them in the workspace in batches

Usage:
    python -m kms.scripts.resync_embeddings                        # from config
    python -m kms.scripts.resync_embeddings --api-key AK-xxx       # explicit key
    python -m kms.scripts.resync_embeddings --dry-run               # preview only
    python -m kms.scripts.resync_embeddings --folders 30_Permanent-Notes  # subset
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from pathlib import Path

from kms.app.anythingllm_client import AnythingLLMClient
from kms.app.config import load_config, vault_paths

_LOG = logging.getLogger(__name__)

_DEFAULT_FOLDERS = [
    "30_Permanent-Notes",
    "20_Source-Notes",
    "10_Sources/web",
    "10_Sources/pdf",
]

_EXTENSIONS = {".md", ".txt", ".pdf"}


def _collect_files(vault_root: Path, folders: list[str], extensions: set[str]) -> list[Path]:
    """Collect files from vault subdirectories."""
    files: list[Path] = []
    for folder in folders:
        folder_path = vault_root / folder
        if not folder_path.exists():
            _LOG.warning("Folder not found, skipping: %s", folder_path)
            continue
        for ext in extensions:
            files.extend(sorted(folder_path.rglob(f"*{ext}")))
    return files


def _resolve_api_key(cfg: dict, cli_key: str | None) -> str:
    """Resolve API key: CLI arg > env var > empty."""
    if cli_key:
        return cli_key
    env_name = cfg.get("anythingllm", {}).get("api_key_env", "ANYTHINGLLM_API_KEY")
    return os.getenv(str(env_name), "")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Full vault re-embed for AnythingLLM (after model/chunking change)."
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="AnythingLLM API key (or set ANYTHINGLLM_API_KEY env var)",
    )
    parser.add_argument(
        "--folders",
        nargs="+",
        default=None,
        help=f"Vault subdirectories to embed (default: {_DEFAULT_FOLDERS})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Documents to embed per API call (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without uploading",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s  %(message)s",
    )

    # ── Load config ──
    cfg = load_config()
    api_cfg = cfg.get("anythingllm", {})
    vp = vault_paths(cfg)
    vault_root: Path = vp["root"]

    api_key = _resolve_api_key(cfg, args.api_key)
    if not api_key and not args.dry_run:
        _LOG.error(
            "No API key. Use --api-key AK-xxx or set %s env var.",
            api_cfg.get("api_key_env", "ANYTHINGLLM_API_KEY"),
        )
        return 2

    base_url = str(api_cfg.get("base_url", "http://localhost:3001"))
    slug = str(api_cfg.get("workspace_slug", "my-workspace"))
    folders = args.folders or _DEFAULT_FOLDERS

    # ── Collect files ──
    files = _collect_files(vault_root, folders, _EXTENSIONS)
    _LOG.info("Found %d files in %s", len(files), ", ".join(folders))

    if not files:
        _LOG.warning("No files found. Check vault path: %s", vault_root)
        return 1

    if args.dry_run:
        _LOG.info("── DRY RUN ── (no uploads)")
        for f in files:
            rel = f.relative_to(vault_root)
            size_kb = f.stat().st_size / 1024
            _LOG.info("  %s  (%.1f KB)", rel, size_kb)
        _LOG.info("Total: %d files", len(files))
        return 0

    # ── Upload + Embed ──
    client = AnythingLLMClient(
        base_url=base_url,
        workspace_slug=slug,
        api_key=api_key,
    )

    uploaded: list[str] = []
    failed: list[str] = []
    t0 = time.time()

    for i, filepath in enumerate(files, 1):
        rel = str(filepath.relative_to(vault_root))
        _LOG.info("[%d/%d] Uploading %s ...", i, len(files), rel)
        try:
            result = client.upload_document_file(filepath)
            docs = result.get("documents") or []
            if result.get("success") and docs:
                loc = docs[0].get("location", "")
                uploaded.append(loc)
                _LOG.info("  ✓ %s", loc)
            else:
                err = result.get("error", "unknown error")
                failed.append(f"{rel}: {err}")
                _LOG.error("  ✗ %s", err)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{rel}: {exc}")
            _LOG.error("  ✗ %s", exc)

    if not uploaded:
        _LOG.error("No files uploaded successfully.")
        return 3

    # ── Embed in workspace (batched) ──
    _LOG.info("")
    _LOG.info("Embedding %d documents in workspace '%s' ...", len(uploaded), slug)
    embed_ok = 0
    for batch_start in range(0, len(uploaded), args.batch_size):
        batch = uploaded[batch_start : batch_start + args.batch_size]
        batch_num = batch_start // args.batch_size + 1
        _LOG.info("  Batch %d: %d docs ...", batch_num, len(batch))
        try:
            client.update_embeddings(batch)
            embed_ok += len(batch)
            _LOG.info("  ✓ batch %d done", batch_num)
        except Exception as exc:  # noqa: BLE001
            _LOG.error("  ✗ batch %d failed: %s", batch_num, exc)
            for loc in batch:
                failed.append(f"embed:{loc}: {exc}")

    elapsed = time.time() - t0

    # ── Summary ──
    _LOG.info("")
    _LOG.info("═══════════════════════════════════")
    _LOG.info("  Uploaded:  %d / %d", len(uploaded), len(files))
    _LOG.info("  Embedded:  %d / %d", embed_ok, len(uploaded))
    _LOG.info("  Failed:    %d", len(failed))
    _LOG.info("  Time:      %.1fs", elapsed)
    _LOG.info("═══════════════════════════════════")

    if failed:
        _LOG.warning("Failed items:")
        for f in failed[:20]:
            _LOG.warning("  • %s", f)

    if args.format == "json":
        import json

        print(
            json.dumps(
                {
                    "uploaded": len(uploaded),
                    "embedded": embed_ok,
                    "failed": len(failed),
                    "elapsed_s": round(elapsed, 1),
                    "errors": failed[:20],
                },
                ensure_ascii=False,
            )
        )

    return 0 if not failed else 3


if __name__ == "__main__":
    raise SystemExit(main())
