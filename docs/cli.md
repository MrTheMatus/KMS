# KMS — przewodnik CLI i konfiguracji

Jedno miejsce na **komendy**, **pliki konfiguracyjne**, **AnythingLLM / indeksowanie**, **cron** i **review**.  
Kolejność rozwoju narzędzia (zgodnie z roadmapą): **CLI → plugin Obsidian**.

## Wymagania wstępne

```bash
cd /path/to/KMS
source .venv/bin/activate   # lub: używaj .venv/bin/python bez activate
export PYTHONPATH=.
```

- Konfiguracja: skopiuj [`kms/config/config.example.yaml`](../kms/config/config.example.yaml) do `kms/config/config.yaml` i dostosuj ścieżki.
- Nadpisania środowiskowe (opcjonalnie):
  - `KMS_VAULT_ROOT` — katalog vaultu (nadpisuje `vault.root` w YAML),
  - `KMS_DATABASE_PATH` — ścieżka do `state.db`.

Wszystkie moduły `kms.scripts.*` akceptują:

| Flaga | Znaczenie |
|-------|-----------|
| `--config PATH` | Ścieżka do `config.yaml` (domyślnie `kms/config/config.yaml` lub `config.example.yaml`) |
| `-v` / `--verbose` | Logi na poziomie DEBUG (tam gdzie zaimplementowane) |
| `--dry-run` | Tam gdzie wspierane: bez mutacji vaultu / bez zapisów „ostatecznych” |

Przykład:

```bash
.venv/bin/python -m kms.scripts.scan_inbox --config kms/config/config.yaml -v
```

---

## Indeksowanie (AnythingLLM)

KMS **nie** utrzymuje własnej bazy wektorowej. **Indeksowanie = workspace AnythingLLM** (chunking + embedding).

### 1. Uruchom AnythingLLM

Zobacz [docker-setup.md](docker-setup.md). Domyślnie UI często jest na porcie **3001** (sprawdź `docker-compose.yml`).

### 2. Włącz sekcję w `kms/config/config.yaml`

```yaml
anythingllm:
  enabled: true
  base_url: "http://localhost:3001"
  workspace_slug: "my-workspace"   # slug workspace z UI AnythingLLM
  api_key_env: "ANYTHINGLLM_API_KEY"
```

### 3. Ustaw klucz API

W AnythingLLM wygeneruj **API key** (ustawienia aplikacji) i w shellu:

```bash
export ANYTHINGLLM_API_KEY="twój-klucz"
```

Nazwa zmiennej musi zgadzać się z `api_key_env` w YAML.

### 4. Kiedy wołać sync z KMS

Skrypt **`sync_to_anythingllm`** działa tylko na rekordach, które przeszły **`apply_decisions`** (tabela `artifacts`, plik jeszcze bez `workspace_name` w sensie „nie zsynchronizowany” według logiki skryptu).

Typowy łańcuch:

```bash
.venv/bin/python -m kms.scripts.scan_inbox
.venv/bin/python -m kms.scripts.make_review_queue
# edycja 00_Admin/review-queue.md: decision: approve | reject | postpone
.venv/bin/python -m kms.scripts.apply_decisions --dry-run
.venv/bin/python -m kms.scripts.apply_decisions
.venv/bin/python -m kms.scripts.sync_to_anythingllm --dry-run
.venv/bin/python -m kms.scripts.sync_to_anythingllm
```

Jeśli widzisz `anythingllm.enabled=false, skipping sync` — w YAML jest `enabled: false` albo używasz innego pliku `--config`.

### Uwaga (API upload)

Endpoint `/api/v1/document/upload` w AnythingLLM oczekuje **`multipart/form-data` z polem `file`** (treść pliku). KMS wysyła bajty pliku z hosta — **nie** polega na współdzieleniu ścieżek z kontenerem Docker; osobny mount vaultu pod tą samą ścieżką absolutną nie jest wymagany do sync z KMS.

PDF-y **bez wyciągalnego tekstu** (np. skany bez OCR, uszkodzone lub zbyt „minimalne” strukturalnie) mogą dać po stronie AnythingLLM komunikat w stylu `A processing error occurred` — wtedy przetwórz plik lokalnie (`convert_pdf_to_markdown`) albo użyj innego źródła.

### Prompt workspace + ścieżki Obsidian

Gotowy **System Prompt**, temperatura, historia czatu i tekst odmowy „query mode”: **[anythingllm-workspace.md](anythingllm-workspace.md)** (wklejka do UI AnythingLLM).

---

## Przegląd modułów (`python -m kms.scripts.…`)

| Moduł | Opis | `--dry-run` |
|-------|------|-------------|
| `scan_inbox` | Skanuje `00_Inbox`, upsert do SQLite | tak |
| `make_review_queue` | Tworzy propozycje i regeneruje `review-queue.md` | tak |
| `apply_decisions` | Czyta decyzje z markdowna, przenosi pliki, source note, artefakty + snapshot `executions` | tak |
| `revert_apply` | Cofnięcie apply: `--proposal-id`, przy indeksie OK wywołuje **usunięcie z embeddingów** AnythingLLM (gdy zapisano `anythingllm_doc_location`), potem pliki. Wymaga **`executions`**; stare wpisy bez snapshotu — revert nie zadziała | tak |
| `status` | Odczyt lifecycle / indeksu (`--proposal-id`, `--json`) | — |
| `generate_source_note` | Nowa source note z szablonu (`--title`, `--source-type`, `--source-url`, `--file-link`, `-o`) | tak |
| `daily_report` | Raport do `00_Admin/reports` (`--since 1d\|7d\|30d`) | tak |
| `verify_integrity` | Sprawdzenie spójności vault ↔ SQLite: brakujące pliki, zmienione hashe, pliki w inbox bez wpisu DB (`--json`) | — (read-only) |
| `inbox_merge_advisor` | Głębsze sugestie vs warstwa kanoniczna: duplikat / konflikt / merge / prompt → **AnythingLLM API** (`--proposal-id`, `--json`, `--out`, opcjonalnie `--invoke-anythingllm`) | tak (bez audytu przy dry-run) |
| `sync_to_anythingllm` | Upload + `update-embeddings` dla niesyncowanych artefaktów | tak |
| `resync_embeddings` | Pełny re-embed vault po zmianie modelu embeddingów lub chunkingu (`--dry-run`, `--folders`, `--api-key`, `--batch-size`) | tak |
| `convert_pdf_to_markdown` | PDF → MD (inbox lub `--input`) | tak |
| `convert_conversation` | Surowa rozmowa/czat → source-note w `00_Inbox/` z `source_type: conversation` (`--input` **lub** `--batch-dir`, `--title` tylko przy pojedynczym pliku, opcjonalnie `--invoke-anythingllm`) | tak |
| `list_batches` | Lista operacji batch w formacie JSON (`--active-only`, `--limit`) | — (read-only) |

**Powłoki (repozytorium):**

| Skrypt | Opis |
|--------|------|
| `scripts/setup.sh` | Setup venv / zależności |
| `scripts/generate_knowledge_seed.py` | Notatki `type: permanent-note` z `status: inbox` → `00_Inbox/seed/**` (`python scripts/generate_knowledge_seed.py`) |
| `scripts/ingest_conversations.py` | Folder `*.pdf` (eksporty czatów) → Markdown w `00_Inbox/conversations/` (`--source-dir`, `--target-dir`, `--max-size-mb` [domyślnie **bez limitu**], `--dry-run`, opcjonalnie `--config` dla audytu) |
| `kms/scripts/backup.sh` | Backup vault (+ SQLite wg configu) |

---

## Review (markdown)

Decyzje są w **`paths.review_queue_file`** (domyślnie `00_Admin/review-queue.md`):

- W bloku YAML między `<!-- kms:begin -->` a `<!-- kms:end -->` ustaw:
  - `decision`: `pending` \| `approve` \| `reject` \| `postpone`
  - `reviewer`: zalecane przy approve/reject
  - opcjonalnie `override_target`, `review_note`

**Checkboxy Obsidiana** same z siebie nie aktualizują tego YAML — bez wtyczki typu Meta Bind / osobnego UI nadal edytujesz tekst.

Kontrakt: [architecture.md](architecture.md) (sekcja review-queue).

---

## Cron i harmonogram

**Bezpieczny domyślny wzorzec** — bez automatycznego `apply` (mutacje tylko po świadomym review):

```cron
0 7 * * * cd /path/to/KMS && . .venv/bin/activate && export PYTHONPATH=. && \
  python -m kms.scripts.scan_inbox && \
  python -m kms.scripts.make_review_queue && \
  python -m kms.scripts.daily_report
```

**Opcjonalnie** po review (np. raz dziennie na hoście, gdy zatwierdzasz offline):

```cron
15 8 * * * cd /path/to/KMS && . .venv/bin/activate && export PYTHONPATH=. && \
  export ANYTHINGLLM_API_KEY="..." && \
  python -m kms.scripts.apply_decisions && \
  python -m kms.scripts.sync_to_anythingllm && \
  python -m kms.scripts.make_review_queue
```

Nie umieszczaj klucza API w crontab w produkcji — lepiej plik env ładowany przez wrapper lub menedżer sekretów.

---

## Weryfikacja spójności

```bash
.venv/bin/python -m kms.scripts.verify_integrity --config kms/config/config.yaml
.venv/bin/python -m kms.scripts.verify_integrity --json
```

Sprawdza: pliki w DB, których brak na dysku; pliki w inbox bez wpisu w SQLite; różnice hashów. Zwraca exit code `1` przy wykrytym dryfcie.

---

## Merge advisor (inbox vs kanon) — **opcjonalny**

Ten sam leksykalny „podgląd” co w `make_review_queue`, plus klasyfikacja duplikat/konflikt i markdown pod LLM. **Nie zastępuje** edycji `review-queue.md`; mutacje tylko przez `apply_decisions`.

```bash
python -m kms.scripts.inbox_merge_advisor --config kms/config/config.yaml
python -m kms.scripts.inbox_merge_advisor --proposal-id 3 --dry-run
python -m kms.scripts.inbox_merge_advisor --out example-vault/00_Admin/merge-advisor-report.md
export ANYTHINGLLM_API_KEY="..."   # opcjonalnie: odpowiedź z workspace (model w UI AnythingLLM)
python -m kms.scripts.inbox_merge_advisor --invoke-anythingllm
```

Endpoint: `POST /api/v1/workspace/{slug}/chat` — te same `anythingllm.*` co przy sync. `merge_advisor.anythingllm_chat_mode`: `chat` \| `query` \| `automatic`.

Notatki seed (HITL): `00_Inbox/seed/**` — ten sam układ tematyczny co wcześniej (`principles`, `cpp/*`, `system-design/*`, …, `domain/govtech/*`); `python scripts/generate_knowledge_seed.py`, potem `scan_inbox` → `review-queue` → `apply`. Korpus w `30_Permanent-Notes/` możesz utrzymywać osobno po apply. Zob. [kms-principles.md](kms-principles.md) §9.

---

## Konwerter rozmów

Surowe rozmowy (WhatsApp, Discord, czat, transkrypcja) → sformatowana source-note w `00_Inbox/`.

```bash
python -m kms.scripts.convert_conversation --input rozmowa.txt --title "Debug z Bobem"
python -m kms.scripts.convert_conversation --batch-dir ./folder_z_txt/   # tytuł z nazwy pliku
python -m kms.scripts.convert_conversation --input rozmowa.txt --dry-run
export ANYTHINGLLM_API_KEY="..."
python -m kms.scripts.convert_conversation --input rozmowa.txt --invoke-anythingllm
```

Z flagą `--invoke-anythingllm` prompt jest wysyłany do workspace (model z UI AnythingLLM) i odpowiedź staje się treścią notatki. Bez niej — prompt trafia bezpośrednio do notatki (do ręcznego wklejenia do LLM).

**PDF → MD w inbox (wiele plików):** domyślnie `pdf_converter` bierze **pierwszy** udany backend w kolejności **markitdown** → docling → pymupdf4llm → pypdf. Dla eksportów czatu (ChatGPT itd.) często lepszy jest tryb **`--converter-pick best`**: uruchamiane są wszystkie dostępne backendy i wybierany jest wynik z najwyższą heurystyką „transkryptu”. Zależność **pymupdf4llm** jest w `requirements.txt`. Batch:

```bash
python scripts/ingest_conversations.py --source-dir conversations/ \\
  --target-dir example-vault/00_Inbox/conversations/ \\
  --converter-pick best
# opcjonalnie limit: --max-size-mb 200
# opcjonalnie: --config kms/config/config.yaml  # wpis audit_log
```

Pojedynczy PDF z vaultu: `python -m kms.scripts.convert_pdf_to_markdown --converter-pick best --input ...`

Domyślnie skrypt przetwarza wszystkie rozmiary PDF (`--max-size-mb <= 0`). Wyjście JSON: `ok` / `skipped` / `failed` + `topics_found` + `new_topics`.
Dodatkowo zapisuje raport `00_Inbox/conversations/_topics_discovered.md` z licznikami tematów (np. Java/TypeScript/Angular), żeby łatwo utworzyć kolejne notatki permanent.

Notatka z `source_type: conversation` przechodzi standardowy pipeline: `scan_inbox → make_review_queue → apply`.

---

## Co dalej (TUI / web)

- **TUI / lekki panel** — zaplanowane jako ergonomia v2; na razie źródłem prawdy dla decyzji pozostaje markdown + SQLite.
- **Gateway** — cienki HTTP do decyzji z telefonu; `apply` nadal na hoście: [gateway.md](gateway.md).

## Powiązane dokumenty

- [workflow.md](workflow.md) — dzień pracy, profile local/cloud
- [docker-setup.md](docker-setup.md) — AnythingLLM w Dockerze
- [architecture.md](architecture.md) — granice systemu, SoT
- [testing-baseline.md](testing-baseline.md) — testy 2-tygodniowe
