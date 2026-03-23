---
id: "canon-2026-0003"
type: canonical-note
domain: security
status: active
confidence: high
owner: "security-champion"
reviewer: "kms-demo-owner"
last_reviewed_at: "2026-03-23"
sensitivity: internal
---

# Canonical: Remote access boundary for KMS

## Decision or rule
- Expose only a thin decision gateway for remote users.
- Keep model runtimes and file mutation operations on the host.
- Use VPN/private tunnel and token auth for gateway access.

## When to use
- When planning mobile or travel workflows.
- Before exposing any endpoint outside local host.

## Known trade-offs
- Better security and smaller blast radius, but less convenience.
- Additional auth and network setup for remote usage.

## Related sources
- [[docs/gateway.md]]
- [[docs/adr/ADR-005-gateway-deferred.md]]
- [[docs/architecture.md]]
