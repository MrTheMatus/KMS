# ADR-005: Gateway zdalny dopiero po stabilnym lokalnym workflow

**Status:** Accepted → **Superseded by implementation (Etap 6)**  
**Data:** 2026-03-23  
**Aktualizacja:** 2026-03-24 — Etap 6 zrealizowany; gateway istnieje w `kms/gateway/server.py`.

## Kontekst

Zdalne zatwierdzanie decyzji (np. z telefonu) jest wartościowe, ale nie jest wymagane do pierwszej działającej wersji i niesie koszt auth oraz ekspozycji sieciowej.

## Decyzja

**Gateway** (cienki serwis tylko do decyzji) **nie** wchodzi do MVP. Najpierw lokalny workflow i markdown review; gateway w osobnym etapie, preferencyjnie za VPN/Tailscale.

## Realizacja

Gateway został wdrożony w ramach Etapu 6 roadmapy:

- `GET /api/pending` + `POST /api/decisions` z tokenem Bearer.
- Decyzje zapisywane w SQLite z wpisem `audit_log`.
- Apply nadal na hoście (`apply_decisions`), nie w gateway.
- Uruchamianie za VPN/Tailscale, zgodnie z założeniem.

ADR pozostaje jako zapis **kolejności** (najpierw lokal, potem zdalnie) — ta kolejność została zachowana.

## Uzasadnienie

- Ograniczenie scope i powierzchni ataku
- Szybsze MVP i prostsza architektura

## Konsekwencje

**Plusy:** prostsze demo i mniej komponentów.  
**Minusy:** brak mobilnego review do czasu gatewaya; późniejszy koszt projektowy API i auth.
