# ADR-006: Human-in-the-loop zamiast autonomicznego agenta

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

Automatyczne mutacje wiedzy w vaultcie są trudne do audytu i podatne na błędy modeli.

## Decyzja

System może **proponować** działania (propozycje w SQLite + review queue); **mutacje** wykonuje wyłącznie jawny krok `apply` po zatwierdzeniu przez człowieka.

## Uzasadnienie

- Mniejszy blast radius błędów
- Lepsza zgodność z celem „control plane”
- Silniejsza narracja inżynierska (audyt, odtwarzalność)

## Konsekwencje

**Plusy:** zaufanie i przewidywalność.  
**Minusy:** więcej pracy ręcznej w review.
