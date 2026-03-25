# Memory Manager API - Extraction Complète

**Date d'extraction**: 2025-11-05
**Source**: `memory_manager.py`
**Classe**: `MemoryManager`

## 📊 Statistiques

- **Total méthodes publiques**: 24
- **Méthodes synchrones**: 12
- **Méthodes asynchrones**: 12

---

## 📚 API Publique

### Initialization

#### `__init__()`

```python
def __init__(self, db_path: Path, index_path: Path, embedding_dim: int, archiviste_ia, embedding_ia, status_queue, *, use_formula_on_update: bool, settings_manager)
```

**Description**:

Initialise le gestionnaire de mémoire.

Args:
db_path: Chemin vers la base SQLite
index_path: Chemin vers l'index FAISS
embedding_dim: Dimension des vecteurs d'embedding
archiviste_ia: Contrôleur IA pour enrichissement/synthèse
embedding_ia: Contrôleur IA pour génération d'embeddings
status_queue: Queue pour messages de statut UI
settings_manager: Gestionnaire des paramètres pour accès aux prompts

---

#### `save_index()`

```python
def save_index(self)
```

**Description**:

Sauvegarde l'index FAISS sur disque.

---

#### `cleanup()`

```python
def cleanup(self)
```

**Description**:

Nettoie les ressources et ferme proprement les connexions.

---

#### `__del__()`

```python
def __del__(self)
```

**Description**:

Destructeur pour s'assurer du nettoyage.

---

### Memory CRUD

#### `add_memory()` `async`

```python
async def add_memory(self, memory_id: str, text_brut: str, chat_controller, conversation_context: str, interlocutor: str) -> bool
```

**Description**:

Ajoute un nouveau souvenir via le pipeline complet.

Pipeline MODIFIÉ - IA Principale scoring:
1. IA Principale calcule score_impact émotionnel/relationnel
2. IA Archiviste enrichit le texte brut (sans recalculer le score)
3. Génération embedding du contenu sémantique
4. Stockage SQLite du souvenir structuré
5. Ajout vecteur à l'index FAISS
6. Sauvegarde index

Args:
memory_id: Identifiant unique du souvenir
text_brut: Texte original à mémoriser
chat_controller: Contrôleur IA Principale pour scoring (optionnel)
conversation_context: Contexte conversationnel récent
interlocutor: Nom de l'interlocuteur privilégié

Returns:
bool: True si succès, False sinon

---

#### `update_memory()` `async`

```python
async def update_memory(self, memory_id: str, *, title: Optional[str], summary: Optional[str], text_original: Optional[str], valence: Optional[int], base_factor: Optional[float], intensite: Optional[float], liberte: Optional[float], creation: Optional[float], procreation: Optional[float], intensite_ctx: Optional[float], score_impact: Optional[float], reembed: bool) -> Optional[Dict[str, float]]
```

**Description**:

Met à jour un souvenir sans recalcul serveur de l'impact (politique IA-only).

- score_impact: si fourni, remplace la valeur existante; sinon, conserve la valeur stockée.
- signed_score: dérivé du signe de la valence (0 ⇒ 0, >0 ⇒ +score, <0 ⇒ -score).

Retourne { 'score_impact': float, 'signed_score': float } en cas de succès, sinon None.

---

#### `delete_memory()`

```python
def delete_memory(self, memory_id: str) -> bool
```

**Description**:

Supprime un souvenir (SQLite seulement, FAISS non modifiable).

---

#### `delete_all_memories()`

```python
def delete_all_memories(self) -> Dict[str, Any]
```

**Description**:

Supprime TOUS les souvenirs de manière sécurisée avec backup automatique.

Chaîne complète :
1. Backup automatique de la base SQLite
2. Suppression de tous les enregistrements SQLite
3. Réinitialisation de l'index FAISS
4. Clear des mappings id_to_faiss et faiss_to_id
5. Synchronisation ego_prompt.txt

Returns:
Dict avec les statistiques de suppression et info backup

---

#### `get_memory_by_id()`

```python
def get_memory_by_id(self, memory_id: str) -> Optional[Dict]
```

**Description**:

Récupère un souvenir par son ID depuis SQLite.

---

#### `get_memory_count()`

```python
def get_memory_count(self) -> int
```

**Description**:

Retourne le nombre total de souvenirs.

---

#### `get_all_memories_data()`

```python
def get_all_memories_data(self) -> List[dict]
```

**Description**:

Retourne toutes les données des mémoires depuis SQLite.

---

### Search & Retrieval

#### `search_memories()` `async`

```python
async def search_memories(self, query: str, limit: int, threshold: float) -> List[Dict]
```

**Description**:

Recherche directe dans FAISS/SQLite SANS censure pour Phase 0 introspection.

Args:
query: Requête de recherche (ex: "taille pénis")
limit: Nombre max de résultats
threshold: Seuil de similarité (plus bas = plus de résultats)

Returns:
Liste de souvenirs avec 'content', 'id', 'similarity'

---

#### `retrieve_and_synthesize_context()` `async`

```python
async def retrieve_and_synthesize_context(self, query_text: str, k: int) -> str
```

**Description**:

Récupère et synthétise les souvenirs pertinents pour une requête.

Pipeline HYBRIDE FAISS + FTS5:
1. Nettoyage de la requête (expansion pronoms + extraction mots-clés)
2. Génération embedding de la requête nettoyée
3. Recherche FAISS (similarité sémantique)
4. Recherche FTS5 (correspondance mots-clés)
5. Fusion des scores: (0.6 × FAISS) + (0.4 × FTS5) + (0.2 × exact_match)
6. Récupération contenu complet depuis SQLite
7. IA Archiviste génère une synthèse contextuelle

Args:
query_text: Requête utilisateur
k: Nombre de souvenirs à récupérer

Returns:
str: Note de synthèse de l'Archiviste

---

#### `retrieve_synthesis_and_memories()` `async`

```python
async def retrieve_synthesis_and_memories(self, query_text: str, k: int, top_memories: int) -> Tuple[Optional[str], List[Dict]]
```

**Description**:

Version hybride: récupère synthèse + souvenirs détaillés pour Luna.

Args:
query_text: Requête utilisateur
k: Nombre de souvenirs à récupérer via FAISS
top_memories: Nombre de souvenirs détaillés à retourner (les meilleurs)

Returns:
Tuple[synthèse_archiviste, liste_souvenirs_détaillés]

---

#### `retrieve_hybrid_optimized()` `async`

```python
async def retrieve_hybrid_optimized(self, query_text: str, k: int) -> Tuple[Optional[str], List[Dict]]
```

**Description**:

NOUVELLE ARCHITECTURE HYBRIDE OPTIMISÉE :
- 2 souvenirs DIRECTS (top pertinence, sans filtrage Archiviste)
- 3 souvenirs via Archiviste (2 pertinence + 1 impact)
- Synthèse Archiviste sur 5 souvenirs suivants avec consigne détails/chiffres

Args:
query_text: Requête utilisateur
k: Nombre de souvenirs à récupérer via FAISS (défaut: 12)

Returns:
Tuple[synthèse_archiviste, liste_5_souvenirs_avec_flags]

---

#### `retrieve_mixed_context()` `async`

```python
async def retrieve_mixed_context(self, query_text: str, k: int) -> Tuple[Optional[str], List[Dict]]
```

**Description**:

LEGACY : Ancienne logique mixte, remplacée par retrieve_hybrid_optimized.
Gardée pour compatibilité temporaire.

---

#### `retrieve_full_texts_context()` `async`

```python
async def retrieve_full_texts_context(self, query_text: str, k: int) -> Tuple[Optional[str], List[Dict]]
```

**Description**:

Version textes intégraux : récupère synthèse + textes complets des souvenirs.
Utilisée quand l'utilisateur demande explicitement plus de détails.

Args:
query_text: Requête utilisateur
k: Nombre de souvenirs à récupérer via FAISS

Returns:
Tuple[synthèse_archiviste, liste_souvenirs_avec_textes_complets]

---

### Ego & Identity

#### `store_ego_trait()` `async`

```python
async def store_ego_trait(self, trait_text: str, chat_controller, conversation_context: str, interlocutor: str) -> str
```

**Description**:

Stocke un trait de personnalité ego avec métadonnées spéciales.
Utilise exactement le même système de calcul de score que add_memory().

Args:
trait_text: Le trait de personnalité à stocker
chat_controller: Contrôleur IA Principale pour scoring (obligatoire)
conversation_context: Contexte conversationnel récent
interlocutor: Nom de l'interlocuteur (défaut: "self" pour ego)

Returns:
str: L'ID mémoire généré (format #MEM_XXXXX)

---

#### `sync_ego_prompt_references()`

```python
def sync_ego_prompt_references(self) -> bool
```

**Description**:

Synchronise automatiquement le fichier ego_prompt.txt avec la base de données.
Supprime les références orphelines et détecte les traits manquants.

Returns:
bool: True si des modifications ont été faites

---

### Maintenance

#### `rebuild_faiss_index()`

```python
def rebuild_faiss_index(self) -> Dict[str, int]
```

**Description**:

Reconstruit l'index FAISS à partir des embeddings SQLite.

Returns un dict stats: { 'added': n, 'skipped': m, 'total': t }

---

#### `repair_mapping_inconsistencies()`

```python
def repair_mapping_inconsistencies(self) -> Dict[str, int]
```

**Description**:

Répare les incohérences de mapping FAISS sans reconstruire l'index complet.

Identifie et corrige les positions FAISS qui existent dans l'index mais
ne sont pas dans les mappings id_to_faiss/faiss_to_id.

Returns:
Dict avec statistiques de réparation

---

#### `reembed_memory()` `async`

```python
async def reembed_memory(self, memory_id: str) -> bool
```

**Description**:

Recalcule l'embedding d'un souvenir et met à jour SQLite (ne touche pas FAISS).

---

#### `re_enrich_memory()` `async`

```python
async def re_enrich_memory(self, memory_id: str, *, reembed: bool, rebuild_faiss: bool) -> Optional[Dict[str, Any]]
```

**Description**:

Ré-enrichit un souvenir via l'Archiviste, met à jour SQLite, puis réembede et reconstruit FAISS si demandé.

Retourne un dict avec quelques champs clés mis à jour, sinon None.

---

#### `diagnose_search_quality()` `async`

```python
async def diagnose_search_quality(self, query_text: str, k: int) -> None
```

**Description**:

Diagnostique la qualité de recherche FAISS pour une requête donnée.
Affiche les détails des embeddings et scores pour debug.

---
