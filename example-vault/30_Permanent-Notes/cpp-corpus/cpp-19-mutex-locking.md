---
id: cpp-19-mutex-locking
type: permanent-note
domain: engineering
language: pl
title: C++: blokady mutexów
topics: [cpp, mutex, concurrency]
status: active
confidence: 0.9
---
# Mutex

**Prefer** `std::scoped_lock` (C++17) dla wielu mutexów.

Unikaj ręcznego `lock`/`unlock` — użyj RAII lock guard.
