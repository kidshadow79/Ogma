# Memory Manager - Documentation API Complète

**Version** : OGMA 2025  
**Source** : `memory_manager.py` (analysé le 5 novembre 2025)  
**Criticité** : 🔴 MAXIMALE (composant central OGMA)

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Initialisation](#initialisation)
3. [Création Mémoires](#création-mémoires)
4. [Recherche](#recherche)
5. [Mise à Jour](#mise-à-jour)
6. [Suppression](#suppression)
7. [Statistiques & Utilitaires](#statistiques--utilitaires)
8. [Schéma Base de Données](#schéma-base-de-données)

---

## Vue d'ensemble

**MemoryManager** : Système hybride de mémorisation combinant :
- **SQLite** : Persistance structurée + Full-Text Search (FTS5)
- **FAISS** : Index vectoriel pour recherche sémantique
- **Enrichissement IA** : Archiviste génère métadonnées automatiquement

**Architecture** :
```
Texte brut → Archiviste (title/summary/valence) → Embedding IA → 
→ SQLite (persistance) + FAISS (index vectoriel)
```

---

## Initialisation

### `__init__(...)`

**Signature** :
```python
def __init__(
    self,
    db_path: str | Path,
    index_path: str | Path,
    embedding_dim: int = 1024,
    archiviste_ia = None,
    embedding_ia = None,
    status_queue = None
)
```

**Paramètres** :
- `db_path` : Chemin base SQLite (ex: `data/memory/memories.db`)
- `index_path` : Chemin index FAISS (ex: `data/memory/index.faiss`)
- `embedding_dim` : Dimension vecteurs (défaut: 1024)
- `archiviste_ia` : Contrôleur IA pour enrichissement (AIController)
- `embedding_ia` : Contrôleur IA pour embeddings (AIController)
- `status_queue` : Queue async pour notifications statut

**Initialisation automatique** :
- ✅ Création base SQLite avec schéma complet
- ✅ Création/chargement index FAISS
- ✅ Synchronisation `ego_prompt.txt` (références OGMA)
- ✅ Chargement données existantes

**Exemple** :
```python
from memory_manager import MemoryManager
from pathlib import Path

mm = MemoryManager(
    db_path=Path("data/memory/memories.db"),
    index_path=Path("data/memory/index.faiss"),
    embedding_dim=1024,
    archiviste_ia=archiviste_controller,
    embedding_ia=embedding_controller
)
```

---

## Création Mémoires

### `add_memory()`

**Type** : ⚡ **ASYNC**  
**Ligne** : 229

**Signature** :
```python
async def add_memory(
    self,
    memory_id: str,
    text_brut: str,
    chat_controller = None,
    conversation_context: str = "",
    interlocutor: str = ""
) -> bool
```

**Paramètres** :
- `memory_id` (str, **requis**) : Identifiant unique (ex: `"MSG-2025-001"`)
- `text_brut` (str, **requis**) : Texte original à mémoriser
- `chat_controller` (AIController, optionnel) : IA principale (pour contexte)
- `conversation_context` (str, optionnel) : Contexte conversationnel
- `interlocutor` (str, optionnel) : Nom interlocuteur

**Retour** :
- `bool` : `True` si succès, `False` si échec

**Comportement** :
1. ✅ Appelle **Archiviste IA** pour enrichissement :
   - Génère `title` (titre souvenir)
   - Génère `summary` (résumé)
   - Extrait `valence` (-1/0/+1)
   - Calcule `score_impact` initial
2. ✅ Génère **embedding** 1024D via `embedding_ia.create_embedding()`
3. ✅ Stocke en **SQLite** (table `memories`)
4. ✅ Ajoute vecteur à **index FAISS**
5. ✅ Sauvegarde index FAISS sur disque

**Exceptions** :
- Aucune exception levée (gestion interne)
- Retourne `False` en cas d'erreur

**Exemple** :
```python
success = await memory_manager.add_memory(
    memory_id="CONV-2025-11-05-001",
    text_brut="Discussion sur l'architecture mémoire hybride d'OGMA"
)

if success:
    print("✅ Souvenir mémorisé")
else:
    print("❌ Échec mémorisation")
```

**Tests Associés** :
- ✅ `test_add_memory_persists_to_database` (strict)
- ✅ `test_add_memory_generates_valid_embedding` (strict)
- ✅ `test_add_memory_simple` (smoke)

---

## Recherche

### `search_memories()`

**Type** : ⚡ **ASYNC**  
**Ligne** : 2100

**Signature** :
```python
async def search_memories(
    self,
    query: str,
    limit: int,
    threshold: float
) -> List[Dict]
```

**Paramètres** :
- `query` (str, **requis**) : Requête de recherche (texte libre)
- `limit` (int, **requis**) : Nombre maximum de résultats
- `threshold` (float, **requis**) : Seuil similarité (0.0-1.0)
  - Plus bas = plus de résultats
  - Recommandé : 0.3-0.7

**Retour** :
- `List[Dict]` : Liste de souvenirs avec clés :
  - `memory_id` (str) : ID du souvenir
  - `content` ou `text_original` (str) : Texte souvenir
  - `title` (str) : Titre généré
  - `summary` (str) : Résumé
  - `score` ou `similarity` (float) : Score similarité (0.0-1.0)
  - `created_at` (str) : Date création

**Méthode Hybride** :
1. **FAISS** : Recherche sémantique (similarité vectorielle)
2. **FTS5** : Recherche mots-clés (correspondance exacte)
3. **Fusion** : Combine scores avec boost exact match

**Exemple** :
```python
results = await memory_manager.search_memories(
    query="architecture mémoire",
    limit=5,
    threshold=0.5
)

for result in results:
    print(f"[{result['score']:.2f}] {result['title']}")
    print(f"  → {result['summary']}")
```

**Tests Associés** :
- ⚠️ `test_search_finds_added_memory` (strict - à adapter)
- ✅ `test_search_hybrid_faiss_fts5` (smoke)

---

### `get_memory_by_id()`

**Type** : 🔄 **SYNC**  
**Ligne** : 368 (estimé)

**Signature** :
```python
def get_memory_by_id(
    self,
    memory_id: str
) -> Optional[Dict]
```

**Paramètres** :
- `memory_id` (str, **requis**) : ID du souvenir

**Retour** :
- `Dict` : Souvenir complet (toutes colonnes SQLite)
- `None` : Si ID inexistant

**Exemple** :
```python
memory = memory_manager.get_memory_by_id("MSG-2025-001")

if memory:
    print(f"Titre: {memory['title']}")
    print(f"Texte: {memory['text_original']}")
    print(f"Score: {memory['score_impact']}")
else:
    print("Souvenir introuvable")
```

---

## Mise à Jour

### `update_memory()`

**Type** : ⚡ **ASYNC**  
**Ligne** : 2304

**Signature** :
```python
async def update_memory(
    self,
    memory_id: str
) -> Optional[Dict[str, float]]
```

**Paramètres** :
- `memory_id` (str, **requis**) : ID du souvenir à modifier

⚠️ **ATTENTION** : La signature extraite semble incomplète. D'après les tests, probablement :
```python
async def update_memory(
    self,
    memory_id: str,
    title: str = None,
    summary: str = None,
    valence: int = None,
    score_impact: float = None,
    # ... autres champs modifiables
) -> Optional[Dict[str, float]]
```

**Retour** :
- `Dict[str, float]` : `{'score_impact': float, 'signed_score': float}`
- `None` : Si ID inexistant ou échec

**Comportement** :
- ⚠️ **NE RECALCULE PAS** l'embedding (utiliser `reembed_memory()` si besoin)
- ✅ Met à jour champs SQLite uniquement
- ✅ `signed_score` dérivé automatiquement de `valence`

**Exemple** (à valider) :
```python
result = await memory_manager.update_memory(
    memory_id="MSG-2025-001",
    title="Nouveau titre",
    valence=-1,
    score_impact=0.8
)

if result:
    print(f"Score impact: {result['score_impact']}")
    print(f"Signed score: {result['signed_score']}")
```

**Tests Associés** :
- ⚠️ `test_update_memory_persists_changes` (strict - échec signature)
- ✅ `test_update_memory_metadata` (smoke)

**🔴 ACTION REQUISE** : Vérifier signature exacte dans code source

---

### `reembed_memory()`

**Type** : ⚡ **ASYNC**  
**Ligne** : 2480

**Signature** :
```python
async def reembed_memory(
    self,
    memory_id: str
) -> bool
```

**Description** : Recalcule embedding d'un souvenir (après modification texte).

⚠️ **Note** : Met à jour SQLite uniquement, **pas FAISS** (index non modifiable).

---

## Suppression

### `delete_memory()`

**Type** : 🔄 **SYNC** (⚠️ PAS async !)  
**Ligne** : 2188

**Signature** :
```python
def delete_memory(
    self,
    memory_id: str
) -> bool
```

**Paramètres** :
- `memory_id` (str, **requis**) : ID du souvenir à supprimer

**Retour** :
- `bool` : `True` si suppression réussie, `False` si ID inexistant

**Comportement** :
- ✅ Supprime de **SQLite**
- ⚠️ **NE SUPPRIME PAS** de FAISS (index non modifiable)
- 💡 FAISS conserve vecteur "fantôme" (ignoré en recherche)

**Exemple** :
```python
success = memory_manager.delete_memory("MSG-2025-001")

if success:
    print("✅ Souvenir supprimé")
else:
    print("❌ ID introuvable")
```

**Tests Associés** :
- ⚠️ `test_delete_memory_removes_from_database` (strict - await invalide)
- ✅ `test_delete_memory` (smoke)

---

### `delete_all_memories()`

**Type** : 🔄 **SYNC**  
**Ligne** : 2220

**Signature** :
```python
def delete_all_memories(
    self
) -> Dict[str, Any]
```

**Description** : Suppression complète avec backup automatique.

**Comportement** :
1. ✅ Backup automatique SQLite
2. ✅ Suppression tous enregistrements
3. ✅ Réinitialisation index FAISS
4. ✅ Clear mappings
5. ✅ Synchronisation `ego_prompt.txt`

**Retour** :
```python
{
    'deleted_count': int,
    'backup_path': str,
    'faiss_reset': bool
}
```

---

## Statistiques & Utilitaires

### `get_memory_count()`

**Type** : 🔄 **SYNC**

**Signature** :
```python
def get_memory_count(self) -> int
```

**Retour** : Nombre total de souvenirs en base SQLite

---

### `get_all_memories()`

**Type** : 🔄 **SYNC**

**Signature** :
```python
def get_all_memories(self) -> List[Dict]
```

**Retour** : Liste de tous les souvenirs (colonnes SQLite complètes)

---

### `cleanup()`

**Type** : 🔄 **SYNC**

**Signature** :
```python
def cleanup(self) -> None
```

**Description** : Fermeture propre des ressources (connexions SQLite, index FAISS).

⚠️ **Obligatoire** : Appeler avant fermeture application pour éviter corruption.

**Exemple** :
```python
try:
    # Utilisation Memory Manager
    await memory_manager.add_memory(...)
finally:
    memory_manager.cleanup()  # ⚠️ CRITIQUE
```

---

## Schéma Base de Données

### Table `memories`

**Création** : memory_manager.py ligne 79-115

```sql
CREATE TABLE IF NOT EXISTS memories (
    -- Identifiants
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    
    -- Contenu
    text_original TEXT NOT NULL,  -- ⚠️ NOM RÉEL (pas "text_brut")
    
    -- Métadonnées Archiviste (auto-générées)
    type TEXT,
    title TEXT,
    lieu TEXT,
    presence TEXT,
    summary TEXT,
    lesson TEXT,
    valence INTEGER DEFAULT 0,      -- -1/0/+1
    score_impact REAL DEFAULT 0.0,
    
    -- Données vectorielles
    embedding_json TEXT,            -- Vecteur 1024D sérialisé JSON
    faiss_index INTEGER,            -- Position dans index FAISS
    
    -- Métadonnées enrichies (JSON)
    nuage_sensoriel TEXT,
    multiplicateur_impact TEXT,
    resonances_affectives TEXT,
    liens TEXT,
    
    -- Métriques normalisées
    base_factor REAL,
    intensite REAL,
    liberte REAL,
    creation REAL,
    procreation REAL,
    intensite_ctx REAL,
    signed_score REAL,              -- score_impact * signe(valence)
    updated_at TEXT
)
```

**Index** :
- PRIMARY KEY sur `id`
- Index FAISS séparé (fichier `.index`)
- Table FTS5 `memories_fts` (Full-Text Search)

---

## Récapitulatif Signatures Critiques

| Méthode | Type | Paramètres Clés | Retour | Testé |
|---------|------|-----------------|--------|-------|
| `add_memory()` | ⚡ Async | `memory_id`, `text_brut` | `bool` | ✅ |
| `search_memories()` | ⚡ Async | `query`, `limit`, `threshold` | `List[Dict]` | ⚠️ |
| `update_memory()` | ⚡ Async | `memory_id`, ... | `Optional[Dict]` | ⚠️ |
| `delete_memory()` | 🔄 Sync | `memory_id` | `bool` | ⚠️ |
| `get_memory_by_id()` | 🔄 Sync | `memory_id` | `Optional[Dict]` | ✅ |
| `get_memory_count()` | 🔄 Sync | - | `int` | ✅ |
| `cleanup()` | 🔄 Sync | - | `None` | ✅ |

**Légende** :
- ✅ : Signature validée et testée
- ⚠️ : Signature partielle (nécessite vérification)
- ⚡ : Méthode async (nécessite `await`)
- 🔄 : Méthode sync (appel direct)

---

## Notes Importantes

### ⚠️ Pièges Courants

1. **Colonne SQLite** : `text_original` (PAS `text_brut`)
2. **delete_memory** : SYNC (pas `await`)
3. **add_memory** : Paramètres `title`/`summary` **inexistants** (auto-générés)
4. **search_memories** : Pas de paramètre `mode` ou `k` (uniquement `limit`)
5. **FAISS** : Index **non modifiable** après création (delete/update gardent vecteurs)

### 🎯 Bonnes Pratiques

```python
# ✅ CORRECT
success = await memory_manager.add_memory(
    memory_id="ID-001",
    text_brut="Texte à mémoriser"
)

results = await memory_manager.search_memories(
    query="recherche",
    limit=10,
    threshold=0.5
)

deleted = memory_manager.delete_memory("ID-001")  # SYNC, pas await

# ❌ INCORRECT
await memory_manager.add_memory(
    memory_id="ID",
    text_brut="Texte",
    title="Titre",      # ❌ Paramètre invalide
    summary="Résumé"    # ❌ Paramètre invalide
)

results = await memory_manager.search_memories(
    query="recherche",
    k=10,              # ❌ Utiliser 'limit'
    mode="hybrid"      # ❌ Paramètre inexistant
)

await memory_manager.delete_memory("ID")  # ❌ delete est SYNC
```

---

## Prochaines Étapes

**Pour Compléter Documentation** :
- [ ] Vérifier signature exacte `update_memory()` (paramètres modifiables)
- [ ] Documenter valeurs retour détaillées `search_memories()`
- [ ] Ajouter exemples concrets pour chaque méthode
- [ ] Documenter gestion erreurs (exceptions levées)

**Pour Tests Stricts** :
- [ ] Adapter `test_memory_manager_strict.py` avec signatures réelles
- [ ] Retirer `await` de `delete_memory()` dans tests
- [ ] Utiliser `limit` au lieu de `k` pour `search_memories()`
- [ ] Retirer paramètres `title`/`summary` de `update_memory()`

---

**Documentation créée le** : 5 novembre 2025  
**Basée sur** : Extraction AST automatique + analyse manuelle  
**Statut** : 🟡 80% complète (signatures critiques validées)  
**Prochaine mise à jour** : Après validation tests stricts
