# Le système de mémoire — `MemoryManager`

**Source vérifiée** : `memory_manager.py` (classe `MemoryManager`)

---

## Ce que c'est

La mémoire d'OGMA n'est pas un simple fichier de notes. C'est un système hybride qui combine une base de données structurée (SQLite) et un index de recherche sémantique (FAISS). Ensemble, ils permettent à l'IA de retrouver des souvenirs pertinents non pas juste par mots-clés, mais par sens — même si l'utilisateur ne se souvient pas des termes exacts utilisés lors de la conversation où le souvenir a été créé.

---

## Architecture : SQLite + FAISS

**SQLite** stocke les souvenirs sous forme de lignes structurées. Chaque souvenir contient son texte original, son type (affectif, conceptuel, sensoriel, événement), un titre, un résumé, une valence (positif/négatif/neutre), un score d'impact calculé, et diverses métadonnées enrichies par l'Archiviste au moment de la création.

**FAISS** (Facebook AI Similarity Search) maintient un index vectoriel parallèle. Chaque souvenir a un vecteur numérique — son "empreinte sémantique" — généré par l'`EmbeddingController`. FAISS permet de trouver en quelques millisecondes les souvenirs dont le sens est proche d'une requête, même formulée différemment.

Ces deux bases sont maintenues synchronisées : quand un souvenir est ajouté à SQLite, son vecteur est ajouté à FAISS avec un identifiant correspondant. Les dictionnaires `id_to_faiss` et `faiss_to_id` assurent la correspondance entre les deux systèmes.

---

## Thread-safety

FAISS n'est pas thread-safe par design. `MemoryManager` utilise deux verrous distincts :

- `_faiss_lock` : protège toutes les opérations sur l'index FAISS (ajout de vecteurs, recherche)
- `_mapping_lock` : protège les dictionnaires de correspondance id↔position FAISS

Toute opération sur FAISS doit se faire dans un bloc `with self._faiss_lock:`.

---

## Ajouter un souvenir — `add_memory()`

L'ajout d'un souvenir est un processus en plusieurs étapes :

1. **Vérification de redondance** : avant tout, le système génère l'embedding du nouveau texte et le compare aux souvenirs existants. Si un souvenir très similaire existe déjà (similarité ≥ seuil, par défaut 92%), l'ajout est refusé. Ce mécanisme évite de saturer la mémoire avec des doublons quasi-identiques.

2. **Enrichissement par l'Archiviste** : le texte brut est envoyé à l'Archiviste qui en fait un souvenir structuré (JSON) avec scoring d'impact, type, titre, résumé, résonances affectives, commentaire analytique.

3. **Génération d'embedding** : le texte est transformé en vecteur par l'`EmbeddingController`.

4. **Écriture double** : le souvenir est inséré dans SQLite et le vecteur est ajouté à FAISS.

---

## Chercher des souvenirs — pipeline hybride

La recherche combine trois signaux :

| Signal | Poids | Ce qu'il mesure |
|---|---|---|
| FAISS (sémantique) | 60% | Proximité de sens entre la requête et les souvenirs |
| FTS5 (mots-clés) | 40% | Présence des mots exacts de la requête dans les textes |
| Exact match | +20% bonus | Mots de la requête présents dans le titre/résumé |

La requête est d'abord nettoyée (expansion des pronoms personnels, extraction des mots-clés) pour améliorer la qualité de l'embedding. Les résultats des deux moteurs sont fusionnés par score pondéré, puis les `k` meilleurs souvenirs sont récupérés depuis SQLite.

L'Archiviste lit ensuite ces souvenirs et génère une **synthèse contextuelle** — une note qui résume ce qui est pertinent par rapport à la question posée. C'est cette note qui est injectée dans le contexte de l'IA principale.

---

## Protection à la suppression

`delete_all_memories()` crée un backup automatique de la base SQLite dans `data/memory/backup/` avant toute suppression. La suppression d'un souvenir individuel (`delete_memory()`) retire l'entrée de SQLite mais ne reconstruit pas l'index FAISS — cela est pris en charge par la procédure de reconstruction (`rebuild_faiss_safe.py`).

---

## Initialisation et chargement

Au démarrage, `MemoryManager` :
1. Crée ou ouvre la base SQLite (avec migration automatique si des colonnes manquent)
2. Initialise un index FAISS vide (`IndexFlatL2` — recherche exacte, adaptée à des volumes modérés)
3. Charge tous les embeddings existants depuis SQLite pour les réinjecter dans FAISS

Cette étape peut prendre quelques secondes si la base contient beaucoup de souvenirs.
