# Changelog

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
