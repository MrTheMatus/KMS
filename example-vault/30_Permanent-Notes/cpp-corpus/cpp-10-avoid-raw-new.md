---
id: cpp-10-avoid-raw-new
type: permanent-note
domain: engineering
language: pl
title: C++: unikaj surowego new
topics: [cpp, memory, safety]
status: active
confidence: 0.9
---
# Unikaj surowego new/delete

**Avoid** `new`/`delete` w aplikacyjnym kodzie — stosuj factory (`make_unique`) i kontenery.

Wyjątki: niskopoziomowe API, interoperacyjność z C.
