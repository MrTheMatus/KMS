# Workflow użytkownika

Pełna lista poleceń, flag (`--config`, `--dry-run`, `-v`), konfiguracja AnythingLLM i przykłady crona: **[docs/cli.md](cli.md)**. Zasady rozwoju narzędzia (kolejność feature'ów, HITL): **[kms-principles.md](kms-principles.md)**.

## Role narzędzi

| Narzędzie | Rola |
|-----------|------|
| **Obsidian** | Pisanie, vault, source notes, interaktywny review (`review-queue.md` z pluginem kms-review) |
| **Ollama + Qwen 2.5:14b** | Lokalne streszczenia AI do review queue (~8s/notatkę na M4 Pro) |
| **AnythingLLM** | (Opcjonalnie) Pytania i odpowiedzi nad dokumentami, workspace'y — szablon promptu: [anythingllm-workspace.md](anythingllm-workspace.md) |
| **Skrypty KMS** | Skan inboxu, kolejka, apply, status, revert, merge advisor, convert, sync, raport |
| **SQLite** | Source of truth dla decyzji i stanu operacyjnego |

## Wymagania

| Komponent | Instalacja | Cel |
|-----------|------------|-----|
| Python 3.14 + venv | `.venv/bin/python` | Skrypty KMS |
| Ollama | `brew install ollama && brew services start ollama` | Lokalny LLM |
| Qwen 2.5:14b | `ollama pull qwen2.5:14b` (9 GB) | Streszczenia AI (polski) |
| Obsidian + plugin kms-review | Vault: `example-vault/`, plugin w `.obsidian/plugins/kms-review/` | Interaktywny przegląd |
| SQLite | Wbudowane (state.db) | Stan pipeline, audit trail |
| AnythingLLM | (Opcjonalnie) Docker/standalone na porcie 3001 | RAG/Q&A nad dokumentami |

## Pipeline — pełny cykl

```
 ┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
 │  00_Inbox/   │────▶│   scan_inbox     │────▶│  items (DB)   │
 │  (pliki)     │     │                  │     │  status: new  │
 └──────────────┘     └──────────────────┘     └───────┬───────┘
                                                       │
                      ┌──────────────────┐             │
                      │ make_review_queue │◀────────────┘
                      │  --ai-summary    │
                      │                  │
                      │ • triage (TF-IDF)│
                      │ • domain/topics  │
                      │ • AI streszczenie│
                      └────────┬─────────┘
                               │
                      ┌────────▼─────────┐
                      │  review-queue.md │
                      │  (Obsidian)      │
                      │                  │
                      │  approve/reject/ │
                      │  postpone        │
                      └────────┬─────────┘
                               │
                      ┌────────▼─────────┐     ┌──────────────────┐
                      │ apply_decisions  │────▶│ 10_Sources/pdf/  │
                      │                  │     │ 10_Sources/web/  │
                      │ • przenosi pliki │     │ 20_Source-Notes/ │
                      │ • tworzy source  │     └──────────────────┘
                      │   notes          │
                      │ • index_status=  │
                      │   'pending'      │
                      └────────┬─────────┘
                               │ (opcjonalnie)
                      ┌────────▼─────────────┐
                      │ sync_to_anythingllm  │
                      │                      │
                      │ • upload do workspace│
                      │ • update_embeddings  │
                      │ • index_status='ok'  │
                      └──────────────────────┘
```

---

## Etap 1: Skanowanie inboxa

```bash
.venv/bin/python -m kms.scripts.scan_inbox
```

**Co robi:**
- Przegląda `00_Inbox/` rekurencyjnie (podfoldery `seed/`, `conversations/` też)
- Nowy plik → `INSERT INTO items` ze `status = 'new'`
- Zmieniony hash → `UPDATE items SET status = 'new'` (ponowna ocena)
- Bez zmian → pomija
- Wykrywa duplikaty hashów → ostrzeżenie w audit_log

**Wejście:** Pliki w `00_Inbox/`
**Wyjście:** Tabela `items` w SQLite

---

## Etap 2: Generowanie propozycji + review queue

```bash
# Bez AI streszczeń (szybko)
.venv/bin/python -m kms.scripts.make_review_queue

# Z AI streszczeniami (Ollama, ~8s/notatkę)
.venv/bin/python -m kms.scripts.make_review_queue --ai-summary

# Podgląd bez zapisu
.venv/bin/python -m kms.scripts.make_review_queue --ai-summary --dry-run
```

**Co robi:**

1. Dla każdego itema **bez propozycji** tworzy wiersz w `proposals`:
   - Heurystycznie sugeruje akcję (`move_to_pdf` / `move_to_web`)
   - Uruchamia triage: TF-IDF + bigramy + title boost vs `30_Permanent-Notes/`
   - Auto-detekcja domeny (cpp, angular, sql, devops, java, python, ...)
   - Auto-detekcja tematów (performance, migration, debugging, architecture, ...)
   - Zapisuje `suggested_metadata_json` w DB

2. Flaga `--ai-summary`:
   - Próbuje **Ollama** (preferowane, lokalne, bez API key)
   - Fallback na **AnythingLLM** (jeśli Ollama niedostępna)
   - Wysyła do 4000 znaków treści + system prompt po polsku
   - Post-processing: usuwanie znaków CJK (Qwen czasem przeskakuje na chiński)
   - ~8 sekund na streszczenie na M4 Pro

3. Renderuje `00_Admin/review-queue.md`:
   - Tylko propozycje z `decision IN ('pending', 'postpone')`
   - Każda propozycja = blok `kms-review` (kontrolki) + body markdown (metadane + streszczenie)
   - Separator `***` między propozycjami

**Wejście:** Tabela `items`, pliki w vault, `30_Permanent-Notes/`
**Wyjście:** `00_Admin/review-queue.md`, tabela `proposals`

### Hierarchia backendów AI (automatyczna):

```
1. Ollama (localhost:11434) → qwen2.5:14b
2. AnythingLLM (localhost:3001) → workspace chat
3. Heurystyka → obcięcie tekstu do 400 znaków (fallback)
```

Konfiguracja w `kms/config/config.yaml`:

```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "qwen2.5:14b"

anythingllm:
  enabled: false  # true jeśli używasz AnythingLLM
  base_url: "http://localhost:3001"
  workspace_slug: "my-workspace"
  api_key_env: "ANYTHINGLLM_API_KEY"
```

---

## Etap 3: Przegląd w Obsidian (człowiek)

Otwórz `00_Admin/review-queue.md` w Obsidian (Reading View).

> **Dla PO:** Zamiast terminala użyj **Ctrl+P** (Command Palette) w Obsidian:
> - `KMS: Refresh review queue` — skan + AI streszczenia + dashboard (zastępuje etapy 1-2)
> - `KMS: Apply decisions` — zastosuj decyzje (zastępuje etap 4)
> - `KMS: Approve all pending` — zatwierdź wszystkie naraz
> - `KMS: Reject all pending` — odrzuć wszystkie naraz
> - `KMS: Open dashboard` — podgląd statystyk

Plugin **kms-review** renderuje dla każdej propozycji:
- **Nagłówek** z numerem propozycji i badge statusu (PENDING/APPROVE/REJECT)
- **Przyciski** Approve / Reject / Postpone (klik → automatyczny zapis do YAML)
- **Input** na review note (debounced, auto-save po 800ms)
- **Body** renderowany jako markdown (ścieżka, domain, topics, streszczenie AI, linki Obsidiana)

### Znaczenie decyzji

| Decyzja | Skutek w etapie 4 | Plik źródłowy | W następnej kolejce |
|---------|--------------------|---------------|---------------------|
| `approve` | Przeniesienie + source note | Przeniesiony do `10_Sources/` | Nie |
| `reject` | Archiwizacja | Przeniesiony do `99_Archive/rejected/YYYY-MM/` | Nie |
| `postpone` | **Nic** — odroczona | Zostaje w `00_Inbox/` | **Tak** (wraca) |
| `pending` | Czeka na decyzję | Zostaje | Tak |

### Opcjonalne pola:
- `override_target` — nadpisanie sugerowanej ścieżki docelowej
- `review_note` — uzasadnienie decyzji (audit trail)

---

## Etap 4: Zastosowanie decyzji

```bash
# Podgląd co zostanie wykonane
.venv/bin/python -m kms.scripts.apply_decisions --dry-run -v

# Wykonanie
.venv/bin/python -m kms.scripts.apply_decisions -v
```

**Co robi:**

1. **Parsuje** `review-queue.md` → upsert do tabeli `decisions`
2. **Przelicza** `lifecycle_status` każdej propozycji
3. **Dla `approve`:**
   - Przenosi plik: `00_Inbox/x.pdf` → `10_Sources/pdf/x.pdf`
   - Tworzy source note w `20_Source-Notes/src-2026-NNNN.md` (z template Jinja2)
   - Wstawia wiersz do `artifacts` z `index_status = 'pending'`
   - Zapisuje snapshot w `executions` (do revert)
4. **Dla `reject`** — przenosi plik do `99_Archive/rejected/YYYY-MM/`, zapisuje decyzję w DB
5. **Dla `postpone`** — tylko zapis decyzji, plik zostaje w `00_Inbox/`, propozycja wraca do następnej kolejki

**Wejście:** `review-queue.md`, tabela `proposals`
**Wyjście:** Przeniesione pliki, source notes, tabela `artifacts`

### Idempotencja

Apply jest idempotentny — powtórne uruchomienie:
- Pomija propozycje, dla których istnieje artifact (nie przenosi ponownie)
- Bezpiecznie upsertuje decisions (ON CONFLICT UPDATE)

---

## Etap 5: Indeksowanie w AnythingLLM (opcjonalnie)

```bash
.venv/bin/python -m kms.scripts.sync_to_anythingllm
```

**Co robi:**

1. Szuka artifactów z `index_status IN ('pending', 'failed')`
2. Dla każdego:
   - Upload pliku do AnythingLLM (multipart/form-data)
   - Wywołanie `update_embeddings` → wektoryzacja dokumentu
   - `index_status = 'ok'`, zapis `workspace_name` i `anythingllm_doc_location`
3. Przy błędzie: `index_status = 'failed'` → ponowna próba przy następnym uruchomieniu

### Kiedy AnythingLLM jest wyłączony

| Etap | Zachowanie |
|------|------------|
| `apply_decisions` | **Działa normalnie** — nigdy nie wywołuje AnythingLLM |
| `sync_to_anythingllm` | Kończy się błędem, `index_status = 'failed'` |
| Ponowne uruchomienie sync | Retryje `pending` + `failed` — odzyskuje się automatycznie |
| Pliki w vault | **Zawsze dostępne** — AnythingLLM to opcjonalna warstwa Q&A |

### Lifecycle statusy

```
awaiting_decision → approved → applied → indexed
                                  ↓
                            index_failed (retry)
```

---

## Operacje dodatkowe

### Odświeżenie propozycji (po zmianach w pipeline/AI)

Gdy chcesz przebudować propozycje od zera (np. po dodaniu AI streszczeń, zmianie triageera):

```bash
# 1. Usuń stare propozycje (TYLKO pending/postpone — nie ruszaj approved!)
.venv/bin/python -c "
from kms.app.config import abs_path, load_config
from kms.app.db import connect, ensure_schema
from kms.app.paths import project_root

cfg = load_config()
conn = connect(abs_path(cfg, 'database', 'path'))
ensure_schema(conn, project_root() / 'kms' / 'app' / 'schema.sql')

conn.execute('''
    DELETE FROM decisions WHERE proposal_id IN (
        SELECT p.id FROM proposals p
        LEFT JOIN decisions d ON d.proposal_id = p.id
        WHERE COALESCE(d.decision, 'pending') IN ('pending', 'postpone')
    )
''')
conn.execute('''
    DELETE FROM proposals WHERE id NOT IN (
        SELECT proposal_id FROM decisions WHERE decision = 'approve'
    ) AND id NOT IN (
        SELECT proposal_id FROM artifacts
    )
''')
conn.commit()
print(f'Usunięto propozycji: {conn.execute(\"SELECT changes()\").fetchone()[0]}')
conn.close()
"

# 2. Przegeneruj z AI streszczeniami
.venv/bin/python -m kms.scripts.make_review_queue --ai-summary
```

### Cofnięcie zatwierdzonej propozycji

```bash
.venv/bin/python -m kms.scripts.revert_apply --proposal-id 5
```

Co robi:
- Jeśli `index_status = 'ok'` → wywołuje `remove_embeddings` na AnythingLLM (best-effort)
- Przenosi plik z powrotem: `10_Sources/` → `00_Inbox/`
- Usuwa artifact i execution z DB
- Propozycja wraca do stanu `awaiting_decision`

### Podgląd stanu systemu

```bash
.venv/bin/python -m kms.scripts.status              # tabela
.venv/bin/python -m kms.scripts.status --json        # JSON lines
.venv/bin/python -m kms.scripts.status --proposal-id 5  # konkretna propozycja
```

### Raport dzienny

```bash
.venv/bin/python -m kms.scripts.daily_report
```

---

## Procedura 15 min dla PO (guided markdown)

Cel: PO ma umieć podjąć decyzję o pliku bez znajomości kodu.

1. Otwórz vault `example-vault` w Obsidian.
2. Wrzuć plik do `00_Inbox` (drag & drop).
3. Operator uruchamia:

```bash
.venv/bin/python -m kms.scripts.scan_inbox
.venv/bin/python -m kms.scripts.make_review_queue --ai-summary
```

4. Otwórz `00_Admin/review-queue.md` (Reading View w Obsidian).
5. Dla każdej propozycji:
   - Przeczytaj streszczenie AI i metadane
   - Kliknij **Approve** / **Reject** / **Postpone**
   - (Opcjonalnie) Wpisz review note
6. Operator uruchamia:

```bash
.venv/bin/python -m kms.scripts.apply_decisions --dry-run -v
.venv/bin/python -m kms.scripts.apply_decisions -v
.venv/bin/python -m kms.scripts.make_review_queue --ai-summary
```

7. Sprawdź, czy pozycja zniknęła z aktywnej kolejki.

---

## Ingestion dodatkowy

### Rozmowy/czaty (tekst)

```bash
.venv/bin/python -m kms.scripts.convert_conversation --input rozmowa.txt
# lub batch:
.venv/bin/python -m kms.scripts.convert_conversation --batch-dir folder_z_txt/
```

### PDF z eksportów czatu

```bash
python scripts/ingest_conversations.py \
  --source-dir conversations/ \
  --target-dir example-vault/00_Inbox/conversations/ \
  --converter-pick best
```

### Seed wiedzy

```bash
python scripts/generate_knowledge_seed.py
```

Tworzy szkice permanent-note w `00_Inbox/seed/**` (status: inbox) — zatwierdzasz je w review-queue.

---

## Cron (przykład)

```cron
# Codzienny scan + kolejka (bez apply — wymaga review)
0 7 * * * cd /path/to/KMS && .venv/bin/python -m kms.scripts.scan_inbox && .venv/bin/python -m kms.scripts.make_review_queue --ai-summary && .venv/bin/python -m kms.scripts.daily_report
```

> **Apply NIE powinien być w cronie** — wymaga ręcznego review (HITL).

---

## Uruchomienie Ollama

```bash
# Jako daemon (autostart przy logowaniu)
brew services start ollama

# Jednorazowo z optymalizacjami
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 ollama serve

# Sprawdzenie modeli
ollama list

# Pobranie modelu
ollama pull qwen2.5:14b
```

---

## Shippable v1: 2-week protocol (2 devices)

Cel: potwierdzić, że starter kit jest przenoszalny i przewidywalny bez rozbudowanej infrastruktury.

### Topologia testu

- **Device A (host):** pełny stack (vault, SQLite, skrypty mutujące, Ollama, ewentualnie local profile).
- **Device B (client):** review i pytania do korpusu (cloud profile, bez mutacji plików).

### Tydzień 1 (stabilność i jakość odpowiedzi)

1. Zasil `00_Inbox/` mieszanymi tematami (engineering/product/security/operations).
2. Prowadź codzienny cykl `scan → review → apply → report`.
3. Testuj pytania demo z `docs/conference-demo.md` na warstwie source i canonical.
4. Rejestruj override w review queue (czy sugestia była wystarczająca bez ręcznej korekty).

### Tydzień 2 (powtarzalność i failure handling)

1. Powtarzaj apply dla tych samych decyzji (idempotencja).
2. Symuluj edge cases: brak pliku źródłowego, kolizja ścieżki docelowej.
3. Weryfikuj, że błędy kończą się statusem `failed` i wpisem w `audit_log`.
4. Sprawdzaj czas od ingestu do decyzji oraz czy backlog nie rośnie bez kontroli.

### Exit criteria po 2 tygodniach

- brak krytycznych błędów utraty danych,
- >= 80% decyzji zatwierdzanych bez `override_target`,
- testowe scenariusze failure są obsługiwane przewidywalnie,
- inny deweloper potrafi przejść onboarding i jeden pełny cykl bez wsparcia autora.

Szczegółowa checklista i tabela metryk: [`docs/testing-baseline.md`](testing-baseline.md).
