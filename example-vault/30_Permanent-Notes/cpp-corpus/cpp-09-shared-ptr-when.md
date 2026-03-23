---
id: cpp-09-shared-ptr-when
type: permanent-note
domain: engineering
language: pl
title: C++: kiedy shared_ptr
topics: [cpp, shared_ptr, graphs]
status: active
confidence: 0.9
---
# shared_ptr

Używaj gdy obiekt musi żyć tak długo, jak ostatni użytkownik — grafy, cache współdzielony.

Pamiętaj o `weak_ptr` do łamania cykli.
