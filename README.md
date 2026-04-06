# KMS — local-first knowledge operations

**Local-first knowledge management**: Obsidian vault (content) + SQLite (decisions) + Python scripts (pipeline) + Obsidian plugin (UI). Human-in-the-loop — AI proposes, you decide.

## How it works

```
00_Inbox/  →  scan_inbox  →  make_review_queue  →  YOU decide  →  apply_decisions  →  10_Sources/
                                                  (approve/reject)                      99_Archive/
```

1. Drop files into `00_Inbox/`
2. Pipeline scans, classifies, and creates proposals
3. You review in Obsidian (or edit review-queue.md manually)
4. Apply moves approved files to target folders, rejected to archive

## Quick start (5 minutes)

```bash
git clone https://github.com/MrTheMatus/KMS.git && cd KMS
bash scripts/setup.sh          # creates venv, installs deps, copies config
source .venv/bin/activate
export PYTHONPATH=.

# Drop some files into example-vault/00_Inbox/, then:
python -m kms.scripts.scan_inbox
python -m kms.scripts.make_review_queue
python -m kms.scripts.generate_dashboard
```

Open `example-vault/` in Obsidian → the plugin's onboarding wizard guides you through the rest.

Without Obsidian: edit `example-vault/00_Admin/review-queue.md` manually → `python -m kms.scripts.apply_decisions`.

**Full installation guide:** [docs/INSTALL.md](docs/INSTALL.md) (single-machine + Docker paths)

## Obsidian plugin (v0.3.1)

Pre-installed in `example-vault/.obsidian/plugins/kms-review/`. Features:

- **6-step onboarding wizard** with profile selection (core / AI-local / AI-cloud) and help
- **Sidebar control panel** — pipeline actions, stats, domain breakdown, settings, help
- **Interactive review** — approve/reject/postpone with one click, next-step guidance
- **Ask knowledge base** — hybrid search: AnythingLLM RAG + vault keyword search with context injection
- **Contradiction detection** — LLM flags when new notes contradict existing knowledge
- **Search & detail modals** — find proposals by keyword, view full metadata
- **Bulk operations** — approve/reject all pending at once
- **Batch revert** — undo entire operations with one click
- **Error modals** — copyable error details with action buttons (replaces transient toasts)
- **i18n** — full Polish and English interface
- **Dark mode** — uses Obsidian theme variables

To install in another vault: copy `main.js`, `manifest.json`, `styles.css` to your vault's `.obsidian/plugins/kms-review/`.

## CLI commands

| Command | Description |
|---------|-------------|
| `scan_inbox` | Scan 00_Inbox, register files in SQLite |
| `make_review_queue` | Generate review-queue.md with proposals |
| `apply_decisions` | Move approved files, archive rejected |
| `generate_dashboard` | Build stats dashboard |
| `verify_integrity` | Check vault ↔ SQLite consistency |
| `revert_apply` | Undo applied decisions (single or batch) |
| `list_batches` | List active operation batches |
| `search_proposals` | Search proposals by text |
| `status` | Show proposal lifecycle status |
| `daily_report` | Generate daily summary |
| `sync_to_anythingllm` | Push artifacts to AnythingLLM for RAG |
| `resync_embeddings` | Full vault re-embed after model/chunking change |

Full reference with all flags: [docs/cli.md](docs/cli.md)

## Remote gateway (optional)

Thin HTTP API for reviewing proposals from a phone or another machine:

```bash
export KMS_GATEWAY_TOKEN="your-secret-token"
PYTHONPATH=. python -m kms.gateway.server --port 8780
```

3 endpoints: `GET /api/pending`, `POST /api/decisions`, `GET /api/status`. Decisions only — no vault access, no auto-apply. Run behind VPN/Tailscale.

Full docs: [docs/gateway.md](docs/gateway.md)

## Architecture

```
Obsidian vault = content plane (source of truth for files)
SQLite         = decision plane (source of truth for proposals)
Python scripts = pipeline (stateless transforms)
Plugin         = UI (read-only view + decision input)
```

Key principles:
- **Human-in-the-loop**: AI never auto-executes — every mutation requires explicit approval
- **Idempotent**: safe to re-run any script; no double-moves, no data loss
- **Auditable**: every operation logged in `audit_log` table with timestamps
- **Reversible**: any applied decision can be reverted

Full architecture: [docs/architecture.md](docs/architecture.md) · ADRs: [docs/adr/](docs/adr/README.md)

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALL.md](docs/INSTALL.md) | Installation — single-machine + Docker quickstarts |
| [docs/USAGE.md](docs/USAGE.md) | Demo scenario + daily operational workflow |
| [docs/UPGRADE.md](docs/UPGRADE.md) | Version upgrade guide with migration steps |
| [docs/workflow.md](docs/workflow.md) | Detailed pipeline workflow |
| [docs/cli.md](docs/cli.md) | CLI command reference |
| [docs/gateway.md](docs/gateway.md) | Remote gateway API (decisions via HTTP) |
| [docs/architecture.md](docs/architecture.md) | System design, components, failure model |
| [docs/adr/README.md](docs/adr/README.md) | Architecture Decision Records (10 ADRs) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Developer setup, testing, plugin development |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Requirements

- Python 3.11+
- Obsidian 1.0+ (optional — CLI works standalone)
- (Optional) Docker — for AnythingLLM + Ollama
- (Optional) Node.js 18+ — only if rebuilding plugin from source

## License

MIT — see [LICENSE](LICENSE).
