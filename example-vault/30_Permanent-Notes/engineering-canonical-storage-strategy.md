---
id: "canon-2026-0001"
type: canonical-note
domain: engineering
status: active
confidence: high
owner: "architecture-team"
reviewer: "kms-demo-owner"
last_reviewed_at: "2026-03-23"
sensitivity: internal
---

# Canonical: Storage strategy for KMS content

## Decision or rule
- Keep content as markdown in vault folders.
- Keep workflow state in SQLite only.
- Treat retrieval indexes as replaceable tool caches, not source of truth.

## When to use
- When deciding where a new field or status should be stored.
- During debugging of inconsistent state between tools.

## Known trade-offs
- Strong traceability and recovery, but more explicit synchronization logic.
- Slightly more manual review than autonomous AI pipelines.

## Related sources
- [[docs/architecture.md]]
- [[docs/adr/ADR-001-sqlite-vs-postgres.md]]
- [[docs/adr/ADR-008-canonical-knowledge-boundary.md]]
