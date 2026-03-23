# ADR-002: Markdown review queue zamiast web UI

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

Potrzebny jest interfejs do przeglądu i zatwierdzania decyzji przy minimalnym nakładzie i bez budowy frontendu.

## Decyzja

Na MVP review odbywa się przez generowany plik Markdown, np. `vault/00_Admin/review-queue.md` (ścieżka konfigurowalna).

## Uzasadnienie

- Spójność z pracą w Obsidianie
- Brak dodatkowego UI do utrzymania
- Szybkie demo i czytelna narracja „human-in-the-loop”

## Konsekwencje

**Plusy:** mały scope, brak zależności od frameworków webowych.  
**Minusy:** mniej wygodne na mobile; batch operations wymagają dyscypliny edycji lub późniejszego gatewaya.
