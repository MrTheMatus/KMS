# ADR-004: Source notes obowiązkowe dla ważnych PDF

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

Plik PDF jest słabym bytem operacyjnym: trudniejsze metadane, tagowanie i spójny workflow w vaultcie w porównaniu z notatką Markdown.

## Decyzja

Dla **ważnych** PDFów obowiązuje powiązana **source note** w Markdown z metadanymi (`file_link`, `title`, itd.).

## Uzasadnienie

- Jawna semantyka i status w vaultcie
- Łatwiejszy review i filtrowanie
- Rozdzielenie binariów od opisu źródła

## Konsekwencje

**Plusy:** przewidywalny workflow.  
**Minusy:** dodatkowy krok dla użytkownika.
