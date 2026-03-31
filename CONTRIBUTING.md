# Contributing

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp kms/config/config.example.yaml kms/config/config.yaml
```

## Running tests

```bash
export PYTHONPATH=.
python -m pytest tests/ -v
```

## Linting

```bash
pip install ruff
ruff check kms/ tests/ scripts/
ruff format --check kms/ tests/
```

## Python code

- All code in `kms/` — scripts in `kms/scripts/`, core logic in `kms/app/`
- Every function must be fully typed (no implicit `Any`)
- Use `from __future__ import annotations` in every module
- Follow existing patterns: `build_parser` + `load_setup_logging` for CLI scripts
- Tests go in `tests/` with matching naming (`test_<module>.py`)

## Obsidian plugin

The plugin lives in `example-vault/.obsidian/plugins/kms-review/`:

- `main.js` — single-file plugin (no build step, plain CommonJS)
- `styles.css` — all CSS with custom properties for dark/light mode
- `manifest.json` — plugin metadata

To develop:
1. Open `example-vault` in Obsidian
2. Enable the `kms-review` plugin in Settings → Community plugins
3. Edit `main.js` or `styles.css`
4. `Ctrl+P` → "Reload app without saving" to see changes

Guidelines:
- Use Obsidian CSS variables (`var(--text-normal)`, `var(--background-primary)`, etc.)
- Use `--kms-*` custom properties for KMS-specific colors
- All user-facing strings should support PL (primary) and EN

## Version sync

Keep versions aligned:
- `manifest.json` → `version`
- `pyproject.toml` → `version`
- `CHANGELOG.md` → latest entry

## Commit messages

Follow conventional style: `feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`.
