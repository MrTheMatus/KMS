# Future readiness: knowledge continuity

Ten dokument opisuje **fundament** pod późniejsze przechwytywanie wiedzy ekspertów (np. przed emeryturą), **bez** wdrażania teraz ciężkiego „enterprise KMS”.

## Zasady

1. **Ten sam control plane** — nowe typy spraw to nowe `kind` / propozycje w SQLite, nie nowy silnik.
2. **Capture-first, structure-later** — dopuszczalne są surowe wejścia (notatka, transkrypcja), potem draft + review.
3. **Rozszerzalne typy notatek** — `type` w frontmatterze; obecnie `source-note`, w przyszłości m.in. `decision-note`, `risk-note`, `expert-interview`.

## Metadane (rezerwa w szablonach)

Pola opcjonalne już w `source_note.md.j2`: `owner`, `reviewer`, `domain`, `last_reviewed_at`, `sensitivity`. Możesz je stopniowo wypełniać.

## Szablony (Etap 8)

- [`kms/templates/decision_note.md.j2`](../kms/templates/decision_note.md.j2) — krótka notatka decyzyjna (problem, opcje, decyzja, trade-offy).
- [`kms/templates/risk_note.md.j2`](../kms/templates/risk_note.md.j2) — znane ryzyka / „nie ruszaj bez testu X”.

## Co świadomie odkładamy

- Pełna ontologia organizacji, knowledge graph, automatyczny merge wiedzy.
- Ciężkie workflow HR/onboarding w jednym repozytorium.

Gdy nadejdzie etap continuity: rozszerz `make_review_queue` o nowe sekcje (np. „transkrypcje do review”) zamiast budować osobny produkt.

**Stan obecny:** `inbox_merge_advisor` — opcjonalna warstwa (heurystyka + prompt; opcjonalnie chat AnythingLLM); granice: [kms-principles.md](kms-principles.md) §9. Korpus C++: `cpp-corpus/` + `scripts/generate_cpp_corpus.py`.
