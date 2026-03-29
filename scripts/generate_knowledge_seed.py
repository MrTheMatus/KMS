#!/usr/bin/env python3
"""Generate permanent-note seeds under example-vault/00_Inbox/seed/ (HITL inbox first).

Run from repo root: python scripts/generate_knowledge_seed.py

Notes have status inbox and type permanent-note so scan_inbox → review-queue → apply
can promote them to 30_Permanent-Notes.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "example-vault" / "00_Inbox" / "seed"

# (subdir, slug, title, topics[], body)
NOTES: list[tuple[str, str, str, list[str], str]] = [
    # ── principles ──
    ("principles", "heurystyki-inzynierskie", "Heurystyki inżynierskie", ["principles", "heuristics"],
     """# Heurystyki inżynierskie

## Zasada
Dobre decyzje inżynierskie opierają się na powtarzalnych heurystykach, nie na intuicji ad hoc.
Przykłady: KISS, YAGNI, Zasada Najmniejszego Zaskoczenia, Fail Fast.

## Kiedy stosować
Przy każdej decyzji projektowej — najpierw sprawdź, czy istnieje znana heurystyka.

## Trade-offy
Heurystyki upraszczają, ale mogą prowadzić do cargo-cultu gdy stosowane bezkrytycznie.

## Powiązane
- [[principles/podejmowanie-decyzji]]
- [[principles/prostota-vs-overengineering]]
"""),

    ("principles", "podejmowanie-decyzji", "Podejmowanie decyzji technicznych", ["principles", "decisions"],
     """# Podejmowanie decyzji technicznych

## Zasada
Decyzja odwracalna → podejmij szybko. Decyzja nieodwracalna → zbierz dane, prototypuj, dokumentuj.
Zapisuj decyzje (ADR) — przyszły Ty podziękuje.

## Kiedy stosować
Architektura, wybór technologii, granice modułów, API publiczne.

## Trade-offy
Za dużo analizy → paraliż. Za mało → costly rework.
"""),

    ("principles", "prostota-vs-overengineering", "Prostota vs overengineering", ["principles", "simplicity", "yagni"],
     """# Prostota vs overengineering

## Zasada
Kod powinien rozwiązywać dzisiejszy problem, nie jutrzejszy hipotetyczny.
Overengineering objawia się: warstwami abstrakcji bez konsumentów, interfejsami z jedną implementacją,
configami na rzeczy, które nigdy się nie zmienią.

## Kiedy stosować
Review kodu, planowanie sprintu, design doc.

## Trade-offy
Za prosta implementacja może wymagać refaktoru. Za złożona — nikt jej nie zrozumie.
"""),

    ("principles", "debugging-mindset", "Mentalność debugowania", ["principles", "debugging", "mindset"],
     """# Mentalność debugowania

## Zasada
Bug to informacja, nie porażka. Systematyczne podejście (hipoteza → test → zawężenie) bije "wpatrywanie się w kod".

## Kiedy stosować
Każdy bug — szczególnie te, które "nie powinny się zdarzyć".

## Trade-offy
Dyscyplina kosztuje czas na początku, oszczędza dni na końcu.

## Powiązane
- [[debugging/techniques/binary-search-debugging]]
- [[debugging/techniques/root-cause-analysis]]
"""),

    ("principles", "dokumentowanie-wiedzy", "Dokumentowanie wiedzy", ["principles", "documentation", "knowledge"],
     """# Dokumentowanie wiedzy

## Zasada
Wiedza w głowie jednej osoby to ryzyko projektowe. Minimum: ADR, komentarze "dlaczego" (nie "co"),
README z onboardingiem, runbook operacyjny.

## Kiedy stosować
Przy każdej decyzji, trudnym bugu, niestandardowym workaroundzie.

## Trade-offy
Dokumentacja starzeje się — trzeba ją pielęgnować. Ale brak dokumentacji starzeje się jeszcze szybciej.
"""),

    # ── cpp/memory ──
    ("cpp/memory", "raii", "C++: RAII — zarządzanie zasobami", ["cpp", "raii", "resource"],
     """# RAII — Resource Acquisition Is Initialization

## Zasada
Czas życia zasobu = czas życia obiektu. Konstruktor przydziela, destruktor zwalnia.

```cpp
struct File {
  FILE* f{};
  explicit File(const char* p) : f(std::fopen(p, "rb")) {}
  ~File() { if (f) std::fclose(f); }
};
```

## Kiedy stosować
Pliki, sockety, mutexy, pamięć, transakcje, handle systemowe.

## Trade-offy
Wymaga dyscypliny przy kopiowaniu/przenoszeniu (Rule of 5/0).
"""),

    ("cpp/memory", "rule-of-3-5-0", "C++: Rule of 3/5/0", ["cpp", "rule-of-zero", "rule-of-five", "special-members"],
     """# Rule of 3/5/0

## Zasada
- **Rule of 3** (C++98): definiujesz destruktor → definiuj też copy ctor i copy assign.
- **Rule of 5** (C++11): dodaj move ctor i move assign.
- **Rule of 0** (preferowane): nie definiuj żadnych — użyj `unique_ptr`, kontenerów.

## Kiedy stosować
Zawsze gdy klasa zarządza zasobem. Preferuj Rule of 0.

## Trade-offy
Rule of 0 wymaga, by wszystkie składowe same się sprzątały.
"""),

    ("cpp/memory", "stack-vs-heap", "C++: stos vs sterta", ["cpp", "memory", "stack", "heap", "allocation"],
     """# Stos vs sterta

## Zasada
Stos: szybki (O(1)), automatyczne sprzątanie, ograniczony rozmiar (~1-8 MB).
Sterta: wolniejszy (`malloc`/`new`), wymaga zarządzania, nieograniczony.

## Kiedy stosować
Domyślnie stos. Sterta gdy: duży obiekt, czas życia > scope, polimorfizm przez wskaźnik.

## Trade-offy
Fragmentacja sterty, cache misses, koszt alokatora.
"""),

    ("cpp/memory", "move-vs-copy", "C++: move vs copy semantics", ["cpp", "move", "copy", "rvalue"],
     """# Move vs copy

## Zasada
Copy = duplikuj dane. Move = „kradnij" wewnętrzne zasoby (zeruj źródło).
`std::move` to tylko cast do rvalue — nie przenosi sam w sobie.

## Kiedy stosować
Move: zwracanie lokalnych obiektów, wstawianie do kontenerów, transfer ownership.

## Trade-offy
Po move obiekt jest w "valid but unspecified state" — nie używaj go bez ponownej inicjalizacji.
"""),

    ("cpp/memory", "smart-pointers", "C++: smart pointers — przewodnik", ["cpp", "unique_ptr", "shared_ptr", "weak_ptr"],
     """# Smart pointers

## Zasada
- `unique_ptr` — wyłączna własność, zerowy narzut. **Domyślny wybór.**
- `shared_ptr` — współdzielenie z ref-count. Tylko gdy semantyka wymaga.
- `weak_ptr` — obserwacja bez wydłużania życia (łamanie cykli).

## Kiedy stosować
Zamiast surowego `new`/`delete`. `make_unique`/`make_shared` jako factory.

## Trade-offy
`shared_ptr`: narzut atomowego ref-count, ryzyko cykli bez `weak_ptr`.
"""),

    # ── cpp/stl ──
    ("cpp/stl", "vector-vs-list", "C++: vector vs list", ["cpp", "stl", "vector", "list", "cache"],
     """# vector vs list

## Zasada
`std::vector` prawie zawsze wygrywa dzięki cache locality. `std::list` sensowna tylko
przy częstym wstawianiu/usuwaniu w środku BEZ iteracji po elementach.

## Kiedy stosować
Domyślnie `vector`. `list`/`deque` tylko z pomiarem.

## Trade-offy
`vector::insert` w środku jest O(n) ale z niskim stałym kosztem (memcpy, cache-friendly).
"""),

    ("cpp/stl", "unordered-map-vs-map", "C++: unordered_map vs map", ["cpp", "stl", "map", "hash"],
     """# unordered_map vs map

## Zasada
`unordered_map`: O(1) average lookup (hash). `map`: O(log n) (drzewo, posortowane klucze).

## Kiedy stosować
Domyślnie `unordered_map` dla lookupu. `map` gdy potrzebujesz porządku kluczy lub iteracji zakresowej.

## Trade-offy
Hash: gorszy worst-case, więcej pamięci, potrzebna dobra funkcja hashująca.
"""),

    ("cpp/stl", "emplace-vs-push", "C++: emplace vs push_back", ["cpp", "stl", "emplace", "construction"],
     """# emplace vs push_back

## Zasada
`emplace_back(args...)` konstruuje in-place. `push_back(obj)` kopiuje/przenosi gotowy obiekt.

## Kiedy stosować
`emplace_back` gdy konstruujesz nowy element. `push_back` gdy masz gotowy obiekt do wstawienia.

## Trade-offy
`emplace` z niejawnymi konwersjami może maskować błędy kompilacji.
"""),

    ("cpp/stl", "string-handling", "C++: obsługa stringów", ["cpp", "string", "string_view", "sso"],
     """# Obsługa stringów

## Zasada
- `std::string` — posiada dane, SSO dla krótkich.
- `std::string_view` — widok, nie posiada. Idealny jako parametr funkcji.
- **Nigdy** nie zwracaj `string_view` do tymczasowego `string`.

## Kiedy stosować
Parametry read-only: `string_view`. Przechowywanie: `string`.

## Trade-offy
`string_view` + lifetime mismatch = dangling reference (UB).
"""),

    # ── cpp/concurrency ──
    ("cpp/concurrency", "mutex-vs-atomics", "C++: mutex vs atomics", ["cpp", "concurrency", "mutex", "atomic"],
     """# mutex vs atomics

## Zasada
`std::atomic<T>` — proste flagi, liczniki. Mutex (`scoped_lock`) — złożone invarianty struktury.

## Kiedy stosować
Atomic: izolowane wartości, CAS. Mutex: wielopolowe invarianty, sekcja krytyczna.

## Trade-offy
Atomic: szybszy ale ograniczony do trywialnych operacji. Mutex: wolniejszy, ale uniwersalny.
"""),

    ("cpp/concurrency", "producer-consumer", "C++: producent-konsument", ["cpp", "concurrency", "pattern", "queue"],
     """# Producent-konsument

## Zasada
Wątek producenta wrzuca do kolejki, konsument pobiera. Synchronizacja: mutex + condition_variable
lub lock-free queue.

## Kiedy stosować
Pipeline przetwarzania, I/O → CPU, sensor → analiza.

## Trade-offy
Sizing kolejki, backpressure, co robić gdy konsument nie nadąża.
"""),

    ("cpp/concurrency", "condition-variable", "C++: condition_variable", ["cpp", "concurrency", "cv", "synchronization"],
     """# condition_variable

## Zasada
Czekaj na warunek bez busy-wait. Zawsze z mutexem i pętlą `while(!pred)` (spurious wakeup).

```cpp
std::unique_lock lk(mtx);
cv.wait(lk, [&]{ return !queue.empty(); });
```

## Trade-offy
Spurious wakeup wymaga predykatu. Lost notification przy braku locka.
"""),

    ("cpp/concurrency", "false-sharing", "C++: false sharing", ["cpp", "concurrency", "cache", "performance"],
     """# False sharing

## Zasada
Dwa wątki modyfikują różne zmienne w tej samej linii cache → wymuszony transfer linii między rdzeniami.

## Kiedy stosować
Diagnostyka: `perf stat` / `perf c2c`. Rozwiązanie: `alignas(64)` padding.

## Trade-offy
Padding zużywa pamięć. Mierz przed optymalizacją.
"""),

    ("cpp/concurrency", "thread-safety", "C++: bezpieczeństwo wątkowe", ["cpp", "concurrency", "thread-safety"],
     """# Bezpieczeństwo wątkowe

## Zasada
Funkcja jest thread-safe jeśli poprawnie działa przy równoczesnym wywołaniu z wielu wątków.
Poziomy: immutable > thread-safe > conditionally safe > unsafe.

## Kiedy stosować
Dokumentuj poziom bezpieczeństwa każdego API. Domyślnie zakładaj "unsafe".

## Trade-offy
Thread-safety kosztuje (locki, atomiki, immutability). Nie rób thread-safe na zapas.
"""),

    # ── cpp/idioms ──
    ("cpp/idioms", "value-semantics", "C++: semantyka wartości", ["cpp", "value-semantics", "design"],
     """# Semantyka wartości

## Zasada
Obiekty zachowują się jak inty — kopiowanie tworzy niezależną kopię, porównanie po wartości.

## Kiedy stosować
Małe typy danych, struktury matematyczne, konfiguracje. Domyślne podejście w C++.

## Trade-offy
Kopiowanie dużych obiektów kosztowne — wtedy move semantics lub referencje.
"""),

    ("cpp/idioms", "ownership", "C++: model ownership", ["cpp", "ownership", "design", "lifetime"],
     """# Model ownership

## Zasada
Każdy zasób ma dokładnie jednego właściciela. Transfer = move. Współdzielenie = `shared_ptr` (jawne).

## Kiedy stosować
Projektowanie API, konstruktorów, interfejsów fabrycznych.

## Trade-offy
Strict ownership wymaga planowania grafu życia obiektów na etapie designu.
"""),

    ("cpp/idioms", "const-correctness", "C++: poprawność const", ["cpp", "const", "api"],
     """# Poprawność const

## Zasada
Oznaczaj `const` wszystko co nie musi się zmieniać: parametry, metody, zmienne lokalne.

## Kiedy stosować
Zawsze. To dokumentacja intencji i umożliwia optymalizacje kompilatora.

## Trade-offy
`const_cast` to code smell — jeśli musisz go używać, API jest źle zaprojektowane.
"""),

    ("cpp/idioms", "error-handling", "C++: obsługa błędów", ["cpp", "errors", "exceptions", "expected"],
     """# Obsługa błędów

## Zasada
- Wyjątki: błędy nieoczekiwane, które przerywają normalny flow.
- Kody / `std::expected` (C++23) / `std::optional`: oczekiwane braki wartości.
- **Nigdy** nie ignoruj błędów cicho.

## Kiedy stosować
Wyjątki w logice biznesowej. Kody/expected w hot path (brak narzutu przy braku błędu? — zależy od impl).

## Trade-offy
Wyjątki: zerowy narzut na happy path, kosztowny throw. Expected: jawność, ale boilerplate.
"""),

    # ── cpp/pitfalls ──
    ("cpp/pitfalls", "undefined-behavior", "C++: undefined behavior", ["cpp", "ub", "safety"],
     """# Undefined behavior

## Zasada
UB = kompilator może zrobić cokolwiek. Najczęstsze: null deref, out-of-bounds, data race, signed overflow.

## Kiedy stosować
Sanitizers (`-fsanitize=address,undefined`) w CI. Code review: szukaj surowych pointerów i castów.

## Trade-offy
Sanitizers spowalniają runtime 2-5x — włączaj w testach, nie w produkcji.
"""),

    ("cpp/pitfalls", "dangling-reference", "C++: dangling reference", ["cpp", "lifetime", "reference", "ub"],
     """# Dangling reference

## Zasada
Referencja/wskaźnik do obiektu, który już nie istnieje. Najczęstszy powód: zwracanie referencji do lokala,
`string_view` do tymczasowego `string`, iterator po modyfikacji kontenera.

## Kiedy stosować
Code review, sanitizers, `-Wdangling-gsl`.
"""),

    ("cpp/pitfalls", "lifetime-bugs", "C++: błędy czasu życia", ["cpp", "lifetime", "scope", "destruction"],
     """# Błędy czasu życia

## Zasada
Obiekt jest niszczony w odwrotnej kolejności do tworzenia (w scope). Lambda capture by reference
do zmiennej, która wychodzi z scope → dangling.

## Kiedy stosować
Async callbacks, coroutines, lambdy przechowywane poza scope.

## Trade-offy
Capture by value (kopia) jest bezpieczniejsze ale droższe.
"""),

    ("cpp/pitfalls", "premature-optimization", "C++: przedwczesna optymalizacja", ["cpp", "performance", "principles"],
     """# Przedwczesna optymalizacja

## Zasada
„Premature optimization is the root of all evil" (Knuth). Najpierw poprawność, potem profiling, potem optymalizacja.

## Kiedy stosować
Zawsze pytaj: „Czy zmierzyłem?" przed refaktorem wydajnościowym.

## Trade-offy
Opóźnianie optymalizacji architekturalnej (layout danych) jest kosztowniejsze niż opóźnianie mikro-optymalizacji.
"""),

    # ── system-design/patterns ──
    ("system-design/patterns", "factory", "Wzorzec: Factory", ["design-patterns", "factory", "creation"],
     """# Factory

## Zasada
Oddziel tworzenie obiektu od jego użycia. Factory method / abstract factory / builder.

## Kiedy stosować
Wiele wariantów obiektu, konfiguracja runtime, ukrywanie szczegółów konstrukcji.

## Trade-offy
Dodatkowa warstwa abstrakcji. Nie używaj dla prostych obiektów.
"""),

    ("system-design/patterns", "observer", "Wzorzec: Observer / Event", ["design-patterns", "observer", "events"],
     """# Observer / Event

## Zasada
Subskrybenci rejestrują się na zdarzenia. Publisher nie zna subskrybentów bezpośrednio.

## Kiedy stosować
UI, systemy reaktywne, luźne sprzężenie modułów.

## Trade-offy
Trudność debugowania (kto nasłuchuje?), ryzyko memory leak przy braku unsubscribe.
"""),

    ("system-design/patterns", "pipeline", "Wzorzec: Pipeline / Chain", ["design-patterns", "pipeline", "composition"],
     """# Pipeline / Chain

## Zasada
Dane przepływają przez sekwencję etapów (filtr → transform → output). Każdy etap jest niezależny.

## Kiedy stosować
ETL, przetwarzanie sygnałów, compilery, CI/CD.

## Trade-offy
Latency rośnie z liczbą etapów. Backpressure wymaga osobnego mechanizmu.
"""),

    ("system-design/patterns", "producer-consumer-pattern", "Wzorzec: Producer-Consumer (system)", ["design-patterns", "producer-consumer", "queue"],
     """# Producer-Consumer (poziom systemu)

## Zasada
Komponenty komunikują się przez kolejkę. Producent nie czeka na konsumenta (asynchroniczność).

## Kiedy stosować
Mikroserwisy, pipeline I/O, bufory sensorów.

## Trade-offy
Kolejka = dodatkowa pamięć + latency. Trzeba obsłużyć overflow (drop, backpressure, resize).
"""),

    # ── system-design/tradeoffs ──
    ("system-design/tradeoffs", "polling-vs-event-driven", "Polling vs event-driven", ["design", "polling", "events", "tradeoffs"],
     """# Polling vs event-driven

## Zasada
Polling: prostsze, przewidywalne latency, marnuje CPU. Event-driven: efektywne, ale złożoność sterowania.

## Kiedy stosować
Polling: niski throughput, proste systemy. Events: wysoki throughput, I/O-bound.

## Trade-offy
Event-driven: callback hell, trudniejsze debugowanie, edge-triggered vs level-triggered.
"""),

    ("system-design/tradeoffs", "sync-vs-async", "Sync vs async", ["design", "sync", "async", "tradeoffs"],
     """# Sync vs async

## Zasada
Sync: łatwy reasoning, blokuje wątek. Async: skalowalność, złożoność.

## Kiedy stosować
Sync domyślnie. Async gdy I/O-bound i wiele jednoczesnych operacji.

## Trade-offy
Async wymaga event loop / coroutines / futures — debugowanie trudniejsze.
"""),

    ("system-design/tradeoffs", "monolith-vs-modules", "Monolit vs moduły", ["design", "monolith", "modules", "architecture"],
     """# Monolit vs moduły

## Zasada
Monolit z dobrymi granicami modułów > rozbity mikroserwisowo monolit z bad boundaries.

## Kiedy stosować
Start od monolitu. Wydzielaj serwis gdy: osobny zespół, osobny scaling, osobny deploy.

## Trade-offy
Mikroserwisy: narzut sieciowy, distributed debugging, eventual consistency.
"""),

    ("system-design/tradeoffs", "simplicity-vs-flexibility", "Prostota vs elastyczność", ["design", "simplicity", "flexibility"],
     """# Prostota vs elastyczność

## Zasada
Elastyczność ma koszt: więcej kodu, więcej testów, więcej opcji do zrozumienia.

## Kiedy stosować
Zawsze pytaj: „Ile wariantów będzie w praktyce?" Jeśli 1-2 → hardcode/enum. Jeśli N → plugin/config.

## Trade-offy
Za mała elastyczność → fork. Za duża → nikt nie rozumie systemu.
"""),

    # ── system-design/communication ──
    ("system-design/communication", "queues", "Kolejki w komunikacji", ["design", "queues", "messaging"],
     """# Kolejki

## Zasada
Bufor między producentem a konsumentem. FIFO, priorytetowe, bounded/unbounded.

## Kiedy stosować
Decoupling tempa produkcji i konsumpcji. Cross-thread, cross-process, cross-service.

## Trade-offy
Bounded: backpressure. Unbounded: ryzyko OOM. Persistent: latency.
"""),

    ("system-design/communication", "inter-thread-comm", "Komunikacja między wątkami", ["design", "concurrency", "ipc"],
     """# Komunikacja między wątkami

## Zasada
Shared memory + mutex (C++), message passing (channels), lock-free structures.

## Kiedy stosować
Shared memory: niski latency. Message passing: prostsze reasoning.

## Trade-offy
Shared memory: data races. Message passing: narzut kopiowania, latency queue.
"""),

    ("system-design/communication", "backpressure", "Backpressure", ["design", "backpressure", "flow-control"],
     """# Backpressure

## Zasada
Gdy konsument nie nadąża za producentem: zwolnij producenta (backpressure), dropuj wiadomości, lub buforuj.

## Kiedy stosować
Pipeline danych, streaming, I/O, sensory.

## Trade-offy
Drop: utrata danych. Buffer: pamięć. Slow-down: propagacja latency w górę.
"""),

    # ── system-design/reliability ──
    ("system-design/reliability", "failure-modes", "Tryby awarii", ["reliability", "failure", "design"],
     """# Tryby awarii

## Zasada
Każdy komponent może zawieść. Projektuj z myślą o: partial failure, timeout, crash, corrupt data.

## Kiedy stosować
Projektowanie każdego systemu — pytaj: „Co się stanie jak X padnie?"

## Trade-offy
Obsługa awarii zwiększa złożoność. Ale brak obsługi → kaskadowe awarie.
"""),

    ("system-design/reliability", "retries-timeouts", "Retries i timeouty", ["reliability", "retries", "timeouts"],
     """# Retries i timeouty

## Zasada
Timeout: nie czekaj w nieskończoność. Retry: z exponential backoff i jitter.

## Kiedy stosować
Każde wywołanie sieciowe, I/O, zewnętrzne API.

## Trade-offy
Retry storm: wszyscy retryują naraz → przeciążenie. Max retries + circuit breaker.
"""),

    ("system-design/reliability", "observability", "Obserwowalność", ["reliability", "logging", "metrics", "tracing"],
     """# Obserwowalność

## Zasada
Trzy filary: logi (co się stało), metryki (ile), tracing (jak przepływa request).

## Kiedy stosować
Od dnia pierwszego. Trudno dodać retrospektywnie.

## Trade-offy
Narzut na throughput i storage. Ale: „nie możesz naprawić tego, czego nie widzisz."
"""),

    # ── performance/profiling ──
    ("performance/profiling", "perf-basics", "Podstawy profilowania", ["performance", "profiling", "measurement"],
     """# Podstawy profilowania

## Zasada
Mierz, nie zgaduj. Profiler (perf, VTune, Instruments) wskazuje hotspoty — optymalizuj tam.

## Kiedy stosować
Przed każdą optymalizacją wydajnościową.

## Trade-offy
Profiler zmienia timing (observer effect). Sampling vs instrumentation.
"""),

    ("performance/profiling", "benchmark-rules", "Zasady benchmarkowania", ["performance", "benchmark", "methodology"],
     """# Zasady benchmarkowania

## Zasada
1. Izoluj mierzony kod. 2. Warmup. 3. Wiele iteracji. 4. Statystyki (mediana, p99).
5. Nie optymalizuj pod benchmark, optymalizuj pod production workload.

## Trade-offy
Mikrobenchmark ≠ system benchmark. Cache cold vs warm.
"""),

    ("performance/profiling", "flamegraph", "Flamegraph — wizualizacja", ["performance", "flamegraph", "perf"],
     """# Flamegraph

## Zasada
Wizualizacja stosu wywołań z próbkowania. Szerokość = czas CPU. Czytaj od dołu (main) w górę.

## Kiedy stosować
Identyfikacja hotspotów CPU. `perf record` + `FlameGraph` (Brendan Gregg).

## Trade-offy
Nie pokazuje wall-clock time (I/O). Do tego: off-CPU flamegraph.
"""),

    # ── performance/latency ──
    ("performance/latency", "latency-sources", "Źródła latency", ["performance", "latency"],
     """# Źródła latency

## Zasada
Latency = suma: CPU compute + cache miss + memory access + I/O + syscall + network + scheduling.
Mierz E2E i rozbijaj na komponenty.

## Kiedy stosować
Diagnostyka „dlaczego wolne" — zacznij od top-down (E2E), nie bottom-up.
"""),

    ("performance/latency", "syscall-cost", "Koszt syscalli", ["performance", "syscall", "kernel"],
     """# Koszt syscalli

## Zasada
Każdy syscall to context switch user↔kernel. Batch operacje (sendmsg, writev, io_uring).

## Kiedy stosować
Hot path I/O: minimalizuj liczbę syscalli na operację.

## Trade-offy
io_uring: wydajny ale złożony API. epoll: prostszy, mniej throughput.
"""),

    ("performance/latency", "lock-contention", "Lock contention", ["performance", "concurrency", "locks"],
     """# Lock contention

## Zasada
Wiele wątków czeka na ten sam lock → serialization. Rozwiązania: mniejsze sekcje krytyczne,
sharding (per-thread/per-shard lock), lock-free, MVCC.

## Kiedy stosować
Profiler pokazuje czas w `__lll_lock_wait` / `futex`.

## Trade-offy
Lock-free: poprawność trudna do udowodnienia. Sharding: złożoność agregacji.
"""),

    ("performance/latency", "allocation-cost", "Koszt alokacji pamięci", ["performance", "memory", "allocator"],
     """# Koszt alokacji

## Zasada
`malloc` / `new` → syscall (brk/mmap) przy braku wolnych bloków. Arena / pool allocator dla hot path.

## Kiedy stosować
Profiler wskazuje `malloc` w top hotspots. Wiele małych obiektów tworzonych i niszczonych.

## Trade-offy
Custom allocator: szybszy, ale trudniejszy w debugowaniu i mniej portable.
"""),

    # ── performance/cache ──
    ("performance/cache", "cache-locality", "Cache locality", ["performance", "cache", "data-oriented"],
     """# Cache locality

## Zasada
CPU cache ładuje linie (64B). Sekwencyjny dostęp (array) >> losowy (linked list, hash map z pointerami).

## Kiedy stosować
Data-oriented design: Structure of Arrays > Array of Structures dla hot-path iteration.

## Trade-offy
SoA trudniejszy w utrzymaniu kodu. AoS wygodniejszy ergonomicznie.
"""),

    ("performance/cache", "memory-layout", "Układ danych w pamięci", ["performance", "cache", "layout", "struct"],
     """# Układ danych

## Zasada
Kompilator padduje struktury do alignment. Kolejność pól wpływa na rozmiar. Używaj `-Wpadded`.

## Kiedy stosować
Struktury w kontenerach na hot path. Sizeof matters × millions.

## Trade-offy
Ręczne pakowanie (`__attribute__((packed))`) → wolniejszy dostęp na niektórych architekturach.
"""),

    ("performance/cache", "padding-alignment", "Padding i alignment", ["performance", "alignment", "cacheline"],
     """# Padding i alignment

## Zasada
`alignas(N)` wymusza wyrównanie. `alignas(64)` = osobna linia cache (false sharing fix).

## Kiedy stosować
Współdzielone zmienne atomowe, per-thread countery, hot fields.

## Trade-offy
Zużycie pamięci rośnie. Nie rób bez pomiaru.
"""),

    # ── sql ──
    ("sql", "join-patterns", "SQL: wzorce JOIN", ["sql", "join", "queries"],
     """# Wzorce JOIN

## Zasada
INNER: tylko dopasowane. LEFT: wszystkie z lewej + dopasowane z prawej. CROSS: iloczyn kartezjański.

## Kiedy stosować
LEFT JOIN dla „pokaż nawet gdy brak dopasowania". INNER JOIN domyślnie.

## Trade-offy
LEFT JOIN bez filtra na prawej tabeli może zwrócić dużo NULL-i.
"""),

    ("sql", "indexes", "SQL: indeksy", ["sql", "index", "performance"],
     """# Indeksy

## Zasada
B-tree (domyślne): dobry dla range query i equality. Hash: tylko equality.
Composite index: kolejność kolumn ma znaczenie (leftmost prefix).

## Kiedy stosować
Kolumny w WHERE, JOIN ON, ORDER BY. Nie indeksuj wszystkiego — koszt INSERT/UPDATE.

## Trade-offy
Indeks = dodatkowe I/O przy zapisie + dodatkowe miejsce na dysku.
"""),

    ("sql", "explain-plan", "SQL: EXPLAIN i query tuning", ["sql", "explain", "optimization"],
     """# EXPLAIN

## Zasada
`EXPLAIN QUERY PLAN` (SQLite), `EXPLAIN ANALYZE` (Postgres). Sprawdź: sequential scan vs index scan,
estymowane vs rzeczywiste wiersze, sort in memory vs on disk.

## Kiedy stosować
Wolne zapytanie → EXPLAIN zanim zmieniasz logikę.
"""),

    ("sql", "sqlite-gotchas", "SQLite: pułapki i specyfika", ["sql", "sqlite", "gotchas"],
     """# SQLite: pułapki

## Zasada
- Jeden pisarz naraz (WAL mode pomaga).
- `PRAGMA foreign_keys = ON` trzeba włączyć per-connection.
- Typy luźne (type affinity, nie strict typing — chyba że `STRICT` table).

## Kiedy stosować
Zawsze gdy pracujesz z SQLite — te pułapki kąsają prędzej czy później.
"""),

    # ── debugging/techniques ──
    ("debugging/techniques", "binary-search-debugging", "Debugowanie bisekcją", ["debugging", "bisect", "technique"],
     """# Debugowanie bisekcją

## Zasada
Zawęź problem o połowę na każdym kroku: komentuj połowę kodu, git bisect, printf w środku pipeline.

## Kiedy stosować
Bug, którego przyczyny nie widać „na pierwszy rzut oka". Duży codebase.

## Trade-offy
Wymaga reprodukowalnego bugu. Losowe / timing-dependent bugi uciekają bisekcji.
"""),

    ("debugging/techniques", "logging-strategy", "Strategia logowania", ["debugging", "logging", "observability"],
     """# Strategia logowania

## Zasada
Loguj: wejście (request/input), decyzje (branch taken), wyjście (response/result), błędy (z kontekstem).
Nie loguj: haseł, PII, binarnych danych.

## Kiedy stosować
Od początku projektu. Poziomy: ERROR > WARN > INFO > DEBUG.

## Trade-offy
Za dużo logów = szum. Za mało = ślepota przy incydencie.
"""),

    ("debugging/techniques", "root-cause-analysis", "Root cause analysis", ["debugging", "rca", "postmortem"],
     """# Root cause analysis

## Zasada
„5 Why": pytaj „dlaczego?" aż dojdziesz do przyczyny systemowej, nie objawu.

## Kiedy stosować
Po każdym poważnym incydencie / trudnym bugu.

## Trade-offy
Nadgorliwe 5-why prowadzi do absurdu („dlaczego istnieje ten projekt?"). Zatrzymaj się na actionable level.
"""),

    ("debugging/techniques", "repro-strategy", "Strategia reprodukcji buga", ["debugging", "repro", "methodology"],
     """# Strategia reprodukcji

## Zasada
Bug bez repro = bug nienaprawiony. Minimum: dokładne kroki, środowisko, dane wejściowe.
Automate repro w teście zanim zaczniesz naprawiać.

## Kiedy stosować
Każdy bug report.
"""),

    # ── debugging/case-studies ──
    ("debugging/case-studies", "race-condition-case", "Case study: race condition", ["debugging", "concurrency", "case-study"],
     """# Case study: race condition

## Kontekst
Cykliczne joby odpalane co 5 minut generowały nakładające się transakcje.
Objaw: dane losowo niekompletne. Debugowanie: śledzenie po thread ID w logach, wyodrębnianie w notatniku.

## Lekcja
1. Logi z thread ID od początku.
2. grep/awk po PID/TID > ręczne kopiowanie.
3. Serializable poziom izolacji lub jawna kolejka zamiast równoległych jobów.

## Powiązane
- [[cpp/concurrency/mutex-vs-atomics]]
- [[debugging/techniques/logging-strategy]]
"""),

    ("debugging/case-studies", "missing-field-mapping", "Case study: brakujące pole w mapperze", ["debugging", "mapping", "case-study"],
     """# Case study: brakujące pole w mapperze

## Kontekst
Ręczny mapper (zamiast MapStruct) pominął 1 z 30 pól. Efekt: dane traciły jedno pole przy GET.
Odkrycie: pola audytowe (metoda + timestamp) w bazie wskazały, kto ostatnio modyfikował rekord.

## Lekcja
1. Automatyczne mappery z `unmappedTargetPolicy = ERROR`.
2. Pola audytowe w bazie (kto, kiedy, jaka metoda) — tanie a ratują debugging.
3. Testy z pełnym porównaniem obiektów (assertj `isEqualTo` nie `hasFieldOrPropertyWithValue`).
"""),

    ("debugging/case-studies", "reflection-debug-nightmare", "Case study: debugowanie kodu z refleksją", ["debugging", "java", "reflection", "case-study"],
     """# Case study: debugowanie z refleksją

## Kontekst
Spring @Autowired / AOP + custom adnotacje oparte na refleksji. Kod zachowywał się inaczej niż sugerował źródłowy plik
bo aspekty zmieniały behavior w runtime. Stack trace prowadził do proxy, nie do realnej implementacji.

## Lekcja
1. Znaj system i jego aspekty zanim debugujesz — nie polegaj tylko na kodzie źródłowym.
2. Loguj obficie instancje i typy runtime (`getClass().getName()`).
3. W C++ analogia: vtable dispatch — ale przynajmniej widzisz deklarację virtual.
"""),

    # ── domain/control-systems ──
    ("domain/control-systems", "pid-basics", "PID — podstawy regulacji", ["control", "pid", "feedback"],
     """# PID — podstawy

## Zasada
P = proporcjonalny (reaguj na błąd), I = całkujący (eliminuj stały offset), D = różniczkujący (tłum oscylacje).

## Kiedy stosować
Regulacja temperatury, pozycji, przepływu, prędkości — procesy z opóźnieniem i inercją.

## Trade-offy
Zbyt agresywne P → oscylacje. Zbyt duże I → windup. D → wzmacnia szum.
"""),

    ("domain/control-systems", "feedback-loops", "Pętle sprzężenia zwrotnego", ["control", "feedback", "systems"],
     """# Pętle sprzężenia zwrotnego

## Zasada
Negatywne sprzężenie zwrotne → stabilizacja (termostat). Pozytywne → eskalacja (mikrofon + głośnik).

## Kiedy stosować
Każdy system regulacji. Ale też: alerty → interwencja → poprawa (operations feedback loop).

## Trade-offy
Opóźnienie w pętli (dead time) → niestabilność. Im szybszy pomiar, tym lepsza regulacja.
"""),

    ("domain/control-systems", "stability", "Stabilność systemów", ["control", "stability", "margins"],
     """# Stabilność

## Zasada
System jest stabilny jeśli po zaburzeniu wraca do stanu ustalonego. Miary: margines fazy, margines wzmocnienia.

## Kiedy stosować
Projektowanie regulatora, tuning PID, analiza nowych instalacji.

## Trade-offy
Margines bezpieczeństwa vs szybkość reakcji — nie da się mieć obu jednocześnie.
"""),

    ("domain/control-systems", "regulator-tuning", "Strojenie regulatorów", ["control", "tuning", "pid"],
     """# Strojenie regulatorów

## Zasada
Metody: Ziegler-Nichols (klasyka), relay tuning (auto), model-based. Zawsze weryfikuj na obiekcie rzeczywistym.

## Kiedy stosować
Nowa instalacja, zmiana dynamiki procesu, po wymianie aktuatora/czujnika.

## Trade-offy
Zbyt konserwatywny tuning = wolna reakcja. Zbyt agresywny = oscylacje i zużycie aktuatora.
"""),

    # ── domain/signals-models ──
    ("domain/signals-models", "signal-vs-noise", "Sygnał vs szum", ["signals", "noise", "filtering"],
     """# Sygnał vs szum

## Zasada
Każdy pomiar = sygnał + szum. Szum: losowy (biały), systematyczny (bias), impulsowy (glitch).

## Kiedy stosować
Przed jakąkolwiek analizą danych: oceń SNR. Niska SNR → najpierw filtruj.

## Trade-offy
Filtrowanie opóźnia sygnał. Agresywny filtr = utrata informacji.
"""),

    ("domain/signals-models", "filtering", "Filtracja sygnałów", ["signals", "filter", "lowpass", "kalman"],
     """# Filtracja

## Zasada
Filtr dolnoprzepustowy: tłumi szum, opóźnia. Medianowy: odporny na impulsy. Kalman: optymalne łączenie modelu z pomiarem.

## Kiedy stosować
Surowe pomiary z czujników, preprocessing przed regulatorem / ML.

## Trade-offy
Każdy filtr dodaje opóźnienie (latency vs gładkość). Kalman wymaga modelu dynamiki.
"""),

    ("domain/signals-models", "modeling", "Modelowanie procesów", ["modeling", "first-principles", "data-driven"],
     """# Modelowanie

## Zasada
First-principles (fizyka/chemia) vs data-driven (ML). Hybrid: fizyka dla struktury, dane dla parametrów.

## Kiedy stosować
First-principles gdy znasz fizykę. Data-driven gdy relacje nieznane.

## Trade-offy
Fizyka: ekstrapoluje dobrze, wymaga wiedzy. ML: interpoluje dobrze, black box poza zakresem treningowym.
"""),

    # ── domain/physical-models ──
    ("domain/physical-models", "process-dynamics", "Dynamika procesów", ["physics", "dynamics", "control"],
     """# Dynamika procesów

## Zasada
Każdy proces fizyczny ma: stałą czasową (jak szybko reaguje), opóźnienie (dead time), wzmocnienie (jak mocno).

## Kiedy stosować
Modelowanie i tuning regulatorów, symulacje, predykcja zachowania instalacji.

## Trade-offy
Linearyzacja upraszcza model ale traci nieliniowości (np. zawór nie jest liniowy w pełnym zakresie).
"""),

    ("domain/physical-models", "measurement-uncertainty", "Niepewność pomiarowa", ["measurement", "uncertainty", "sensors"],
     """# Niepewność pomiarowa

## Zasada
Żaden pomiar nie jest idealny. Niepewność: ±X jednostek przy Y% confidence.
Propagacja niepewności przez obliczenia (Gauss error propagation).

## Kiedy stosować
Każdy system oparty na danych z czujników. Kalibracja, porównanie z modelem.

## Trade-offy
Zbyt duży margines → nadmiarowy sprzęt. Zbyt mały → fałszywe alarmy / złe decyzje.
"""),

    ("domain/physical-models", "first-principles-models", "Modele z pierwszych zasad", ["physics", "first-principles", "modeling"],
     """# Modele z pierwszych zasad

## Zasada
Bilans masy, energii, pędu. Równania stanu. Termodynamika + kinetyka.

## Kiedy stosować
Gdy znasz fizykę procesu. Najlepsza ekstrapolacja poza zakres danych treningowych.

## Trade-offy
Kosztowne w budowie, wymaga wiedzy domenowej, parametry często trudne do identyfikacji.
"""),

    # ── domain/govtech (C++ w sektorze publicznym) ──
    ("domain/govtech", "govtech-constraints", "GovTech: ograniczenia prawne i architektura", ["govtech", "compliance", "architecture", "cpp"],
     """# GovTech — ograniczenia prawne i architektura

## Zasada
Systemy publiczne projektuje się pod **audytowalność**, **RODO / dane osobowe**, **interoperacyjność**
i często **długowieczność** (10–20 lat). WCAG i dokumentacja procedur to nie opcja.

## Kiedy stosować
Na etapie designu API, modelu danych, logowania i retention — nie po audycie.

## Trade-offy
Więcej warstw zgodności vs szybkość dostawy. C++ daje kontrolę nad deterministyką i wydajnością, ale koszt utrzymania jest wyższy.
"""),

    ("domain/govtech", "legacy-integration", "GovTech: integracja z legacy", ["govtech", "legacy", "integration", "esb", "soap"],
     """# GovTech — integracja z legacy

## Zasada
ESB, SOAP/WSDL, XSD, mainframe, mosty z COBOL — to nadal **źródło prawdy** w wielu resortach.
Nowe usługi (np. C++ + REST) muszą mapować kontrakty starego świata, nie odwracać go siłą.

## Kiedy stosować
Każda migracja „stopniowa”: adapter, façade, kolejka, idempotentne synchronizacje.

## Trade-offy
Duplikacja modeli danych vs ryzyko „dużego bang". Eventual consistency akceptowalna tylko gdy biznes to podpisze.
"""),

    ("domain/govtech", "audit-trail-design", "GovTech: ścieżka audytu", ["govtech", "audit", "logging", "database"],
     """# GovTech — ścieżka audytu

## Zasada
Kto, kiedy, którą operacją zmodyfikował rekord — **pola audytowe w bazie** + skorelowane logi aplikacji.
Bez tego trudno udowodnić zgodność i debugować incydenty.

## Kiedy stosować
Każda mutacja danych wrażliwych lub decyzyjnych; spójny identyfikator żądania (request/correlation id).

## Trade-offy
Większy rozmiar tabel i indeksów; retencja logów musi być polityką, nie przypadkiem.
"""),

    ("domain/govtech", "interoperability", "GovTech: interoperacyjność międzyresortowa", ["govtech", "xml", "json", "api"],
     """# GovTech — interoperacyjność

## Zasada
Wymiana danych często w **XML/XSD**, coraz częściej REST/JSON — zależnie od standardu krajowego i bram (API Gateway).
ePUAP i podobne kanały wymagają znajomości formatów i procesów, nie tylko „HTTP 200".

## Kiedy stosować
Projektowanie kontraktów na granicy systemów; wersjonowanie schematów.

## Trade-offy
Sztywne XSD vs elastyczność; walidacja kosztuje, ale zapobiega kosztownym błędom produkcyjnym.
"""),

    ("domain/govtech", "long-lived-systems", "GovTech: systemy długowieczne", ["govtech", "maintenance", "architecture", "cpp"],
     """# GovTech — systemy długowieczne

## Zasada
Wdrożenia publiczne często żyją **10+ lat**. Architektura musi przewidywać migracje wersji języka (C++),
zależności OS, protokołów i legislacji — bez „rewrite co 3 lata".

## Kiedy stosować
Granice modułów, API publiczne, formaty danych na dysku i w sieci; testy regresji i CI jako długoterminowy koszt.

## Trade-offy
Konservative tech choices vs presja „bycia na czasie". Techniczny dług trzeba **widzieć i planować**, nie ukrywać.
"""),

    # ── cross-domain ──
    ("cross-domain", "sensor-pipeline-to-ai", "Od czujnika do decyzji AI", ["cross-domain", "sensors", "pipeline", "ml"],
     """# Od czujnika do decyzji AI

## Analogia
Pipeline danych: sensor → filtracja → feature extraction → model → decyzja.
To ten sam wzorzec co: I/O → preprocessing → transform → business logic → output w systemach software.

## Lekcja
Problemy na etapie czujnika (szum, drift, opóźnienie) propagują się do końca pipeline — „garbage in, garbage out."
"""),

    ("cross-domain", "physics-vs-data-driven", "Fizyka vs dane", ["cross-domain", "modeling", "ml", "physics"],
     """# Fizyka vs podejście data-driven

## Analogia
First-principles model ≈ statyczne typowanie w kodzie: ograniczenia znane z góry, łatwiejszy debugging.
ML model ≈ dynamiczne typowanie: elastyczny, ale black box przy edge cases.

## Lekcja
Najlepsza architektura łączy oba: fizyka definiuje strukturę, dane dopasowują parametry.
"""),

    ("cross-domain", "latency-vs-control-loop", "Niska latency w sterowaniu i w software", ["cross-domain", "latency", "control", "performance"],
     """# Niska latency: sterowanie vs software

## Analogia
W regulatorze: dead time = opóźnienie pomiarowe + obliczeniowe + aktuatora. W trading/networking: wire-to-wire latency.
Obie domeny: mierz E2E, optymalizuj najwolniejsze ogniwo, unikaj niepotrzebnych warstw.

## Lekcja
Techniki z embedded (DMA, zero-copy, polling I/O) mają analogie w HFT i systemach realtime w chmurze.
"""),

    ("cross-domain", "engineering-identity", "Tożsamość inżynierska", ["cross-domain", "principles", "identity"],
     """# Tożsamość inżynierska

## Zasada
Inżynier to nie „programista C++" ani „automatyk". To ktoś, kto **rozwiązuje problemy** używając narzędzi z różnych domen.

## Lekcja
Zdolność łączenia wiedzy z systemów sterowania, programowania, fizyki i danych to
przewaga — nie wada „braku specjalizacji". Specjalizacja w T-shape: głęboko w jednym, szeroko w wielu.
"""),
]


def main() -> None:
    seen: set[str] = set()
    for subdir, slug, title, topics, body in NOTES:
        if slug in seen:
            raise SystemExit(f"Duplicate slug: {slug}")
        seen.add(slug)

        out_dir = BASE / subdir
        out_dir.mkdir(parents=True, exist_ok=True)

        fm = "\n".join([
            "---",
            f"id: {slug}",
            "type: permanent-note",
            f"domain: {subdir.split('/')[0]}",
            "language: pl",
            f"title: \"{title}\"",
            f"topics: [{', '.join(topics)}]",
            "status: inbox",
            "confidence: 0.85",
            "owner: null",
            "reviewer: null",
            "last_reviewed_at: null",
            "sensitivity: internal",
            "---",
            "",
        ])

        path = out_dir / f"{slug}.md"
        path.write_text(fm + body.strip() + "\n", encoding="utf-8")

    print(f"Generated {len(NOTES)} notes under {BASE}")


if __name__ == "__main__":
    main()
