# Extension Journal de Bord — Documentation Exhaustive

**Dossier** : `extensions/journal_de_bord/`
**Rôle** : Tenue automatique d'un journal de conversation — résumé des échanges via l'Archiviste, détection des **états utilisateur** (santé, projet, apprentissage, humeur), injection du contexte dans chaque conversation, et enrichissement par plusieurs modules autonomes (curiosité, introspection post-rêve, apprentissage des corrections).

---

## Concept

Le Journal de Bord archive les **résumés de conversations** et suit les **états actifs de l'utilisateur** (situations en cours : problème de santé, projet démarré, apprentissage engagé, humeur du jour, etc.). Il fournit :

- Un **contexte injecté** à chaque début de conversation : 1 entrée récente + états actifs + préfixe temporel
- Une **détection live d'états utilisateur** : patterns regex sur les messages → catégorisation automatique
- Une **résolution automatique** des états par TTL (délai d'expiration par catégorie) et analyse LLM optionnelle
- Un **moteur de curiosité** : l'IA génère des questions pendant les rêves (cycle `detected → queued → explored → shared`)
- Une **introspection post-rêve** : l'IA principale écrit son journal intime après chaque rêve (`IntrospectionIA`)
- Un **apprentissage des corrections** : l'extension mémorise les reformulations utilisateur
- Un **purge manager** pour compresser et transférer les anciennes entrées vers FAISS

---

## Architecture — Fichiers

| Fichier | Classe / Rôle |
|---------|---------------|
| `__init__.py` | API publique, singleton |
| `config.py` | `JournalConfig` — paramètres de configuration |
| `core_journal.py` | `JournalCore`, `JournalState` (enum 6 états) |
| `json_manager.py` | `JSONManager` — fichier annuel hiérarchique + index mémoire |
| `entry_generator.py` | `EntryGenerator` — génération entrées via Archiviste |
| `context_provider.py` | `ContextProvider` — cascade contexte + états actifs + préfixe temporel |
| `live_state_detector.py` | `LiveStateDetector` — détection patterns utilisateur (regex) |
| `auto_resolution.py` | Module utilitaire — expiration TTL + résolution LLM des états |
| `correction_learner.py` | Singleton module — apprend des reformulations utilisateur |
| `curiosity_engine.py` | Singleton module — curiosités spontanées explorées pendant les rêves |
| `purge_manager.py` | `PurgeManager` — compression via Archiviste + transfert FAISS |
| `shutdown_state_analyzer.py` | `ShutdownStateAnalyzer` — détection états manqués inter-sessions |
| `introspection_ia.py` | Singleton module — journal intime post-rêve de l'IA principale |
| `scheduler.py` | `MaintenanceScheduler` — timer hebdomadaire de maintenance |
| `calendar_viewer.py` | `CalendarViewer` — navigation temporelle calendrier |
| `ui_components.py` | `JournalUI` — interface NiceGUI (bouton header + modal) |

**Scripts de maintenance** (non-core) : `analyze_retroactive.py`, `run_retroactive.py`

---

## `config.py` — Classe `JournalConfig`

- `VERSION = "1.0.0"`, `EXTENSION_NAME = "journal_de_bord"`
- **Fichier de persistance** : `extensions/journal_de_bord/data/journal_settings.json` (section `"journal_de_bord"`)

**Paramètres `DEFAULT_SETTINGS` (extrait des paramètres clés)** :

| Clé | Défaut | Description |
|-----|--------|-------------|
| `extension_enabled` | `True` | Extension activée |
| `auto_context_display` | `True` | Injection automatique du contexte journal |
| `context_max_entries` | `3` | Nombre max d'entrées retournées par `get_today_context()` |
| `context_format` | `"summary"` | Format du contexte injecté |
| `auto_archive_enabled` | `True` | Archivage automatique |
| `auto_archive_frequency` | `20` | Fréquence (en nombre d'échanges) pour archiver |
| `update_same_conversation` | `True` | Met à jour l'entrée si même conversation |
| `enable_active_states` | `True` | Active le suivi d'états utilisateur |
| `max_active_states` | `10` | Nombre max d'états simultanément actifs |
| `auto_resolve_states` | `True` | Résolution automatique des états |
| `state_auto_resolve_days` | `30` | Jours avant résolution forcée |
| `archive_retention_months` | `3` | Rétention avant compression |
| `faiss_transfer_months` | `6` | Âge déclenchant le transfert FAISS |
| `enable_progressive_purge` | `True` | Purge progressive activée |
| `purge_check_frequency` | `"weekly"` | Fréquence de vérification purge |
| `lazy_loading` | `True` | Chargement paresseux du journal |
| `cache_size` | `100` | Taille du cache d'entrées |
| `data_retention_days` | `365` | Rétention données en jours |

**Méthodes clés** : `is_enabled()`, `get_generation_settings()` → `{min_tokens, max_tokens, style, auto_tags, importance_detection}`, `get_ui_settings()` → `{button_position, modal_size, theme_mode}`

---

## `core_journal.py`

### `JournalState` (enum)

| Valeur | Description |
|--------|-------------|
| `UNINITIALIZED` | Non initialisé (état de départ) |
| `INITIALIZING` | Initialisation en cours |
| `READY` | Prêt, en attente |
| `ACTIVE` | Traitement en cours |
| `ERROR` | Erreur récupérable |
| `DISABLED` | Désactivé explicitement |

### Classe `JournalCore`

**`__init__(config)`** — Le constructeur ne prend que la config. Les contrôleurs IA sont passés à `initialize()`.

**`initialize(archiviste_controller, memory_manager=None, ui_container=None) -> bool`** — Charge les sous-modules dans cet ordre : `JSONManager` → `EntryGenerator` → `ContextProvider` → `LiveStateDetector`

| Attribut clé | Description |
|-------------|-------------|
| `state` | `JournalState` courant |
| `config` | Instance `JournalConfig` |
| `json_manager` | `JSONManager` |
| `entry_generator` | `EntryGenerator` |
| `context_provider` | `ContextProvider` |
| `live_state_detector` | `LiveStateDetector` |
| `_archiviste` | Contrôleur IA Archiviste (passé à `initialize()`) |
| `_memory_manager` | Manager FAISS (optionnel) |

**`is_ready() -> bool`** — `True` si state dans `[READY, ACTIVE]` ET les 3 composants core non-None.  
**`is_enabled() -> bool`** — `config.is_enabled() and state != DISABLED`  
**`update_archiviste(controller)`** — Met à jour le contrôleur ET celui de `LiveStateDetector`

### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `get_today_context(max_entries=None) -> str` | Cache 5 min — délègue à `context_provider.get_recent_context_with_cascade()` |
| `async create_entry_from_conversation(conversation_id, **metadata)` | Génère entrée via Archiviste + sauvegarde |
| `search_entries(query, **filters)` | Recherche fulltext dans le journal |
| `get_entries_for_date(target_date)` | Entrées pour une date précise |
| `get_journal_stats()` | Statistiques agrégées |
| `export_journal(format, date_range)` | Export JSON/Markdown/CSV |

---

## `json_manager.py` — Classe `JSONManager`

### Structure fichiers

```
extensions/journal_de_bord/data/
└── {YYYY}/
    └── journal_{YYYY}.json      ← un seul fichier par année (structure hiérarchique interne)
```

Le fichier annuel contient une hiérarchie `months → days → entries` :

```json
{
  "year": 2025,
  "months": {
    "12": {
      "days": {
        "01": {
          "date": "2025-12-01",
          "entries": [...],
          "total_entries": 3,
          "day_summary": "...",
          "tags": ["projet", "santé"],
          "importance_level": "high"
        }
      }
    }
  },
  "INTROSPECTIONS_IA": [...],
  "CORRECTIONS_APPRISES": [...],
  "CURIOSITES_IA": [...]
}
```

**Index en mémoire** (5 dimensions) : `tags`, `keywords`, `importance`, `participants`, `dates`

### Méthodes

| Méthode | Description |
|---------|-------------|
| `save_entry(entry)` | Écrit dans l'arborescence year/month/day + met à jour index |
| `delete_entry(entry_id)` | Supprime entrée + maj index |
| `get_day_entries(date_str)` | Entrées pour une date |
| `search_entries(query, filters)` | Recherche fulltext + filtres |
| `get_all_entries_sorted()` | Toutes les entrées triées par date |
| `get_active_states()` | États utilisateur actifs |
| `resolve_state(state_id)` | Marque un état comme résolu |
| `get_statistics()` | Stats agrégées |

---

## `entry_generator.py` — Classe `EntryGenerator`

**`__init__(archiviste_controller, config)`**

### 4 styles d'entrée

| Style | Description |
|-------|-------------|
| `"formal"` | Ton formel, neutre |
| `"casual"` | Ton décontracté, naturel |
| `"technical"` | Vocabulaire technique, précis |
| `"balanced"` | Équilibre entre clarté et chaleur |

### Méthodes

| Méthode | Description |
|---------|-------------|
| `async generate_entry(conversation_id, **metadata) -> Dict` | Appelle l'Archiviste pour générer le résumé de conversation |
| `_get_style()` | Retourne style courant depuis `config.get_generation_settings()` |

**Paramètres de génération** (via `config.get_generation_settings()`) : `min_tokens`, `max_tokens`, `style`, `auto_tags`, `importance_detection`

---

## `context_provider.py` — Classe `ContextProvider`

### Méthode principale : `get_recent_context_with_cascade(max_entries=3) -> str`

La méthode construit le contexte d'injection en 3 parties assemblées dans l'ordre :

#### 1. Section États Actifs (prioritaire)

- Charge `json_manager.get_active_states()`
- Injecte **états non résolus** + **états récemment résolus** (dans les 48h) sauf catégories éphémères
- Catégories éphémères (non ré-injectées après résolution) : `{"humeur", "personnel"}`
- Format :
  ```
  🎯 **ÉTATS ACTIFS (CONTEXTE)**
  [icône catégorie] catégorie: description [badge importance]
  ...
  ~~catégorie: description~~ RÉSOLU
  ```

#### 2. Préfixe Temporel

```
⏰ **CONTEXTE TEMPOREL ACTUEL**: Nous sommes le DD/MM/YYYY, il est HHhMM (moment_journée)
```

#### 3. Contexte Journal Classique

- Toujours **1 entrée récente** (indépendamment de la date)
- En-tête adaptatif : `"Aujourd'hui"`, `"Hier"`, `"Il y a X jours"`, `"Il y a X semaines"`, `"Il y a X mois"`, `"Il y a X ans"`

**Sortie finale** : `active_states_context + temporal_prefix + journal_context`

---

## `live_state_detector.py` — Classe `LiveStateDetector`

Détecte les **états de l'utilisateur** (situations concrètes signalées dans ses messages) via patterns regex.  
Singleton via `initialize_live_detector(json_manager, archiviste_controller)` / `get_live_detector()`.

### 4 catégories de détection (`creation_patterns`)

| Catégorie | Exemple de contexte |
|-----------|---------------------|
| `santé` | Problème médical, douleur, traitement |
| `projet` | Projet démarré, deadline, objectif |
| `apprentissage` | Formation, lecture, acquisition de compétences |
| `humeur` | État émotionnel exprimé (fatigue, enthousiasme, stress) |

### Types d'états

| Type | Catégories |
|------|-----------|
| `temporaire` | `santé`, `projet`, `apprentissage`, `technique` |
| `durable` | `humeur`, `personnel`, `identité`, `relation` |

**Catégories remplaçables** (remplacement au lieu de résolution) : `["humeur", "personnel"]`

### Patterns de résolution

15+ patterns regex couvrant : terminaison explicite, négation, guérison, abandon, succès, remplacement d'humeur.

---

## `auto_resolution.py` — Module utilitaire

Fonctions pures (pas de classe) pour l'expiration automatique des états.

### TTL par catégorie (`CATEGORY_TTL_HOURS`)

| Catégorie | TTL |
|-----------|-----|
| `humeur` | 12h |
| `personnel` | 12h |
| `santé` / `sante` | 168h (7 jours) |
| `technique` | 168h |
| `apprentissage` | 168h |
| `projet` | 720h (30 jours) |
| `identité`, `relation` | **Jamais** (protégées) |

### Fonctions publiques

| Fonction | Description |
|----------|-------------|
| `auto_expire_by_category(json_manager)` | Expire les états dépassant leur TTL depuis `created_at` |
| `auto_resolve_states(json_manager, archiviste_controller, dry_run=False)` | Résolution validée par LLM (avec mode `dry_run`) |

---

## `correction_learner.py` — Singleton module

**`initialize_correction_learner(json_manager, archiviste_controller, memory_manager=None)`**

Apprend les reformulations que l'utilisateur apporte aux réponses de l'IA.

### Patterns reconnus (`CORRECTION_PATTERNS`)

12+ regex couvrant les reformulations explicites de l'utilisateur (ex. `"non je voulais dire"`, corriger une incompréhension, préciser une demande).

### Cycle

1. `analyze_for_corrections(user_message, ai_response, conversation_context, conversation_id)` — async
2. Si correction détectée : sauvegarde dans section `CORRECTIONS_APPRISES` du fichier annuel
3. Si correction importante : crée un `#MEM` pour ancrage mémoire long terme (via `memory_manager`)

### Fonctions publiques

| Fonction | Description |
|----------|-------------|
| `analyze_for_corrections(...)` | Async — analyse un échange pour détecter corrections |
| `get_corrections_stats()` | `{total, categories}` |

---

## `curiosity_engine.py` — Singleton module

**`initialize_curiosity_engine(json_manager, archiviste_controller, chat_controller=None)`**

L'IA principale génère des questions sur des sujets émergents des conversations. Les explorations ont lieu **pendant les rêves** (appelé depuis `dream_core.py`).

### Cycle d'une curiosité

```
detected → queued → explored (pendant rêve, via dream_core.py) → shared (mentionnée à l'utilisateur)
```

### Fonctions publiques

| Fonction | Description |
|----------|-------------|
| `detect_curiosities(user_message, ai_response, conversation_context, conversation_id)` | Détecte curiosités dans un échange |
| `explore_curiosity_during_dream()` | Exploration IA pendant rêve (appelé par `dream_core.py`) |
| `get_unshared_explorations()` | Explorations prêtes à partager |
| `mark_exploration_shared(curiosity_id)` | Marque une curiosité comme partagée |

**Stockage** : section `CURIOSITES_IA` du fichier annuel `journal_{YYYY}.json`

---

## `introspection_ia.py` — Singleton module

**`initialize_introspection(json_manager, chat_controller, archiviste_controller)`**

L'IA principale rédige son **journal intime** après chaque rêve. L'Archiviste analyse le rêve et produit un JSON structuré ensuite rédigé en prose par l'IA principale.

### Flux

Après chaque rêve, `dream_core.py` appelle `generate_post_dream_introspection()` une fois le rêve terminé et l'ego compilé.

### Format de sortie (JSON de l'Archiviste)

```json
{
  "titre": "...",
  "contenu": "...",
  "themes": ["..."],
  "emotion_dominante": "curiosité",
  "question_ouverte": "..."
}
```

**Émotions possibles** : `curiosité`, `sérénité`, `questionnement`, `gratitude`, `mélancolie`, `détermination`, `émerveillement`

### Fonctions publiques

| Fonction | Description |
|----------|-------------|
| `async generate_post_dream_introspection(dream_content, dream_analysis, ego_flags, active_states) -> Dict` | Génère l'entrée journal intime |
| `get_last_introspection_context()` | Dernière introspection non encore mentionnée à l'utilisateur |
| `mark_introspection_mentioned(introspection_id)` | Marque comme mentionnée (pour ne pas répéter) |

**Stockage** : section `INTROSPECTIONS_IA` du fichier annuel `journal_{YYYY}.json`

---

## `purge_manager.py` — Classe `PurgeManager`

**`__init__(json_manager, memory_manager=None, archiviste_controller=None)`**

### Stratégie de purge

1. **Compression** : résumé via `archiviste.send_message()` (max `500` caractères par défaut), garde `content_original` + `content` compressé
2. **Transfert FAISS** : via `memory_manager` pour les entrées archivables

**Répertoire backup** : `extensions/journal_de_bord/data/purge_backups/`

### Méthodes

| Méthode | Description |
|---------|-------------|
| `get_purgeable_entries(age_days=90, exclude_active_states=True)` | Scanne les répertoires year/month pour identifier les entrées éligibles |
| `compress_entry(entry_id, max_summary_chars=500)` | Compresse via Archiviste (`send_message()`) |

---

## `shutdown_state_analyzer.py` — Classe `ShutdownStateAnalyzer`

Analyse les conversations modifiées **depuis le dernier shutdown** pour détecter des résolutions d'états manquées entre les sessions.

**`__init__(json_manager, archiviste_controller, conversations_dir=Path("data/conversations"))`**

| Attribut | Description |
|----------|-------------|
| `state_types.ephemere` | `[humeur, personnel]` |
| `state_types.temporaire` | `[santé, technique, apprentissage]` |
| `state_types.long_terme` | `[projet]` |
| `state_types.durable` | `[identité, relation]` |

**Horodatage** : `extensions/journal_de_bord/data/.last_shutdown_analysis`

---

## `scheduler.py` — Classe `MaintenanceScheduler`

Timer de maintenance **hebdomadaire** basé sur `threading.Timer`.

- `auto_start=False` (démarré manuellement depuis l'UI)
- Config dans `journal_settings.json` section `"maintenance"` :
  - `auto_purge_enabled: False`, `purge_age_days: 90`, `purge_mode: "compress"`
  - `auto_resolve_enabled: False`, `resolve_threshold_days: 30`, `require_llm_validation: True`
  - `maintenance_interval_days: 7`
- Utilise `auto_resolve_states()` de `auto_resolution.py` et `get_purge_manager()`

---

## `calendar_viewer.py` — Classe `CalendarViewer`

Vue calendrier NiceGUI pour navigation temporelle dans le journal.

**`__init__(json_manager, config)`** — vues : `"month"` ou `"year"` (`view_mode`)

### Méthodes

| Méthode | Description |
|---------|-------------|
| `async create_calendar_widget(container)` | Crée le widget dans un container NiceGUI |
| `navigate_to(year, month)` | Change la vue + rechargement données |

---

## `ui_components.py` — Classe `JournalUI`

**`__init__(config, core_journal, json_manager)`**

### Interface NiceGUI

| Composant | Description |
|-----------|-------------|
| Bouton header | `inject_header_button(header_container)` |
| Modal principal | Calendrier + navigation + panneau détail |
| Callbacks | `on_entry_selected`, `on_date_changed`, `on_search_performed` |

**Paramètres UI** (via `config.get_ui_settings()`) : `button_position`, `modal_size`, `theme_mode`

---

## `__init__.py` — API Publique

### Singleton

```python
_journal: Optional[JournalCore] = None
```

### Ordre d'initialisation des sous-modules

`PurgeManager` → `Scheduler (auto_start=False)` → `LiveStateDetector` → `CorrectionLearner` → `CuriosityEngine`

### Fonction d'initialisation

```python
initialize_journal(
    archiviste_controller,
    memory_manager=None,
    ui_container=None
) -> bool
```

> **Note** : pas de `chat_controller` ni de `settings_manager` dans cette fonction.  
> `get_journal()` lève `RuntimeError` si `initialize_journal()` n'a pas encore été appelé.

### Fonctions exposées

| Fonction | Description |
|----------|-------------|
| `initialize_journal(archiviste_controller, memory_manager=None, ui_container=None)` | Init complète + sous-modules |
| `get_journal() -> JournalCore` | Retourne le singleton (lève `RuntimeError` si non init) |
| `is_available() -> bool` | `_journal is not None` |
| `update_archiviste(archiviste_controller)` | Met à jour le contrôleur Archiviste à chaud |
| `initialize_ui()` | Initialise la partie UI (bouton header) |

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `extensions/journal_de_bord/data/{YYYY}/journal_{YYYY}.json` | Fichier annuel unique contenant `months/days/entries` + sections `INTROSPECTIONS_IA`, `CORRECTIONS_APPRISES`, `CURIOSITES_IA` |
| `extensions/journal_de_bord/data/journal_settings.json` | Configuration persistée |
| `extensions/journal_de_bord/data/.last_shutdown_analysis` | Horodatage dernière analyse shutdown |
| `extensions/journal_de_bord/data/purge_backups/` | Backups avant compression |
