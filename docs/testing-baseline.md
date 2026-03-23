# Testing baseline (2-week run, 2 devices)

Ten dokument zamraza baseline przed uruchomieniem testow na:
- Device A (host),
- Device B (client).

## 1) Baseline freeze checklist (Dzien 0)

- [ ] Potwierdzony config profilu (`cloud-default` lub `local-optional`).
- [ ] Wyczyszczony stan testowy (`kms/data/state.db`) albo jawny snapshot startowy.
- [ ] Sprawdzony seed danych w `example-vault` (mixed topics + permanent notes).
- [ ] Suchy przebieg: `scan_inbox`, `make_review_queue`, `apply_decisions --dry-run`.
- [ ] Wykonane testy regresji:
  - [ ] `tests/test_review_queue.py`
  - [ ] `tests/test_smoke_pipeline.py`
- [ ] Ustalony owner testu i reviewer wynikow.

## 2) Metryki bazowe (zapisz przed startem)

Wypelnij wartosci poczatkowe:

| Metryka | Baseline (D0) | Cel po 2 tyg. |
|---|---:|---:|
| Czas `ingest -> decyzja` (mediana, h) |  | <= 24h |
| Czas `approve -> apply` (mediana, min) |  | <= 30 min |
| % decyzji bez `override_target` |  | >= 80% |
| Liczba bledow `apply` / dzien |  | <= 1 |
| Liczba retry po bledzie |  | trend malejacy |
| Backlog `pending + postpone` |  | stabilny lub malejacy |

## 3) Tygodniowa checklista operacyjna

### Week 1 (stabilnosc i jakość odpowiedzi)
- [ ] Codziennie wykonano `scan -> review -> apply -> report`.
- [ ] Przetestowano pytania demo ze `docs/conference-demo.md`.
- [ ] Potwierdzono rozroznienie source layer vs canonical layer w odpowiedziach.
- [ ] Zebrano przyklady decyzji wymagajacych override.

### Week 2 (powtarzalnosc i niezawodnosc)
- [ ] Zweryfikowano idempotencje (ponowne `apply` bez duplikatow).
- [ ] Zweryfikowano obsluge `missing source` (status `failed` + audit).
- [ ] Zweryfikowano obsluge `target collision` (status `failed` + audit).
- [ ] Potwierdzono, ze brak niejawnych mutacji poza zatwierdzonym `apply`.

## 4) Raport koncowy (Dzien 14)

Podsumuj:
- co dzialalo stabilnie,
- jakie scenariusze wymagaly recznych obejsc,
- ktore reguly review trzeba doprecyzowac,
- czy system jest gotowy na szerszy test (3+ urzadzenia lub gateway etap 6).

Decyzja koncowa:
- [ ] Go: rozszerzamy rollout.
- [ ] No-go: najpierw poprawki control plane.
