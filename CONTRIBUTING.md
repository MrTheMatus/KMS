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

```
src/
  constants.js   — shared constants, DEFAULT_SETTINGS
  i18n.js        — PL/EN translation dictionary + _t() helper
  main.js        — plugin entry point (commands, pipeline, review block)
  modals.js      — search, detail, revert, confirm, progress modals
  panel.js       — sidebar panel (stats, actions, domains)
  settings.js    — settings tab
  wizard.js      — 5-step onboarding wizard
esbuild.config.mjs — bundler config
main.js          — built output (DO NOT edit directly)
styles.css       — all CSS with custom properties for dark/light mode
manifest.json    — plugin metadata
```

To develop:
1. `cd example-vault/.obsidian/plugins/kms-review && npm install`
2. `npm run dev` — starts esbuild in watch mode
3. Open `example-vault` in Obsidian, enable the `kms-review` plugin
4. Edit files in `src/` — esbuild rebuilds `main.js` automatically
5. `Ctrl+P` → "Reload app without saving" to see changes

Guidelines:
- **Never** edit `main.js` directly — always edit `src/*.js` and rebuild
- Use Obsidian CSS variables (`var(--text-normal)`, `var(--background-primary)`, etc.)
- Use `--kms-*` custom properties for KMS-specific colors
- All user-facing strings must go through `_t()` (i18n.js) — PL primary, EN secondary
- Test both languages before committing

## Version sync

Keep versions aligned across all four files:
- `example-vault/.obsidian/plugins/kms-review/manifest.json` → `version`
- `example-vault/.obsidian/plugins/kms-review/package.json` → `version`
- `pyproject.toml` → `version`
- `CHANGELOG.md` → latest entry
- `kms/gateway/server.py` → health endpoint version string

## Commit messages

Follow conventional style: `feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`.
