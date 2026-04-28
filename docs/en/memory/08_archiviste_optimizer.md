# Archivist Memory Optimizer

**Verified source**: `archiviste_memory_optimizer.py`

> French version: [../../fr/memory/08_archiviste_optimizer.md](../../fr/memory/08_archiviste_optimizer.md)

---

## Problem solved

Default memory search embeds the full user query and compares it to memories. This approach works for short, precise queries. It fails for long conversational messages where important words represent less than 20% of the text.

`ArchivisteMemoryOptimizer` is an optional layer that replaces this direct search with an AI pipeline.

---

## 5-step pipeline

### Step 1 — Intent analysis

The Archivist analyzes the message to understand what the user is really looking for. It generates up to 5 "strategic queries": short formulations (2-4 words) targeting the essential concepts from different semantic angles.

### Step 2 — Batch search with Smart Stop

The 5 queries are submitted in parallel to `search_memories_batch()`. The Smart Stop mechanism monitors the redundancy rate between results. If new queries return more than 80% of memories already found, the search stops without using the remaining queries.

### Step 2.5 — Cooldown filtering

Recently injected memories (in cooldown period) are excluded, unless their lexical match score exceeds 0.70. This bypass threshold lets a user who explicitly returns to a recent topic retrieve the associated memories despite the cooldown.

### Step 3 — Candidate selection

The top 7 memories (by hybrid FAISS + FTS5 score) are passed to the Archivist for contextual evaluation.

### Step 4 — Contextual filtering by the Archivist

The Archivist evaluates the actual relevance of each candidate relative to the original message. It can discard a memory with a high vector score if it is not connected to the current conversation. Retained memories are re-ranked by contextual relevance.

### Step 5 — Formatting and cooldown injection

The top 2 retained memories are formatted as full text, the rest as summaries. Only effectively retained memories enter cooldown in the deduplicator.

---

## Integration

The optimizer is used in `get_parallel_context()` if an instance is available. Its absence does not block the pipeline: `get_parallel_context()` falls back to direct hybrid search.

---

## Measured performance (from source file documentation)

| Metric | Without optimizer | With optimizer |
|---|---|---|
| Accuracy | ~20% | ~80% |
| Embedding API calls | 2 | 1.4 average |
| Latency | 310 ms | 267 ms |
| Token cost | $0.0042 | $0.0041 |
