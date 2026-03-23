#!/usr/bin/env python3
"""Generate ~30 C++ idiom / style notes under example-vault for merge-advisor testing.

Run from repo root: python scripts/generate_cpp_corpus.py

Creates: example-vault/30_Permanent-Notes/cpp-corpus/*.md
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "example-vault" / "30_Permanent-Notes" / "cpp-corpus"

# Intentional overlaps for duplicate/conflict testing:
# - RAII: cpp-01 + cpp-18 (similar)
# - smart pointers: cpp-08 vs cpp-24 (prefer unique vs discuss shared — tension)
# - Rule of Zero: cpp-06 + cpp-22

NOTES: list[tuple[str, str, list[str], str]] = [
    # slug, title, tags, body (markdown)
    (
        "cpp-01-raii-basics",
        "C++ Idiom: RAII — podstawy",
        ["cpp", "raii", "resource"],
        """# C++ Idiom: RAII — podstawy

**Prefer** wiązanie czasu życia zasobu z czasem życia obiektu. Konstruktor przydziela, destruktor zwalnia.

```cpp
struct File {
  FILE* f{};
  explicit File(const char* p) : f(std::fopen(p, "rb")) {}
  ~File() { if (f) std::fclose(f); }
};
```

**Zalecenie:** unikaj jawnego `new`/`delete` w nowym kodzie — patrz notatki o smart pointerach.
""",
    ),
    (
        "cpp-02-smart-pointers-overview",
        "C++: inteligentne wskaźniki — przegląd",
        ["cpp", "memory", "smart-pointers"],
        """# Inteligentne wskaźniki

- `std::unique_ptr` — wyłączna własność, zerowy narzut.
- `std::shared_ptr` — współdzielenie z licznikiem; **prefer** tylko gdy semantyka wymaga.
- `std::weak_ptr` — obserwacja cykli.

**Prefer** `make_unique` / `make_shared` zamiast surowych konstruktorów.
""",
    ),
    (
        "cpp-03-rule-of-three",
        "C++: reguła trzech (legacy)",
        ["cpp", "rule-of-three", "legacy"],
        """# Reguła trzech

Jeśli definiujesz jedno z: destruktor, konstruktor kopiujący, operator przypisania — rozważ wszystkie trzy.

W C++11+ często zastąpione przez regułę pięciu / zera z move semantics.
""",
    ),
    (
        "cpp-04-rule-of-five",
        "C++: reguła pięciu",
        ["cpp", "rule-of-five", "move"],
        """# Reguła pięciu

Dodaj do „trzech”: move constructor i move assignment, jeśli zarządzasz zasobem.

Alternatywa: **Rule of Zero** — użyj składowych zarządzających zasobem (np. `unique_ptr`).
""",
    ),
    (
        "cpp-05-rule-of-zero",
        "C++: reguła zera (preferowana)",
        ["cpp", "rule-of-zero", "style"],
        """# Rule of Zero

**Prefer** kompozycję typów std (kontenery, smart pointers) zamiast ręcznego zarządzania.

Mniej kodu, mniej błędów, łatwiejsze utrzymanie.
""",
    ),
    (
        "cpp-06-special-members-defaulted",
        "C++: = default dla składowych specjalnych",
        ["cpp", "default", "special-members"],
        """# = default

Jawnie zaznacz, że chcesz domyślnej semantyki:

```cpp
MyType(const MyType&) = default;
MyType& operator=(MyType&&) = default;
```

Ułatwia review i dokumentuje intencję.
""",
    ),
    (
        "cpp-07-move-semantics",
        "C++: semantyka przenoszenia",
        ["cpp", "move", "rvalue"],
        """# Move semantics

`std::move` to tylko cast do rvalue — nie „przenosi” magicznie bez typów move-ready.

Implementuj move ctor/assign gdy zasób można tanio przenieść (np. wskaźnik w `unique_ptr`).
""",
    ),
    (
        "cpp-08-unique-ptr-prefer",
        "C++: preferuj unique_ptr",
        ["cpp", "unique_ptr", "ownership"],
        """# unique_ptr jako domyślny wskaźnik właścicielski

**Prefer** `std::unique_ptr<T>` dla wyłącznej własności. Jest tanie i wyraźne.

```cpp
auto p = std::make_unique<Foo>(args...);
```

**Unikaj** `shared_ptr` jeśli nie potrzebujesz współdzielenia — narzut i ryzyko cykli.
""",
    ),
    (
        "cpp-09-shared-ptr-when",
        "C++: kiedy shared_ptr",
        ["cpp", "shared_ptr", "graphs"],
        """# shared_ptr

Używaj gdy obiekt musi żyć tak długo, jak ostatni użytkownik — grafy, cache współdzielony.

Pamiętaj o `weak_ptr` do łamania cykli.
""",
    ),
    (
        "cpp-10-avoid-raw-new",
        "C++: unikaj surowego new",
        ["cpp", "memory", "safety"],
        """# Unikaj surowego new/delete

**Avoid** `new`/`delete` w aplikacyjnym kodzie — stosuj factory (`make_unique`) i kontenery.

Wyjątki: niskopoziomowe API, interoperacyjność z C.
""",
    ),
    (
        "cpp-11-constexpr-basics",
        "C++: constexpr — podstawy",
        ["cpp", "constexpr", "compile-time"],
        """# constexpr

Pozwala wykonywać obliczenia w czasie kompilacji, ogranicza koszty runtime.

Od C++17/20/23 możliwości rosną — sprawdzaj standard docelowy projektu.
""",
    ),
    (
        "cpp-12-const-correctness",
        "C++: poprawność const",
        ["cpp", "const", "style"],
        """# const correctness

**Prefer** `const` dla parametrów referencyjnych i metod niezmieniających stanu.

Ułatwia równoległość i czytelność.
""",
    ),
    (
        "cpp-13-enum-class",
        "C++: enum class zamiast enum",
        ["cpp", "enum", "type-safety"],
        """# enum class

Silnie typowane enumeracje — brak niejawnych konwersji do int, osobne przestrzenie nazw.

```cpp
enum class Mode { Fast, Safe };
```
""",
    ),
    (
        "cpp-14-auto-guidelines",
        "C++: kiedy auto",
        ["cpp", "auto", "style"],
        """# auto

**Prefer** `auto` dla złożonych iteratorów i typów oczywistych z inicjalizacji.

**Unikaj** nadużywania tam, gdzie typ jest kontraktem API — czasem jawny typ jest czytelniejszy.
""",
    ),
    (
        "cpp-15-range-for",
        "C++: pętle for po zakresie",
        ["cpp", "ranges", "loops"],
        """# Range-for

```cpp
for (const auto& x : vec) { ... }
```

Używaj `const auto&` dla dużych typów, `auto&&` dla forwarding w szablonach.
""",
    ),
    (
        "cpp-16-stl-algorithms",
        "C++: algorytmy STL",
        ["cpp", "stl", "algorithms"],
        """# <algorithm>

**Prefer** `std::sort`, `std::find_if`, `std::transform` zamiast ręcznych pętli tam, gdzie to idiomatyczne.

Czytelność intencji i mniej off-by-one.
""",
    ),
    (
        "cpp-17-string-view",
        "C++: std::string_view",
        ["cpp", "string_view", "api"],
        """# string_view

Nie posiada danych — widok na zewnętrzny bufor. Idealne dla parametrów funkcji przyjmujących tekst.

**Never** zwracaj `string_view` do tymczasowego `std::string` utworzonego lokalnie.
""",
    ),
    (
        "cpp-18-raii-deep-dive",
        "C++ Idiom: RAII — głębsze wzorce",
        ["cpp", "raii", "mutex", "scope-guard"],
        """# RAII — więcej niż pliki

RAII dotyczy też mutexów (`std::lock_guard`, `unique_lock`), timerów, transakcji.

**Prefer** jeden poziom zasobu = jeden obiekt — łatwiejszy reasoning.

To rozwija temat z notatki o podstawach RAII — rozważ scalenie sekcji jeśli powielasz wstęp.
""",
    ),
    (
        "cpp-19-mutex-locking",
        "C++: blokady mutexów",
        ["cpp", "mutex", "concurrency"],
        """# Mutex

**Prefer** `std::scoped_lock` (C++17) dla wielu mutexów.

Unikaj ręcznego `lock`/`unlock` — użyj RAII lock guard.
""",
    ),
    (
        "cpp-20-atomics-basics",
        "C++: atomics — podstawy",
        ["cpp", "atomic", "concurrency"],
        """# std::atomic

Dla prostych liczników flag. Pamiętaj o modelu pamięci (`memory_order`).

Nie zastępuje mutexów przy złożonych invariantach struktur.
""",
    ),
    (
        "cpp-21-concepts-c20",
        "C++20: concepts — wstęp",
        ["cpp", "concepts", "templates"],
        """# Concepts

Ograniczenia na szablony z czytelnymi komunikatami błędów.

```cpp
template<std::integral T> T twice(T x) { return x + x; }
```
""",
    ),
    (
        "cpp-22-rule-of-zero-vs-five",
        "C++: Rule of Zero vs Five — decyzja",
        ["cpp", "rule-of-zero", "rule-of-five", "design"],
        """# Zero vs Five

**Prefer** Rule of Zero gdy możesz — kompozycja.

Rule of Five gdy musisz opakować niestandardowy zasób (surody deskryptory).

Nie duplikuj wyjaśnień z osobnych notatek o regule pięciu — linkuj.
""",
    ),
    (
        "cpp-23-pimpl-idiom",
        "C++: idiom PIMPL",
        ["cpp", "pimpl", "abi"],
        """# PIMPL

Redukuje czasy kompilacji i stabilizuje ABI — implementacja w `.cpp`.

Koszt: dodatkowy poziom pośrednictwa.
""",
    ),
    (
        "cpp-24-shared-ptr-first-anti",
        "C++: ostrożnie z domyślnym shared_ptr",
        ["cpp", "shared_ptr", "performance", "style"],
        """# shared_ptr nie jest domyślnym wyborem

W niektórych kodbases **prefer** zaczynać od `unique_ptr` i eskalować do `shared` tylko przy udokumentowanej potrzebie.

**Avoid** „domyślnie shared” — niepotrzebny narzut referencyjny.

*To może brzmieć inaczej niż notatki promujące shared dla grafów — rozróżnij kontekst.*
""",
    ),
    (
        "cpp-25-nrvo-rvo",
        "C++: NRVO / RVO",
        ["cpp", "rvo", "performance"],
        """# Return value optimization

Kompilator często eliminuje kopie przy zwrocie lokalnych obiektów.

Nie „optymalizuj na siłę” przez `std::move` na return lokalnego — może zablokować NRVO.
""",
    ),
    (
        "cpp-26-structured-bindings",
        "C++17: structured bindings",
        ["cpp", "structured-bindings", "tuple"],
        """# Structured bindings

```cpp
auto [a, b] = f();
```

Czytelniejsze niż `std::tie` w wielu przypadkach.
""",
    ),
    (
        "cpp-27-string-view-lifetime",
        "C++: string_view — ostrzeżenia (lifetime)",
        ["cpp", "string_view", "lifetime", "ub"],
        """# string_view — lifetime

**Never** trzymaj `string_view` dłużej niż żywot bufora źródłowego.

Łatwy do złamania invariant jeśli źródło to tymczasowy `std::string`.

Uzupełnia notatkę o `string_view` jako parametrze — tu fokus na **błędach czasu życia**.
""",
    ),
    (
        "cpp-28-optional",
        "C++: std::optional",
        ["cpp", "optional", "types"],
        """# optional

Reprezentuje brak wartości bez sentinel wartości magicznych.

**Prefer** zamiast wyjątków dla oczekiwanych „braków” w API parsującym.
""",
    ),
    (
        "cpp-29-variant",
        "C++: std::variant",
        ["cpp", "variant", "sum-types"],
        """# variant

Sum type z dyskryminacją — `std::visit` dla obsługi wariantów.

Unikaj rozległych łańcuchów `if` na indeksach — rozważ `visit`.
""",
    ),
    (
        "cpp-30-ranges-pipelines",
        "C++20: ranges i pipeliness",
        ["cpp", "ranges", "views"],
        """# ranges

Składanie transformacji lazy — czytelne pipeline’y na kontenerach.

Sprawdź dostępność w toolchainie — wymaga C++20.
""",
    ),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for slug, title, tags, body in NOTES:
        if slug in seen:
            raise SystemExit(f"duplicate slug: {slug}")
        seen.add(slug)
        fm = "\n".join(
            [
                "---",
                f"id: {slug}",
                "type: permanent-note",
                "domain: engineering",
                "language: pl",
                f"title: {title}",
                f"topics: [{', '.join(tags)}]",
                "status: active",
                "confidence: 0.9",
                "---",
                "",
            ]
        )
        path = OUT / f"{slug}.md"
        path.write_text(fm + body.strip() + "\n", encoding="utf-8")
        print(path)
    print(f"Wrote {len(NOTES)} files under {OUT}")


if __name__ == "__main__":
    main()
