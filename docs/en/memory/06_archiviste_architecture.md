# The Archivist — The Second Analytical Brain

**Verified sources**: `core_logic.py` (class `AIController`, flag `_is_archiviste`), `archiviste_memory_optimizer.py`, `archiviste_logger.py`, `ogma_ng.py` (instantiation `_archiviste_controller`)

> French version: [../../fr/memory/06_archiviste_architecture.md](../../fr/memory/06_archiviste_architecture.md)

---

## Why a second brain?

OGMA is built on an architectural conviction: an AI that must simultaneously be warm, spontaneous, and empathetic in dialogue, AND rigorous, precise, and exhaustive in memory management, cannot do both well with the same parameter set.

The main AI is tuned for creativity and fluidity (temperature 0.7). It converses, feels, adapts. The Archivist is tuned for precision and consistency (temperature 0.3). It analyzes, encodes, structures.

These two controllers are distinct instances of the same `AIController` class, but configured differently — and potentially on different backends.

---

## What the Archivist does

The Archivist intervenes at three moments:

**1. When adding a memory**
When the main AI triggers the memorization magic phrase, the raw text is sent to the Archivist. It produces structured JSON: memory type, title in Jeopardy style (two questions for which the text is the answer), summary, impact scoring with the multiplier formula, valence, affective resonances, analytical comment. This JSON is stored in SQLite.

**2. During contextual search**
When the main AI needs memory context (before responding), the Archivist receives the closest memories and generates a targeted synthesis. It does not produce a raw list — it summarizes what is relevant to the current question.

**3. In the memory optimizer**
`ArchivisteMemoryOptimizer` is an additional layer that, before even launching the FAISS search, asks the Archivist to analyze the query and extract the key concepts. This produces embeddings more focused on the useful signal, and determines whether the search should cover personal memories, conversational memories, or both.

---

## `ArchivisteMemoryOptimizer` — search smarter, not more

The optimizer solves a concrete problem: embedding a long question ("do you remember when I told you about my career change project, we also talked about organizing my time") produces a diluted vector. The query contains too many ideas for a single vector to be precise on all of them.

The solution: the Archivist reads the question and extracts 2 to 4 essential keywords. These keywords are embedded separately, producing more focused vectors. Results are deduplicated, then the Archivist generates a unified synthesis in a single call (instead of two separate calls for retrieval then synthesis).

---

## Token monitoring — `ArchivisteLogger`

The Archivist is identified by the `_is_archiviste = True` flag on its controller. When this flag is active and `ARCHIVISTE_LOGGING_ENABLED` is `True`, every call to `call_chat_api()` is recorded in `data/archiviste_tokens_debug.jsonl`.

Each entry contains the call's source, the messages sent, the response received, and an estimated token count (calculated heuristically: 4 characters ≈ 1 token). This journal allows precise understanding of what the Archivist consumes and identification of the most expensive call sources.

---

## Transparency toward the user

The user does not see the Archivist. They do not talk to it, they do not read its outputs directly. The Archivist always works in the background, silently. The only visible trace is the quality of stored memories and the relevance of the context injected into the main AI's responses.
