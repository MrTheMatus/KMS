# ADR-003: AnythingLLM zamiast własnego RAG

**Status:** Accepted  
**Data:** 2026-03-23

## Kontekst

Potrzebny jest retrieval i Q&A nad dokumentami; celem projektu nie jest implementacja własnego stacku embeddingów, chunkingu i vector store.

## Decyzja

Używamy **AnythingLLM** (lub równoważnego narzędzia dokumentowego) do retrievalu; własny kod nie implementuje RAG od zera.

## Uzasadnienie

- Skupienie na system design (control plane) zamiast na infrastrukturze ML
- Szybsze dowiezienie wartości
- Mniejszy koszt utrzymania

## Konsekwencje

**Plusy:** gotowy workflow workspace’ów i dokumentów.  
**Minusy:** zależność od produktu; ograniczona kontrola nad wewnętrznym retrievalu.
