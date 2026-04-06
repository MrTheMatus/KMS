---
id: raii
type: permanent-note
domain: cpp
language: pl
title: "C++: RAII — zarządzanie zasobami"
topics: [cpp, raii, resource]
status: active
confidence: 0.85
owner: null
reviewer: null
last_reviewed_at: null
sensitivity: internal
---
# RAII — Resource Acquisition Is Initialization

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
