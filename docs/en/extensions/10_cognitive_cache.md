# Cognitive Cache — The AI's Working Memory

**Verified source**: `extensions/cognitive_cache/__init__.py`

> French version: [../../fr/extensions/10_cognitive_cache.md](../../fr/extensions/10_cognitive_cache.md)

---

## Concept

The Cognitive Cache is the main AI's **working memory** — a space for temporary notes, specific to each conversation, that the AI manages itself.

Unlike FAISS memory (persistent, long-term), the cognitive cache is tied to a conversation and lives for its duration.

---

## AI control

The main AI writes to this cache via internal magic phrases:

```
CACHE_ADD:[type]:[content]    → Adds a note
CACHE_DELETE:[id]             → Deletes a note
CACHE_UPDATE:[id]:[content]   → Modifies a note
CACHE_CLEAR                   → Clears the cache
```

These phrases are intercepted in the AI response post-processing, never shown to the user.

---

## Persistence

The cache is persisted per conversation in `data/cognitive_cache/{conv_id}.json`. Only 10 conversations are kept (automatic pruning at shutdown).

This behavior allows the AI to resume a conversation with its working notes intact, while avoiding indefinite accumulation.
