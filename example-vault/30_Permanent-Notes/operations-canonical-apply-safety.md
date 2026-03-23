---
id: "canon-2026-0004"
type: canonical-note
domain: operations
status: active
confidence: high
owner: "ops-owner"
reviewer: "kms-demo-owner"
last_reviewed_at: "2026-03-23"
sensitivity: internal
---

# Canonical: Apply safety checklist

## Decision or rule
- Always run `apply_decisions --dry-run` before real apply.
- Never auto-apply from cron without explicit human approval.
- Record reviewer and short review note for every approve/reject.

## When to use
- During daily control plane operations.
- During incident handling when queue quality degrades.

## Known trade-offs
- Extra step before mutation, but significantly fewer accidental moves.
- More manual work, but strong auditability.

## Related sources
- [[docs/workflow.md]]
- [[docs/adr/ADR-007-idempotent-apply.md]]
- [[00_Admin/reports/daily-2026-03-23.txt]]
