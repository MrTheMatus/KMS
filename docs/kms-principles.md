# Zasady rozwoju KMS (control plane)

Ten dokument **spina filozofię** z planów (rdzeń operacyjny, human-in-the-loop, odwracalność) i jest **filtrem** przy nowych pomysłach: najpierw spójność z tymi zasadami, dopiero rozszerzenia.

## 1. Granice systemu

| Tak | Nie (na tym etapie) |
|-----|----------------------|
| **Vault (Obsidian)** = treść i ścieżki | Własna baza wektorowa / własny RAG w Pythonie |
| **SQLite** = decyzje, propozycje, artefakty, audyt, lifecycle | Embeddingi w SQLite |
| **AnythingLLM** (lub następca) = retrieval / Q&A nad plikami | Ciężki orchestrator (Airflow), „magia” bez audytu |
| Cienkie **skrypty CLI** + opcjonalnie później TUI | Duży panel web jako priorytet |

## 2. Human-in-the-loop

- Model i heurystyki **proponują** (scan → propozycja → kolejka).
- **Człowiek zatwierdza** w `review-queue.md` (lub później TUI/gateway).
- **Apply** wykonuje mutacje vaultu dopiero po decyzji.
- Brak autonomicznego „AI nadpisuje vault bez pytania”.

## 3. Operacyjny pipeline (kolejność myślenia)

1. Wykrycie (`scan_inbox`)  
2. Propozycja (`make_review_queue`)  
3. Review (edycja YAML / decyzja)  
4. Wykonanie (`apply_decisions`) + snapshot `executions`  
5. Indeks zewnętrzny (`sync_to_anythingllm`) — opcjonalnie  
6. Cofnięcie (`revert_apply`) — gdy potrzebne  

**Scheduler (cron / systemd)** to warstwa wygody **nad** stabilnym rdzeniem — nie zastępuje idempotencji ani statusów.

## 4. Idempotencja i stan

- Powtórne uruchomienie **scan / apply / sync** nie tworzy duplikatów ani nie psuje spójności tam, gdzie to jest zdefiniowane w kodzie.
- **Lifecycle** (`proposals.lifecycle_status`) jest cache wyliczalnym — jeden sposób prawdy z `decisions` + `artifacts` + `items`.
- **Indeks AnythingLLM**: `artifacts.index_status` + opcjonalnie `anythingllm_doc_location` do usuwania z indeksu przy revert.

## 5. Audyt i odwracalność

- Znaczące akcje zostawiają ślad w `audit_log`.
- Apply zapisuje **snapshot** w `executions` (revert plików).
- Revert stara się **usunąć embedding** przez API (`update-embeddings` z `deletes`), gdy znany jest `anythingllm_doc_location`; w razie braku (stare rekordy) lub błędu API — audyt + ewentualna ręczna korekta w UI.

## 6. Błędy częściowe

- **Apply OK, sync FAIL**: pliki w vaultcie zostają; `index_status = failed`; retry sync — **bez** automatycznego cofania plików.
- **Transakcje**: tam gdzie sensowne, ograniczają rozjechanie się stanu; przy konflikcie preferuj jawny `failed` + audyt zamiast „cichej naprawy”.

## 7. Rozszerzanie zakresu — kolejność

1. Domknij **rdzeń** (statusy, revert, indeks, dokumentacja).  
2. **TUI** do review (ergonomia bez rozpychania backendu).  
3. **Scheduler** (timer), gdy przepływ jest stabilny.  
4. **GUI** dla mniej technicznej publiczności — na końcu lub wcale.

## 8. Konwencje techniczne (skrót)

- Nazewnictwo i ścieżki zgodne z [`architecture.md`](architecture.md).
- Zmiany schematu: `schema.sql` + migracja w [`kms/app/db.py`](../kms/app/db.py).
- Testy regresyjne dla parserów, lifecycle i ścieżek krytycznych (`tests/`).

## 9. Opcjonalne rozszerzenia (bez „drugiego produktu”)

Żeby **domknąć** KMS jako starter kit **bez puchnięcia** rdzenia:

| Element | Rola | Co **nie** jest |
|---------|------|------------------|
| **`inbox_merge_advisor`** | Ten sam indeks leksykalny co `make_review_queue` / `llm_triage`, plus heurystyki duplikat/konflikt i **gotowy prompt**; opcjonalnie jedno wywołanie **AnythingLLM** `/workspace/.../chat` (model z UI) | Osobny silnik decyzji, automatyczny merge plików, drugi RAG |
| **Korpus testowy** (`cpp-corpus` + generator) | Materiał pod regresję i demo „kanon vs inbox” | Wymóg produkcyjny — można go nie używać |
| **Gateway HTTP** | Tylko zapis `decisions` + audyt | Zastąpienie `review-queue.md` jako jedynego źródła prawdy |

Zasada: **sugestia ≠ wykonanie** — merge plików wyłącznie po `approve` w `review-queue.md` / gatewayu, zgodnie z §2.

---

Powiązane: [architecture.md](architecture.md), [cli.md](cli.md), [workflow.md](workflow.md).
