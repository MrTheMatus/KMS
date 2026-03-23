# Workflow użytkownika

Pełna lista poleceń, flag (`--config`, `--dry-run`, `-v`), konfiguracja AnythingLLM i przykłady crona: **[docs/cli.md](cli.md)**. Zasady rozwoju narzędzia (kolejność feature’ów, HITL): **[kms-principles.md](kms-principles.md)**.

## Ról narzędzi

| Narzędzie | Rola |
|-----------|------|
| **Obsidian** | Pisanie, vault, source notes, edycja `review-queue.md` |
| **AnythingLLM** | Pytania i odpowiedzi nad dokumentami, workspace’y — szablon promptu i ustawień: [anythingllm-workspace.md](anythingllm-workspace.md) |
| **Ollama** (opcjonalnie) | Lokalne modele; `OLLAMA_MODELS` może wskazywać dysk zewnętrzny |
| **Skrypty KMS** | Skan inboxu, kolejka, apply, **`status`** (stan), **`revert_apply`** (cofnięcie), **`inbox_merge_advisor`** (merge/konflikt vs kanon), sync, raport, backup |
| **SQLite** | Source of truth dla decyzji i stanu operacyjnego |

## Docker / AnythingLLM

Instalacja obrazu i porty: [docker-setup.md](docker-setup.md).

## Profil **local**

1. Zainstaluj [Ollama](https://ollama.com) na hoście.
2. W AnythingLLM wybierz endpoint Ollamy (typowo `http://host.docker.internal:11434` z kontenera Docker na macOS).
3. (Opcjonalnie) Pobierz modele do Ollamy:

```bash
python -m kms.scripts.ollama_pull_models --models "llama3.1:8b, nomic-embed-text"
```

4. Ustaw `runtime.profile: local` w `kms/config/config.yaml` (informacyjnie dla raportów).

## Profil **cloud**

1. W AnythingLLM skonfiguruj klucz API (OpenAI, Anthropic, itd.).
2. Nie musisz instalować Ollamy — vault i KMS działają tak samo.
3. Ustaw `runtime.profile: cloud` w configu.

## Typowy dzień

1. Wrzuć pliki do `00_Inbox/` (MarkDownload, PDF, itp.).
2. `python -m kms.scripts.scan_inbox`
3. `python -m kms.scripts.make_review_queue`
3b. *(Opcjonalnie)* `python -m kms.scripts.inbox_merge_advisor` — heurystyki + prompt (opcjonalnie wysłany do **AnythingLLM** przez API — model w UI workspace): duplikat, konflikt z notatkami kanonicznymi (np. `30_Permanent-Notes/cpp-corpus/`), sugestia scalenia. Szczegóły: [cli.md](cli.md) (*Merge advisor*).
4. Otwórz `00_Admin/review-queue.md` w Obsidianie; dla każdego bloku YAML ustaw `decision` i opcjonalnie `reviewer`.
5. `python -m kms.scripts.apply_decisions --dry-run`, potem bez `--dry-run`.
6. `apply_decisions` automatycznie tworzy minimalne `source note` dla zatwierdzonych propozycji (`move_to_pdf`/`move_to_web`). Opcjonalnie uzupełnij notatki.
7. (Opcjonalnie) Indeksowanie w AnythingLLM: włącz `anythingllm.enabled` w configu, ustaw `ANYTHINGLLM_API_KEY`, potem `python -m kms.scripts.sync_to_anythingllm`. Szczegóły: [cli.md](cli.md).

## Procedura 15 min dla PO (guided markdown)

Cel: PO ma umieć podjąć decyzję o pliku bez znajomości kodu.

1. Otwórz vault `example-vault` w Obsidian.
2. Wrzuć plik do `00_Inbox` (drag & drop).
3. Operator uruchamia:

```bash
python -m kms.scripts.scan_inbox
python -m kms.scripts.make_review_queue
```

4. Otwórz `00_Admin/review-queue.md`.
5. Dla każdego bloku:
   - przeczytaj `Open source in Obsidian`,
   - ustaw `decision`: `approve` / `reject` / `postpone`,
   - opcjonalnie ustaw `override_target`,
   - wpisz `review_note` (krótkie uzasadnienie).
6. Operator uruchamia:

```bash
python -m kms.scripts.apply_decisions --dry-run -v
python -m kms.scripts.apply_decisions -v
python -m kms.scripts.make_review_queue
```

7. Sprawdź, czy pozycja zniknęła z aktywnej kolejki (pending/postpone zostają).

## Cron (przykład)

```cron
0 7 * * * cd /path/to/KMS && . .venv/bin/activate && export PYTHONPATH=. && python -m kms.scripts.scan_inbox && python -m kms.scripts.make_review_queue && python -m kms.scripts.daily_report
```

Apply **nie** powinien być domyślnie w cronie bez Twojej zgody — zostaw jako jawny krok po review.

## Shippable v1: 2-week protocol (2 devices)

Cel: potwierdzić, ze starter kit jest przenoszalny i przewidywalny bez rozbudowanej infrastruktury.

### Topologia testu

- **Device A (host):** pelny stack (vault, SQLite, skrypty mutujace, ewentualnie local profile).
- **Device B (client):** review i pytania do korpusu (cloud profile, bez mutacji plikow).

### Tydzien 1 (stabilnosc i jakosc odpowiedzi)

1. Zasil `00_Inbox/` mieszanymi tematami (engineering/product/security/operations).
2. Prowadz codzienny cykl `scan -> review -> apply -> report`.
3. Testuj pytania demo z `docs/conference-demo.md` na warstwie source i canonical.
4. Rejestruj override w review queue (czy sugestia byla wystarczajaca bez recznej korekty).

### Tydzien 2 (powtarzalnosc i failure handling)

1. Powtarzaj apply dla tych samych decyzji (idempotencja).
2. Symuluj edge cases: brak pliku zrodlowego, kolizja sciezki docelowej.
3. Weryfikuj, ze bledy koncza sie statusem `failed` i wpisem w `audit_log`.
4. Sprawdzaj czas od ingestu do decyzji oraz czy backlog nie rosnie bez kontroli.

### Exit criteria po 2 tygodniach

- brak krytycznych bledow utraty danych,
- >= 80% decyzji zatwierdzanych bez `override_target`,
- testowe scenariusze failure sa obslugiwane przewidywalnie,
- inny deweloper potrafi przejsc onboarding i jeden pelny cykl bez wsparcia autora.

Szczegolowa checklista i tabela metryk: [`docs/testing-baseline.md`](testing-baseline.md).
