# Données mémoire

**Sources vérifiées** : `data/memory/` (inspection directe), `memory_manager.py` (structure vérifiée dans sessions précédentes)

---

## Contenu du dossier `data/memory/`

| Fichier | Description |
|---|---|
| `memories.db` | Base SQLite principale — souvenirs, métadonnées, FTS5 |
| `faiss.index` | Index vectoriel FAISS (IndexFlatL2) |
| `memories.seed.db` | Base de souvenirs initiaux (`SEED_*`) — préservés lors des resets |
| `i2i_lessons.db` | Base SQLite dédiée aux leçons image-to-image |
| `backup/` | Backups automatiques rotatifs (10 fichiers max) |

---

## `memories.db`

Contient trois tables principales :
- `memories` — souvenirs avec contenu, type, score d'importance, timestamps
- `memory_fts` — table FTS5 pour la recherche plein texte (BM25)
- Index sur `memory_type` pour filtrage rapide

---

## `faiss.index`

Index vectoriel `IndexFlatL2` (distance euclidienne). Chaque souvenir est représenté par son vecteur d'embedding. L'index est reconstruit depuis zéro (`rebuild_faiss_index()`) après chaque suppression de souvenir, car IndexFlatL2 ne supporte pas la suppression individuelle.

---

## `memories.seed.db`

Contient les souvenirs de type `SEED_*` — les souvenirs d'amorçage créés lors de l'installation. Ces souvenirs sont préservés lors de `delete_all_memories()` pour garantir un état minimal cohérent.

---

## `backup/`

Backups rotatifs créés avant chaque opération destructive (suppression globale). Maximum 10 fichiers conservés, les plus anciens sont supprimés automatiquement. Nomenclature : `memories_backup_YYYYMMDD_HHMMSS.db`.
