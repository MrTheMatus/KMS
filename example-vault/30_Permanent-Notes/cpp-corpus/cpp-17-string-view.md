---
id: cpp-17-string-view
type: permanent-note
domain: engineering
language: pl
title: C++: std::string_view
topics: [cpp, string_view, api]
status: active
confidence: 0.9
---
# string_view

Nie posiada danych — widok na zewnętrzny bufor. Idealne dla parametrów funkcji przyjmujących tekst.

**Never** zwracaj `string_view` do tymczasowego `std::string` utworzonego lokalnie.
