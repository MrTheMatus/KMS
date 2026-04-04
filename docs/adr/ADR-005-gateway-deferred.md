# ADR-005: Gateway zdalny — cienki serwis do decyzji

**Status:** Accepted → Superseded → **Re-implemented (v0.3.1, thin gateway)**
**Data:** 2026-03-23
**Aktualizacja:** 2026-04-04 — v0.3.1: thin gateway (stdlib only, zero deps)

## Kontekst

Zdalne zatwierdzanie decyzji (np. z telefonu przez VPN) jest wartościowe, ale nie jest wymagane do pierwszej działającej wersji. Poprzednia implementacja (Flask-based, v0.2.0) została usunięta w v0.3.0 jako overengineering.

## Decyzja

**Thin gateway** wchodzi jako osobny, opcjonalny komponent:
- Zero zewnętrznych zależności (Python stdlib `http.server`)
- Tylko 3 endpointy: `GET /api/pending`, `POST /api/decisions`, `GET /api/status`
- Bearer token z `KMS_GATEWAY_TOKEN` env var
- **Nie** ma dostępu do vaulta, modeli, AnythingLLM
- **Nie** wykonuje apply — tylko ustawia decyzje w SQLite
- Przeznaczony do uruchamiania za VPN/Tailscale

## Realizacja

`kms/gateway/server.py` — stdlib HTTPServer, ~200 LOC:
- `GET /api/pending` — lista propozycji pending z metadanymi
- `GET /api/status` — liczniki decyzji + ostatni batch
- `POST /api/decisions` — ustaw decision na approve/reject/postpone
- `GET /api/health` — liveness check

Uruchomienie: `python -m kms.gateway.server --host 0.0.0.0 --port 8780`

## Uzasadnienie

- Ograniczony scope: read pending + write decisions, nic więcej
- Zero nowych zależności (no Flask, no FastAPI)
- Apply nadal wymaga jawnego uruchomienia na hoście
- Audyt: każda decyzja logowana z `reviewer=gateway`

## Konsekwencje

**Plusy:** mobilne review przez VPN, audytowalność, zero nowych deps
**Minusy:** brak HTTPS (TLS na poziomie VPN/reverse proxy), brak WebSocket push
