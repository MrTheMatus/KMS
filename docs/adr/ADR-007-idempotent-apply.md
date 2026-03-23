# ADR-007: Idempotentny apply jako twardy wymóg

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

Skrypty będą uruchamiane wielokrotnie (cron, retry po błędach); częściowe wykonanie musi być bezpieczne do ponowienia.

## Decyzja

`apply_decisions` musi być **idempotentny**: ponowne uruchomienie nie powiela przeniesień, nie tworzy duplikatów source notes ani nie psuje statusów dla już zakończonych operacji.

## Uzasadnienie

- Bezpieczny retry
- Przewidywalność operacyjna
- Zgodność z dobrymi praktykami pipeline’ów

## Konsekwencje

**Plusy:** łatwiejsze recovery.  
**Minusy:** konieczność jawnego śledzenia artefaktów i stanu w SQLite.
