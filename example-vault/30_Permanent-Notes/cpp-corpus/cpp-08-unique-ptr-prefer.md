---
id: cpp-08-unique-ptr-prefer
type: permanent-note
domain: engineering
language: pl
title: C++: preferuj unique_ptr
topics: [cpp, unique_ptr, ownership]
status: active
confidence: 0.9
---
# unique_ptr jako domyślny wskaźnik właścicielski

**Prefer** `std::unique_ptr<T>` dla wyłącznej własności. Jest tanie i wyraźne.

```cpp
auto p = std::make_unique<Foo>(args...);
```

**Unikaj** `shared_ptr` jeśli nie potrzebujesz współdzielenia — narzut i ryzyko cykli.
