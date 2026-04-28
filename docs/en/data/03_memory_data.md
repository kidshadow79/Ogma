# Memory Data

**Verified sources**: `data/memory/` (direct inspection), `memory_manager.py` (structure verified in previous sessions)

> French version: [../../fr/data/03_memory_data.md](../../fr/data/03_memory_data.md)

---

## Contents of `data/memory/`

| File | Description |
|---|---|
| `memories.db` | Main SQLite database — memories, metadata, FTS5 |
| `faiss.index` | FAISS vector index (IndexFlatL2) |
| `memories.seed.db` | Initial memory base (`SEED_*`) — preserved during resets |
| `i2i_lessons.db` | Dedicated SQLite database for image-to-image lessons |
| `backup/` | Automatic rotating backups (10 files max) |

---

## `memories.db`

Contains three main tables:
- `memories` — memories with content, type, importance score, timestamps
- `memory_fts` — FTS5 table for full-text search (BM25)
- Index on `memory_type` for fast filtering

---

## `faiss.index`

`IndexFlatL2` vector index (Euclidean distance). Each memory is represented by its embedding vector. The index is rebuilt from scratch (`rebuild_faiss_index()`) after each memory deletion, because IndexFlatL2 does not support individual deletion.

---

## `memories.seed.db`

Contains `SEED_*` type memories — bootstrap memories created during installation. These memories are preserved during `delete_all_memories()` to guarantee a minimal coherent state.

---

## `backup/`

Rotating backups created before each destructive operation (global deletion). Maximum 10 files kept, oldest deleted automatically. Naming: `memories_backup_YYYYMMDD_HHMMSS.db`.
