# Backups and Recovery

**Verified sources**: `memory_manager.py` (methods `delete_memory`, `delete_all_memories`, `rebuild_faiss_index`), `profile_manager.py`

> French version: [../../fr/memory/04_backup_recovery.md](../../fr/memory/04_backup_recovery.md)

---

## Protection philosophy

The memory database is OGMA's most precious asset: it contains years of memories built through conversations. Every destructive operation is surrounded by automatic protections that make accidental deletion difficult and recovery possible.

---

## Backup before full deletion

The `delete_all_memories()` function never deletes without first creating a backup. The exact sequence is:

1. Create a `memories_backup_before_delete_all_[timestamp].db` file in `data/memory/backup/`
2. Delete all memories except foundational seeds (identifiers starting with `SEED_`)
3. Compact the database via SQLite `VACUUM` (frees space occupied by embeddings)
4. Rebuild the FAISS index to reintegrate the preserved seeds

The `backup/` folder is created automatically if it doesn't exist.

---

## Foundational seed protection

Memories whose identifier starts with `SEED_` are protected by the code: they survive `delete_all_memories()`, and any `delete_memory()` attempt on a seed is refused with an explicit message. These seeds form the minimal memory that the main AI must retain under all circumstances.

---

## Backup on single memory deletion

Deleting an individual memory (`delete_memory()`) does not create a full file backup. However, since the `IndexFlatL2` FAISS index does not support direct vector deletion, it is entirely **rebuilt** from the remaining embeddings in SQLite. This rebuild is more costly but guarantees consistency between the SQLite database and the vector index.

---

## FAISS index reconstruction

`rebuild_faiss_index()` is the recovery procedure for any inconsistency between SQLite and FAISS:

1. The FAISS index is reset
2. All embeddings stored in SQLite are reloaded in chronological order
3. The `id_to_faiss` and `faiss_to_id` mappings are rebuilt
4. The index is saved to disk

Memories without embeddings (null `embedding_json` column) are skipped and counted in the reconstruction statistics (key `skipped`).

A `rebuild_faiss_safe.py` script is available at the project root for manually triggering this reconstruction in case of corruption.

---

## Backup rotation (profiles)

`ProfileManager` keeps at most 10 backups per profile (configurable via `max_backups_to_keep`). The oldest files are deleted automatically when the threshold is exceeded. The same rotation logic is applied by extensions that manage their own backups (daily journal, etc.).
