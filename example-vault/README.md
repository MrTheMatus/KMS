# Example vault (KMS)

Struktura zgodna z dokumentacją (`00_Inbox`, `10_Sources/web|pdf`, `20_Source-Notes`, …).

## Przykładowe treści (do AnythingLLM / testów)

| Lokalizacja | Opis |
|-------------|------|
| `10_Sources/web/clip-pv-costs.md` | Symulowany clipping — porównanie kosztów PV |
| `10_Sources/pdf/minimal-demo.pdf` | Mały PDF z **tekstem** (AnythingLLM potrafi zwrócić błąd dla „pustych” PDF bez treści) |
| `20_Source-Notes/src-2026-0001.md` | Source note (taryfa — demo pytań) |
| `20_Source-Notes/src-2026-0002.md` | Source note powiązany z PDF (gwarancja — demo) |
| `30_Permanent-Notes/*.md` | Przykładowe notatki kanoniczne (engineering/product/security/operations) |
| `30_Permanent-Notes/cpp-corpus/*.md` | **30 notatek** o idiomach C++ (testy merge/konflikt/duplikat dla `inbox_merge_advisor`); regeneracja: `python scripts/generate_cpp_corpus.py` |
| `00_Inbox/draft-inbox-item.md` | **Seed** do ponownego `scan_inbox` → `make_review_queue` |

## Stan po pełnym teście control plane

Jeśli uruchomiłeś `apply_decisions`, część plików mogła zostać przeniesiona z inboxu do `10_Sources/`. Aby zacząć od zera:

1. Usuń `kms/data/state.db` (lokalnie; plik jest w `.gitignore`).
2. Przywróć układ plików (np. `git checkout -- example-vault`) albo skopiuj seed z `00_Inbox/draft-inbox-item.md`.

## Raporty

- Dzienne raporty tekstowe: `00_Admin/reports/daily-*.txt` (generuje `daily_report.py`).
