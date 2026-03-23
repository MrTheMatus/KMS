# KMS — local-first knowledge operations + control plane

**Idea:** Obsidian (treść) + AnythingLLM (retrieval) + SQLite (decyzje i stan) + cienkie skrypty Python. AI i narzędzia **nie** są source of truth dla workflow — patrz [docs/architecture.md](docs/architecture.md).

**Git:** repozytorium z gałęzią `main`, pierwszy commit = starter kit pod **user testy** i CI (`.github/workflows`). Plik `kms/config/config.yaml` jest w `.gitignore` — kopiuj z `kms/config/config.example.yaml`.

## Szybki start (ok. 15 min)

1. Sklonuj repozytorium i uruchom setup:

```bash
chmod +x scripts/setup.sh kms/scripts/backup.sh
./scripts/setup.sh
source .venv/bin/activate
export PYTHONPATH=.
```

2. Opcjonalnie: skopiuj `.env.example` do `.env` i ustaw zmienne (ścieżki vault/DB).

3. (Opcjonalnie) AnythingLLM lokalnie — **wymaga uruchomionego Docker Desktop** (lub innego daemona). Szczegóły: [docs/docker-setup.md](docs/docker-setup.md).

```bash
docker compose pull
docker compose up -d
```

4. Cykl control plane (po wrzuceniu plików do `example-vault/00_Inbox/`):

```bash
python -m kms.scripts.scan_inbox
python -m kms.scripts.make_review_queue
# Edytuj example-vault/00_Admin/review-queue.md — ustaw decision: approve | reject | postpone
python -m kms.scripts.apply_decisions --dry-run
python -m kms.scripts.apply_decisions
```

5. Source note + raport:

```bash
python -m kms.scripts.generate_source_note --title "Tytuł źródła" --source-type web --source-url "https://..."
python -m kms.scripts.daily_report --since 7d
./kms/scripts/backup.sh
```

## 15 min onboarding dla PO

1. Otwórz `example-vault` w Obsidian.
2. Dodaj plik do `example-vault/00_Inbox`.
3. Operator uruchamia:

```bash
python -m kms.scripts.scan_inbox
python -m kms.scripts.make_review_queue
```

4. PO edytuje `example-vault/00_Admin/review-queue.md`:
   - `decision`: `approve` / `reject` / `postpone`
   - opcjonalnie `override_target`
   - `review_note`: krótkie uzasadnienie
5. Operator uruchamia:

```bash
python -m kms.scripts.apply_decisions --dry-run -v
python -m kms.scripts.apply_decisions -v
python -m kms.scripts.make_review_queue
```

Po wykonaniu decyzji znikają z aktywnej kolejki (zostają tylko `pending` i `postpone`).

## Profile: local vs cloud

- **Local:** `runtime.profile: local` w `kms/config/config.yaml` + Ollama na hoście; modele opcjonalnie na zewnętrznym dysku (`OLLAMA_MODELS`). Szczegóły: [docs/workflow.md](docs/workflow.md).
- **Cloud:** ten sam vault i control plane; w AnythingLLM wybierasz providera API zamiast lokalnej Ollamy — **bez zmiany** skryptów KMS.

## Shippable solution v1 (dla devów)

Docelowy format dystrybucji to **starter kit**, nie gotowy produkt SaaS:
- markdown vault jako content plane,
- SQLite + skrypty Python jako decision plane,
- profile uruchomienia: `cloud-default` i `local-optional`,
- jawny flow: `scan -> review -> apply -> report`.

Minimalny onboarding (15 min):
1. `./scripts/setup.sh`
2. ustaw `kms/config/config.yaml` (lub użyj `config.example.yaml`)
3. wrzuć 1-2 pliki do `00_Inbox/`
4. uruchom `scan_inbox`, `make_review_queue`, `apply_decisions --dry-run`
5. dopiero potem `apply_decisions`

Bezpieczeństwo w v1:
- gateway zdalny (`kms/gateway/server.py`) jest dostępny, ale opcjonalny — **tylko** za VPN/Tailscale,
- mutacje plików robi tylko host wykonawczy (`apply_decisions`), gateway zapisuje wyłącznie decyzje,
- token auth wymagany; szczegóły: [docs/gateway.md](docs/gateway.md).

## Dokumentacja

| Dokument | Opis |
|----------|------|
| [docs/cli.md](docs/cli.md) | **CLI**: wszystkie komendy, `status`, `revert_apply`, `inbox_merge_advisor`, config, AnythingLLM/sync, cron, review |
| [docs/kms-principles.md](docs/kms-principles.md) | **Zasady rozwoju** — human-in-the-loop, idempotencja, kolejność feature’ów |
| [docs/anythingllm-workspace.md](docs/anythingllm-workspace.md) | Prompt systemowy, temperatura, historia czatu, linki Obsidian (wklejka do UI) |
| [docs/architecture.md](docs/architecture.md) | Cel, non-goals, komponenty, diagramy, DoD |
| [docs/adr/README.md](docs/adr/README.md) | ADR (indeks) |
| [docs/workflow.md](docs/workflow.md) | Codzienna praca + AnythingLLM/Ollama |
| [docs/conference-demo.md](docs/conference-demo.md) | Scenariusz demo (~40 min) |
| [docs/gateway.md](docs/gateway.md) | Lekki gateway (Tailscale/VPN) |
| [docs/continuity.md](docs/continuity.md) | Fundament pod knowledge continuity |
| [docs/testing-baseline.md](docs/testing-baseline.md) | Baseline metryk i checklista testow 2 tygodnie |

## Struktura

- `example-vault/` — przykładowa struktura Obsidiana
- `kms/app/` — SQLite, config, parser `review-queue.md`
- `kms/scripts/` — CLI (`scan_inbox`, `make_review_queue`, `apply_decisions`, `verify_integrity`, `inbox_merge_advisor`, …)
- `scripts/generate_cpp_corpus.py` — generuje korpus testowy C++ w `30_Permanent-Notes/cpp-corpus/`
- `kms/gateway/` — opcjonalny HTTP tylko do decyzji (Etap 6)
- `tests/` — pytest (gateway, revert, config, db, pipeline smoke, parser, lifecycle, hashing, PDF, triage)
- `.github/workflows/ci.yml` — CI: testy + lint (ruff)
- `Dockerfile` — obraz KMS (skrypty CLI)

## Wymagania

- Python 3.11+
- Zależności: `requirements.txt` (PyYAML, Jinja2, Flask dla gatewaya)
- (Opcjonalnie) Docker — `Dockerfile` do budowy obrazu, `docker-compose.yml` do AnythingLLM

## Licencja

Dodaj według potrzeb projektu.
