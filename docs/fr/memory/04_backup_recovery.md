# Sauvegardes et récupération

**Source vérifiée** : `memory_manager.py` (méthodes `delete_memory`, `delete_all_memories`, `rebuild_faiss_index`), `profile_manager.py`

---

## Philosophie de protection

La base mémoire est l'actif le plus précieux d'OGMA : elle contient des années de souvenirs construits au fil des conversations. Toute opération destructrice est entourée de protections automatiques qui rendent la suppression accidentelle difficile et la récupération possible.

---

## Backup avant suppression totale

La fonction `delete_all_memories()` ne supprime jamais sans créer d'abord une sauvegarde. La séquence exacte est :

1. Création d'un fichier `memories_backup_before_delete_all_[timestamp].db` dans `data/memory/backup/`
2. Suppression de tous les souvenirs sauf les mémoires fondatrices (identifiants `SEED_*`)
3. Compactage de la base via `VACUUM` SQLite (libère l'espace occupé par les embeddings)
4. Reconstruction de l'index FAISS pour réintégrer les seeds préservés

Le dossier `backup/` est créé automatiquement s'il n'existe pas.

---

## Protection des seeds fondateurs

Les souvenirs dont l'identifiant commence par `SEED_` sont protégés par le code : ils survivent à `delete_all_memories()` et toute tentative de `delete_memory()` sur un seed est refusée avec un message explicite. Ces seeds forment la mémoire minimale que l'IA principale doit conserver en toutes circonstances.

---

## Backup lors de la suppression d'un souvenir unique

La suppression d'un souvenir individuel (`delete_memory()`) ne crée pas de backup du fichier complet. En revanche, comme l'index FAISS `IndexFlatL2` ne supporte pas la suppression directe d'un vecteur, il est entièrement **reconstruit** à partir des embeddings restants en SQLite. Ce rebuild est plus coûteux mais garantit la cohérence entre la base SQLite et l'index vectoriel.

---

## Reconstruction de l'index FAISS

`rebuild_faiss_index()` est la procédure de récupération après toute incohérence entre SQLite et FAISS :

1. L'index FAISS est réinitialisé
2. Tous les embeddings stockés en SQLite sont rechargés dans l'ordre chronologique
3. Les mappings `id_to_faiss` et `faiss_to_id` sont reconstruits
4. L'index est sauvegardé sur disque

Les souvenirs sans embedding (colonne `embedding_json` nulle) sont ignorés et comptés dans les statistiques de reconstruction (clé `skipped`).

Un script `rebuild_faiss_safe.py` est disponible à la racine du projet pour lancer cette reconstruction manuellement en cas de corruption.

---

## Rotation des backups (profils)

Le `ProfileManager` maintient au maximum 10 backups par profil (configurable via `max_backups_to_keep`). Les fichiers les plus anciens sont supprimés automatiquement quand le seuil est dépassé. Cette même logique de rotation est appliquée par les extensions qui gèrent leurs propres backups (journal de bord, etc.).
