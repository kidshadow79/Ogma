# Vector Search and FTS5

**Verified source**: `memory_manager.py` (methods `_search_fts5`, `retrieve_and_synthesize_context`, `_expand_personal_pronouns`, `_extract_keywords`)

> French version: [../../fr/memory/02_vector_search.md](../../fr/memory/02_vector_search.md)

---

## Why two search engines?

Each engine has a blind spot:

- **Semantic search (FAISS)** retrieves memories by meaning, even if the words differ. But it can miss exact matches on proper names, dates, or very specific terms.
- **Full-text search (FTS5)** retrieves memories that contain exactly the query terms. But it is insensitive to paraphrases and synonyms.

Combining them covers both cases.

---

## Semantic search with FAISS

FAISS (Facebook AI Similarity Search) is a vector search library. Each memory was converted into a fixed-dimension numeric vector (the "embedding dimension") at creation time. This vector encodes the text's meaning in mathematical form.

When a query arrives, it is also converted into a vector. FAISS then calculates the distance between this vector and all vectors in the index, and returns the `k` closest vectors. The more semantically similar two texts are, the closer their vectors are in this mathematical space.

The index used is `IndexFlatL2` — exact search by L2 distance (Euclidean distance). It is precise but linear in time: the search traverses all vectors. For larger volumes, a migration to `IndexIVFFlat` (faster approximate search) is planned [NOT IMPLEMENTED at verification date].

---

## Full-text search with FTS5

SQLite includes a full-text search engine called FTS5. OGMA maintains an FTS5 index of memory original texts. Queries use BM25 ranking (a standard document relevance algorithm) provided natively by FTS5.

FTS5 scores are negative by SQLite convention (more negative = better result). `MemoryManager` converts them to positive normalized scores before merging.

---

## Query preprocessing

Before any search, the user's query goes through two steps:

1. **Pronoun expansion**: personal pronouns ("I", "you", "he", "me"...) are replaced or expanded with the corresponding names if available in context. This improves embedding quality.

2. **Keyword extraction**: stop words (articles, prepositions...) are removed. Only meaningful terms are kept to generate the embedding.

---

## Score merging

A memory's final score is computed as:

$$\text{hybrid\_score} = (0.6 \times \text{FAISS\_score}) + (0.4 \times \text{FTS5\_score}) + \text{exact\_match\_bonus}$$

The exact match bonus adds up to 0.2 if the query words are found in the memory's title, summary, or text.

Memories are sorted by descending hybrid score, and the top `k` are passed to the Archivist for synthesis.

---

## From search to synthesis

Retrieved memories are not injected raw into the conversation. The Archivist reads them and generates a **synthesis note**: a short, relevant text that summarizes what is useful relative to the question asked. This note is what arrives in the main AI's context, not the raw data dump.

This pass through the Archivist is deliberate: the main AI receives already-digested information linked to the question, not a raw data dump.
