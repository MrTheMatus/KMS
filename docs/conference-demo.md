# Scenariusz demo (ok. 40 min)

**Teza:** Nie buduję własnego RAG-a — buduję **local-first operacje na wiedzy** z **human-in-the-loop** i rozdziałem content plane / decision plane.

## Przygotowanie (przed publicznością)

- Działający `example-vault` z 10–20 plikami (web markdown + 1–2 PDF).
- AnythingLLM z workspace zawierającym wybrane dokumenty z vaultu.
- Ollama lub model chmurowy — jedna ścieżka, żeby nie tracić czasu.
- Wyczyszczony lub znany stan `kms/data/state.db` (opcjonalnie kopia zapasowa).

## Akt 1 — „Mam korpus i rozumiem źródła” (10 min)

1. Pokaż strukturę vaultu (`00_Inbox`, `10_Sources`, `20_Source-Notes`, `30_Permanent-Notes`).
2. Pokaż **source note** z frontmatterem (id, `file_link`, status).
3. Pokaż jedną **canonical note** (np. `30_Permanent-Notes/engineering-canonical-storage-strategy.md`) i wyjaśnij, że to warstwa referencyjna.
4. W AnythingLLM zadaj 2–3 **pytania testowe** z listy poniżej; pokaż cytowania / fragmenty.

### Przykładowe pytania testowe (dostosuj do swoich danych)

- „Jaką mamy kanoniczną zasadę dla granicy source of truth i gdzie jest opisana?”
- „Który dokument opisuje warunki gwarancji i jaka canonical note mówi, jak bezpiecznie robić apply?”
- „Gdzie mam porównanie kosztów PV i jaka jest reguła obsługi sprzecznych źródeł?”
- „Jaka jest polityka zdalnego dostępu i dlaczego gateway jest oddzielony od mutacji plików?”

## Akt 2 — „Control plane: propozycja ≠ wykonanie” (15 min)

1. Wrzuć nowy plik do `00_Inbox/`.
2. `scan_inbox` → `make_review_queue`.
3. Otwórz `00_Admin/review-queue.md`: pokaż blok YAML (`proposal_id`, `decision: pending`).
4. Zmień na `approve` / `reject` — wyjaśnij audyt i brak autonomicznych mutacji.
5. `apply_decisions --dry-run`, potem `apply_decisions` — pokaż przeniesienie do `10_Sources/...`.

## Akt 3 — „Granice systemu” (10 min)

1. Slajd lub `docs/architecture.md`: **source of truth** (vault vs SQLite vs nie-SoT dla AnythingLLM).
2. **Out of scope:** własny vector DB, agent bez review, publiczny stack.
3. Krótko: ADR-003 (AnythingLLM zamiast RAG), ADR-006 (human-in-the-loop), ADR-008 (permanent-notes jako kanon).

## Q&A (5 min)

- Jak to przenieść na laptop bez Ollamy? → profil cloud.
- Co z telefonem? → gateway za VPN (Etap 6), tylko decyzje.

## Definition of Done demo

- Zero improwizacji na ścieżce „inbox → review → apply”.
- Jedno zdanie tezy na początku i powtórzenie na końcu.
- Widzowie rozumieją różnicę: `10_Sources/20_Source-Notes` (warstwa dowodowa) vs `30_Permanent-Notes` (warstwa kanoniczna).
