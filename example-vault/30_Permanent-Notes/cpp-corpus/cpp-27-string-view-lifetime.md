---
id: cpp-27-string-view-lifetime
type: permanent-note
domain: engineering
language: pl
title: C++: string_view — ostrzeżenia (lifetime)
topics: [cpp, string_view, lifetime, ub]
status: active
confidence: 0.9
---
# string_view — lifetime

**Never** trzymaj `string_view` dłużej niż żywot bufora źródłowego.

Łatwy do złamania invariant jeśli źródło to tymczasowy `std::string`.

Uzupełnia notatkę o `string_view` jako parametrze — tu fokus na **błędach czasu życia**.
