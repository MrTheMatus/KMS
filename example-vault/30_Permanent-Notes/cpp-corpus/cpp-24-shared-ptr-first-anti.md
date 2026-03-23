---
id: cpp-24-shared-ptr-first-anti
type: permanent-note
domain: engineering
language: pl
title: C++: ostrożnie z domyślnym shared_ptr
topics: [cpp, shared_ptr, performance, style]
status: active
confidence: 0.9
---
# shared_ptr nie jest domyślnym wyborem

W niektórych kodbases **prefer** zaczynać od `unique_ptr` i eskalować do `shared` tylko przy udokumentowanej potrzebie.

**Avoid** „domyślnie shared” — niepotrzebny narzut referencyjny.

*To może brzmieć inaczej niż notatki promujące shared dla grafów — rozróżnij kontekst.*
