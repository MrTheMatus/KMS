---
id: cpp-25-nrvo-rvo
type: permanent-note
domain: engineering
language: pl
title: C++: NRVO / RVO
topics: [cpp, rvo, performance]
status: active
confidence: 0.9
---
# Return value optimization

Kompilator często eliminuje kopie przy zwrocie lokalnych obiektów.

Nie „optymalizuj na siłę” przez `std::move` na return lokalnego — może zablokować NRVO.
