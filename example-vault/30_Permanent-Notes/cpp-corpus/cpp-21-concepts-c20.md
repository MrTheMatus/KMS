---
id: cpp-21-concepts-c20
type: permanent-note
domain: engineering
language: pl
title: C++20: concepts — wstęp
topics: [cpp, concepts, templates]
status: active
confidence: 0.9
---
# Concepts

Ograniczenia na szablony z czytelnymi komunikatami błędów.

```cpp
template<std::integral T> T twice(T x) { return x + x; }
```
