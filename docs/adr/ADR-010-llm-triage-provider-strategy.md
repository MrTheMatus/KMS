# ADR-010: Strategia providera dla LLM triage

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

Triage ma generować streszczenia i sugestie względem permanent-notes. Użytkownicy mogą działać w trybie cloud albo local, a API retrieval może czasowo zawodzić.

## Decyzja

- Moduł triage korzysta z adaptera providera i wspiera:
  - `anythingllm` (HTTP API),
  - `heuristic` fallback bez zewnętrznego LLM.
- Brak odpowiedzi z LLM nie zatrzymuje pipeline: wpis trafia do manual review z odpowiednim statusem.
- Człowiek nadal zatwierdza wszystkie mutacje treści.

## Uzasadnienie

- Zapewnia ciągłość działania przy awariach lub braku konfiguracji API.
- Utrzymuje przenośność między środowiskami local/cloud.
- Pozwala wdrażać triage iteracyjnie bez utraty kontroli.

## Konsekwencje

**Plusy:** odporność operacyjna i łatwiejsza adopcja przez różne zespoły.  
**Minusy:** utrzymanie dwóch ścieżek wykonania i potrzeba kalibracji jakości sugestii.
