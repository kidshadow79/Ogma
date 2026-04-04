# 🧠 COGNITIVE CACHE — Plan d'Implémentation OGMA

**Date de rédaction** : 4 avril 2026  
**Auteur** : Yohan BROCARD + GitHub Copilot  
**Version cible** : OGMA v2.3  
**Statut** : 🟡 En cours de planification

---

## 🎯 Concept

Le **Cache Cognitif** est un espace de pensées persistant par conversation.
L'IA Principale peut y écrire librement via des **phrases magiques dédiées**,
sans appel API supplémentaire. Ce cache suit fidèlement la conversation,
survive entre les sessions (10 conversations max), et alimente le Dream Engine
comme carburant mémoriel.

---

## 🏗️ Architecture Finale

```
data/
└── cognitive_cache/
    ├── {conv_id_1}.json   ← plus ancienne
    ├── {conv_id_2}.json
    └── {conv_id_N}.json   ← plus récente (max 10 fichiers)
```

### Structure d'un fichier cache

```json
{
  "conv_id": "2026-04-04_14-23-11",
  "created_at": "2026-04-04T14:23:11",
  "updated_at": "2026-04-04T15:01:45",
  "entries": [
    {
      "id": "cache-uuid-1234",
      "type": "directive",
      "content": "ne pas écrire le CV à sa place, corriger seulement la syntaxe",
      "created_at": "2026-04-04T14:25:00",
      "active": true
    },
    {
      "id": "cache-uuid-5678",
      "type": "observation",
      "content": "l'utilisateur semble fatigué, j'observe avant d'en parler",
      "created_at": "2026-04-04T14:55:00",
      "active": true
    },
    {
      "id": "cache-uuid-9999",
      "type": "idea_pending",
      "content": "lui parler du concept de mémoire distribuée plus tard",
      "created_at": "2026-04-04T15:01:00",
      "active": true
    }
  ]
}
```

### Types d'entrées

| Type | Description | Exemple |
|---|---|---|
| `directive` | Contrainte utilisateur explicite | "ne pas écrire à ma place" |
| `observation` | Pensée secrète en attente | "utilisateur fatigue, j'observe" |
| `idea_pending` | Idée à aborder plus tard | "parler du concept X" |
| `context_anchor` | Ancrage thématique | "on travaille sur son CV" |

---

## 📝 Phrases Magiques (syntaxe IA Principale)

L'IA Principale utilise ces commandes dans ses réponses :

```
CACHE_ADD:[type]:[contenu]
CACHE_DELETE:[id]
CACHE_UPDATE:[id]:[nouveau contenu]
CACHE_CLEAR
```

**Exemples concrets :**
```
CACHE_ADD:directive:ne pas rédiger à sa place, corriger seulement la syntaxe
CACHE_ADD:observation:l'utilisateur semble fatigué, surveiller avant d'en parler
CACHE_DELETE:cache-uuid-5678
CACHE_CLEAR
```

---

## 🔄 Cycle de Vie Complet

```
💬 PENDANT LA CONVERSATION
   IA Principale écrit via CACHE_ADD/DELETE/UPDATE/CLEAR
   → Détection post-streaming (comme phrases magiques mémoire)
   → Mise à jour data/cognitive_cache/{conv_id}.json
   → Log flux_cognitif (type 'cache')

🌅 AU DÉMARRAGE (_async_awakening, Vague 4.5)
   → Charger les N fichiers JSON existants (max 10)
   → Injecter résumé de continuité en system prompt P0
   → (pas d'élagage ici — fait à la fermeture)

😴 PENDANT DREAM ENGINE
   → Snapshot cache au début (lecture figée)
   → dream_fuel() = souvenirs + #MEM + snapshot cache cognitif
   → Si entrée importante → migration vers FAISS
   → Cache session nettoyé des entrées migrées

🔴 À LA FERMETURE (delayed_shutdown)
   Ordre garanti :
   1. run_shutdown_analysis()         ← Journal
   2. compile_ego_incremental()       ← Ego absorbé
   3. cognitive_cache_cleanup()       ← Élagage top 10 ← NOUVEAU
   4. os._exit(0)
```

---

## 🗺️ POINTS D'ANCRAGE CODE (références exactes ogma_ng.py)

| Étape | Fonction / Ligne | Action |
|---|---|---|
| Import | Ligne ~195 (bloc `try/except` imports extensions) | Ajouter import cognitive_cache |
| Init démarrage | `_async_awakening()` ligne 7555 | Charger cache après mémoire |
| Injection prompt | `_send_chat_message()` ligne 1903 → après `magic_ai = _extract_magic_memories(scan_text)` ligne 2538 | Détecter CACHE_* |
| Reset conv | `_new_conversation()` (dans ogma_ui_conversations.py) | Nouveau conv_id cache |
| Fermeture | `delayed_shutdown()` ligne 8225 → après `compile_ego_incremental()` ligne 8249, avant `os._exit(0)` ligne 8255 | Élagage top 10 |
| Flux cognitif | `extensions/flux_cognitif/__init__.py` → `_default_filters` ligne 40 | Ajouter filtre `'cache'` |
| Dream fuel | `extensions/dream_engine/dream_memory.py` → `extract_dream_fuel()` ligne 80 | Ajouter snapshot cache |

---

## ✅ TODO LIST — Ordre d'Implémentation

### PHASE 1 — Extension cognitive_cache (nouveau module)

- [ ] **1.1** Créer `extensions/cognitive_cache/__init__.py`
  - Pattern singleton standard OGMA
  - API publique : `initialize`, `is_available`, `cleanup`

- [ ] **1.2** Créer `extensions/cognitive_cache/cache_manager.py`
  - `load_cache(conv_id)` → charge ou crée le JSON
  - `save_cache(conv_id, data)` → sauvegarde atomique
  - `add_entry(conv_id, type, content)` → ajoute entrée
  - `delete_entry(conv_id, entry_id)` → supprime entrée
  - `update_entry(conv_id, entry_id, content)` → modifie
  - `clear_cache(conv_id)` → vide tout
  - `get_active_entries(conv_id)` → retourne entrées actives
  - `get_summary_for_injection(conv_id)` → texte pour system prompt
  - `get_snapshot(conv_id)` → copie profonde pour Dream Engine

- [ ] **1.3** Créer `extensions/cognitive_cache/cache_parser.py`
  - `parse_magic_phrases(text)` → regex sur CACHE_ADD/DELETE/UPDATE/CLEAR
  - Retourne liste d'opérations à appliquer
  - Tolérant aux variations de casse et espaces

- [ ] **1.4** Créer `extensions/cognitive_cache/cache_cleanup.py`
  - `cleanup_old_caches(max_conversations=10)` → élagage
  - Lit tous les fichiers `data/cognitive_cache/*.json`
  - Trie par `updated_at`
  - Supprime les plus anciens au-delà de max_conversations

- [ ] **1.5** Créer `data/cognitive_cache/` (dossier vide + `.gitkeep`)

---

### PHASE 2 — Intégration dans ogma_ng.py

> ⚠️ `ogma_ng.py` est quasi-gelé. Modifications minimales et chirurgicales uniquement.

- [ ] **2.1** Import du module en tête de fichier
  ```python
  try:
      from extensions.cognitive_cache import initialize_cognitive_cache, get_cache_manager
      COGNITIVE_CACHE_AVAILABLE = True
  except ImportError:
      COGNITIVE_CACHE_AVAILABLE = False
  ```

- [ ] **2.2** Initialisation dans `_async_awakening` (après Vague 4, avant Vague 6)
  - Charger le cache de la conv courante si elle existe
  - Injecter résumé dans `messages` au démarrage

- [ ] **2.3** Injection du cache dans `_send_chat_message`
  - Position : après injection mémoire FAISS, avant message utilisateur
  - Format : `[CACHE COGNITIF ACTIF]\n{résumé des entrées actives}`
  - Seulement si `len(active_entries) > 0`

- [ ] **2.4** Instruction dans le system prompt principal
  - Ajouter bloc dans `settings.json` → `prompts.cognitive_cache_instruction`
  - Expliquer à l'IA les 4 commandes CACHE_*
  - Injecter avec les autres instructions

- [ ] **2.5** Détection post-streaming (dans `_send_chat_message`, section post-traitement)
  - Après la section `magic_ai = _extract_magic_memories(cleaned_reply)`
  - Appeler `parse_magic_phrases(cleaned_reply)`
  - Appliquer les opérations au `cache_manager`
  - Logger dans flux_cognitif

- [ ] **2.6** Reset conv_id à chaque `_new_conversation()`
  - Créer un nouveau cache JSON pour la nouvelle conversation
  - Stocker `_current_cognitive_cache_id` en global

---

### PHASE 3 — Intégration Dream Engine

- [ ] **3.1** Modifier `extensions/dream_engine/dream_memory.py`
  - Dans `extract_dream_fuel()` : ajouter snapshot du cache cognitif
  - Format : `cognitive_snapshot = get_snapshot(current_conv_id)`
  - Passer au générateur de rêve comme nouvelle source

- [ ] **3.2** Modifier `extensions/dream_engine/dream_prompts.py`
  - Ajouter section cache cognitif dans le prompt de rêve
  - Format : `[PENSÉES EN FOND]\n{snapshot}`

- [ ] **3.3** Modifier `extensions/dream_engine/dream_analysis.py`
  - Après analyse PSY : identifier entrées cache à migrer en FAISS
  - Si score entrée > seuil → `mem.add_memory(...)` + supprimer du cache

---

### PHASE 4 — Intégration Flux Cognitif

- [ ] **4.1** Modifier `extensions/flux_cognitif/__init__.py`
  - Ajouter type d'événement `'cache'`
  - Style visuel distinct (couleur, icône)

- [ ] **4.2** Logger chaque opération CACHE_* dans le flux
  ```python
  log_cognitive_event('cache', f'CACHE_ADD:directive:{content[:60]}')
  log_cognitive_event('cache', f'CACHE_DELETE:{entry_id}')
  ```

---

### PHASE 5 — Intégration Fermeture (delayed_shutdown)

- [ ] **5.1** Modifier `cleanup_on_exit()` dans `ogma_ng.py`
  - Ajouter appel `cognitive_cache_cleanup()` APRÈS `compile_ego_incremental`
  - AVANT `os._exit(0)`

- [ ] **5.2** Vérifier que `delayed_shutdown()` est async et attend bien
  - La fonction est déjà async (`await asyncio.sleep(0.5)`)
  - Ajouter `await cognitive_cache_cleanup_async()` dans la séquence

---

### PHASE 6 — Instruction IA Principale

- [ ] **6.1** Rédiger l'instruction pour `settings.json`
  ```
  prompts.cognitive_cache_instruction :
  "Tu disposes d'un cache cognitif personnel. Tu peux y écrire librement...
  CACHE_ADD:[type]:[contenu] — ajouter une pensée
  CACHE_DELETE:[id] — supprimer une entrée
  CACHE_UPDATE:[id]:[contenu] — modifier
  CACHE_CLEAR — tout effacer
  Types : directive / observation / idea_pending / context_anchor
  Ces commandes sont invisibles pour l'utilisateur."
  ```

- [ ] **6.2** Injecter cette instruction dans `_send_chat_message`
  - Position : avec les autres instructions système (P1)

---

### PHASE 7 — Tests

- [ ] **7.1** Créer `tests/test_cognitive_cache.py`
  - Test add/delete/update/clear
  - Test parse_magic_phrases
  - Test cleanup_old_caches
  - Test snapshot (copie profonde)

- [ ] **7.2** Test intégration Dream Engine
  - Vérifier que le snapshot est bien passé
  - Vérifier migration FAISS si score élevé

- [ ] **7.3** Test fermeture
  - Simuler 12 conversations → vérifier que seules 10 restent

---

## ⚠️ Points de Vigilance

### Collisions Dream Engine
- **TOUJOURS** prendre un snapshot avant de lancer le rêve
- Ne jamais passer le cache live au Dream Engine
- L'élagage se fait APRÈS `compile_ego_incremental` (ego absorbé en premier)

### Indentation Python
- `parse_magic_phrases` utilise des regex : tester avec `re.IGNORECASE`
- Les opérations cache dans `_send_chat_message` sont dans un bloc `if reply is not None`
- Vérifier l'imbrication exacte (+4 espaces par niveau)

### ogma_ng.py gelé
- **Maximum 6 ajouts** dans ce fichier (import + init + injection + détection + reset + fermeture)
- Tout le reste dans `extensions/cognitive_cache/`

### JSON atomique
- Utiliser écriture en deux temps (fichier temp + rename) pour éviter corruption
- En cas d'erreur lecture : retourner cache vide, ne jamais crasher

---

## 📁 Fichiers Créés / Modifiés

### Nouveaux fichiers
```
extensions/cognitive_cache/__init__.py
extensions/cognitive_cache/cache_manager.py
extensions/cognitive_cache/cache_parser.py
extensions/cognitive_cache/cache_cleanup.py
data/cognitive_cache/.gitkeep
tests/test_cognitive_cache.py
docs/COGNITIVE_CACHE_IMPLEMENTATION_PLAN.md  ← CE FICHIER
```

### Fichiers modifiés (minimal)
```
ogma_ng.py                                    ← 6 touches chirurgicales
extensions/dream_engine/dream_memory.py       ← snapshot + carburant
extensions/dream_engine/dream_prompts.py      ← section cache dans prompt rêve
extensions/dream_engine/dream_analysis.py     ← migration FAISS
extensions/flux_cognitif/__init__.py           ← type 'cache'
data/settings.json                             ← instruction IA cache
```

---

## 🚀 Ordre d'Implémentation Recommandé

```
Phase 1 → Phase 4 → Phase 6 → Phase 2 → Phase 3 → Phase 5 → Phase 7
   ↑           ↑         ↑         ↑          ↑          ↑         ↑
Module    Flux log   Instruct  Inject    Dream     Fermeture  Tests
seul      (debug)    IA        ogma_ng   Engine    shutdown
```

Commencer par Phase 1+4+6 permet de tester le module seul
sans toucher à ogma_ng.py, puis intégrer progressivement.

---

## ✅ Définition de "Done"

- [ ] L'IA Principale peut écrire dans le cache sans appel API supplémentaire
- [ ] Le cache est injecté dans chaque prompt automatiquement
- [ ] Le Flux Cognitif affiche les opérations cache en temps réel
- [ ] Le Dream Engine utilise le snapshot cache comme carburant
- [ ] L'élagage fonctionne : max 10 fichiers après fermeture
- [ ] Aucun crash si le cache est corrompu ou absent
- [ ] Tests unitaires passent à 100%
