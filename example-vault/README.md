# Example vault (KMS)

Szkielet katalogów zgodny z dokumentacją (`00_Inbox`, `10_Sources/web|pdf`, `20_Source-Notes`, …).  
**Treści bazy wiedzy i generaty (inbox, kolejka, raporty, PDF, notatki)** są wykluczone przez **`example-vault/.gitignore`** — zostają tylko u Ciebie lokalnie.

## Co jest wersjonowane w Git

| Element | Opis |
|---------|------|
| `.obsidian/plugins/kms-review/` | Plugin Obsidian (interaktywny review) |
| `.obsidian/*.json` (oprócz `workspace*.json`) | Konfiguracja vaultu / pluginów |
| `**/.gitkeep` w folderach pipeline | Puste gałęzie katalogów |
| `README.md`, `docs/` | Opis szkieletu |

## Jak zbudować treści lokalnie

- **Seed / demo:** `python scripts/generate_knowledge_seed.py`, potem `scan_inbox` → `make_review_queue` → `apply` (szczegóły: [docs/workflow.md](../docs/workflow.md)).
- **Konwersacje z PDF:** `python scripts/ingest_conversations.py` (katalog `conversations/` w root repozytorium jest w głównym `.gitignore`).
- **Czysty start DB:** usuń `kms/data/state.db` (jest w `.gitignore` w root).

## Raporty (lokalnie)

Pliki `00_Admin/reports/daily-*.txt` i wygenerowane `review-queue.md` / `dashboard.md` nie trafiają do Git — generuje je pipeline KMS.
