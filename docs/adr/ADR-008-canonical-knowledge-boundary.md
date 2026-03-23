# ADR-008: Permanent-notes jako kanon wiedzy

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

W projekcie istnieją różne warstwy informacji: surowe dokumenty, source notes, odpowiedzi narzędzi retrieval oraz notatki trwałe. Bez wyraźnego podziału łatwo o konflikt „co jest obowiązującą wiedzą”.

## Decyzja

- `30_Permanent-Notes` są kanoniczną warstwą wiedzy treściowej.
- `source notes` i surowe źródła pozostają warstwą dowodową/roboczą.
- SQLite pozostaje source of truth dla workflow, decyzji i audytu.
- AnythingLLM nie jest source of truth; służy do retrieval i zapytań.

## Uzasadnienie

- Jednoznacznie definiuje, gdzie utrwalamy wiedzę referencyjną.
- Ułatwia triage nowych źródeł i decyzje o aktualizacji kanonu.
- Upraszcza onboarding osób nietechnicznych (jedna warstwa „oficjalna”).

## Konsekwencje

**Plusy:** mniej konfliktów semantycznych, prostsze review, klarowny ownership treści.  
**Minusy:** potrzeba procesu aktualizacji permanent-notes i regularnej walidacji ich jakości.
