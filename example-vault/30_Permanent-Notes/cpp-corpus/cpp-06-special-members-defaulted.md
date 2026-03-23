---
id: cpp-06-special-members-defaulted
type: permanent-note
domain: engineering
language: pl
title: C++: = default dla składowych specjalnych
topics: [cpp, default, special-members]
status: active
confidence: 0.9
---
# = default

Jawnie zaznacz, że chcesz domyślnej semantyki:

```cpp
MyType(const MyType&) = default;
MyType& operator=(MyType&&) = default;
```

Ułatwia review i dokumentuje intencję.
