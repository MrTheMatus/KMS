"""Validate KMS config on startup — friendly errors instead of crashes."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from urllib import error, request


class ConfigError:
    """A single validation issue."""

    def __init__(self, level: str, message: str, fix: str) -> None:
        self.level = level  # "error" or "warning"
        self.message = message
        self.fix = fix

    def __str__(self) -> str:
        icon = "ERROR" if self.level == "error" else "WARNING"
        return f"[{icon}] {self.message}\n         Fix: {self.fix}"


def validate_config(cfg: dict[str, Any], project_root: Path) -> list[ConfigError]:
    """Run all checks, return list of issues (empty = all good)."""
    issues: list[ConfigError] = []

    # 1. Vault root exists
    vault_root_rel = cfg.get("vault", {}).get("root", "")
    vault_root = (project_root / vault_root_rel).resolve() if vault_root_rel else None
    if not vault_root or not vault_root.is_dir():
        issues.append(ConfigError(
            "error",
            f"Vault root not found: {vault_root or '(not set)'}",
            f"Set vault.root in config.yaml or create directory: mkdir -p {vault_root_rel}",
        ))
    else:
        # Check subdirectories
        for key in ("inbox_dir", "admin_dir", "sources_web", "sources_pdf", "source_notes", "permanent_notes"):
            sub = cfg.get("vault", {}).get(key, "")
            if sub and not (vault_root / sub).is_dir():
                issues.append(ConfigError(
                    "warning",
                    f"Vault directory missing: {vault_root / sub}",
                    f"mkdir -p \"{vault_root / sub}\"",
                ))

    # 2. Database path writable
    db_rel = cfg.get("database", {}).get("path", "")
    if db_rel:
        db_path = (project_root / db_rel).resolve()
        db_dir = db_path.parent
        if not db_dir.is_dir():
            issues.append(ConfigError(
                "warning",
                f"Database directory missing: {db_dir}",
                f"mkdir -p \"{db_dir}\"",
            ))

    # 3. LLM provider availability (warning only)
    # Supports new llm: section and legacy ollama: fallback
    llm_cfg = cfg.get("llm") or {}
    llm_url = str(llm_cfg.get("base_url", "")).rstrip("/")
    llm_model = str(llm_cfg.get("model", ""))
    llm_key_env = str(llm_cfg.get("api_key_env", "") or "")

    # Fallback to legacy ollama: if llm: not configured
    if not llm_url:
        ollama_cfg = cfg.get("ollama", {})
        llm_url = str(ollama_cfg.get("base_url", "http://localhost:11434")).rstrip("/")
        llm_model = str(ollama_cfg.get("model", "qwen2.5:14b"))

    # Check API key for cloud providers
    if llm_key_env and not os.getenv(llm_key_env, "").strip():
        issues.append(ConfigError(
            "warning",
            f"LLM API key not set (env: {llm_key_env})",
            f"export {llm_key_env}=your-api-key",
        ))

    # Check connectivity via /v1/models (works for Ollama and OpenAI-compat)
    try:
        import json

        check_url = f"{llm_url}/v1/models"
        headers = {}
        if llm_key_env:
            key = os.getenv(llm_key_env, "")
            if key:
                headers["Authorization"] = f"Bearer {key}"
        req = request.Request(check_url, method="GET", headers=headers)
        with request.urlopen(req, timeout=3) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("id", "") for m in data.get("data", [])]
            if llm_model:
                model_base = llm_model.split(":")[0]
                if not any(model_base in m for m in models):
                    issues.append(ConfigError(
                        "warning",
                        f"LLM model '{llm_model}' not found (available: {', '.join(models[:5]) or 'none'})",
                        f"ollama pull {llm_model}" if "localhost" in llm_url else f"Check model name: {llm_model}",
                    ))
    except Exception:  # noqa: BLE001
        issues.append(ConfigError(
            "warning",
            f"LLM not reachable at {llm_url}",
            "brew services start ollama" if "localhost" in llm_url or "11434" in llm_url
            else f"Check LLM provider at {llm_url}",
        ))

    # 4. AnythingLLM (warning only if enabled)
    allm = cfg.get("anythingllm", {})
    if allm.get("enabled", False):
        allm_url = str(allm.get("base_url", "http://localhost:3001"))
        key_env = str(allm.get("api_key_env", "ANYTHINGLLM_API_KEY"))
        if not os.getenv(key_env, "").strip():
            issues.append(ConfigError(
                "warning",
                f"AnythingLLM enabled but API key not set (env: {key_env})",
                f"export {key_env}=your-api-key",
            ))
        try:
            req = request.Request(f"{allm_url}/api/health", method="GET")
            request.urlopen(req, timeout=3)  # noqa: S310
        except Exception:  # noqa: BLE001
            issues.append(ConfigError(
                "warning",
                f"AnythingLLM not reachable at {allm_url}",
                "docker compose up -d",
            ))

    # 5. Archive directory
    if vault_root and vault_root.is_dir():
        archive_dir_name = cfg.get("vault", {}).get("archive_dir", "")
        if archive_dir_name:
            archive_path = vault_root / archive_dir_name
            if not archive_path.is_dir():
                issues.append(ConfigError(
                    "warning",
                    f"Archive directory missing: {archive_path}",
                    f"mkdir -p \"{archive_path}\"",
                ))

    # 6. Template files exist
    templates = cfg.get("templates", {})
    for tpl_key, tpl_rel in templates.items():
        if not tpl_rel:
            continue
        tpl_path = project_root / tpl_rel
        if not tpl_path.is_file():
            issues.append(ConfigError(
                "warning",
                f"Template file missing: {tpl_path} (templates.{tpl_key})",
                f"Check path in config.yaml: templates.{tpl_key}",
            ))

    # 7. Review queue file path
    rq_file = cfg.get("paths", {}).get("review_queue_file", "")
    if not rq_file:
        issues.append(ConfigError(
            "error",
            "paths.review_queue_file not set in config",
            "Add to config.yaml: paths:\n  review_queue_file: \"00_Admin/review-queue.md\"",
        ))

    return issues


def print_validation(issues: list[ConfigError]) -> bool:
    """Print issues to stderr. Return True if any errors (not just warnings)."""
    if not issues:
        return False
    print("\n  KMS Config Validation\n  " + "=" * 40, file=sys.stderr)
    for issue in issues:
        print(f"\n  {issue}", file=sys.stderr)
    print("", file=sys.stderr)
    return any(i.level == "error" for i in issues)
