# README — Conversation Summarizer

**Fichier source** : `conversation_summarizer.py` (racine OGMA)  
**Type** : Module core (pas une extension)  
**Rôle** : Compression progressive des conversations longues par résumés persistants + analyse critique "subconsciente" via l'Archiviste

---

## 1. Concept Fondamental

### Le Problème

Une conversation longue dépasse rapidement la fenêtre de contexte d'un LLM. Envoyer tout l'historique brut à chaque message est coûteux en tokens et souvent impossible.

### La Solution OGMA : Fenêtre Glissante 30/20

```
Frontend (NiceGUI)  : affiche TOUS les messages (historique complet)
Backend (LLM)       : reçoit résumés compressés + N messages récents en clair
```

**Cycle de résumisation** :

```
20 messages récents en clair
        ↓ (l'utilisateur continue à parler)
30 messages non résumés atteints → DÉCLENCHEMENT
        ↓
Résumé du bloc [0-9] créé par l'Archiviste (10 messages → ~300 tokens)
        ↓
Retour à : 1 résumé + 20 messages récents en clair
        ↓ (cycle recommence)
```

Les résumés s'accumulent. Quand il y en a plus de 5, ils sont **fusionnés par paires** jusqu'à ce qu'il en reste ≤ 3 (voir §5).

---

## 2. Feature "Subconscient Archiviste"

C'est la fonctionnalité la plus originale du module : pendant la résumisation, l'Archiviste ne fait pas que compresser — il **analyse et critique** le comportement de l'IA Principale.

### Principe

Si le fichier `data/ego_compiled.json` est disponible, chaque résumé déclenche une analyse critique :

> *"L'IA Principale a-t-elle été trop complaisante ? A-t-elle contredit son EGO ? A-t-elle produit une information douteuse ?"*

L'Archiviste retourne simultanément :
- Le résumé narratif habituel
- Des **réflexions critiques** (`reflexions_archiviste`) notées 1–5 en importance

### Format de réponse JSON (mode EGO actif)

```json
{
  "resume": "Yohan a demandé une explication des réseaux de neurones. Luna a répondu...",
  "reflexions_archiviste": [
    {"message": "L'IA a validé une affirmation inexacte sur les transformers", "importance": 4},
    {"message": "Ton trop enthousiaste, potentiellement complaisant", "importance": 3},
    {"message": "Réponse cohérente avec l'EGO sur ce point", "importance": 2}
  ]
}
```

### Règles des réflexions

| Paramètre | Valeur |
|---|---|
| Maximum de réflexions | 3 |
| Importance min/max | 1 – 5 |
| Longueur max par réflexion | 300 caractères |
| Seuil d'injection dans le contexte | importance >= 3 (configurable) |

### Injection dans le contexte IA

Les réflexions haute importance (>= seuil) sont récupérées via `get_pending_reflexions(seuil=3)` et injectées dans le contexte de la prochaine requête à l'IA Principale, lui permettant de s'autocorriger sans intervention explicite de l'utilisateur.

---

## 3. Deux Modes de Résumisation

Le mode est choisi **automatiquement** selon la disponibilité de l'EGO.

### Mode A — JSON avec analyse critique (EGO disponible)

```
ego_compiled.json présent → use_json = True
```

| Paramètre | Valeur |
|---|---|
| `temperature` | 0.3 (précis, analytique) |
| `max_tokens` | 600 |
| `is_json` | True |
| Sortie | `{resume, reflexions_archiviste: [...]}` |

### Mode B — Texte libre (sans EGO)

```
ego_compiled.json absent → use_json = False
```

| Paramètre | Valeur |
|---|---|
| `temperature` | 0.7 (plus libre) |
| `max_tokens` | 400 |
| `is_json` | False |
| Sortie | Texte narratif brut |

---

## 4. Architecture et Persistance

### Persistance : JSON conversation étendu

Les résumés ne sont **plus sauvegardés dans des fichiers `.txt` séparés**. Ils sont intégrés directement dans le JSON de la conversation :

```json
{
  "messages": [ ... ],
  "summaries": {
    "ranges": [
      {
        "start": 0,
        "end": 10,
        "text": "Yohan a demandé une explication...",
        "cache_key": "abc123def456",
        "reflexions": [
          {"message": "Réponse trop permissive", "importance": 4}
        ]
      },
      {
        "start": 10,
        "end": 20,
        "text": "La conversation a continué sur...",
        "cache_key": "fedcba654321"
      }
    ],
    "last_index": 20,
    "interval": 10
  }
}
```

### Cache RAM de session

En plus du JSON, un cache RAM `_session_cache` (dict `cache_key → texte`) évite de réappeler l'API pour des blocs déjà résumés dans la même session.

**Clé de cache** : SHA256[:16] du contenu sérialisé des messages du bloc.

```
Bloc messages → SHA256[:16] → "_session_cache[key]" ou appel API
```

### Attributs clés

| Attribut | Défaut | Description |
|---|---|---|
| `summary_interval` | `10` | Taille d'un bloc à résumer |
| `summarize_trigger` | `30` | Déclenchement quand N messages non résumés |
| `min_recent_messages` | `20` | Messages récents gardés en clair (minimum garanti) |
| `max_summary_tokens` | `300` | Cible tokens par résumé |
| `archiviste` | `None` | Configuré post-init via `set_archiviste()` |
| `_session_cache` | `{}` | Cache RAM (clé → texte résumé) |
| `_current_summaries` | `[]` | Liste des entrées `{start, end, text, cache_key, reflexions}` |
| `_last_summarized_index` | `0` | Index du dernier message résumé |
| `_last_reflexions` | `[]` | Tampon réflexions du dernier appel API |

---

## 5. Fusion des Résumés

Quand le nombre de résumés dépasse **5**, `optimize_conversation_history()` déclenche une phase de fusion :

```
> 5 résumés → fusion par paires jusqu'à ≤ 3 résumés
```

**Exemple** : 6 résumés → fusion [R1+R2], [R3+R4], [R5+R6] → 3 résumés fusionnés

La fusion utilise `fuse_summaries()`, qui appelle `_generate_summary_prompt(is_fusion=True)` avec un prompt spécialisé "résumé de résumés" (mode texte libre, sans analyse EGO).

Les fusions sont également mises en cache avec la clé `fusion_{SHA256[:16]}`.

---

## 6. Méthode Principale : `optimize_conversation_history()`

C'est le point d'entrée appelé depuis `ogma_ng.py` avant chaque requête LLM.

```python
summaries_texts, recent_messages = await summarizer.optimize_conversation_history(chat_history)
```

**Flux interne** :

```
1. Filtrer messages (role=user|assistant uniquement)
2. Charger résumés existants depuis _current_summaries (déjà en mémoire)
3. Boucle : tant que (total - last_index) >= summary_interval
   a. Calculer la plage [start, end]
   b. Vérifier cache RAM
   c. Si absent → create_summary() → réflexions stockées dans _last_reflexions
   d. add_summary_range() avec réflexions
4. Déterminer messages récents à garder :
   keep_from = min(last_summarized_index, total - min_recent_messages)
5. Si > 5 résumés → fusion par paires jusqu'à ≤ 3
6. Retourner (all_summaries_texts, recent_messages)
```

**Garantie de continuité** : même si des messages chevauchent un résumé existant, `keep_from` assure que les N derniers messages sont toujours présents en clair pour la continuité du contexte.

---

## 7. API Publique

### Classe `ConversationSummarizer`

| Méthode | Description |
|---|---|
| `set_archiviste(archiviste)` | Configure l'Archiviste post-init (appelé depuis `ogma_ng.py`) |
| `get_summaries_data()` | Exporte `{ranges, last_index, interval}` pour sauvegarde JSON |
| `load_summaries_data(data)` | Charge depuis JSON, restaure cache RAM |
| `add_summary_range(start, end, text, cache_key, reflexions)` | Enregistre une entrée résumé avec ses réflexions |
| `clear_session_state()` | Reset complet (nouvelle conversation) |
| `get_cached_summaries_texts()` | Liste textes résumés triés chronologiquement |
| `get_pending_reflexions(seuil=3)` | Réflexions importance >= seuil, triées par importance desc |
| `create_summary(messages)` | Crée un résumé pour un bloc de messages (async) |
| `fuse_summaries(summaries)` | Fusionne plusieurs résumés en un seul (async) |
| `should_summarize(message_count)` | `True` si `(total - last_index) >= summarize_trigger` |
| `get_summary_range(message_count)` | Retourne `(start_idx, end_idx)` du prochain bloc à résumer |
| `optimize_conversation_history(chat_history)` | **Méthode principale** : retourne `(summaries_texts, recent_messages)` |

### Fonctions module-level

| Fonction | Description |
|---|---|
| `get_all_summaries_from_conversations(dir, max)` | Lit tous les JSON et extrait les résumés persistants (avec métadonnées) |
| `get_all_summary_texts(dir, max)` | Version simplifiée : retourne juste les textes |
| `create_conversation_tool_prompt()` | Génère un prompt listant les 10 conversations archivées les plus récentes |

### Instances globales

```python
summarizer = ConversationSummarizer()   # Singleton utilisé par ogma_ng.py
archive    = ConversationArchive()      # Accès lectures/recherches conversations
```

---

## 8. Classe `ConversationArchive`

Gestion des conversations archivées (lecture, recherche) — indépendante du summarizer.

| Méthode | Description |
|---|---|
| `list_conversations()` | Liste toutes les conversations JSON, triées par date |
| `load_conversation(filename)` | Charge le contenu d'une conversation |
| `search_conversations(query, max_results=5)` | Cherche `query` dans le contenu de toutes les conversations |

---

## 9. Intégrations Externes

### `ogma_ng.py`
- Appelle `summarizer.set_archiviste(archiviste_controller)` au démarrage
- Appelle `summarizer.optimize_conversation_history(history)` avant chaque requête LLM
- Appelle `summarizer.get_summaries_data()` / `load_summaries_data()` pour la persistance JSON
- Appelle `summarizer.get_pending_reflexions(seuil=3)` pour injecter les réflexions critiques dans le contexte

### `extensions/contextual_recall/`
- Utilise `get_all_summaries_from_conversations()` pour indexer les résumés passés
- Permet de répondre aux questions du type "qu'est-ce qu'on a dit sur X il y a 3 semaines ?"

### `extensions/dream_engine/`
- Utilise `get_all_summary_texts()` comme "carburant mémoriel" pour les rêves
- Les 10 derniers résumés alimentent le contenu onirique de l'IA Principale

### `extensions/biographie_profil/`
- Utilise `get_all_summaries_from_conversations()` pour construire la biographie de l'utilisateur
- Analyse les résumés pour extraire les patterns, préférences, événements marquants

---

## 10. Flux Complet d'une Résumisation

```
Message utilisateur reçu
        │
        ▼
ogma_ng.py → optimize_conversation_history(history)
        │
        ├─ Résumés existants chargés depuis _current_summaries
        │
        ├─ (total - last_index) >= 30 ?
        │         │
        │         ▼ OUI
        │  ego_compiled.json présent ?
        │         │
        │   OUI   ▼   NON
        │   JSON  ●   Texte libre
        │   mode      mode
        │         │
        │         ▼
        │  archiviste.call_chat_api()
        │         │
        │         ▼
        │  Résumé + réflexions extraits
        │  _last_reflexions mis à jour
        │  add_summary_range() → JSON
        │
        ▼
> 5 résumés ? → fusion par paires → ≤ 3 résumés
        │
        ▼
Contexte envoyé au LLM :
  [résumés compressés] + [20 derniers messages en clair]

En arrière-plan (prochaine requête) :
  get_pending_reflexions(3) → injectés dans system prompt
```

---

## 11. Notes Importantes

- **Pas de déclenchement immédiat** : le résumé est créé dans `optimize_conversation_history()`, pas à la réception du message. La résumisation est donc toujours asynchrone, en amont de la génération LLM.
- **Timeout API** : `create_summary()` est appelé avec `asyncio.wait_for(..., timeout=15.0)`. En cas de timeout, la boucle de résumisation s'arrête proprement (messages non résumés restent en clair).
- **Cache RAM vs persistance JSON** : le cache RAM est perdu à la fermeture de l'app, mais les résumés dans le JSON conversation sont permanents. Au chargement d'une conversation, `load_summaries_data()` restitue le cache RAM depuis le JSON.
- **Résumés sans EGO** : si `ego_compiled.json` est absent ou vide, le système fonctionne normalement en mode texte libre — seul le feature "subconscient" est désactivé.
