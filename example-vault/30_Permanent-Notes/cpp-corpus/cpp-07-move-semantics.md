---
id: cpp-07-move-semantics
type: permanent-note
domain: engineering
language: pl
title: C++: semantyka przenoszenia
topics: [cpp, move, rvalue]
status: active
confidence: 0.9
---
# Move semantics

`std::move` to tylko cast do rvalue — nie „przenosi” magicznie bez typów move-ready.

Implementuj move ctor/assign gdy zasób można tanio przenieść (np. wskaźnik w `unique_ptr`).
