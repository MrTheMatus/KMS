"""Tests for kms.app.config: load, merge env, abs_path, vault_paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from kms.app.config import abs_path, load_config, vault_paths


def _write_cfg(tmp: Path, data: dict[str, Any]) -> Path:
    cfg_dir = tmp / "kms" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    p = cfg_dir / "config.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


@pytest.fixture
def minimal_cfg() -> dict[str, Any]:
    return {
        "vault": {
            "root": "example-vault",
            "admin_dir": "00_Admin",
            "inbox_dir": "00_Inbox",
            "sources_web": "10_Sources/web",
            "sources_pdf": "10_Sources/pdf",
            "source_notes": "20_Source-Notes",
            "permanent_notes": "30_Permanent-Notes",
            "archive_dir": "99_Archive",
        },
        "database": {"path": "kms/data/state.db"},
        "paths": {
            "review_queue_file": "00_Admin/review-queue.md",
            "daily_report_dir": "00_Admin/reports",
        },
        "templates": {"source_note": "kms/templates/source_note.md.j2"},
        "runtime": {"profile": "local"},
        "logging": {"level": "INFO"},
    }


class TestLoadConfig:
    def test_loads_explicit_path(
        self, tmp_path: Path, minimal_cfg: dict[str, Any]
    ) -> None:
        p = tmp_path / "custom.yaml"
        p.write_text(yaml.safe_dump(minimal_cfg), encoding="utf-8")
        cfg = load_config(p)
        assert cfg["vault"]["root"] == "example-vault"

    def test_missing_file_falls_back_to_example(self) -> None:
        bogus = Path("/no_such_dir/nonexistent.yaml")
        cfg = load_config(bogus)
        assert "vault" in cfg, "should fall back to config.example.yaml"

    def test_missing_all_configs_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("kms.app.config.project_root", lambda: tmp_path)
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")

    def test_non_dict_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text("- list\n- not dict\n", encoding="utf-8")
        with pytest.raises(ValueError, match="mapping"):
            load_config(p)

    def test_env_overrides_vault_root(
        self,
        tmp_path: Path,
        minimal_cfg: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        p = tmp_path / "c.yaml"
        p.write_text(yaml.safe_dump(minimal_cfg), encoding="utf-8")
        monkeypatch.setenv("KMS_VAULT_ROOT", "/custom/vault")
        cfg = load_config(p)
        assert cfg["vault"]["root"] == "/custom/vault"

    def test_env_overrides_db_path(
        self,
        tmp_path: Path,
        minimal_cfg: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        p = tmp_path / "c.yaml"
        p.write_text(yaml.safe_dump(minimal_cfg), encoding="utf-8")
        monkeypatch.setenv("KMS_DATABASE_PATH", "/tmp/custom.db")
        cfg = load_config(p)
        assert cfg["database"]["path"] == "/tmp/custom.db"


class TestAbsPath:
    def test_resolves_relative(self, minimal_cfg: dict[str, Any]) -> None:
        result = abs_path(minimal_cfg, "database", "path")
        assert result.is_absolute()
        assert result.name == "state.db"

    def test_preserves_absolute(self, minimal_cfg: dict[str, Any]) -> None:
        minimal_cfg["database"]["path"] = "/absolute/state.db"
        result = abs_path(minimal_cfg, "database", "path")
        assert str(result) == "/absolute/state.db"

    def test_missing_key_raises(self, minimal_cfg: dict[str, Any]) -> None:
        with pytest.raises(KeyError):
            abs_path(minimal_cfg, "nonexistent", "key")

    def test_non_string_raises(self, minimal_cfg: dict[str, Any]) -> None:
        minimal_cfg["database"]["path"] = 42
        with pytest.raises(TypeError):
            abs_path(minimal_cfg, "database", "path")


class TestVaultPaths:
    def test_returns_expected_keys(self, minimal_cfg: dict[str, Any]) -> None:
        vp = vault_paths(minimal_cfg)
        expected_keys = {
            "root",
            "admin",
            "inbox",
            "sources_web",
            "sources_pdf",
            "source_notes",
            "permanent_notes",
            "archive",
            "review_queue",
            "reports",
        }
        assert set(vp.keys()) == expected_keys

    def test_all_paths_are_absolute(self, minimal_cfg: dict[str, Any]) -> None:
        vp = vault_paths(minimal_cfg)
        for key, path in vp.items():
            assert path.is_absolute(), f"{key} should be absolute"
