# ADR-001: SQLite zamiast Postgresa

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

System potrzebuje lekkiej bazy na: itemy, propozycje, decyzje, artefakty, audyt operacyjny. Nie wymaga na starcie wielu użytkowników, rozproszonych zapytań, osobnego serwera DB ani wysokiej współbieżności zapisu.

## Decyzja

Używamy **SQLite** jako magazynu control plane.

## Uzasadnienie

- Brak dodatkowej infrastruktury i procesów
- Prosty backup i inspekcja pliku `.db`
- Wystarczające dla pojedynczego hosta i local-first
- Niski koszt wejścia dla innych deweloperów

## Konsekwencje

**Plusy:** prostota, łatwy deployment, łatwy debug.  
**Minusy:** ograniczona współbieżność zapisu; ewentualna migracja przy skoku do multi-user lub wielu hostów z równoczesnym zapisem.
