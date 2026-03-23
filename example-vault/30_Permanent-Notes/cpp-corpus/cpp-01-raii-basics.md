---
id: cpp-01-raii-basics
type: permanent-note
domain: engineering
language: pl
title: C++ Idiom: RAII — podstawy
topics: [cpp, raii, resource]
status: active
confidence: 0.9
---
# C++ Idiom: RAII — podstawy

**Prefer** wiązanie czasu życia zasobu z czasem życia obiektu. Konstruktor przydziela, destruktor zwalnia.

```cpp
struct File {
  FILE* f{};
  explicit File(const char* p) : f(std::fopen(p, "rb")) {}
  ~File() { if (f) std::fclose(f); }
};
```

**Zalecenie:** unikaj jawnego `new`/`delete` w nowym kodzie — patrz notatki o smart pointerach.
