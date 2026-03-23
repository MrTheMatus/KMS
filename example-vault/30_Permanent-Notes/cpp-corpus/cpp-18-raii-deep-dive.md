---
id: cpp-18-raii-deep-dive
type: permanent-note
domain: engineering
language: pl
title: C++ Idiom: RAII — głębsze wzorce
topics: [cpp, raii, mutex, scope-guard]
status: active
confidence: 0.9
---
# RAII — więcej niż pliki

RAII dotyczy też mutexów (`std::lock_guard`, `unique_lock`), timerów, transakcji.

**Prefer** jeden poziom zasobu = jeden obiekt — łatwiejszy reasoning.

To rozwija temat z notatki o podstawach RAII — rozważ scalenie sekcji jeśli powielasz wstęp.
