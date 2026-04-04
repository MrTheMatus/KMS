# Changelog

## 0.3.0 — 2026-04-03 (Modular plugin, i18n, product polish)

### Obsidian Plugin — Modularization
- **Source split into 7 modules** (`src/constants`, `i18n`, `panel`, `settings`, `wizard`, `modals`, `main`) bundled via esbuild
- Build: `npm run build` produces single `main.js`; `npm run dev` for watch mode
- Each module has a single responsibility — panel, wizard, modals, settings, i18n

### Obsidian Plugin — Features
- **Full i18n (PL/EN)**: all UI strings use `_t()` helper with translation dictionary
- **5-step onboarding wizard**: Welcome → Profile → Environment → Inbox → First Scan
- **Profile setting**: `core` / `ai-local` / `ai-cloud` — controls feature visibility
- **Batch revert modal**: list active batches, revert entire bulk operation with one click
- **Retriage command**: re-classify proposals via LLM without full rescan
- **Search modal**: find proposals by text, filter pending-only
- **Panel sections**: Pipeline, Bulk, Navigate, Advanced — profile-aware visibility

### Pipeline
- **Batch tracking**: every `apply_decisions` run creates a UUID batch grouping all operations
- `list_batches` script: JSON API for plugin's batch revert modal
- `revert_apply --batch-id <UUID>`: revert all proposals from a batch at once
- Dashboard: time-range filtering (24h + 7d collapsible), batch history table

### Dead Code Removed
- Removed `ollama_client.py` (82 LOC), `gateway/` (121 LOC), `ollama_pull_models.py` (53 LOC)
- Removed Flask from dependencies
- Removed `tests/test_gateway.py`, `docs/gateway.md`

### Documentation & Product
- Fixed docs↔code drift: `workflow.md` now correctly describes reject→archive flow
- Added wizard, dashboard, and batch tracking sections to `workflow.md`
- Updated command list: all 12 Obsidian commands documented
- Added MIT LICENSE
- Removed 7 junk `Untitled*.base/canvas` files from example-vault
- `manifest.json`: `isDesktopOnly: true` (was false but plugin uses child_process)

---

## 0.2.0 — 2026-03-30 (Product release)

### Architecture
- Removed plugin from non-goals; Obsidian plugin is now an official component (§3)
- Updated roadmap: Etap 7 (Plugin) = Done, Etap 8 (Product polish) in progress
- ADR-005 marked as superseded (gateway implemented in Etap 6)

### Pipeline
- Archive flow: rejected proposals automatically moved to `99_Archive/rejected/YYYY-MM/`
- Config validator: checks for archive directory, template files existence
- Full e2e test coverage for all CLI scripts (generate_dashboard, status, daily_report, generate_source_note, convert_conversation)

### Obsidian Plugin
- **Settings tab**: Python path, project root, language (PL/EN), AnythingLLM toggle
- **First-run health check**: modal checking Python, config.yaml, and verify_integrity
- **Confirmation modals**: bulk approve/reject now requires confirmation
- **Progress modal**: step-by-step progress with elapsed time instead of simple Notice
- **Error surfacing**: parsed Traceback display, "Copy error" button
- **Dark mode**: all colors use CSS custom properties with Obsidian var() fallbacks
- **Responsive**: modals use `min(Xpx, 90vw)`, stats grid uses `auto-fill`
- **Accessibility**: `aria-label` on decision buttons, `focus-visible` outlines

### CI
- Added Python 3.14 to test matrix
- Added `ruff check scripts/` to lint job
- Added `verify_integrity` smoke test job

### Documentation
- Rewritten README: "5 minutes to first review" quick start
- Updated testing-baseline.md with Day 0 checks completed (117 tests green)
- Added CHANGELOG.md and CONTRIBUTING.md

## 0.1.0 — 2026-03-24 (MVP)

- Initial release: scan, review, apply, revert, sync, gateway
- Obsidian plugin: review blocks, search, dashboard, revert
- CI: pytest + ruff on Python 3.11–3.13
- Docker support for AnythingLLM
