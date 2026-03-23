---
id: cpp-02-smart-pointers-overview
type: permanent-note
domain: engineering
language: pl
title: C++: inteligentne wskaźniki — przegląd
topics: [cpp, memory, smart-pointers]
status: active
confidence: 0.9
---
# Inteligentne wskaźniki

- `std::unique_ptr` — wyłączna własność, zerowy narzut.
- `std::shared_ptr` — współdzielenie z licznikiem; **prefer** tylko gdy semantyka wymaga.
- `std::weak_ptr` — obserwacja cykli.

**Prefer** `make_unique` / `make_shared` zamiast surowych konstruktorów.
