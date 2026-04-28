# Full-Text Search (FTS5)

**Verified source**: `memory_manager.py` (function `_search_fts5`, table `memories_fts`)

> French version: [../../fr/memory/03_fulltext_search.md](../../fr/memory/03_fulltext_search.md)

---

## Role in hybrid search

Full-text search is one of the two engines in OGMA's hybrid search system. It complements FAISS vector search by finding memories whose words exactly match the query, even when semantic similarity is low.

Practical example: if the query mentions a first name, a specific location, or an exact technical term, FAISS may not find the right memory (embeddings capture semantics, not exact lexical matches). FTS5 handles this directly.

---

## `memories_fts` table

A virtual SQLite FTS5 table is created as a mirror of the main `memories` table. It is maintained automatically by SQLite on every insert or update.

FTS5 uses the **BM25** algorithm to calculate relevance. BM25 accounts for a term's frequency in the document (TF) and its rarity across all documents (IDF), naturally giving more weight to distinctive terms.

---

## Query sanitization

Before submitting a query to FTS5, special characters are stripped (FTS5 interprets some symbols as search operators and may raise errors). The query is normalized to simple spaces.

---

## FTS5 score

The `rank` value returned by FTS5 is a negative number: the more negative it is, the better the result. The module converts it to a positive score normalized between 0 and 1 via:

$$score = \frac{1}{1 + |rank|}$$

This normalization makes the FTS5 score compatible with the FAISS score for hybrid merging.

---

## Merging with FAISS

The final score for a candidate memory is computed by combining both engines:

$$score_{final} = 0.6 \times score_{FAISS} + 0.4 \times score_{FTS5} + 0.2 \times bonus_{exact}$$

The 0.2 bonus is added when the query term appears verbatim (exact match) in the memory text.

A memory absent from one of the two engines simply gets a score of 0 for that engine — it is not excluded, but its priority decreases.
