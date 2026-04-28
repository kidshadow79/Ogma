# Memory Optimization

**Verified sources**: `memory_manager.py` (function `clean_conversational_noise`), `archiviste_memory_optimizer.py` (pipeline `get_optimized_context`)

> French version: [../../fr/memory/05_memory_optimization.md](../../fr/memory/05_memory_optimization.md)

---

## The semantic dilution problem

When a user writes "you know, I feel like my relationship with work has changed since we talked about my projects", the embedding of this full sentence is dominated by common words (feel, relationship, since). The important concepts (work, projects) are drowned out by noise.

A FAISS search on this embedding returns memories vaguely similar in register to the sentence, not the most relevant memories.

---

## Conversational noise cleanup

`clean_conversational_noise()` in `memory_manager.py` applies a purely algorithmic first filter: removing stop words, polite formulas, and discourse markers. The query "you know, I feel like my relationship with work has changed" becomes "work changed".

This cleanup is systematic and costs nothing in tokens.

---

## Adaptive threshold: Python or AI

If the cleaned query contains **6 words or fewer**, it is used directly as the embedding query — the Python cleanup is sufficient.

If it exceeds 6 words, the Archivist is called for semantic filtering: it selects 4 to 6 essential keywords from those present. It can only filter, not add. This prevents hallucinating concepts absent from the original message.

---

## Strategic query generation

The Archivist generates up to 5 strategic queries covering different semantic angles:

- The primary query (direct intent)
- A version with possessive pronoun resolution (`my` → user's name)
- Synonyms or variations
- A temporal context if the query mentions a time period
- A declarative rephrasing

These 5 queries are submitted in batch to `search_memories_batch()`.

---

## Smart Stop mechanism

The batch search stops before using all 5 queries if the redundancy rate between results exceeds 80% (threshold `stop_threshold`). When new queries only bring back memories already found by earlier ones, continuing is pointless.

Search metrics indicate the number of queries actually used vs. planned.

---

## Final Archivist filtering

Among the retained candidates (maximum 7), the Archivist evaluates the real contextual relevance of each memory relative to the original message. It does not rely on the vector score but on its understanding of the link between the memory and the ongoing conversation.

The top 2 retained memories are passed as full text to the main AI. The following ones are passed as short summaries.

Only memories retained by this final filter enter cooldown in the deduplicator — not discarded candidates.
