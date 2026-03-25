# Mémoire Hybride (SQLite + FAISS) — Documentation Exhaustive

**Fichier principal** : `memory_manager.py`
**Concept** : Système de mémoire persistante à deux niveaux — stockage structuré SQLite (texte + métadonnées) et index vectoriel FAISS (recherche sémantique par similarité).

---

## Architecture

```
MemoryManager
├── SQLite (data/memory/ogma_memory.db)
│   ├── memories table          ← stockage principal
│   ├── conversations table     ← historique conversations
│   └── FTS5 virtual table      ← recherche plein texte
│
└── FAISS Index (data/memory/faiss.index)
    └── vecteurs float32        ← embeddings en mémoire RAM
```

---

## `MemoryStructure` — Format d'un souvenir

### Identifiant unique

**Format** : `MC2-{YYYYMMDD}-{NNN}`

Exemples :
- `MC2-20251201-001` — premier souvenir du 1er décembre 2025
- `MC2-20251201-042` — 42ème souvenir de cette date

### Schéma SQLite `memories`

| Colonne | Type | Description |
|---------|------|-------------|
| `memory_id` | TEXT PK | Identifiant MC2-... |
| `content` | TEXT | Contenu brut du souvenir |
| `summary` | TEXT | Résumé court (généré par Archiviste) |
| `importance` | REAL | Score 0.0-10.0 |
| `memory_type` | TEXT | `"episodic"`, `"semantic"`, `"procedural"`, `"emotional"` |
| `tags` | TEXT | JSON array de tags |
| `source` | TEXT | Origine : `"conversation"`, `"#MEM"`, `"archiviste"`, `"introspection"` |
| `embedding_id` | INTEGER | ID ligne dans FAISS index |
| `access_count` | INTEGER | Nombre d'accès (recherche ou récupération) |
| `last_accessed` | TEXT | ISO timestamp dernier accès |
| `created_at` | TEXT | ISO timestamp création |
| `consolidated` | INTEGER | `0/1` — utilisé par DreamEngine |
| `session_id` | TEXT | Session de création |
| `metadata` | TEXT | JSON arbitraire (extensions libres) |

### Schéma SQLite `conversations`

| Colonne | Type | Description |
|---------|------|-------------|
| `conv_id` | TEXT PK | UUID conversation |
| `title` | TEXT | Titre auto-généré |
| `summary` | TEXT | Résumé Archiviste |
| `messages_json` | TEXT | JSON array messages |
| `message_count` | INTEGER | Nombre messages |
| `created_at` | TEXT | ISO timestamp |
| `last_active` | TEXT | ISO timestamp dernière activité |
| `tags` | TEXT | JSON array |

### FTS5 virtual table `memories_fts`

Permet `MATCH` fulltext sur colonnes `content`, `summary`, `tags`.

---

## Système de backup FIFO

**4 fichiers de backup rotatifs** :
- `data/memory/backup_1.db` ← le plus récent
- `data/memory/backup_2.db`
- `data/memory/backup_3.db`
- `data/memory/backup_4.db` ← le plus ancien

**Déclencheur** : À chaque sauvegarde `save_memory()`, rotation FIFO :
1. `backup_4.db` → supprimé
2. `backup_3.db` → renommé `backup_4.db`
3. `backup_2.db` → renommé `backup_3.db`
4. `backup_1.db` → renommé `backup_2.db`
5. `ogma_memory.db` → copié en `backup_1.db`

---

## `MemoryManager` — Classe principale

### `__init__(data_dir, embedding_controller, settings_manager)`

| Attribut | Description |
|----------|-------------|
| `_db_path` | `data/memory/ogma_memory.db` |
| `_faiss_index` | Index FAISS L2 (Inner Product) dim 1536 (OpenAI) ou 768 (Ollama) |
| `_embedding_map` | `dict[str, int]` — memory_id → FAISS row idx |
| `_faiss_lock` | `threading.RLock()` — toutes ops FAISS thread-safe |
| `_embedding_dim` | Dimension auto-détectée au premier embedding |
| `_embedding_controller` | Instance AIController pour embeddings |

### Initialisation

**`initialize()`** :
1. Crée SQLite + tables si nexistant pas (CREATE TABLE IF NOT EXISTS)
2. Active FTS5 trigger (INSERT INTO `memories_fts`)
3. Charge FAISS index si `faiss.index` existe
4. Reconstruit `_embedding_map` depuis DB si FAISS chargé

---

## Opérations CRUD

### `async save_memory(content, importance, memory_type, tags, source, metadata)` → `str` (memory_id)

1. Génère `memory_id` format MC2-...
2. `await _generate_embedding(content)` → vecteur
3. `with _faiss_lock: _faiss_index.add(vecteur)` → `embedding_id`
4. INSERT dans `memories` + INSERT INTO `memories_fts`
5. Backup FIFO (si `importance >= 7`)
6. Retourne `memory_id`

### `async save_memory_from_conversation(user_msg, ai_response, context)` → `str`

- Appelle Archiviste pour extraire contenu mémorisable + importance + tags
- Délègue à `save_memory()`

### `delete_memory(memory_id)` → `bool`

1. Récupère `embedding_id` depuis DB
2. `with _faiss_lock:` retire vecteur (FAISS ne supporte pas delete direct → reconstruire index sans ce vecteur)
3. DELETE depuis `memories` et `memories_fts`
4. Reconstruit `_embedding_map`

### `update_memory(memory_id, updates)` → `bool`

- UPDATE colonnes spécifiées
- Si `content` mis à jour → regénère embedding + remplace dans FAISS

---

## Recherche

### `async search_memories_semantic(query, k, threshold)` → `list[dict]`

1. `await _generate_embedding(query)` → vecteur requête
2. `with _faiss_lock: _faiss_index.search(vecteur, k)` → `(distances, indices)`
3. Filtre `distance > threshold` (cosine similarity via Inner Product sur vecteurs normalisés)
4. Lookup DB par `embedding_id` pour récupérer données complètes
5. Incrémente `access_count` + met à jour `last_accessed`
6. Retourne `[{memory_id, content, summary, importance, score_similarity, tags, ...}]`

### `search_memories_fts(query, limit)` → `list[dict]`

```sql
SELECT * FROM memories m
JOIN memories_fts f ON m.memory_id = f.memory_id
WHERE memories_fts MATCH ?
ORDER BY rank
LIMIT ?
```

### `search_memories_hybrid(query, k, threshold)` → `list[dict]`

1. `search_memories_semantic(query, k*2, threshold)` → résultats vectoriels
2. `search_memories_fts(query, k*2)` → résultats FTS5
3. Fusion et re-ranking : score combiné = `0.7 * semantic_score + 0.3 * fts_rank_normalized`
4. Déduplique par `memory_id`, retourne top `k`

### `get_memories_by_type(memory_type, limit)` → `list[dict]`

```sql
SELECT * FROM memories WHERE memory_type = ? ORDER BY importance DESC, created_at DESC LIMIT ?
```

### `get_recent_memories(hours, limit)` → `list[dict]`

Filtre `created_at >= now - timedelta(hours=hours)`

### `get_high_impact_memories(min_score, limit)` → `list[dict]`

```sql
SELECT * FROM memories WHERE importance >= ? ORDER BY access_count DESC LIMIT ?
```

---

## `EmbeddingController` — Génération de vecteurs

**Délégué** : `AIController` en mode embedding

### `async _generate_embedding(text)` → `np.ndarray` float32

1. Prétraite texte (tronque à 8192 tokens max)
2. `embedding_controller.get_embedding(text)` → `list[float]`
3. `np.array(embedding, dtype=np.float32)`
4. Normalise L2 (pour cosine similarity via FAISS Inner Product)

### Dimension auto-détection

Premier appel → mesure `len(embedding)` → initialise FAISS index avec cette dimension.  
Dimensions communes :
- OpenAI `text-embedding-3-small` : 1536
- OpenAI `text-embedding-3-large` : 3072
- Ollama (nomic-embed-text) : 768
- Ollama (mxbai-embed-large) : 1024

---

## Pipeline de récupération contextuelle — `ArchivisteMemoryOptimizer`

**Fichier** : `archiviste_memory_optimizer.py`  
**Rôle** : Choisit quels souvenirs injecter dans le contexte de l'IA principale, avec double intervention de l'Archiviste pour maximiser la pertinence.

### Vue d'ensemble du pipeline (5 étapes)

```
Message utilisateur
        │
        ▼
[Étape 1] _analyze_user_intent()
  L'Archiviste génère 8-10 requêtes SMART
        │
        ▼
[Étape 2] search_memories_batch()
  70% FAISS vectoriel + 30% FTS5 keywords
  Smart Stop si redondance > 80%
  Dédup L1 (IDs) + L2 (cosine > 0.85)
        │
        ▼
[Étape 2.5] Filtre cooldown
  Exclut souvenirs récemment injectés
  (sauf si keyword_score ≥ 0.70)
        │
        ▼
[Étape 3] Top 7 candidats sélectionnés
        │
        ▼
[Étape 4] _filter_by_archiviste()
  L'Archiviste retourne JSON → 0-4 IDs vraiment pertinents
        │
        ▼
[Étape 5] Formatage final
  Top 2 : texte complet
  Reste : résumé 200 chars
  Cooldown appliqué uniquement aux retenus
```

### Étape 1 — `_analyze_user_intent()`

L'Archiviste (température 0.3) reçoit le message utilisateur et génère **8 à 10 requêtes SMART** diversifiées :
- Requêtes larges (thème général)
- Requêtes spécifiques (entités nommées, dates, lieux)
- Requêtes émotionnelles (ressentis associés)
- Requêtes contextuelles (situation, projet en cours)

Objectif : couvrir toutes les dimensions sémantiques du message pour maximiser le rappel.

### Étape 2 — `search_memories_batch()`

Pour chaque requête générée :
- **70%** du score = similarité vectorielle FAISS (cosine)
- **30%** du score = correspondance FTS5 plein-texte SQLite

**Smart Stop** : si un nouveau lot présente > 80% de souvenirs déjà vus, la recherche s'arrête (évite le bruit).

**Déduplication en deux niveaux** :
- L1 : par ID (souvenir exact déjà dans la liste)
- L2 : par similarité cosine > 0.85 entre embeddings (doublons sémantiques)

### Étape 2.5 — Filtre cooldown

Chaque souvenir injecté reçoit un **cooldown** (durée variable selon importance). Un souvenir en cooldown est exclu des candidats.

**Bypass** : si `keyword_score ≥ 0.70` (forte correspondance textuelle exacte), le cooldown est ignoré — le souvenir est trop directement pertinent pour être supprimé.

### Étape 3 — Top 7 candidats

Les candidats restants sont triés par score hybride. Les **7 meilleurs** sont transmis à l'Archiviste pour filtrage final.

### Étape 4 — `_filter_by_archiviste()`

L'Archiviste reçoit les 7 candidats (résumés + scores) et le message utilisateur. Il retourne un **JSON strict** contenant 0 à 4 IDs réellement pertinents pour ce message précis.

Critères de sélection de l'Archiviste :
- Lien direct ou indirect avec le sujet du message
- Apport informationnel réel (pas de répétition de ce qui est déjà dans la conversation)
- Pertinence émotionnelle ou contextuelle justifiée

### Étape 5 — Formatage final

Parmi les IDs retenus par l'Archiviste :
- **Top 2** (par score) → texte complet du souvenir
- **Suivants** → résumé tronqué à 200 caractères

Le cooldown est mis à jour **uniquement pour les souvenirs effectivement retenus** (pas les 7 candidats, seulement ceux injectés).

### `OptimizedContext` — dataclass de retour

```python
@dataclass
class OptimizedContext:
    memories: List[Dict]        # Souvenirs retenus avec texte/résumé
    queries_used: List[str]     # Requêtes SMART générées (Étape 1)
    total_candidates: int       # Nombre de candidats avant filtrage
    archiviste_filtered: int    # Nombre retenu après Archiviste (Étape 4)
    injection_text: str         # Bloc texte prêt à injecter dans le prompt
```

### Pourquoi deux interventions de l'Archiviste ?

| Problème | Sans double intervention |
|---|---|
| Requêtes trop larges | Dizaines de faux positifs par similarité superficielle |
| Requêtes trop étroites | Manquer des souvenirs thématiquement proches mais formulés différemment |
| Regroupement par impact | FAISS regroupe par proximité vectorielle, pas par pertinence pour *ce* message |

L'Étape 1 résout le problème du rappel (trouver assez de candidats variés).  
L'Étape 4 résout le problème de la précision (ne garder que ce qui compte vraiment).

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/memory/ogma_memory.db` | Base SQLite principale |
| `data/memory/faiss.index` | Index vectoriel FAISS sérialisé |
| `data/memory/backup_{1-4}.db` | Backups rotatifs FIFO |
| `data/memory/rebuild_log.txt` | Log reconstruction FAISS |

---

## Scripts utilitaires

| Script | Usage |
|--------|-------|
| `test_memory_system.py` | Tests complets SQLite + FAISS |
| `rebuild_faiss_safe.py` | Reconstruction index FAISS depuis SQLite sans perte |
