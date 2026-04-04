# Installation Guide

Two paths: **single-machine** (recommended) or **Docker** (cloud-friendly).

## System requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.11 | 3.12+ |
| OS | macOS, Linux, WSL2 | macOS / Ubuntu 22+ |
| RAM | 2 GB free | 8 GB (16 GB if running Ollama locally) |
| Disk | 500 MB + vault size | SSD recommended |
| Obsidian | 1.0+ (optional) | Latest desktop |
| Node.js | 18+ (only if rebuilding plugin) | 20+ |

---

## Path A — Single-machine quickstart (5 minutes)

### 1. Clone and set up Python

```bash
git clone https://github.com/MrTheMatus/KMS.git && cd KMS
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Or use the automated setup script:

```bash
bash scripts/setup.sh
source .venv/bin/activate
```

### 2. Create config

```bash
cp kms/config/config.example.yaml kms/config/config.yaml
```

The defaults work with `example-vault/` out of the box. Edit `config.yaml` only if:
- Your vault is somewhere else → change `vault.root`
- You want cloud LLM → change `llm.base_url` and `llm.model` (see config comments)
- You want AnythingLLM → set `anythingllm.enabled: true` + API key

### 3. Run first pipeline

```bash
# Drop some files into example-vault/00_Inbox/ first
export PYTHONPATH=.
python -m kms.scripts.scan_inbox
python -m kms.scripts.make_review_queue
python -m kms.scripts.generate_dashboard
```

### 4. Review proposals

**With Obsidian plugin (recommended):**
1. Open `example-vault/` as a vault in Obsidian
2. Go to Settings → Community plugins → Enable `KMS Review Queue`
3. The onboarding wizard opens automatically on first run
4. Use the sidebar panel or `Ctrl+P` → KMS commands

**Without plugin (CLI only):**
1. Open `example-vault/00_Admin/review-queue.md` in any editor
2. Change `decision: pending` to `approve`, `reject`, or `postpone`
3. Run: `python -m kms.scripts.apply_decisions`

### 5. Verify setup

```bash
python -m kms.scripts.verify_integrity --json
```

Expected output: `{"ok": true, ...}` — vault and database are in sync.

---

## Path B — Docker / cloud-friendly quickstart

Best for: CI pipelines, headless servers, cloud VMs.

### 1. Clone and configure

```bash
git clone https://github.com/MrTheMatus/KMS.git && cd KMS
cp kms/config/config.example.yaml kms/config/config.yaml
cp .env.example .env
```

Edit `.env` for your environment:
```bash
KMS_VAULT_ROOT=/path/to/your/vault
# If using cloud LLM:
OPENAI_API_KEY=sk-...
# If using AnythingLLM:
ANYTHINGLLM_API_KEY=...
```

### 2. Build and run

```bash
# Build the KMS image
docker build -t kms .

# Run pipeline commands
docker run --rm \
  -v "$(pwd)/example-vault:/app/example-vault" \
  -v "$(pwd)/kms/config:/app/kms/config" \
  -v "$(pwd)/kms/data:/app/kms/data" \
  kms kms.scripts.scan_inbox

docker run --rm \
  -v "$(pwd)/example-vault:/app/example-vault" \
  -v "$(pwd)/kms/config:/app/kms/config" \
  -v "$(pwd)/kms/data:/app/kms/data" \
  kms kms.scripts.make_review_queue
```

### 3. Optional: AnythingLLM companion

```bash
docker compose up -d   # starts AnythingLLM on :3001
```

See [docs/docker-setup.md](docker-setup.md) for full AnythingLLM configuration.

### 4. Cron automation (headless)

```bash
# Safe daily pipeline (scan + review queue + dashboard, no auto-apply)
0 6 * * * cd /path/to/KMS && .venv/bin/python -m kms.scripts.scan_inbox && .venv/bin/python -m kms.scripts.make_review_queue && .venv/bin/python -m kms.scripts.generate_dashboard

# Weekly integrity check
0 0 * * 0 cd /path/to/KMS && .venv/bin/python -m kms.scripts.verify_integrity --json >> /var/log/kms-integrity.log
```

> **Never auto-apply.** Human-in-the-loop is a core design principle (see [ADR-006](adr/006-human-in-the-loop.md)).

---

## Installing the Obsidian plugin

The plugin is pre-built in the repository. No build step needed for normal use.

### Option A — Use the example vault directly

Just open `example-vault/` in Obsidian. The plugin is already installed.

### Option B — Copy to your own vault

```bash
# From the KMS repo root:
cp -r example-vault/.obsidian/plugins/kms-review \
      /path/to/your/vault/.obsidian/plugins/kms-review
```

Required files: `main.js`, `manifest.json`, `styles.css`

Then in Obsidian: Settings → Community plugins → Enable `KMS Review Queue`.

### Option C — Build from source

Only needed if you're modifying the plugin code:

```bash
cd example-vault/.obsidian/plugins/kms-review
npm install
npm run build    # one-time build
npm run dev      # watch mode for development
```

---

## Post-install self-check

Run this after any install or upgrade to verify everything works:

```bash
export PYTHONPATH=.
source .venv/bin/activate

# 1. Python deps OK?
python -c "import yaml, jinja2, pypdf; print('deps: OK')"

# 2. Config valid?
python -m kms.scripts.verify_integrity --json

# 3. Plugin files present?
ls example-vault/.obsidian/plugins/kms-review/{main.js,manifest.json,styles.css}
```

All three should succeed. If `verify_integrity` reports issues on a fresh install, that's normal — there's no data yet.

---

## Troubleshooting

### Python not found / wrong version
```bash
python3 --version   # needs 3.11+
# On macOS: brew install python@3.12
# On Ubuntu: sudo apt install python3.12 python3.12-venv
```

### `ModuleNotFoundError: No module named 'kms'`
You forgot `export PYTHONPATH=.` — run it from the repo root.

### Plugin shows "Python not found" in wizard
Set the Python path in plugin settings: Settings → KMS Review Queue → Python path.
For venv: `/path/to/KMS/.venv/bin/python`

### Config errors
```bash
# Validate your config manually:
python -c "from kms.app.config import load_config; print(load_config())"
```

### Ollama not responding
```bash
curl http://localhost:11434/api/tags   # should list models
# If empty: ollama pull qwen2.5:14b
```

### AnythingLLM connection failed
```bash
curl -H "Authorization: Bearer $ANYTHINGLLM_API_KEY" http://localhost:3001/api/v1/auth
```

---

Next: [Upgrade guide](UPGRADE.md) · [Daily usage](USAGE.md) · [CLI reference](cli.md)
