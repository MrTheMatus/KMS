# Docker (AnythingLLM)

Obraz jest zdefiniowany w [`docker-compose.yml`](../docker-compose.yml) w katalogu głównym repozytorium.

## Wymagania

- Zainstalowany **Docker Desktop** (macOS) lub równoważny daemon.
- Daemon musi być **uruchomiony** przed `docker compose pull` / `up`.

## Typowe komendy

```bash
cd /path/to/KMS
docker compose pull
docker compose up -d
```

Następnie otwórz interfejs AnythingLLM (domyślnie port **3001** — sprawdź `docker-compose.yml`) i skonfiguruj źródło dokumentów / Ollamę według [workflow.md](workflow.md).

Sync z linii poleceń (API key, `sync_to_anythingllm`, cron): [cli.md](cli.md).

## Gdy `Cannot connect to the Docker daemon`

Uruchom Docker Desktop i poczekaj, aż status będzie „running”, potem powtórz `docker compose pull`.

## Gdy `pull access denied` / „repository does not exist”

Na Docker Hub obraz nazywa się **`mintplexlabs/anythingllm`** (bez myślnika między `anything` a `llm`). Starsze wpisy z `mintplexlabs/anything-llm` są błędne.
