# 🗺️ CARTE OGMA — Référence Technique IA
> Usage : navigation rapide codebase. Dense, pas de prose. Dernière MAJ : 24 février 2026 — v2.2

---

## 1. ARBRE FICHIERS RACINE

### 🔴 CORE (toucher avec précaution)
| Fichier | Lignes | Rôle |
|---------|--------|------|
| `ogma_ng.py` | ~8491 | Point d'entrée NiceGUI, orchestration globale, toutes `_ensure_*()`, pipeline `_send_chat_message()`, `main_page()` |
| `core_logic.py` | ~2369 | Contrôleurs IA multi-providers — `AIController`, `EmbeddingController`, `SettingsManager`, `APIManager`, `OllamaManager`, `GGUFManager`, `KoboldManager`, `AIHordeManager` |
| `memory_manager.py` | ~4110 | Système mémoire hybride SQLite+FAISS+FTS5 — classe `MemoryManager`, scoring impact, stopwords FR |
| `logic_callbacks.py` | ~1608 | Callbacks hérités Gradio — mémorisation, génération images, recherche web, archi sensor |
| `conversation_summarizer.py` | ~866 | Résumation progressive — classe `ConversationSummarizer`, persistance JSON, cache RAM |
| `utils.py` | ~780 | Chemins globaux (`DATA_DIR`, `CONVERSATIONS_DIR`), `save_conversation()`, `load_conversation()`, `clean_message_for_save()` |

### 🟡 UI
| Fichier | Rôle |
|---------|------|
| `ogma_ui_conversations.py` | ~4680 — Affichage messages, sidebar historique, gestion JSON conversations, edit messages, memory UI |
| `ogma_modals.py` | ~4233 — Toutes les modales (config modèles, paramètres, organic planner) — accès `ogma_ng` via `sys.modules` |
| `ogma_headers.py` | ~773 — En-tête app, statut IA, bouton Archi Sensor flottant, intégration boutons extensions |
| `ogma_displays.py` | ~860 — Fonctions affichage/formatage, LEDs flux cognitif, injections JS |
| `static/ogma_styles.css` | ~3600 — Styles globaux, variables CSS, animations, scrollbars, boutons (ex: `.header-btn` forcé carré 28x28px via override Quasar) |
| `ogma_config_ui.py` | UI settings providers/modèles/clés API |
| `ogma_extensions_ui.py` | UI gestion extensions (on/off) |
| `ogma_introspection_ui.py` | UI cognitive mirror / introspection |
| `ogma_image_config.py` | UI config génération images |
| `ogma_tts_config.py` | UI config TTS |
| `ogma_profile.py` | UI profil utilisateur/IA |
| `ogma_perception.py` | UI perception webcam |

### 🟢 MANAGERS
| Fichier | Rôle |
|---------|------|
| `identity_manager.py` | ~307 — `IdentityManager` — profils user/IA, `user_name`, `ai_name` dynamiques |
| `profile_manager.py` | ~1236 — `ProfileManager` — save/load/delete profil complet, souvenirs fondateurs |
| `audio_manager.py` | 10 — SHIM → redirige vers `modules/audio/manager.py` |
| `audio_manager_wrapper.py` | Wrapper TTS/STT sans conflit threads |
| `temporal_injector.py` | ~229 — DÉSACTIVÉ — horodatage remplacé par `temporal_guardian` (rétro-compat uniquement) |

### 🔵 GUARDS & HELPERS
| Fichier | Rôle |
|---------|------|
| `injection_deduplicator.py` | Anti-doublon injections ego/Archiviste par session |
| `magic_phrase_guard.py` | Filtrage phrases magiques avant sauvegarde JSON |
| `hybrid_detection.py` | Détection hybride phrases spéciales (regex + embedding) |
| `archiviste_logger.py` | Logging debug tokens Archiviste (JSONL) |
| `archiviste_memory_optimizer.py` | Optimiseur requêtes mémoire Archiviste (query decomposer) |
| `nicegui_error_handler.py` | Gestionnaire erreurs NiceGUI (déconnexion client) |
| `nicegui_client_guard.py` | Protection accès client NiceGUI |
| `notification_killer.py` | Suppression notifications parasites NiceGUI |
| `stop_signal.py` | Signal arrêt streaming ("Stopper") |
| `model_capabilities.py` | Détection capacités modèles (vision, tools, etc.) |
| ~~`ego_selector.py`~~ | ⚠️ OBSOLÈTE — remplacé par `modules/logic/ego_activation.py` (Ego Boolean System, janv. 2026) |
| `api_keys_vault.py` | Coffre-fort clés API (chiffrement) |
| `tts_conflict_free.py` | TTS sans conflit ressources audio |
| `tts_perception_manager.py` | Gestion TTS + perception simultanée |

### 🟣 BOOT
| Fichier | Rôle |
|---------|------|
| `launch_ogma.py` | Production — vérif dépendances, retry ports 8080-8090 |
| `start_ogma.py` | Dev rapide (minimal) |

---

## 2. CLASSES & FONCTIONS PAR FICHIER

### `core_logic.py`

```
SettingsManager (l.151)
  load_settings() / save_settings()
  get_setting(key, default) → any
  → data/settings.json

OllamaManager (l.310)
  list_models() / ping_ollama()
  generate_ollama(messages, stream) / stream_ollama()

GGUFManager (l.422)
  load_model(path) / unload_model()
  generate_gguf() / stream_gguf()
  Support: LlamaCPP + Vision

KoboldManager (l.584)
  generate_kobold() / stream_kobold()

APIManager (l.622)
  configure(provider, key, model, url)
  generate_api() / stream_api()
  Providers : OpenAI | Mistral | Anthropic | Google | GROK | AIHorde

AIController (l.1756)  ← CLASSE CENTRALE
  __init__(role, ollama_mgr, gguf_mgr, kobold_mgr)
  set_active_backend(backend_name)
  generate(messages, stream=True) → async generator
  role : 'chat' | 'archiviste' | 'embedding'
  Attributs : temperature, max_tokens, context_length

EmbeddingController (l.2028)
  embed(text) → np.ndarray
  Providers : OpenAI / Mistral / Google

IntelligentMemoryAI (l.2080)
  Sélection souvenirs pertinents (scoring sémantique)

AIHordeManager (l.2279)
  generate_horde() — provider communautaire gratuit
```

### `memory_manager.py` — Classe `MemoryManager` (l.272)

**Init**
```
__init__(db_path, index_path, embedding_dim, embedding_controller)
_init_database()         → SQLite + FTS5
_init_faiss_index()      → FAISS IndexFlatL2
_load_existing_data()    → chargement au boot
save_index()             → sauvegarde FAISS sur disque
```

**Stockage**
```
store_memory(text, embedding, enriched_data) → memory_id
_store_in_sqlite(...)
_add_to_faiss(embedding, memory_id)
```

**Recherche**
```
search(query, top_k) → List[dict]   ← FAISS + FTS5 fusionné
_search_fts5(query) → List[dict]    ← Full Text Search
_expand_personal_pronouns(query)    ← "moi" → nom user
clean_conversational_noise(query)   ← suppression stopwords FR
calculate_keyword_matching_score(query_words, text) → float
```

**Gestion**
```
get_memory_count() → int
get_memory_by_id(id) → dict
get_all_memories_data() → List[dict]
delete_memory(id) → bool
delete_all_memories() → dict
```

**Maintenance**
```
rebuild_faiss_index() → dict
repair_mapping_inconsistencies()
sync_ego_prompt_references()
cleanup()
_force_close_sqlite_connections()
```

**Scoring**
```
_compute_score_formula(base_factor, intensite, liberte, ...)
_compute_signed_score(valence, score_impact)
_extract_metrics(enriched_data) → Tuple[float×6]
```

### `ogma_ng.py` — Index par catégorie

**Lazy Init `_ensure_*()`**
```
_ensure_settings_manager()       → SettingsManager          l.669
_ensure_audio_manager()          → AudioManager             l.683
_ensure_backends()               → Ollama/GGUF/Kobold        l.816
_ensure_memory_manager()         → MemoryManager            l.844
_ensure_memory_optimizer()       → Optimizer                l.867
_ensure_archiviste_controller()  → AIController             l.880
_ensure_embedding_controller()   → EmbeddingController      l.903
_ensure_temporal_guardian()      → TemporalGuardian         l.931
_ensure_contextual_recall()      → RecallAgent              l.951
_ensure_file_writer()            → FileWriterAgent          l.971
_ensure_capability_advisor()     → CapabilityAdvisor        l.988
_ensure_organic_planner()        → OrganicPlanner           l.1015
_ensure_chat_controller()        → AIController             l.1111
```

**Pipeline chat**
```
_send_chat_message()              l.1880  async ← FONCTION CENTRALE
_handle_conversation_commands()   l.1605  async ← commandes spéciales
_execute_conversation_scanner()   l.1786  async ← scan conversations
_request_stop()                   l.1752  async ← stop streaming
_retrieve_liberating_memory()     l.597   async ← mémoire libératrice
```

**Statut IA**
```
set_ia_working(active)            l.1155
set_archiviste_working(active)    l.1172
_update_header_display()          l.1197
_notify_safe(message, type)       l.1140
```

**UI pages**
```
main_page()                       l.7513  ← rendu page principale
perception_page()                 l.7203  ← page webcam
_header()                         → ogma_headers.py
_input_overlay()                  l.7115  ← zone saisie
_image_modal()                    l.1450  ← modale image
```

**Avatars/Représentations**
```
_get_representation_image_path(is_user)   l.6747
_load_representation_as_dict(path)        l.6778
_get_active_representations()             l.6818
_build_representation_context()           l.6862
_toggle_user_representation()             l.6996
_toggle_ia_representation()               l.7027
```

**API externe**
```
process_external_message()         l.8171  async ← Telegram/API
get_external_api()                 l.8482
run_ogma(host, port)               l.8072
```

### `conversation_summarizer.py` — `ConversationSummarizer`

```
should_summarize(history) → bool        ← interval=10 messages, pas de limite max
summarize_range(start, end, history)    ← async, ~300 tokens/résumé
get_summaries_data() → dict             ← export pour JSON conversation
load_summaries_data(data)               ← import depuis JSON conversation
add_summary_range(start, end, text)
clear_session_state()                   ← reset à new_conversation
_load_cached_summary(key) → str|None    ← cache RAM uniquement (_session_cache)
_save_cached_summary(key, text)

# API module-level
summarizer                              ← instance globale
get_all_summaries_from_conversations(conversations_dir, max_conversations) → List[dict]
get_all_summary_texts(dir, max) → List[str]
```

**Paramètres actuels** : interval=10, tokens/résumé ~300, seuil fusion=5, tokens fusion=500

### `utils.py`

```
DATA_DIR = Path("data/")
CONVERSATIONS_DIR = DATA_DIR / "conversations"

save_conversation(filepath, messages, summaries_data=None)
  → format: {"messages": [...], "summaries": {...}}
load_conversation(filepath) → {"messages": [...], "summaries": {...}}
  → rétrocompat lecture ancien format liste []
clean_message_for_save(message) → dict
make_conversation_id() → str (timestamp-based)
```

### `identity_manager.py` — `IdentityManager`

```
__init__(data_dir)
load_identities() → dict         ← data/identities.json
save_identities()
get_user_name() → str
get_ai_name() → str
set_user_name(name)
set_ai_name(name)
get_active_profile() → dict
switch_profile(profile_id)
```

---

## 3. EXTENSIONS — INDEX API

### `dream_engine/` — Métabolisme Cognitif
**Trigger** : 10 min inactivité OU clic 🌙
**Fichiers** : `dream_core.py` `dream_memory.py` `dream_analysis.py` `dream_journal.py` `dream_ui.py` `dream_prompts.py` `dream_illustration.py`
```python
initialize_dream_engine(chat_ctrl, archiviste_ctrl, memory_mgr) → bool
start_dream()
wake_up()
is_dreaming() → bool
get_last_dream_context() → str|None    # injection contexte matinal
mark_dream_mentioned()
```
**Flux** : extraction fuel → génération 50 tok/min → analyse PSY (score 1-10) → illustration → dual journal (.md/.json) → si score>8 : mentionne au réveil
**Mécanisme sursaut** : message user pendant rêve → accélération max → fin propre

---

### `cognitive_mirror/` — Introspection Conscient↔Inconscient
**Versions** : v2.1 (3 étapes, actif) → fallback v2.0 → fallback v1.0
**Fichiers** : `introspection_engine.py` `introspection_orchestrator.py` `introspection_core.py` `config_v2.py` `ui_parameters_v2.py` `memory_integration.py` `subconscience_orchestrator.py`
```python
initialize_cognitive_mirror(chat_ctrl, archiviste_ctrl, memory_mgr) → bool
initialize_introspection(chat_ctrl, archiviste_ctrl, memory_mgr) → bool
get_cognitive_mirror() → CognitiveMirrorCore
get_engine() → IntrospectionEngine
```

---

### `journal_de_bord/` — Journal Quotidien
**Fichiers** : `core_journal.py` `entry_generator.py` `context_provider.py` `json_manager.py` `scheduler.py` `calendar_viewer.py` `purge_manager.py` `live_state_detector.py` `auto_resolution.py`
```python
initialize_journal(archiviste_ctrl, memory_mgr, ui_container) → bool
get_journal() → JournalCore
journal.get_today_context() → str          # injection contexte matinal
journal.create_entry_from_conversation()   # async
```
**Note** : `context_provider.py` injecte aussi le contexte du dernier rêve non mentionné

---

### ~~`archi_sensor/`~~ — ⚠️ OBSOLÈTE (Métacognition Émotionnelle)
> Remplacé par le **Unified Meta-Analyzer** intégré dans `logic_callbacks.py`. Le hook dans `ogma_ng.py` est entièrement commenté (`DÉSACTIVÉ: Legacy Archi Sensor remplacé par Unified Meta-Analyzer`). Les fichiers existent sur disque mais ne sont jamais chargés.

---

### `capability_advisor/` — Conseiller Capacités (LEDs)
**6 capacités** : 💾 Mémorisation | 🧠 Introspection | 🎨 Image | 📷 Webcam | 🌐 Web | 👤 Biographie
**Fichiers** : `advisor_core.py` `capability_catalog.py` `suggestion_engine.py` `led_manager.py` `ui_components.py`
```python
initialize_capability_advisor(chat_ctrl, archiviste_ctrl, memory_mgr) → CapabilityAdvisor
is_available() → bool
```

---

### `contextual_recall/` — Recall Conversationnel
**Dépend de** : résumés JSON format v2.2 dans fichiers conversations
**Fichiers** : `summary_loader.py` `__init__.py`
```python
initialize_recall(conversations_path="data/conversations") → RecallAgent
is_available() → bool
recall_agent.process_message(user_message) → Optional[str]
```

---

### `web_navigator/` — Recherche Internet (Serper API)
**Commandes** : `/web` `/news` `/image` `/search` `/scholar`
**Phrases magiques** : "cherche sur internet", "recherche sur internet", "actualités sur", "cherche des images"
```python
WebNavigatorConfig(settings_manager)
SerperClient(api_key)
WebNavigatorCommands(config, client)
WebNavigatorExtension(config, client, commands)
```

---

### `text2img/` — Génération Images
**Providers** : GROK (grok-2-image-1212) | OpenAI (DALL-E 3/2) | Google (Imagen 3)
```python
initialize_text2img(settings_manager) → bool
get_text2img_manager() → Text2ImageManager
await manager.generate_image(prompt) → image_data
```

---

### `telegram_connector/` — Bot Telegram (aiogram)
```python
initialize_telegram_connector(chat_ctrl, archiviste_ctrl, memory_mgr,
    settings_mgr, audio_mgr, text2img_mgr, web_navigator) → bool
start_telegram_bot()
stop_telegram_bot()
is_telegram_running() → bool
send_telegram_notification(message)
```

---

### `temporal_guardian/` — Capteur Temporel
**Remplace** `temporal_injector.py` (désactivé)
```python
create_temporal_guardian(debug=True) → TemporalGuardian
guardian.process_user_message(user_message, archiviste_prompt) → str
# Composants : TemporalSensor (mesure délais) + ArchivisteEnricher (enrichit prompt)
```

---

### `organic_planner/` — Agenda IA
**DB** : `data/agenda.db` SQLite
```python
initialize_planner(...) → OrganicPlanner
get_planner() → OrganicPlanner
get_briefing() → str          # injection briefing quotidien
is_available() → bool
```

---

### `biographie_profil/` — Biographies Utilisateurs
**Architecture** : Vol.1 (souvenirs FAISS filtrés) + Vol.2 (journal narratif .txt)
**Fichiers** : `biography_manager.py`
```python
initialize_biography_extension(settings_mgr, memory_mgr, chat_ctrl, archiviste_ctrl, status_queue) → bool
```

---

### `flux_cognitif/` — Visualisation Pensées IA
**UI** : overlay ambre translucide, 50 events max en mémoire
**Sources** : `'archiviste'` `'biography'` `'dream'` `'journal'` `'web'` `'capability'`
```python
initialize_flux_cognitif() → FluxCognitif
flux.log_event(source, message, metadata, event_level)
# event_level: 1=SURFACE | 2=NORMAL | 3=DEEP
```

---

### ~~`ego_selector/`~~ — ⚠️ OBSOLÈTE (Sélection Contextuelle Ego)
> Remplacé par le **Ego Boolean System** (`modules/logic/ego_activation.py`) depuis le 26 janv. 2026.
> Gains : 2 750 → 0–540 tokens, latence 1 550ms → 100–200ms. Les fichiers `ego_selector.py` (388 lignes) et `extensions/ego_selector/` (272 lignes) existent sur disque mais ne sont **jamais importés**.

---

### `file_writer/` — Sauvegarde .md Auto
```python
initialize_file_writer(uploads_dir, debug) → FileWriterAgent
file_writer.process_response(user_message, ai_response) → Optional[Path]
is_available() → bool
get_statistics() → dict
```

---

## 4. MODULES INTERNES

### `modules/ogma_core/`

| Fichier | Rôle |
|---------|------|
| `globals.py` | **Centralise TOUTES les variables globales** : `_chat_controller`, `_archiviste_controller`, `_embedding_controller`, `_memory_manager`, `_settings_manager`, `_audio_manager`, `_chat_history`, `_chat_history_ui`, `_current_conversation_id`, refs UI |
| `controllers.py` | Réimplémente toutes les `ensure_*()` avec accès via `globals.py` |
| `extensions_loader.py` | Cache disponibilité extensions, `_check_extension_available(name)` |
| `compat.py` | Couche compatibilité pour `ogma_ng.py` (rétro-compat) |
| `utils.py` | Helpers core |

### `modules/logic/`

| Fichier | Fonctions clés |
|---------|---------------|
| `perception.py` | `get_visual_events_context()` — contexte webcam |
| ~~`archi_sensor.py`~~ | ⚠️ OBSOLÈTE — stubs legacy non appelés (409 lignes, remplacé par Unified Meta-Analyzer) |
| `memory_utils.py` | `caviarder_phrases_magiques_introspection()`, `trigger_indexing_fn()` |
| `image_generation.py` | `process_image_generation()`, `process_img2img_generation()`, boucle correction img2img |
| `i2i_lessons.py` | `I2ILessonsManager` — apprentissage img2img |
| `ego_activation.py` | Activation ego contextuelle |

### `modules/preanalysis_optimizer/` — Background Threading

```
PreanalysisEngine
  trigger(conversation_history)     ← déclenché quand user tape
  get_results()                     ← récupéré après ENTRÉE
  # Analyse en parallèle : Archi Sensor + Ego Catalog
  # ThreadPoolExecutor (2 workers)
  # Cache ego_catalog TTL=60s

Fichiers :
  preanalysis_engine.py    ← moteur principal
  context_cache.py         ← cache contexte
  parallel_executor.py     ← exécution parallèle
  integration.py           ← interface ogma_ng
  unified_meta_analyzer.py ← analyse unifiée
```

### `modules/audio/manager.py` — `AudioManager` (1884 lignes)

```
initialize_tts()                   ← init moteur TTS
initialize_stt()                   ← init moteur STT
start_recording() / stop_recording()
speak(text)
clean_text_for_tts(text)

TTS supportés : pyttsx3 | SAPI Windows | Google Cloud | ElevenLabs | OpenAI TTS | piper | coqui
STT supportés : SpeechRecognition | vosk (offline) | OpenAI Whisper API | Azure Speech
```

### `modules/voice/`

```
VoiceManager    → voice_manager.py   ← gestionnaire principal
VoiceTriggers   → voice_triggers.py  ← triggers vocaux
VoiceUI         → voice_ui.py        ← interface voix
initialize_voice_manager(settings_mgr, audio_manager)
```

### `utils/` — Utilitaires Transversaux

| Fichier | Fonctions |
|---------|-----------|
| `backend_utils.py` | `map_backend_for_controller(backend) → str` — normalise vers UPPERCASE |
| `formatting_utils.py` | `format_size()`, `format_datetime()`, `truncate_filename()`, `get_file_icon()` |
| `json_cleaner.py` | `clean_json_response()` (retire ```json), `_clean_control_characters()` |
| `message_parsers.py` | `parse_thinking_format()` (JSON thinking Mistral magistral), `parse_introspection_format()` |

---

## 5. PIPELINE `_send_chat_message()` (l.1880)

| # | Étape | Source |
|---|-------|--------|
| 1 | Validation input (vide ?) | `ogma_ng.py` |
| 2 | Pré-analyse Archi Sensor (preanalysis_optimizer, si dispo) | `modules/preanalysis_optimizer/` |
| 3 | Temporal Guardian → enrichissement horodatage | `extensions/temporal_guardian/` |
| 4 | Ego Boolean injection (activate_ego_groups : 0–3 groupes selon contexte) | `modules/logic/ego_activation.py` + `data/ego_compiled.json` |
| 5 | Contextual Recall → injection résumés historiques | `extensions/contextual_recall/` |
| 6 | Capability Advisor → suggestion capacité (LEDs) | `extensions/capability_advisor/` |
| 7 | Biography → contexte biographique user | `extensions/biographie_profil/` |
| 8 | Journal de Bord → contexte journal matinal | `extensions/journal_de_bord/` |
| 9 | Web Navigator → recherche si /web ou phrase magique | `extensions/web_navigator/` |
| 10 | Vision/Webcam → contexte visuel si actif | `modules/logic/perception.py` |
| 11 | Dream Engine → contexte rêve si non mentionné | `extensions/dream_engine/` |
| 12 | Archiviste → injection souvenirs FAISS+FTS5 pertinents | `memory_manager.py` |
| 13 | Organic Planner → briefing agenda | `extensions/organic_planner/` |
| 14 | **Chat Controller → génération streaming** | `core_logic.py` `AIController` |
| 15 | Magic Phrase Guard → détection phrases spéciales post-génération | `magic_phrase_guard.py` `hybrid_detection.py` |
| 16 | File Writer → sauvegarde .md si détecté | `extensions/file_writer/` |
| 17 | Conversation Scanner → si phrase "consulte conversation" | `conversation_scanner.py` |
| 18 | Summarizer → résumé progressif si seuil atteint (tous les 10 messages) | `conversation_summarizer.py` |
| 19 | Save conversation JSON (messages + summaries) | `utils.py` `save_conversation()` |

---

## 6. PATTERNS D'INTÉGRATION

### Pattern Lazy Init (omniprésent dans `ogma_ng.py`)
```python
def _ensure_memory_manager() -> Optional[MemoryManager]:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(
            db_path=DATA_DIR / "memories.db",
            index_path=DATA_DIR / "memory_index.faiss",
            embedding_dim=1536,
            embedding_controller=_ensure_embedding_controller()
        )
    return _memory_manager
```

### Pattern Accès Globals Inter-Modules (via `sys.modules`)
```python
# Utilisé dans : ogma_modals.py, ogma_headers.py, ogma_displays.py
def _get_global_var(var_name, default=None):
    import sys
    ogma_ng = sys.modules.get('ogma_ng')
    if ogma_ng and hasattr(ogma_ng, var_name):
        return getattr(ogma_ng, var_name)
    return default
```
**Ne jamais modifier les globals directement — toujours passer par les `_ensure_*()`**

### Pattern Extension Standard
```python
# extensions/[name]/__init__.py
def initialize_[name](dependencies...) → bool
def is_available() → bool
def get_ui_components() → dict    # optionnel — bouton header
def cleanup()                     # optionnel — nettoyage propre
```

### Pattern Dual-IA
```
_chat_controller        → AIController  role='chat'        temp=0.7  ← conversationnel
_archiviste_controller  → AIController  role='archiviste'  temp=0.3  ← analytique
_embedding_controller   → EmbeddingController                         ← vectoriel
```

### Pattern Déduplication Injections (`injection_deduplicator.py`)
```python
reset_deduplication_session()
register_ego_prompt_injection()
check_archiviste_injection(content) → bool
register_archiviste_injection(content)
get_deduplication_stats() → dict
```

### Pattern Error Handling Défensif
```python
try:
    result = main_operation()
except Exception as e:
    print(f"[COMPONENT] Erreur: {e}")
    _notify_safe(f"Erreur: {e}", type='warning')
    # jamais de fallback silencieux sans confirmation Yohan
```

### Thread Safety FAISS
```python
with self._faiss_lock:
    # toutes les opérations FAISS (lecture + écriture)
```

---

## 7. DONNÉES CRITIQUES

### `data/settings.json` — Structure par contrôleur
```json
{
  "chat_api":         { "provider", "api_key", "api_model", "backend_type", "temperature", "max_tokens", "context_length" },
  "archiviste_api":   { "provider", "api_key", "api_model", "backend_type", "temperature" },
  "reasoning_api":    { "provider", "api_key", "api_model" },
  "embedding_api":    { "provider", "api_key", "api_model", "backend_type" },
  "audio":            { "stt_engine", "tts_engine", "auto_send", "voice_settings" },
  "image_generation": { "provider", "api_key", "vision_compression": 400 },
  "web_search":       { "serper_api_key", "enabled" },
  "telegram":         { "bot_token", "chat_id", "enabled" }
}
```

### Format JSON Conversation v2.2
```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "summaries": {
    "ranges": [
      {"start": 0, "end": 10, "text": "Résumé 1-10", "cache_key": "abc123"},
      {"start": 10, "end": 20, "text": "Résumé 11-20", "cache_key": "def456"}
    ],
    "last_index": 20,
    "interval": 10
  }
}
```
**Rétrocompat lecture** : ancien format `[{...}, {...}]` (liste pure) supporté dans `load_conversation()`

### Paths critiques
```
DATA_DIR              = data/
CONVERSATIONS_DIR     = data/conversations/
memories.db           = data/memories.db          ← SQLite principal
memory_index.faiss    = data/memory_index.faiss   ← Index vectoriel
ego_compiled.json     = data/ego_compiled.json
ego_prompt.txt        = data/ego_prompt.txt
identities.json       = data/identities.json
agenda.db             = data/agenda.db            ← Organic Planner
journal_reves.md      = data/journal_reves.md     ← Journal humain
journal_reves.json    = data/journal_reves.json   ← Journal IA-queryable
backups FAISS         = data/memory/backup/       ← rotation 10 fichiers
```

### Providers IA supportés
```
API Cloud  : OpenAI | Mistral | Anthropic | Google | GROK | AIHorde
Local      : Ollama | GGUF (llama-cpp-python) | KoboldCpp
```

### Démarrage
```
python launch_ogma.py   ← production (retry ports 8080-8090)
python start_ogma.py    ← dev rapide
```

### Variables globales centrales (NE PAS modifier directement)
```python
# Dans modules/ogma_core/globals.py
_chat_controller           # AIController conversationnel
_archiviste_controller     # AIController analytique
_embedding_controller      # EmbeddingController
_memory_manager            # MemoryManager SQLite+FAISS
_settings_manager          # SettingsManager
_audio_manager             # AudioManager
_chat_history              # List[dict] — conversation active (messages)
_chat_history_ui           # List[dict] — état affichage UI
_current_conversation_id   # str|None — ID conversation active
```

---

## 8. TESTS

```
tests/
  conftest.py                             ← Fixtures pytest globales
  unit/
    test_contextual_recall_strict.py      ← OBSOLETE (ref summaries_cache)
    test_conversation_manager_strict.py   ← OBSOLETE (param cache_dir)
  integration/
  e2e/
  legacy/

# Tests rapides à la racine :
test_dream_*.py                  ← dream engine
test_flux_cognitif_*.py          ← flux cognitif
test_ego_*.py                    ← système ego
test_introspection_*.py          ← introspection
test_live_*.py                   ← modèles live
test_memory_*.py, test_adaptive_memory_search.py
tests/test_summarizer_persistence.py     ← 8 tests résumation OK
```

---

## 9. NOTES ESTHÉTIQUES & UI (NiceGUI / Quasar)

### Sidebar & Boutons (Février 2026)
- **Problème de surcouche grise** : Quasar applique des classes `.q-drawer`, `.q-list`, etc. avec des fonds par défaut. Pour obtenir un fond transparent ou un effet "Flux Cognitif" (noir profond `#05090f` + inset shadow), il faut forcer `background: transparent !important;` et `backdrop-filter: none !important;` sur **tous** les conteneurs enfants dans `ogma_displays.py` (ex: `.sidebar-list`, `.sidebar-header`, `.q-drawer--left`).
- **Scrollbars Sobres — Règle Globale** : Une règle `*::-webkit-scrollbar` dans `static/ogma_styles.css` applique le style sobre à **tous** les éléments scrollables de l'app sans exception (`width: 6px`, `var(--border-default)` au repos, `var(--border-focus)` au survol, `border-radius: 3px`, pas d'ombre). Les règles spécifiques par classe (`.sidebar-list`, `.popup-content`, etc.) existent mais sont désormais redondantes — elles servent de documentation visuelle.
- **Boutons Carrés Parfaits (Quasar)** : Les boutons `.q-btn` de Quasar ont des `min-height` et des `padding` internes sur le `.q-btn__wrapper` qui forcent une forme rectangulaire. Pour forcer un carré parfait (ex: `28x28px` pour `.header-btn`), il faut :
  1. `width: 28px !important; height: 28px !important; min-height: 28px !important;` sur le bouton.
  2. `padding: 0 !important; margin: 0 !important;` sur le bouton.
  3. `padding: 0 !important; min-height: 0 !important;` sur le `.q-btn__wrapper`.
- **Cohérence Cyber/Néon** : Utilisation des variables `--neon-pink`, `--neon-gold`, `--neon-cyan`, `--neon-galactic` avec leurs déclinaisons `-glow` et `-glow-hover` dans `static/ogma_styles.css` pour unifier l'esthétique des boutons d'action et des headers.

---

## 10. ARCHITECTURE MISE EN PAGE — LAYOUT COMPLET (Février 2026)

### 10.1 Structure DOM & Grid

```
┌─────────────────────────────────────────── 100vw ────────────────────────────────────────────┐
│  app-header  (position: fixed, height: 80px = --header-height, z-index élevé)                │
│  [boutons gauche]          [boutons outils/extensions]           [logo OGMA 58px]             │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────── 100vw ────────────────────────────────────────────┐
│  app-body  (position: absolute, top: 80px → bottom: 0)                                       │
│  display: grid — 4 colonnes :                                                                │
│                                                                                              │
│  ┌────────────┐ ┌──────────┐ ┌────────────────────────────────────────────┐ ┌──────────┐   │
│  │  COLONNE 1 │ │ COL. 2   │ │  COLONNES 2→4  (grid-column: 2 / 5)        │ │  COL. 4  │   │
│  │            │ │gouttière │ │                                            │ │gouttière │   │
│  │  sidebar   │ │gauche    │ │  chat-panel  (display: flex column)        │ │droite    │   │
│  │            │ │ (auto)   │ │                                            │ │  (auto)  │   │
│  │ 0→360px    │ │          │ │  ┌──────────────────────────────────────┐  │ │          │   │
│  │ (--sidebar │ │          │ │  │ conversation-area (overflow-y: auto) │  │ │          │   │
│  │  -width)   │ │          │ │  │  ┌────────────────────────────────┐  │  │ │          │   │
│  │            │ │          │ │  │  │ chat-viewport-layer (flex)     │  │  │ │          │   │
│  │ transform: │ │          │ │  │  │  ┌──────────────────────────┐  │  │  │ │          │   │
│  │ translateX │ │          │ │  │  │  │ chat-centering-layer      │  │  │  │ │          │   │
│  │ pour anim. │ │          │ │  │  │  │ width: 800px (--chat-width│  │  │  │ │          │   │
│  │            │ │          │ │  │  │  │ margin-left: FORMULE *    │  │  │  │ │          │   │
│  │            │ │          │ │  │  │  │  ┌────────────────────┐   │  │  │  │ │          │   │
│  │            │ │          │ │  │  │  │  │ chat-inner         │   │  │  │  │ │          │   │
│  │            │ │          │ │  │  │  │  │ messages user/ai   │   │  │  │  │ │          │   │
│  │            │ │          │ │  │  │  │  └────────────────────┘   │  │  │  │ │          │   │
│  │            │ │          │ │  │  │  └──────────────────────────┘  │  │  │ │          │   │
│  │            │ │          │ │  │  └────────────────────────────────┘  │  │ │          │   │
│  │            │ │          │ │  └──────────────────────────────────────┘  │ │          │   │
│  │            │ │          │ │                                            │ │          │   │
│  │            │ │          │ │  message-input-footer (display: flex)      │ │          │   │
│  │            │ │          │ │  transform: translateY(-40px)              │ │          │   │
│  │            │ │          │ │  ┌──────────────────────────────────────┐  │ │          │   │
│  │            │ │          │ │  │ input-overlay                        │  │ │          │   │
│  │            │ │          │ │  │ width: 800px (--chat-width)          │  │ │          │   │
│  │            │ │          │ │  │ margin-left: MÊME FORMULE *          │  │ │          │   │
│  │            │ │          │ │  │  ┌────────────────────────────────┐  │  │ │          │   │
│  │            │ │          │ │  │  │ input-container (margin:0 auto)│  │  │ │          │   │
│  │            │ │          │ │  │  │ textarea + boutons             │  │  │ │          │   │
│  │            │ │          │ │  │  └────────────────────────────────┘  │  │ │          │   │
│  │            │ │          │ │  └──────────────────────────────────────┘  │ │          │   │
│  └────────────┘ └──────────┘ └────────────────────────────────────────────┘ └──────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

(position: fixed, hors flux grid)
  🧠 flux-cognitif-overlay  →  top: 80px, right: 10px, width: 200px
  🪞 cognitive mirror panel →  droite écran, width: 350px
  🔔 notifications Quasar   →  toasts NiceGUI
```

### 10.2 Variables CSS Clés (`:root` dans `ogma_styles.css`)

| Variable | Valeur | Rôle |
|----------|--------|------|
| `--sidebar-width` | `0px` → `360px` | Contrôle ouverture sidebar (modifié par JS) |
| `--header-height` | `80px` | Hauteur header fixe |
| `--chat-width` | `800px` | Largeur fixe de la zone conversation |
| `--composer-height-px` | `160px` (dynamique) | Hauteur barre saisie, mis à jour via ResizeObserver JS |
| `--composer-safe` | `140px` | Padding sécurité bas du scroll |

### 10.3 Formule de Centrage — Le Cœur du Système

**Problème résolu** : quand la sidebar s'ouvre (0 → 360px), le `chat-panel` s'étend sur `grid-column: 2/5`. L'espace disponible pour le centrage du contenu se réduit de 180px à gauche → la zone conversation se décalait de **+180px vers la droite**.

**Solution** : `chat-centering-layer` et `input-overlay` utilisent un `margin-left` calculé depuis le bord absolu gauche de l'écran :

```
marge gauche = max(0px, (100vw - 800px) / 2 - --sidebar-width)

Démonstration :
  sidebar = 0px  →  (100vw - 800) / 2 - 0    = (100vw - 800) / 2   ✓ centré
  sidebar = 360px → (100vw - 800) / 2 - 360  = position IDENTIQUE  ✓ immobile

Position absolue dans l'écran :
  = sidebar-width (col 1 du grid) + margin-left
  = sidebar + (100vw - 800) / 2 - sidebar
  = (100vw - 800) / 2   ← CONSTANTE quelle que soit la sidebar
```

**Transition** : `--sidebar-width` est animé en `0.3s ease-in-out` par le JS → `transition: margin-left 0.3s ease-in-out` sur les deux éléments assure la fluidité.

### 10.4 CSS Impacté (fichier : `static/ogma_styles.css`)

| Sélecteur | Ligne approx. | Modification clé |
|-----------|---------------|------------------|
| `.chat-viewport-layer` | ~608 | `justify-content: flex-start` (plus `center`, délégué au margin-left) |
| `.chat-centering-layer` | ~619 | `margin-left: max(0px, calc((100vw - var(--chat-width)) / 2 - var(--sidebar-width)))` + `transition: margin-left 0.3s` |
| `.message-input-footer` | ~709 | `display: flex; justify-content: flex-start` (pour que margin-left de input-overlay fonctionne) |
| `.input-overlay` | ~718 | `width: var(--chat-width)` + même formule `margin-left` que centering-layer |
| `.input-container` | ~733 | `margin: 0 auto` (remplit les 800px de l'overlay) |

### 10.5 JS Toggle Sidebar (`ogma_ng.py` l. ~8083)

```javascript
// Ouverture sidebar
document.documentElement.style.setProperty('--sidebar-width', '360px');
sidebar.style.transform = 'translateX(0)';
// → CSS transition margin-left se déclenche automatiquement

// Fermeture sidebar
sidebar.style.transform = 'translateX(-100%)';
setTimeout(() => {
    document.documentElement.style.setProperty('--sidebar-width', '0px');
}, 50); // délai pour que l'animation glissement se finisse avant le reflow grid
```

**Note** : la `sidebar` utilise `transform: translateX()` pour l'animation visuelle de glissement. La CSS variable `--sidebar-width` est mise à jour en décalé (50ms) uniquement pour le reflow du grid.

### 10.6 Cas Spécial : Mode Métacognitif (`.with-metacognition`)

Quand le panneau Cognitive Mirror (350px) est ouvert, `.app-body` reçoit la classe `with-metacognition` :
- Le grid se recalcule pour absorber les 350px dans les gouttières
- `.input-overlay` reçoit une formule ajustée : `max(0px, (100vw - 800 - 350) / 2 - sidebar-width)`
- Défini en 3 blocs dans le CSS : règle normale + `@media (max-width: 1400px)` + `@media (max-width: 1200px)`

### 10.7 Flux Cognitif Overlay (`extensions/flux_cognitif/stream_ui.py`)

```
position: fixed
top: 80px        ← ajusté manuellement (était 60px → 70px → 80px en févr. 2026)
right: 10px
width: 200px
height: calc((100vh - 60px) * 0.7)
```

L'overlay est **hors du flux grid** → non affecté par sidebar. État géré par `FluxCognitifUI.overlay_visible` (bool, init `False`). L'instance globale `_flux_ui_instance` est recréée à chaque démarrage → toujours propre.

### 10.8 Points de Vigilance pour Interventions Futures

1. **Ne jamais remettre `justify-content: center` sur `.chat-viewport-layer`** — le centrage est désormais intégralement géré par `margin-left` sur `chat-centering-layer`.
2. **Ne jamais remettre `width: 100%` sur `.input-overlay`** — doit rester `var(--chat-width)` (800px fixe).
3. **Ne jamais remettre `margin: 0 auto` sur `.chat-centering-layer`** — incompatible avec la formule de position fixe.
4. **Toujours garder `transition: margin-left 0.3s ease-in-out`** sur les deux éléments clés pour l'animation fluide.
5. **Si on change `--chat-width`**, recalculer mentalement la formule — elle reste valide automatiquement car c'est une variable CSS.
6. **CSS media queries `with-metacognition`** — les 3 blocs doivent rester cohérents entre eux si on modifie la formule principale.

---

*Carte générée le 24 février 2026 — v2.2*
