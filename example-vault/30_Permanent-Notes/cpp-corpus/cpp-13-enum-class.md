---
id: cpp-13-enum-class
type: permanent-note
domain: engineering
language: pl
title: C++: enum class zamiast enum
topics: [cpp, enum, type-safety]
status: active
confidence: 0.9
---
# enum class

Silnie typowane enumeracje — brak niejawnych konwersji do int, osobne przestrzenie nazw.

```cpp
enum class Mode { Fast, Safe };
```
