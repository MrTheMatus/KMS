# ADR-009: PDF→Markdown stack (docling + fallback)

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

Pipeline control plane wymaga konwersji PDF do markdown pod triage, porównania i review. Jakość PDF bywa nierówna (layout, skany, tabele), więc pojedynczy konwerter jest ryzykowny.

## Decyzja

- Domyślny konwerter: `docling` (jeśli dostępny).
- Fallback: `pymupdf4llm`.
- Ostateczny fallback: ekstrakcja tekstu przez `pypdf` i zapis do prostego markdown.
- Oryginalny PDF zawsze zostaje zachowany.

## Uzasadnienie

- Zmniejsza ryzyko zatrzymania ingestu przez pojedynczą bibliotekę.
- Daje lepszą jakość dla dokumentów o złożonym układzie.
- Pozwala działać także na lżejszych środowiskach.

## Konsekwencje

**Plusy:** większa niezawodność ingestu PDF.  
**Minusy:** dodatkowe ścieżki testowe i różna jakość markdown między konwerterami.
