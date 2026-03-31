# KMS — local-first knowledge operations

**Local-first system operacji na wiedzy**: Obsidian vault (treść) + SQLite (decyzje) + skrypty Python + plugin Obsidian. Człowiek w pętli decyzyjnej, AI pomaga — nie decyduje.

## 5 minut do pierwszego review

```bash
git clone <repo-url> && cd kms
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp kms/config/config.example.yaml kms/config/config.yaml
```

Wrzuć pliki do `example-vault/00_Inbox/`, potem:

```bash
export PYTHONPATH=.
python -m kms.scripts.scan_inbox
python -m kms.scripts.make_review_queue
```

Otwórz `example-vault` w Obsidian → `Ctrl+P` → **KMS: Open review queue** → ustaw `decision: approve/reject/postpone` → `Ctrl+P` → **KMS: Apply decisions**.

Lub bez pluginu — edytuj `example-vault/00_Admin/review-queue.md` ręcznie, potem:

```bash
python -m kms.scripts.apply_decisions
```

## Architektura w jednym zdaniu

Obsidian vault = content plane. SQLite = decision plane. Skrypty Python = pipeline. Plugin Obsidian = UI.

Pełna dokumentacja: [docs/architecture.md](docs/architecture.md).

## Plugin Obsidian

Plugin `kms-review` (w `example-vault/.obsidian/plugins/kms-review/`) daje:

- **Sidebar panel** ze statystykami i przyciskami akcji
- **Interaktywne review** w `review-queue.md` (approve/reject/postpone jednym klikiem)
- **Search proposals** z filtrowaniem po domenie/tekście
- **Bulk approve/reject** z potwierdzeniem
- **Progress modal** z krokami pipeline
- **Revert** (pojedynczy lub cały batch)
- **Settings tab** — Python path, projekt, język, AnythingLLM

## Komendy CLI

| Komenda | Opis |
|---------|------|
| `scan_inbox` | Skanuj 00_Inbox, utwórz/aktualizuj rekordy w SQLite |
| `make_review_queue` | Generuj review-queue.md z propozycjami |
| `apply_decisions` | Przenieś zatwierdzone pliki, archiwizuj odrzucone |
| `generate_dashboard` | Dashboard ze statystykami pipeline |
| `daily_report` | Raport dzienny |
| `generate_source_note` | Utwórz source note z szablonu |
| `verify_integrity` | Sprawdź spójność vault ↔ SQLite |
| `status` | Status propozycji (lifecycle, index) |
| `revert_apply` | Cofnij zastosowaną decyzję |
| `sync_to_anythingllm` | Synchronizuj artefakty z AnythingLLM |

Pełna lista z opcjami: [docs/cli.md](docs/cli.md).

## Dokumentacja

| Dokument | Opis |
|----------|------|
| [docs/architecture.md](docs/architecture.md) | Cel, non-goals, komponenty, diagramy, DoD |
| [docs/workflow.md](docs/workflow.md) | Codzienna praca |
| [docs/cli.md](docs/cli.md) | CLI: komendy, config, cron |
| [docs/gateway.md](docs/gateway.md) | Opcjonalny HTTP gateway (za VPN) |
| [docs/continuity.md](docs/continuity.md) | Knowledge continuity |
| [docs/testing-baseline.md](docs/testing-baseline.md) | 2-tygodniowy plan testów |
| [docs/adr/README.md](docs/adr/README.md) | Architecture Decision Records |

## Wymagania

- Python 3.11+
- Obsidian (opcjonalnie z pluginem kms-review)
- (Opcjonalnie) Docker — `docker-compose.yml` do AnythingLLM + Ollama

## Licencja

Dodaj według potrzeb projektu.
