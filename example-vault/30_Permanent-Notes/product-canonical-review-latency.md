---
id: "canon-2026-0002"
type: canonical-note
domain: product
status: active
confidence: medium
owner: "product-owner"
reviewer: "kms-demo-owner"
last_reviewed_at: "2026-03-23"
sensitivity: internal
---

# Canonical: Review latency policy

## Decision or rule
- New inbox items should receive a first decision within 24 hours.
- If confidence is low, use `postpone` with a short review note.
- Apply is a separate explicit step after review completion.

## When to use
- For daily triage planning and backlog grooming.
- To detect whether the review process is becoming a bottleneck.

## Known trade-offs
- Faster triage increases throughput but can reduce metadata quality.
- More strict SLA improves predictability but requires discipline.

## Related sources
- [[00_Admin/review-queue.md]]
- [[docs/workflow.md]]
