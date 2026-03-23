# Lekki gateway decyzyjny (Etap 6)

## Cel

Umożliwić **zatwierdzanie / odrzucanie / odłożenie** propozycji z cienkiego klienta (iPhone, lekki MacBook) **bez** wystawiania całego AnythingLLM ani całego vaultu do internetu.

## Zakres MVP

- `GET /api/pending` — lista propozycji ze statusem `pending`.
- `POST /api/decisions` — body JSON: `proposal_id`, `decision` (`approve` \| `reject` \| `postpone` \| `pending`), opcjonalnie `reviewer`, `override_target`.

**Poza zakresem:** OCR, Ollama, edycja plików, zarządzanie workspace’ami AnythingLLM.

## Uruchomienie

Wymaga **silnego** tokenu (inaczej proces się nie uruchomi):

```bash
export PYTHONPATH=.
export KMS_GATEWAY_TOKEN="$(openssl rand -hex 32)"
# opcjonalnie: export KMS_CONFIG_PATH=/abs/path/to/kms/config/config.yaml
python -m kms.gateway.server
```

Domyślnie nasłuch: `127.0.0.1:8765`. Zdalnie: **Tailscale / VPN**, ewentualnie `KMS_GATEWAY_HOST=100.x.y.z` na interfejsie VPN — **nie** wystawiaj portu na publiczny Internet bez reverse proxy i twardego hardeningu.

## Autoryzacja

Nagłówek: `Authorization: Bearer <token>` lub query `?token=` (wyłącznie w sieci zaufanej).

## Powiązanie z apply

Gateway zapisuje wiersze w tabeli `decisions`. **Mutacje plików** nadal wykonuj na hoście:

```bash
python -m kms.scripts.apply_decisions
```

Opcjonalny cron na Mac mini: co godzinę `apply_decisions` po tym, jak zdalnie zatwierdzisz propozycje.

## Bezpieczeństwo

- Jednoużytkowy token, rotacja, brak logowania hasła w repozytorium.
- Gateway nie zastępuje pełnego IAM — to świadomie mały komponent.
