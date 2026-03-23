---
id: cpp-15-range-for
type: permanent-note
domain: engineering
language: pl
title: C++: pętle for po zakresie
topics: [cpp, ranges, loops]
status: active
confidence: 0.9
---
# Range-for

```cpp
for (const auto& x : vec) { ... }
```

Używaj `const auto&` dla dużych typów, `auto&&` dla forwarding w szablonach.
