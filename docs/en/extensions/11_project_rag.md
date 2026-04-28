# Project RAG — Documents at Your Fingertips

**Verified source**: `extensions/project_rag/__init__.py`

> French version: [../../fr/extensions/11_project_rag.md](../../fr/extensions/11_project_rag.md)

---

## Concept

Project RAG (Retrieval-Augmented Generation) allows uploading documents and making them queryable by the main AI. Each project is isolated with its own knowledge base.

The idea: you have 200 pages of a report, source code, or meeting notes. Instead of pasting everything into a prompt, RAG indexes these documents and injects **only the relevant passages** into each message.

---

## Per-project isolated architecture

Each project has its own SQLite memory + FAISS index, independent of OGMA's main memory. This isolation guarantees that documents from one project do not contaminate searches from another.

| Module | Role |
|---|---|
| `project_config.py` | Per-project JSON configuration |
| `project_manager.py` | Isolated SQLite + FAISS memory |
| `project_chunker.py` | Adaptive chunking by file type |
| `project_retriever.py` | Semantic search + cache |
| `project_injector.py` | Context injection into the chat pipeline |
| `project_ui.py` | NiceGUI overlay interface |

---

## Adaptive chunking

Document splitting depends on the file type (PDF, code, markdown, plain text). Each type uses a splitting strategy optimized to preserve the semantic coherence of passages.

---

## Search cache

`project_retriever.py` maintains a cache of search results to avoid re-indexing the same frequent queries. This cache is session-bound.
