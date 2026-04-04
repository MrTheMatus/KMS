# Remote Gateway

Thin HTTP API for remote proposal review (approve/reject/postpone). Zero external dependencies — uses Python stdlib only.

**Use case:** review proposals from a phone or another machine via VPN/Tailscale, without running Obsidian.

## Quick start

```bash
# 1. Set a token (required)
export KMS_GATEWAY_TOKEN="your-secret-token-here"

# 2. Start the gateway
cd /path/to/KMS && source .venv/bin/activate
PYTHONPATH=. python -m kms.gateway.server --host 127.0.0.1 --port 8780
```

The gateway binds to `127.0.0.1:8780` by default. Use `--host 0.0.0.0` to listen on all interfaces (only behind VPN!).

## API

All endpoints require `Authorization: Bearer <KMS_GATEWAY_TOKEN>`.

### GET /api/pending

Returns pending proposals with metadata.

```bash
curl -H "Authorization: Bearer $KMS_GATEWAY_TOKEN" http://localhost:8780/api/pending
```

```json
[
  {
    "proposal_id": 1,
    "path": "00_Inbox/article.md",
    "action": "move",
    "target": "10_Sources/web/",
    "domain": "programming",
    "topics": ["python", "sqlite"],
    "summary": "Article about SQLite for local-first apps",
    "review_note": null
  }
]
```

### GET /api/status

Returns decision counts and last apply batch.

```bash
curl -H "Authorization: Bearer $KMS_GATEWAY_TOKEN" http://localhost:8780/api/status
```

```json
{
  "counts": {"pending": 5, "approve": 12, "reject": 3},
  "total": 20,
  "last_batch": {
    "id": "a1b2c3d4-...",
    "action": "apply_decisions",
    "proposal_count": 8,
    "created_at": "2026-04-04T10:30:00+00:00"
  }
}
```

### POST /api/decisions

Set decisions for one or more proposals.

```bash
curl -X POST \
  -H "Authorization: Bearer $KMS_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"proposal_id": 1, "decision": "approve"},
    {"proposal_id": 2, "decision": "reject", "review_note": "Duplicate"},
    {"proposal_id": 3, "decision": "postpone"}
  ]' \
  http://localhost:8780/api/decisions
```

```json
{
  "updated": 3,
  "errors": []
}
```

Valid decisions: `approve`, `reject`, `postpone`. Only pending proposals can be changed.

### GET /api/health

```bash
curl -H "Authorization: Bearer $KMS_GATEWAY_TOKEN" http://localhost:8780/api/health
```

```json
{"ok": true, "version": "0.3.1"}
```

## Security

- **Token required**: set `KMS_GATEWAY_TOKEN` env var before starting
- **No HTTPS built-in**: run behind VPN (Tailscale, WireGuard) or reverse proxy (nginx, Caddy)
- **Read-only vault**: the gateway reads/writes only to SQLite — it cannot access vault files
- **No auto-apply**: setting a decision to "approve" does NOT move files — you must run `apply_decisions` separately
- **Audit trail**: every gateway decision logged in `audit_log` with `reviewer=gateway`

## Deployment examples

### Tailscale + systemd

```ini
# /etc/systemd/system/kms-gateway.service
[Unit]
Description=KMS Remote Gateway
After=network.target

[Service]
Type=simple
User=kms
WorkingDirectory=/path/to/KMS
Environment=PYTHONPATH=/path/to/KMS
Environment=KMS_GATEWAY_TOKEN=your-token
ExecStart=/path/to/KMS/.venv/bin/python -m kms.gateway.server --host 100.x.y.z --port 8780
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Docker

```bash
docker run --rm \
  -e KMS_GATEWAY_TOKEN=your-token \
  -v "$(pwd)/kms:/app/kms" \
  -p 8780:8780 \
  kms kms.gateway.server --host 0.0.0.0 --port 8780
```

## Limitations (by design)

- **No file access**: cannot read/serve vault files
- **No AI/LLM**: no retriage, no summaries
- **No AnythingLLM**: no RAG queries
- **No apply**: decisions only — apply runs on the host machine
- **No WebSocket**: poll `/api/status` for updates

These limitations are intentional — see [ADR-005](adr/ADR-005-gateway-deferred.md).
