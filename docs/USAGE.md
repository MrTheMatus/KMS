# Usage Guide

Two scenarios: a **5-minute demo** to show what KMS does, and a **daily operational workflow** for real use.

---

## Demo scenario (5 minutes — hands-on)

Perfect for showing KMS to a colleague or testing after install.

### Prerequisites
- KMS installed ([INSTALL.md](INSTALL.md))
- `example-vault/` open in Obsidian (or CLI only)

### Steps

**1. Seed the inbox (30s)**

Drop 2–3 files into `example-vault/00_Inbox/`:
```bash
# Example: create a test markdown file
cat > example-vault/00_Inbox/test-article.md << 'EOF'
# How to use SQLite for local-first apps

SQLite is the most deployed database engine in the world.
It works great for local-first applications because it needs
no server, supports ACID transactions, and stores everything
in a single file.

Tags: database, sqlite, local-first
EOF
```

**2. Run the pipeline (60s)**
```bash
export PYTHONPATH=.
python -m kms.scripts.scan_inbox          # registers files in DB
python -m kms.scripts.make_review_queue   # creates proposals
python -m kms.scripts.generate_dashboard  # builds stats page
```

**3. Review proposals (60s)**

In Obsidian: `Ctrl+P` → **KMS: Open review queue**

Each proposal shows:
- Source file path
- Suggested action (move to Sources, create source note, etc.)
- Decision buttons: **Approve** / **Reject** / **Postpone**

Click **Approve** on the test article.

Or via CLI: edit `example-vault/00_Admin/review-queue.md`, change `decision: pending` to `decision: approve`.

**4. Apply decisions (60s)**
```bash
python -m kms.scripts.apply_decisions --dry-run   # preview first
python -m kms.scripts.apply_decisions              # execute
```

The file moves from `00_Inbox/` to `10_Sources/`. Check the dashboard: `Ctrl+P` → **KMS: Open dashboard**.

**5. Verify (30s)**
```bash
python -m kms.scripts.verify_integrity --json
# → {"ok": true, ...}
```

**That's it.** Inbox → scan → review → apply → organized knowledge.

---

## Daily operational workflow

### Morning routine (2 minutes)

```bash
cd /path/to/KMS && source .venv/bin/activate && export PYTHONPATH=.

# 1. Refresh: scan any new inbox files + regenerate queue + dashboard
python -m kms.scripts.scan_inbox
python -m kms.scripts.make_review_queue --ai-summary
python -m kms.scripts.generate_dashboard
```

Or in Obsidian: open the **KMS Control Panel** (sidebar) → click **Refresh queue**.

### Review session (5–15 minutes)

Open `review-queue.md` in Obsidian. For each proposal:

| Action | When | What happens on apply |
|--------|------|----------------------|
| **Approve** | File is useful, classification correct | Moves to target folder |
| **Reject** | Not useful or duplicate | Moves to `99_Archive/` |
| **Postpone** | Need more context, decide later | Stays in inbox, skipped |

Tips:
- Use **Bulk approve** / **Bulk reject** (sidebar panel) for batch processing
- Add a `review_note` for future reference
- Click proposal title to see full details (domain, topics, confidence)

### Apply decisions

```bash
python -m kms.scripts.apply_decisions
```

Or in Obsidian: sidebar → **Apply decisions**.

This:
1. Moves approved files to their target folders
2. Archives rejected files to `99_Archive/`
3. Creates a batch ID for the operation (for potential revert)
4. Regenerates the review queue and dashboard

### Weekly maintenance (optional)

```bash
# Integrity check
python -m kms.scripts.verify_integrity

# Status overview
python -m kms.scripts.status

# Daily report
python -m kms.scripts.daily_report
```

### Cron automation

For hands-off scanning (review still requires human):

```bash
# crontab -e
# Scan + queue + dashboard at 6 AM daily
0 6 * * * cd /path/to/KMS && .venv/bin/python -m kms.scripts.scan_inbox && .venv/bin/python -m kms.scripts.make_review_queue && .venv/bin/python -m kms.scripts.generate_dashboard 2>> kms/logs/cron.log
```

---

## Common operations

### Search for a proposal

Obsidian: `Ctrl+P` → **KMS: Search proposals** → type keywords.

### Revert a mistake

Single proposal:
```bash
python -m kms.scripts.revert_apply --proposal-id 42
```

Entire batch:
```bash
python -m kms.scripts.list_batches                    # find the batch UUID
python -m kms.scripts.revert_apply --batch-id <UUID>
```

Or in Obsidian: sidebar → **Revert proposal** / **Revert batch**.

### Re-classify proposals (retriage)

When AI classification seems wrong:
```bash
python -m kms.scripts.make_review_queue --retriage --ai-summary
```

Or in Obsidian: sidebar → **Retriage all** (visible in AI profiles).

### Sync to AnythingLLM

```bash
python -m kms.scripts.sync_to_anythingllm
```

Pushes approved artifacts to your AnythingLLM workspace for RAG queries.

---

## Profile guide

Profiles control which features are visible in the plugin UI:

| Profile | Features | Best for |
|---------|----------|----------|
| **core** | Scan, review, apply, revert, dashboard | No AI / no LLM setup |
| **ai-local** | Core + retriage, AI summaries | Local Ollama models |
| **ai-cloud** | Core + retriage, AI summaries | Cloud API (OpenAI, Groq, etc.) |

Change profile: plugin Settings → Profile, or during the onboarding wizard.

The CLI always has access to all commands regardless of profile — profiles only affect plugin UI visibility.

---

## Vault structure reference

```
example-vault/
├── 00_Admin/
│   ├── review-queue.md    ← generated by make_review_queue
│   ├── dashboard.md       ← generated by generate_dashboard
│   └── reports/           ← daily reports
├── 00_Inbox/              ← DROP FILES HERE
├── 10_Sources/
│   ├── web/               ← approved web articles
│   └── pdf/               ← approved PDFs
├── 20_Source-Notes/        ← AI-generated source notes
├── 30_Permanent-Notes/     ← your canonical knowledge (manual)
└── 99_Archive/             ← rejected/archived files
```

**Rule:** Only `00_Inbox/` and `30_Permanent-Notes/` are for manual edits. Everything else is managed by the pipeline.

---

Next: [Installation](INSTALL.md) · [Upgrade guide](UPGRADE.md) · [CLI reference](cli.md) · [Architecture](architecture.md)
