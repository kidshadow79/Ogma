# Extension Cognitive Mirror (Introspection) — Documentation Exhaustive

**Dossier** : `extensions/cognitive_mirror/`
**version code** : `__version__ = "2.1.0"` (`config_v2.py VERSION = "2.1.0"`) — flux de dialogue interne labellisé **v4** dans l'orchestrateur
**Rôle** : Déclenchement d'un processus d'introspection multi-étapes entre l'IA Principale et l'Archiviste, simulant une "joute intérieure" — l'IA Principale formule, l'Archiviste confronte et questionne — aboutissant à une synthèse finale enrichie par la mémoire.

---

## Concept

### Déclenchement : le rôle du Capability Advisor

L'introspection **n'est pas déclenchée systématiquement**. Elle est activée à la demande, selon l'un de ces deux chemins :

**Chemin principal — Capability Advisor** (`extensions/capability_advisor/`) :
Avant chaque réponse, l'Archiviste analyse le message utilisateur et le contexte conversationnel récent pour détecter si une capacité spécialisée est pertinente. La capacité `"introspection"` est cataloguée avec :
- `triggers` : `["complexe", "dilemme", "éthique", "pourquoi", "comment", "conscience", "philosophie"]`
- `context_chd` : `QUESTION_EXISTENTIELLE | METACOGNITIF | PROFONDEUR > factuel | EXCL: simple/ordinaire`
- `confidence_threshold` : `0.70`

Si la confidence dépasse ce seuil, le Capability Advisor injecte une **directive technique** dans le system prompt de l'IA Principale :
```
PHRASE EXACTE À ÉCRIRE (copier mot pour mot):
il faut que je réfléchisse sur : {theme}
```
Quand l'IA Principale écrit cette phrase dans sa réponse, le système la détecte via regex (`magic_phrase_pattern`) et déclenche le module `cognitive_mirror`.

**Chemin manuel — Phrase magique utilisateur** :
L'utilisateur peut aussi déclencher directement avec des phrases comme `"réfléchis"`, `"lance une introspection"` (liste `user_trigger`). Ce chemin passe par les regex hardcodées dans `ogma_ng.py`.

---

### Dialogue inter-IA

L'introspection est un **dialogue inter-IA** :
- **IA Principale** : cerveau conversationnel, formule sa position et réflexions
- **Archiviste** : analyse froide, confronte, questionne, cherche les contradictions
- Le dialogue alterne (min 4, max 8 échanges) jusqu'à ce que l'IA Principale signale qu'elle est prête à conclure
- La **synthèse finale** est extraite depuis des balises `<RÉPONSE>...</RÉPONSE>` et retournée à l'utilisateur

---

## Architecture — Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | — | API publique + aliases compat legacy |
| `config_v2.py` | `IntrospectionConfigV2` | Configuration complète + phrases magiques + templates |
| `introspection_core.py` | `IntrospectionCore` | Gestion session, callbacks, coordination |
| `introspection_orchestrator.py` | `IntrospectionOrchestrator` | Moteur de dialogue v4 + synthèse |
| `memory_integration.py` | `MemoryIntegration` | Sauvegarde et recherche réflexions mémorisées |
| `ui_components.py` | `CognitiveMirrorUI` | Interface NiceGUI — délègue à `IntrospectionParametersUI` |
| `ui_parameters_v2.py` | `IntrospectionParametersUI` | Popup paramètres complet (config + instructions + phrases magiques) |
| `ui_introspection_display.py` | — | Affichage dialogue en temps réel |

---

## `__init__.py` — API Publique

### Singleton global : `_core_instance : Optional[IntrospectionCore]`

### Fonctions principales

| Fonction | Description |
|----------|-------------|
| `initialize_introspection(chat_controller, archiviste_controller, memory_manager, ui_container, settings_manager)` | Initialise `IntrospectionCore` + appelle `.initialize()` |
| `initialize_cognitive_mirror(...)` | **LEGACY** — redirige vers `initialize_introspection()` |
| `get_introspection()` / `get_cognitive_mirror()` | Retourne `get_introspection_core()` |
| `is_v21()` | Retourne toujours `True` — confirme que le chemin v2.1 (boîte thinking + streaming) est actif |
| `is_available()`, `is_enabled()`, `toggle_enabled()` | États — **note** : `toggle_enabled()` dans `__init__.py` appelle `core.toggle_enableyhud()` (typo, devrait être `toggle_enabled()`) |
| `get_ui_components()` | Retourne `core.get_ui_components()` |
| `async process_user_message(user_message, conversation_context)` | Délègue au core |
| `check_magic_phrases(text, source)` | Délègue au core |
| `stop_current_introspection(reason)`, `cleanup()` | Contrôle session |
| `get_extension_status()` | `dict` complet via `core.get_status()` |

**Aliases** :
- `get_config = get_introspection_config`
- `CognitiveMirrorConfig = IntrospectionConfigV2`

---

## `config_v2.py` — Classe `IntrospectionConfigV2`

### Constantes

| Constante | Valeur |
|-----------|--------|
| `VERSION` | `"2.1.0"` |
| `EXTENSION_NAME` | `"introspection"` |
| `DISPLAY_NAME` | `"🧠 Introspection"` |

### Étapes de dialogue (`DEFAULT_INSTRUCTIONS`)

| Clé | Nom affiché | Tokens défaut |
|-----|-------------|---------------|
| `step1_analysis` | Ouverture | 400 |
| `step2_conscious` | IA Principale | 500 |
| `step2_unconscious` | Archiviste | 600 |
| `step3_synthesis` | Synthèse | 800 |

Variables dans les templates : `{user_message}`, `{memory_context}`, `{conversation_context}`, `{dialogue_history}`, `{exchange_number}`, `{max_exchanges}`, `{conscious_question}`

Balise de sortie synthèse : `<RÉPONSE>...</RÉPONSE>`

### Phrases magiques (`DEFAULT_MAGIC_PHRASES`)

| Catégorie | Phrases |
|-----------|---------|
| `user_trigger` | `"réfléchis"`, `"réfléchis profondément"`, `"il faut que tu réfléchisses"`, `"lance une introspection"`, `"introspection"` |
| `ia_reflection` | 8 variantes (ex. `"je vais prendre un moment pour réfléchir"`) |
| `user_stop` | `"arrête de réfléchir"`, `"stop introspection"`, `"arrête l'introspection"` |
| `synthesis_ready` | 7 variantes de `"je suis prête/prêt à conclure"` |
| `memorize` | `"il faut que je retienne:"`, `"il faut que je me souvienne:"` |

### Paramètres (`DEFAULT_SETTINGS`)

| Clé | Défaut | Description |
|-----|--------|-------------|
| `extension_enabled` | `False` | **Désactivé par défaut** |
| `introspection_mode` | `"on_demand"` | `"always"` ou `"on_demand"` |
| `step1_max_tokens` | `600` | Tokens ouverture |
| `step2_conscious_max_tokens` | `800` | Tokens IA Principale par message |
| `step2_unconscious_max_tokens` | `900` | Tokens Archiviste par message |
| `step3_max_tokens` | `3500` | Tokens synthèse finale |
| `min_dialogue_exchanges` | `4` | Échanges minimum avant synthèse |
| `max_dialogue_exchanges` | `8` | Échanges maximum |
| `max_introspection_duration` | `300` | Timeout global (secondes) |
| `api_timeout` | `60` | Timeout par appel API (secondes) |
| `memory_search_threshold` | `0.5` | Seuil pertinence mémoire |
| `auto_save_enabled` | `False` | Sauvegarde auto réflexions (l'IA décide via `save_decision`) |
| `importance_threshold` | `6` | Score min pour sauvegarder (0-10) |
| `show_dialogue_details` | `True` | Affichage détails dialogue |
| `show_progress_indicator` | `True` | Affichage indicateur progression |
| `typing_animation` | `True` | Animation frappe (streaming simulé) |

> **Note** : `memory_max_results` a été supprimé — `k=5` est hardcodé dans `_get_memory_context_for_question()`.

**Fichier de données** : `data/introspection_settings_v2.json`

### Méthodes clés

| Méthode | Description |
|---------|-------------|
| `get(key, default)` / `set(key, value)` | Lecture/écriture avec sauvegarde auto |
| `get_instruction(step_key)` / `set_instruction(step_key, text)` | CRUD instructions par étape (retourne `dict` complet ou texte) |
| `get_instruction_text(step_key)` | Retourne uniquement le texte d'instruction pour une étape |
| `reset_instruction_to_default(step_key)` / `reset_instructions()` | Reset étapes |
| `reset_all_to_default()` | `reset_all` alias — Reset complet (settings + instructions + phrases magiques) |
| `is_enabled()` | `get("extension_enabled", False)` |
| `get_introspection_mode()` | `"always"` ou `"on_demand"` |
| `get_magic_phrases(category)` | Liste phrases d'une catégorie |
| `build_trigger_patterns()` | Génère regex depuis phrases user_trigger |
| `build_stop_patterns()` | Génère regex depuis phrases user_stop |
| `matches_trigger_pattern(text, source)` | Match déclencheur (source: `"user"` ou `"ia"`) |
| `matches_stop_pattern(text, source)` | Match arrêt |
| `check_synthesis_ready(text)` | Vérifie si l'IA est prête à conclure |
| `get_tokens_for_step(step_key)` | Cherche `{step_key}_max_tokens` dans settings |
| `get_introspection_settings()` | Retourne dict traduit pour l'orchestrateur (`main_ai_tokens_per_message`, `archiviste_tokens_per_message`, `max_exchanges`, `min_exchanges`, `max_duration`, etc.) |

**Singleton** : `get_introspection_config()` → instance globale `_config_instance`

---

## `introspection_core.py` — Classe `IntrospectionCore`

### Initialisation

**`__init__(chat_controller, archiviste_controller, memory_manager, ui_container=None, settings_manager=None)`**

| Attribut | Description |
|----------|-------------|
| `config` | Singleton `get_config()` |
| `introspection_orchestrator` | Initialisé dans `initialize()` |
| `ui_components` | `CognitiveMirrorUI` |
| `memory_integration` | `MemoryIntegration(memory_manager, config)` |
| `is_introspection_active` | `bool` |
| `current_session_id` | `str` |
| `last_introspection_result` | `dict` |
| `stats` | `{total_introspections, total_saved, last_introspection_time, average_duration}` |

**`@property is_enabled`** — lit `config.is_enabled()` dynamiquement (pas d'attribut direct — synchronisation temps réel).
**`@is_enabled.setter`** — écrit `config.set('extension_enabled', value)`.

### Méthode `initialize()`

Crée dans l'ordre :
1. `IntrospectionOrchestrator(config, chat_controller, archiviste_controller, memory_manager, settings_manager, on_message_callback=self._on_dialogue_message)`
2. `CognitiveMirrorUI(config, ui_container, on_toggle_extension, on_settings_change, core_reference=self)`
3. `MemoryIntegration(memory_manager, config)`

### Méthodes async publiques

| Méthode | Retour | Description |
|---------|--------|-------------|
| `async process_user_message(user_message, conversation_context)` | `Optional[str]` | Vérifie `is_enabled` puis `_should_trigger_introspection()`, délègue à `trigger_introspection()` |
| `async trigger_introspection(user_message, conversation_context, trigger_source="manual")` | `Optional[str]` | Génère `session_id`, met `is_introspection_active=True`, appelle orchestrateur, sauvegarde si importance ≥ seuil |
| `async trigger_introspection_sync(user_message, conversation_context)` | `dict` | Appelle `trigger_introspection()`, combine avec `last_introspection_result` |
| `async run_introspection(user_message, context, trigger_source)` | `dict` | API "Chemin B" compatible streaming de `ogma_ng.py` |

### Méthodes sync publiques

| Méthode | Description |
|---------|-------------|
| `check_magic_phrases(text, source)` | Retourne `"stop"`, `"trigger"`, ou `None` — **note v4** : le déclenchement utilisateur réel passe par des regex hardcodées dans `ogma_ng.py` ; cette méthode est le chemin IA (`source="ia"`) |
| `stop_current_introspection(reason)` | `introspection_orchestrator.stop_current_session()` + reset `is_introspection_active` |
| `force_trigger_conversation()` | LEGACY — crée `asyncio.Task(trigger_introspection(...))` |
| `reload_config_from_file()` | Rechargement config + `orchestrator.reload_config()` |
| `get_status()` | `{enabled, introspection_active, current_session_id, mode, stats, version}` |
| `toggle_enabled()` | `config.set("extension_enabled", not is_enabled)` |
| `is_enabled_check()` | Méthode callable équivalente à `is_enabled` (compatibilité appels `is_enabled()`) |
| `enrich_conversation_context(conversation_context)` | Stocke contexte enrichi dans `self.enriched_context` pour futures introspections |
| `set_callbacks(...)` | Configure tous les callbacks |

**Méthodes privées :**

- `_should_trigger_introspection(user_message)` : mode "always" → `True` ; "on_demand" → `check_magic_phrases == "trigger"`
- `async _save_introspection_memory(result)` : vérifie `importance >= importance_threshold (6)`, appelle `memory_integration.save_introspection_conditional()`

---

## `introspection_orchestrator.py` — Classe `IntrospectionOrchestrator`

### État interne

| Attribut | Description |
|----------|-------------|
| `current_session_id` | ID session courante |
| `is_active` | `bool` — dialogue en cours |
| `should_stop` | `bool` — signal arrêt |
| `dialogue_messages` | `list[{role, content, timestamp}]` |
| `synthesis` | Texte synthèse final |
| `save_metadata` | `{save_decision, importance, reason}` |
| `_original_user_message` | Sujet initial conservé pour toutes les étapes |
| `on_config_reload_callbacks` | `list` — callbacks appelés lors de `reload_config()` |

### Flux de dialogue v4

**`async run_introspection_dialogue(user_message, conversation_context, session_id)`** → `dict`

1. **Tour 0** : `_main_ai_opening()` — IA Principale formule position + sujet (step1_analysis, mémoire k=5 top=3)
2. **Boucle joute** (max `max_exchanges`, timeout `max_duration`) :
   - Tour Archiviste : `_archiviste_response(last_message, context)` (step2_unconscious)
   - Tour IA Principale : `_main_ai_reflection_step(user_message, context, exchange_num)` (step2_conscious)
   - Si `exchange_count >= min_exchanges` ET `_detect_synthesis_ready(message)` → sortie anticipée
3. **Fin** : `_main_ai_generate_synthesis(user_message, context)` (step3_synthesis)
4. Retourne `{success, session_id, duration, exchanges_count, dialogue_messages, synthesis, save_decision, importance, save_reason, final_response}`

### Système prompt complet

**`_build_full_system_prompt()`** — concatène dans l'ordre :
1. Instructions système principales (via `settings_manager`)
2. `_load_full_ego()` — charge `data/ego_compiled.json`, tous les groupes de flags en markdown :
   ```
   # EGO BOOLEAN COMPLET (Introspection - N groupes)
   ## {group}
   {flag}: true/false (conviction: N)
   ```
3. `get_persistent_context()` (depuis `logic_callbacks`)

**`_build_archiviste_system_prompt()`** — ego complet injecté dans le rôle Archiviste confronteur.

### Méthodes privées de génération

| Méthode | Description |
|---------|-------------|
| `_main_ai_opening(user_message, context)` | Tour 0 v4 — step1_analysis + mémoire → `_call_main_ai(prompt, max_tokens)` |
| `_main_ai_reflection_step(user_message, context, exchange_num)` | Tours suivants v4 — step2_conscious + recherche sur dernier message + sujet initial |
| `_archiviste_response(main_ai_last_message, context)` | Tour Archiviste v4 — step2_unconscious, system prompt Archiviste avec ego → `_call_archiviste(prompt, max_tokens, system_prompt)` |
| `_main_ai_generate_synthesis(user_message, context)` | step3_synthesis, tronque dialogue à `MAX_DIALOGUE_CHARS = 4000` chars, appel `multiplier=5.0` pour ne jamais tronquer, fallback Archiviste si IA principale échoue (403/filtres) |

### Extraction de la réponse finale

**`_extract_final_response_from_synthesis(synthesis_text)`** → `str`
- Priorité 1 : balises `<RÉPONSE>...</RÉPONSE>`
- Priorité 2 : ancien format `"Réponse construite"`
- Fallback : texte sans bloc `<INSIGHTS>`

### Méthodes utilitaires

| Méthode | Description |
|---------|-------------|
| `@staticmethod _with_token_directive(prompt, max_tokens)` | Préfixe le prompt avec directive longueur indicative (`LONGUEUR CIBLE : environ N tokens`) |
| `async _call_main_ai(prompt, max_tokens, multiplier=2.0)` | Appel IA Principale avec system prompt complet ; `api_max_tokens = int(max_tokens * multiplier)` |
| `async _call_archiviste(prompt, max_tokens, system_prompt="", multiplier=2.0)` | Appel Archiviste ; `log_source="introspection_dialogue"` pour tracking tokens |
| `async _get_memory_context_for_question(question)` | Appelle `memory_manager.retrieve_synthesis_and_memories(question, k=5, top_memories=3)` → synthèse Archiviste + 3 souvenirs formatés |
| `_format_conversation_context(context)` | IDENTITÉS + RELATION + HISTORIQUE RÉCENT (8 derniers messages, 500 chars/message) |
| `_format_dialogue_history()` | Format `💭 IA PRINCIPALE:\n{content}` / `📚 ARCHIVISTE:\n{content}` |
| `_detect_synthesis_ready(message)` | `config.check_synthesis_ready()` |
| `_detect_memorization_phrase(message)` | Extrait contenu après phrase de mémorisation |
| `_extract_save_metadata(text)` | Regex JSON `{"save_decision":...}` → `{save_decision, importance, reason}` |
| `_extract_final_response_from_synthesis(synthesis_text)` | Priorité 1 : `<RÉPONSE>...</RÉPONSE>` ; Priorité 2 : ancien format `"Réponse construite"` ; Fallback : texte sans `<INSIGHTS>` |
| `stop_current_session()` | `should_stop = True` |
| `reload_config()` | `config.load_config()` + déclenche `on_config_reload_callbacks` |
| `add_config_reload_callback(callback)` | Ajoute callback appelé lors rechargement config |

---

## `memory_integration.py` — Classe `MemoryIntegration`

**`__init__(memory_manager, config)`**
- `recent_reflections : list` — cache local (max `config.get("max_cached_reflections", 50)`)
- `stats : dict` — `{total_reflections_saved, last_reflection_time, memory_integration_active}`

### Méthodes

| Méthode | Description |
|---------|-------------|
| `async save_introspection_conditional(introspection_data)` | **Méthode principale appelée par `IntrospectionCore`** — vérifie `save_decision == "yes"` ET `importance >= threshold`, sauvegarde via `_save_to_ogma_memory()`. ID : `introspection_{session_id}`, type : `"introspection_v2"` |
| `async save_reflection_memory(session_id, reflection_context, conversation_context)` | Chemin alternatif — crée entrée `REF_{timestamp}_{uuid8}`, type `"cognitive_reflection"`, calcule score importance, génère tags |
| `get_reflection_context_for_conversation(conversation_topic)` | Recherche réflexions pertinentes, retourne 3 max formatées |
| `search_reflections(query, limit)` | Via `memory_manager.search_memories_by_type()` ou cache local |
| `get_reflection_statistics()` | Retourne `stats` + taille cache + oldest/newest reflection |
| `cleanup_old_reflections(max_age_days=30)` | Filtre cache local (par timestamp) |
| `export_reflections(filepath)` | Export JSON complet (toutes réflexions + stats) |

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/introspection_settings_v2.json` | Configuration complète (settings + instructions + phrases magiques) |
| `data/ego_compiled.json` | Lu par l'orchestrateur pour construire le system prompt |
