# Skrót decyzji architektonicznych (Etap 0)

Pełny opis: [architecture.md](architecture.md). Formalne ADR: [adr/README.md](adr/README.md).

| Obszar | Decyzja |
|--------|---------|
| Stan operacyjny | SQLite jako control plane (nie Postgres na MVP) |
| Review | Markdown `review-queue.md`, nie web UI na start |
| Retrieval | AnythingLLM (gotowe narzędzie), brak własnego RAG |
| PDF | Ważne PDF → obowiązkowa source note |
| Mutacje | Human-in-the-loop; apply idempotentny |
| Zdalnie | Gateway dopiero po stabilnym lokalnym workflow (VPN) |
| Out of scope | Własny vector DB, agent bez review, publiczny stack, plugin Obsidian |
