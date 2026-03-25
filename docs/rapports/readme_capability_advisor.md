# Extension Capability Advisor — Documentation Exhaustive

**Dossier** : `extensions/capability_advisor/`
**Version** : 2.0
**Rôle** : Analyser en continu la conversation via l'Archiviste pour détecter quand une capacité OGMA (recherche web, biographie, génération image, webcam, etc.) pourrait améliorer la réponse. Si détecté, illumine la LED correspondante et injecte la phrase magique d'activation dans le prompt de l'IA.

---

## Concept

L'extension observe chaque message utilisateur avec un cooldown de 3 messages minimum entre suggestions. L'Archiviste analyse le contexte et retourne un JSON indiquant quelle capacité serait utile. La LED correspondante s'allume et la phrase magique exacte est injectée discrètement dans le system prompt.

---

## Architecture — Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | `CapabilityAdvisor` | Orchestrateur principal + singleton |
| `config.py` | `CapabilityAdvisorConfig` | Configuration + prompt (fichier JSON + txt) |
| `capability_catalog.py` | — | Catalogue des 9 capacités avec phrases magiques |
| `advisor_core.py` | `AdvisorCore`, `CapabilitySuggestion` | Appel Archiviste + parsing JSON |
| `led_manager.py` | `LEDManager` | État et contrôle LED par capacité |
| `suggestion_engine.py` | `SuggestionEngine` | Formatage injection + détection usage |
| `ui_components.py` | `CapabilityAdvisorUI` | UI overlay + bouton header + modal |

---

## `__init__.py` — Classe `CapabilityAdvisor` et API Publique

### Singleton global : `_capability_advisor_instance`

### Classe `CapabilityAdvisor`

**`__init__(chat_controller, archiviste_controller, memory_manager)`**

| Attribut | Description |
|----------|-------------|
| `chat_controller` | IA principale (réservé, non utilisé activement) |
| `archiviste_controller` | IA analytique (passe à `AdvisorCore`) |
| `memory_manager` | Gestionnaire mémoire (passé à `AdvisorCore`) |
| `config` | `CapabilityAdvisorConfig()` |
| `advisor_core` | `AdvisorCore(archiviste_controller, config)` |
| `suggestion_engine` | `SuggestionEngine()` |
| `led_manager` | `LEDManager(led_timeout=config.led_timeout)` |
| `ui` | `CapabilityAdvisorUI(led_manager, config)` |
| `current_suggestion` | `Optional[CapabilitySuggestion]` |
| `_message_counter` | `int = 0` |
| `_last_suggestion_at` | `int = -99` |
| `_cooldown_messages` | `int = config.cooldown_messages` (défaut: 3) |

### Méthodes publiques

| Méthode | Paramètres | Description |
|---------|-----------|-------------|
| `async analyze_conversation(user_message, conversation_history)` | `str, List` | Incrémente compteur, vérifie cooldown, détecte demandes explicites (bypass cooldown), appelle `advisor_core.analyze_conversation()`, allume LED si suggestion valide |
| `format_suggestion_for_injection(suggestion)` | `CapabilitySuggestion` | Délègue à `suggestion_engine.format_for_injection()` |
| `detect_capability_usage(ai_response)` | `str` | **DÉSACTIVÉ** — retourne toujours `False` |
| `is_enabled()` | — | Délègue à `config.is_enabled()` |
| `get_ui_components()` | — | `{'header_button': create_header_button(), 'inject_css': inject_css_styles}` |
| `cleanup()` | — | Appelle `led_manager.cleanup()` |

**Extinction des LEDs** : les LEDs ne s'éteignent pas automatiquement après timeout (désactivé). Elles s'éteignent au prochain message de l'utilisateur.

**Détection demandes explicites** (bypass cooldown, 4 patterns regex) :
- web/internet → `web_search`
- biographie/bio → `biography`
- image/photo/génère → `image_gen`
- webcam/caméra/vois-moi → `webcam`

### API module-level

| Fonction | Description |
|----------|-------------|
| `initialize_capability_advisor(chat_controller, archiviste_controller, memory_manager)` | Crée singleton si absent |
| `is_available()` | Singleton non-None |
| `get_capability_advisor()` | Retourne le singleton |
| `cleanup()` | Nettoie et met singleton à `None` |

---

## `config.py` — Classe `CapabilityAdvisorConfig`

### Constantes de classe

| Constante | Valeur |
|-----------|--------|
| `EXTENSION_NAME` | `"capability_advisor"` |
| `EXTENSION_VERSION` | `"2.0"` |
| `CONFIDENCE_THRESHOLD_GLOBAL` | `0.70` |
| `LED_TIMEOUT` | `30` (désactivé) |
| `COOLDOWN_MESSAGES` | `3` |
| `MAX_TOKENS_ANALYSIS` | `500` |
| `TEMPERATURE` | `0.3` |
| `RECENT_CONTEXT_MESSAGES` | `3` |
| `ENABLE_OVERLAY` | `True` |
| `ENABLE_EXTENSION` | `True` |

### Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/capability_advisor_config.json` | Configuration persistée (seuils, activation, cooldown) |
| `data/capability_advisor_prompt.txt` | Prompt custom Archiviste (optionnel) |

### Méthodes

| Méthode | Description |
|---------|-------------|
| `load_config()` | Charge JSON, merge avec defaults, crée si absent |
| `save_config(config=None)` | Écrit JSON |
| `get_advisor_prompt_template()` | Custom (`CUSTOM_PROMPT_FILE`) si présent, sinon `DEFAULT_ADVISOR_PROMPT` |
| `save_custom_prompt(prompt_text)` | Écrit dans `data/capability_advisor_prompt.txt` |
| `reset_to_default_prompt()` | Supprime `CUSTOM_PROMPT_FILE` |
| `is_enabled()` / `set_enabled(enabled)` | Activation extension |
| `get_capability_thresholds()` | Seuils par capacité |
| `get_capability_threshold(capability_id, default)` | Seuil avec fallback |
| `save_capability_thresholds(thresholds)` | Sauvegarde seuils |
| `reset_capability_thresholds()` | Remet seuils à défaut |

### Format du prompt Archiviste

Variables injectées : `{user_message}`, `{recent_context}`, `{available_capabilities}`

Sortie JSON attendue : `{needs_capability, capability_id, reasoning, suggestion, confidence}`

---

## `capability_catalog.py` — Catalogue des Capacités

### 9 capacités enregistrées

| ID | Nom | Seuil défaut | LED | Phrase magique |
|----|-----|------------|-----|----------------|
| `memory` | Mémorisation | 0.85 | `#4CAF50` | `il faut que je me souvienne de ça :` |
| `ego_memory` | Mémorisation EGO | 0.90 | `#9C27B0` | `ceci est une part de moi maintenant :` |
| `introspection` | Introspection | 0.70 | `#2196F3` | `il faut que je réfléchisse sur :` |
| `image_gen` | Génération Image | 0.70 | `#FF9800` | `je dois créer une image de :` |
| `webcam` | Vision Webcam | 0.80 | `#9C27B0` | `il faut que je te vois` |
| `web_search` | Recherche Web | 0.75 | `#00BCD4` | `il faut que je cherche sur internet {subject}` |
| `biography` | Consultation Bio | 0.80 | `#FFC107` | `il faut que je consulte la biographie de {name}` |
| `contextual_recall` | Historique | 0.70 | `#E91E63` | `je dois consulter nos conversations pour {keywords}` |

Chaque capacité contient : `triggers` (mots déclencheurs), `context_chd` (directive CHD), `magic_phrase_pattern` (regex), `example_usage`.

### Fonctions module-level

| Fonction | Description |
|----------|-------------|
| `get_capability(id)` | Retourne dict capacité |
| `get_all_capabilities()` | Dict complet |
| `format_capabilities_list()` | Format texte pour injection dans le prompt Archiviste |
| `set_config_instance(config)` | Injection configuration depuis `__init__.py` |

---

## `advisor_core.py` — Dataclass `CapabilitySuggestion` et Classe `AdvisorCore`

### Dataclass `CapabilitySuggestion`

| Champ | Type | Description |
|-------|------|-------------|
| `needs_capability` | `bool` | Capacité nécessaire |
| `capability_id` | `Optional[str]` | ID de la capacité identifiée |
| `reasoning` | `str` | Justification de l'Archiviste |
| `suggestion` | `str` | Phrase magique exacte à injecter |
| `confidence` | `float` | Score 0.0–1.0 |

### Classe `AdvisorCore`

**`__init__(archiviste_controller, config)`**

**`async analyze_conversation(user_message, conversation_history)`** → `Optional[CapabilitySuggestion]`

1. `_extract_recent_exchanges(history, N=3)` — N×2 derniers messages, tronqués à 200 chars
2. Formate prompt depuis template config + `format_capabilities_list()`
3. `archiviste_controller.call_chat_api(max_tokens=500, temperature=0.3, is_json=True, log_source="capability_advisor")`
4. `_parse_archiviste_response()` — parse JSON, nettoie blocs markdown
5. Calcul seuil effectif : priorité `config_seuil > catalog_seuil > global_threshold`, prend `max(effectif, global)`
6. Retourne `CapabilitySuggestion` si `confidence >= seuil`, sinon `None`

**Méthodes privées de parsing :**

| Méthode | Description |
|---------|-------------|
| `_extract_recent_exchanges(history, last_n)` | Prend `last_n * 2` derniers messages, tronque à 200 chars par message |
| `_parse_archiviste_response(response)` | Nettoie blocs markdown, extrait JSON par comptage accolades |
| `_clean_json_response(response)` | Supprime ` ```json `, extrait `{...}` par comptage |
| `_clean_json_control_chars(json_str)` | Char par char, échappe newlines/tabs dans strings JSON |

---

## `led_manager.py` — Classe `LEDManager`

**`__init__(led_timeout=30)`**

| Attribut | Description |
|----------|-------------|
| `led_timeout` | Non utilisé (feature désactivée) |
| `led_states` | `Dict[str, bool]` — état de chaque LED |
| `led_ui_elements` | `Dict[str, any]` — éléments NiceGUI référencés par `ui_components` |
| `_deactivation_timers` | `Dict[str, asyncio.Task]` — timers asyncio (non déclenchés) |

### Méthodes

| Méthode | Description |
|---------|-------------|
| `activate_led(capability_id)` | `led_states[id]=True`, `_update_ui_led(True)`, annule timer existant |
| `deactivate_led(capability_id)` | `led_states[id]=False`, `_update_ui_led(False)` |
| `schedule_deactivation(capability_id, timeout)` | Crée tâche asyncio — **non appelée actuellement** |
| `get_led_state(capability_id)` | `bool` |
| `get_all_led_states()` | `dict` |
| `reset_all_leds()` | Éteint toutes les LEDs |
| `cleanup()` | Annule tous les timers asyncio |

**Styles LED dans `_update_ui_led()` :**
- ON : `background-color: #FF9800`, glow orange, animation CSS `pulse-led 1.5s`, classe `led-on`
- OFF : `background-color: #444`, opacity 0.6, classe `led-off`

---

## `suggestion_engine.py` — Classe `SuggestionEngine`

**Méthodes :**

| Méthode | Description |
|---------|-------------|
| `format_for_injection(suggestion)` | Format CHD : bloc encadré `╔═══╗` avec phrase exacte, explication trigger, avertissement regex |
| `detect_capability_usage(ai_response, suggested_capability_id)` | Recherche `magic_phrase_pattern` (regex) dans réponse IA — retourne `True` si match |
| `extract_capability_from_response(ai_response)` | Parcourt toutes capacités, première regex matchée → retourne son ID |

---

## `ui_components.py` — Classe `CapabilityAdvisorUI`

**`__init__(led_manager, config)`**

### Éléments créés

| Méthode | Description |
|---------|-------------|
| `create_header_button()` | Bouton 50×50px violet (`#7C3AED → #A855F7`), icône 🧠, toggle overlay |
| `create_overlay()` | `ui.element('div')` fixe `top:80px, right:20px, 200px`, initialement invisible — contient label "Capacités", bouton settings, liste LED cards |
| `_create_led_card(cap_id, cap_info)` | Ligne avec `div.led-indicator.led-off` + label — enregistre l'élément dans `led_manager.led_ui_elements[cap_id]` |
| `create_prompt_editor_modal()` | `ui.dialog()` 900px : section prompt (textarea + variables), toggle activation, grille 2×N seuils `ui.number` (0.0–1.0, pas 0.05), boutons Reset/Annuler/Enregistrer |
| `inject_css_styles()` | `ui.add_head_html()` — animations `pulse-led`, classes `.led-on/.led-off` |

---

## Intégration dans OGMA

```python
# Dans ogma_ng.py — avant appel IA
if capability_advisor and capability_advisor.is_enabled():
    suggestion = await capability_advisor.analyze_conversation(user_message, history)
    if suggestion and suggestion.needs_capability:
        injection = capability_advisor.format_suggestion_for_injection(suggestion)
        system_prompt += "\n\n" + injection
```

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/capability_advisor_config.json` | Configuration (seuils, activation, cooldown) |
| `data/capability_advisor_prompt.txt` | Prompt custom Archiviste (optionnel) |
