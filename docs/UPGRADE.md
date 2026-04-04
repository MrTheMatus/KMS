# Upgrade Guide

## Version compatibility

| From | To | DB migration | Config changes | Plugin rebuild |
|------|----|-------------|----------------|----------------|
| 0.1.0 | 0.2.0 | Auto (schema.sql is additive) | Add `backup:` section | N/A (plugin was new) |
| 0.2.0 | 0.3.0 | Auto (batches table added) | No changes required | Replace `main.js` |
| 0.3.x | 0.3.x | None | None | None |

## General upgrade procedure

```bash
cd /path/to/KMS
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt

# Verify everything works:
export PYTHONPATH=.
python -m kms.scripts.verify_integrity --json
```

Then update the plugin (if using Obsidian):
```bash
# If you use the example vault, the plugin updates with git pull.
# If you copied the plugin to a separate vault:
cp example-vault/.obsidian/plugins/kms-review/{main.js,manifest.json,styles.css} \
   /path/to/your/vault/.obsidian/plugins/kms-review/
```

Restart Obsidian after updating plugin files.

---

## v0.2.0 → v0.3.0

Released: 2026-04-03

### What changed

1. **Plugin modularized** — source split into 7 modules (`src/`), bundled via esbuild. The built `main.js` is still a single file — drop-in replacement.

2. **Full i18n** — all UI strings now go through `_t()`. Language (PL/EN) is set in plugin settings.

3. **Profile setting** — new `profile` field (`core` / `ai-local` / `ai-cloud`). Controls which features are visible in the UI. Default: `core`.

4. **Onboarding wizard** — 5-step setup wizard runs on first launch. If you're upgrading and already configured, set `onboardingDone: true` in plugin's `data.json` to skip it.

5. **Batch tracking** — `apply_decisions` now creates UUID-based batches. New scripts: `list_batches`, `revert_apply --batch-id`.

6. **Dead code removed** — `ollama_client.py`, `gateway/`, `ollama_pull_models.py`, `tests/test_gateway.py`, `docs/gateway.md` all removed. If you had custom code depending on these, refactor to use `llm_client.py` (OpenAI-compatible).

### Upgrade steps

```bash
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt

# DB schema updates automatically on next run.
# The 'batches' table is created by ensure_schema() if missing.
export PYTHONPATH=.
python -m kms.scripts.verify_integrity --json
```

**Plugin update:**
```bash
# Replace plugin files in your vault:
cp example-vault/.obsidian/plugins/kms-review/{main.js,manifest.json,styles.css} \
   /path/to/your/vault/.obsidian/plugins/kms-review/
```

**Optional — skip wizard on upgrade:**
Edit `example-vault/.obsidian/plugins/kms-review/data.json`:
```json
{
  "onboardingDone": true,
  "profile": "core"
}
```

### Breaking changes

- `ollama_client.py` removed → use `llm_client.py` (same API, provider-agnostic)
- `gateway/` removed → see ADR-005 (deferred)
- Plugin constructor signatures changed (internal only — no action needed unless you patched `main.js` manually)

---

## v0.1.0 → v0.2.0

Released: 2026-03-30

### What changed

1. **Archive flow** — rejected proposals now move to `99_Archive/` instead of being deleted.
2. **Plugin added** — first version of `kms-review` Obsidian plugin.
3. **Review queue format** — uses `<!-- kms:begin -->` / `<!-- kms:end -->` markers.
4. **Backup config** — new `backup:` section in config.yaml.

### Upgrade steps

```bash
git pull origin main
pip install -r requirements.txt

# Add backup section to your config.yaml if missing:
# backup:
#   include_sqlite: true
#   dest: "kms/backups"
```

No DB migration needed — schema is additive.

---

## Self-check after any upgrade

Run this checklist after every upgrade:

```bash
export PYTHONPATH=.

# 1. Dependencies
pip install -r requirements.txt

# 2. Integrity
python -m kms.scripts.verify_integrity --json

# 3. Quick smoke test
python -m kms.scripts.scan_inbox --help
python -m kms.scripts.make_review_queue --help

# 4. Plugin version matches
grep '"version"' example-vault/.obsidian/plugins/kms-review/manifest.json
grep 'version' pyproject.toml
```

Both version numbers should show `0.3.0`.

---

Next: [Installation](INSTALL.md) · [Daily usage](USAGE.md) · [Changelog](../CHANGELOG.md)
