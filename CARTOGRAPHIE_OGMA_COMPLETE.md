# 🗺️ CARTOGRAPHIE COMPLÈTE OGMA v2.0

**Date de génération** : 25 octobre 2025  
**Fichier principal** : `ogma_ng.py` (7724 lignes)  
**Architecture** : Monolithe + Extensions modulaires

---

## 📚 TABLE DES MATIÈRES

1. [Structure Globale](#structure-globale)
2. [Variables Globales Critiques](#variables-globales-critiques)
3. [Système d'Initialisation (Lazy Loading)](#système-dinitialisation-lazy-loading)
4. [Gestionnaires Core (Managers)](#gestionnaires-core-managers)
5. [Contrôleurs IA](#contrôleurs-ia)
6. [Système de Messages & Chat](#système-de-messages--chat)
7. [Gestion des Conversations](#gestion-des-conversations)
8. [Système de Mémoire](#système-de-mémoire)
9. [Extensions](#extensions)
10. [UI Components (Interface)](#ui-components-interface)
11. [Magic Phrases System](#magic-phrases-system)
12. [Audio System](#audio-system)
13. [Modals & Dialogs](#modals--dialogs)
14. [Routes & Pages](#routes--pages)
15. [Utilitaires](#utilitaires)
16. [Points d'Injection (Hooks)](#points-dinjection-hooks)

---

## 📁 STRUCTURE GLOBALE

### Fichier Principal
```
ogma_ng.py (7724 lignes)
├── Imports & Configuration (1-170)
├── Lazy Initializers (239-1025)
├── UI Components (1057-2148)
├── Conversation Management (2148-2821)
├── Sidebar & Magic Phrases (2957-3640)
├── Modals (Settings, Images, Profiles) (3646-4345)
├── Backend Communication (4345-4699)
├── Message Handler (_send_chat_message) (4981-6557)
├── Audio & Input (6557-6671)
├── Perception Page (6671-7270)
├── Main Page (7270-7575)
└── Run Function (7581-7644)
```

### Modules Core
```
core_logic.py           - Contrôleurs IA (API/Ollama/GGUF/KoboldCpp)
memory_manager.py       - SQLite + FAISS (mémoire vectorielle)
audio_manager.py        - STT/TTS multi-engines
conversation_summarizer.py - Archivage conversations
utils.py                - Chemins, helpers, ego_prompt
```

### Système de Protection
```
nicegui_error_handler.py    - Anti-crash NiceGUI
magic_phrase_guard.py       - Protection messages historiques
injection_deduplicator.py   - Anti-duplication injections
```

---

## 🔧 VARIABLES GLOBALES CRITIQUES

### État Application
| Variable | Type | Ligne | Description |
|----------|------|-------|-------------|
| `_chat_history` | `List[Dict]` | 131 | Historique conversation courante (full) |
| `_chat_history_ui` | `List[Dict]` | 132 | Messages UI avec metadata |
| `_conversation_history` | `List[Dict]` | 133 | Messages affichés UI actuelle |
| `_current_conversation_id` | `Optional[str]` | 134 | ID conversation active |
| `_current_conversation_title` | `str` | 135 | Titre conversation active |
| `_chat_inner` | UI Element | 136 | Container messages chat |

### Managers (Singletons Lazy)
| Variable | Type | Ligne | Description |
|----------|------|-------|-------------|
| `_settings_manager` | `SettingsManager` | 137 | Config persistante (settings.json) |
| `_memory_manager` | `MemoryManager` | 138 | Mémoire SQLite+FAISS |
| `_audio_manager` | `AudioManager` | 139 | STT/TTS |
| `_chat_controller` | `AIController` | 140 | IA principale conversation |
| `_archiviste_controller` | `AIController` | 141 | IA enrichissement mémoire |
| `_embedding_controller` | `EmbeddingController` | 142 | Génération embeddings FAISS |

### Backend Managers
| Variable | Type | Ligne | Description |
|----------|------|-------|-------------|
| `_api_manager` | `APIManager` | 143 | Providers API (OpenAI, Mistral, etc.) |
| `_ollama_manager` | `OllamaManager` | 144 | Ollama local |
| `_gguf_manager` | `GGUFManager` | 145 | GGUF (llama.cpp) |
| `_kobold_manager` | `KoboldManager` | 146 | KoboldCpp |

### Extensions (Lazy Loaded)
| Variable | Type | Ligne | Description |
|----------|------|-------|-------------|
| `_cognitive_mirror` | Extension | 147 | Introspection/métacognition |
| `_temporal_guardian` | Extension | 148 | Injection contexte temporel |
| `_web_navigator` | Extension | 149 | Recherche web (Serper) |
| `_biography_extension` | Extension | 150 | Profils biographiques |
| `_journal_extension` | Extension | 151 | Journal de bord quotidien |

### UI State
| Variable | Type | Ligne | Description |
|----------|------|-------|-------------|
| `_active_files` | `List[Dict]` | 152 | Fichiers uploadés actifs |
| `_file_tabs_container` | UI Element | 153 | Container tabs fichiers |
| `_thinking_css_injected` | `bool` | 154 | Flag injection CSS thinking |
| `_introspection_box_content` | `List` | 155 | Contenu box introspection |
| `_introspection_md_widget` | UI Element | 156 | Widget markdown introspection |

### Perception Extension
| Variable | Type | Ligne | Description |
|----------|------|-------|-------------|
| `perception_ui` | Module | 158 | Interface Perception |
| `perception_agent` | Module | 159 | Backend webcam OpenCV |

---

## 🚀 SYSTÈME D'INITIALISATION (LAZY LOADING)

### Pattern Utilisé
Toutes les initialisations suivent le pattern **singleton lazy** :

```python
_global_instance = None

def _ensure_component():
    global _global_instance
    if _global_instance is None:
        _global_instance = Component(...)
    return _global_instance
```

### Fonctions d'Initialisation

| Fonction | Ligne | Retour | Description |
|----------|-------|--------|-------------|
| `_ensure_settings_manager()` | 239 | `SettingsManager` | Config app (settings.json) |
| `_ensure_audio_manager()` | 247 | `AudioManager` | STT/TTS |
| `_ensure_backends()` | 268 | Tuple | API, Ollama, GGUF, Kobold managers |
| `_ensure_memory_manager()` | 322 | `MemoryManager` | SQLite + FAISS |
| `_ensure_temporal_guardian()` | 480 | Extension | Contexte temporel |
| `_ensure_cognitive_mirror()` | 840 | Extension | Introspection |
| `_ensure_chat_controller()` | 931 | `AIController` | IA principale |
| `_ensure_archiviste_controller()` | 1025 | `AIController` | IA archiviste |

### Dépendances d'Initialisation

```
run_ogma()
├── main_page()
│   ├── _sidebar()
│   │   └── _load_conversation_index()
│   ├── _header()
│   │   ├── _ensure_settings_manager()
│   │   ├── _initialize_biography_extension()
│   │   └── _initialize_journal_extension()
│   └── _input_overlay()
│       └── _ensure_audio_manager()
├── perception_page()
│   └── Perception UI components
└── _ensure_backends()
    ├── _ensure_chat_controller()
    ├── _ensure_archiviste_controller()
    └── _ensure_memory_manager()
```

---

## 🎛️ GESTIONNAIRES CORE (MANAGERS)

### SettingsManager
**Fichier** : `core_logic.py`  
**Fonction init** : `_ensure_settings_manager()` (ligne 239)

**Responsabilités** :
- Gestion `data/settings.json`
- Sauvegarde configuration IA (providers, modèles, clés API)
- Sauvegarde prompts système
- Configuration extensions

**API Critique** :
```python
settings.get_setting(section, key, default)
settings.set_setting(section, key, value)
settings.save_settings()
settings.reload_settings()
```

### MemoryManager
**Fichier** : `memory_manager.py`  
**Fonction init** : `_ensure_memory_manager()` (ligne 322)

**Responsabilités** :
- Base SQLite `data/memory/memory.db`
- Index FAISS `data/memory/memory.faiss`
- Ajout/recherche/suppression souvenirs
- Embeddings vectoriels

**API Critique** :
```python
await memory.add_memory(mem_id, content, metadata)
await memory.search_memories(query, limit)
memory.get_memory_by_id(mem_id)
await memory.delete_memory(mem_id)
```

**Backup Automatique** : Rotation 10 fichiers dans `data/memory/backup/`

### AudioManager
**Fichier** : `audio_manager_wrapper.py` → `audio_manager.py`  
**Fonction init** : `_ensure_audio_manager()` (ligne 247)

**Responsabilités** :
- STT (Speech-to-Text) : Whisper, Vosk
- TTS (Text-to-Speech) : ElevenLabs, Azure, gTTS, pyttsx3
- Détection moteurs disponibles

**API Critique** :
```python
audio_manager.start_recording()
audio_manager.stop_recording() → text
audio_manager.speak(text, voice_id)
audio_manager.get_available_engines()
```

---

## 🤖 CONTRÔLEURS IA

### Architecture Triple-IA

OGMA utilise **3 contrôleurs IA indépendants** :

1. **Chat Controller** (IA principale conversationnelle)
2. **Archiviste Controller** (Enrichissement mémoire)
3. **Embedding Controller** (Génération vecteurs FAISS)

### Chat Controller
**Fonction init** : `_ensure_chat_controller()` (ligne 931)

**Configuration** : `settings.json → chat_api`
- Provider (OpenAI, Mistral, Anthropic, Ollama, GGUF, etc.)
- Model
- API Key (si provider API)
- Temperature, Max Tokens, Context Length

**Appel Principal** : Ligne 6077 dans `_send_chat_message()`

### Archiviste Controller  
**Fonction init** : `_ensure_archiviste_controller()` (ligne 1025)

**Configuration** : `settings.json → reasoning_api`
- Provider indépendant du Chat
- Utilisé pour mémorisation, injection, synthèses

**Appels Principaux** :
- Mémorisation : Ligne 5724 (`_send_chat_message`)
- Injection : Via `memory_manager.search_memories()`
- Synthèse conversations : `_generate_conversation_summary()` (ligne 3384)

### Embedding Controller
**Fichier** : `core_logic.py` (classe `EmbeddingController`)

**Configuration** : `settings.json → embedding_api`
- Provider spécialisé embeddings
- Génère vecteurs 768/1536 dimensions pour FAISS

---

## 💬 SYSTÈME DE MESSAGES & CHAT

### Fonction Centrale : `_message()`
**Ligne** : 1559-2113 (554 lignes !)

**Responsabilités** :
- Rendu messages user/assistant/system
- Détection phrases magiques **IA** (dans réponses assistant)
- Parsing thinking format
- Injection biographie automatique
- **Hooks Cognitive Mirror** (introspection IA)
- **Hooks Perception** (activation webcam)
- Badges (tags messages)
- Edit mode (modification messages)

### Format Thinking
**Parser** : `_parse_thinking_format()` (ligne 2835)

Structure :
```
<thinking>Pensée interne</thinking>
Réponse visible utilisateur
```

Affiché dans expansion "🧠 réflexion" (dépliable).

### Format Introspection
**Parser** : `_parse_introspection_format()` (ligne 2917)

Structure :
```
<subconscience role="archiviste">Dialogue interne</subconscience>
Réponse synthèse
```

### Hooks dans `_message()` (Détection Phrases Magiques IA)

| Extension | Lignes | Phrases Détectées |
|-----------|--------|-------------------|
| Biography | 1580-1608 | "il faut que je consulte la biographie de [prénom]" |
| Cognitive Mirror | 1610-1706 | "il faut que je réfléchisse" |
| **Perception** | **1708-1777** | **"il faut que je te vois", "je veux te voir"** |

---

## 📦 GESTION DES CONVERSATIONS

### Système d'Index
**Fichier** : `data/conversations/index.json`

Structure :
```json
{
  "conv_id": {
    "id": "conv_id",
    "title": "Titre",
    "created": "ISO datetime",
    "updated": "ISO datetime",
    "message_count": 42,
    "memorized": true/false
  }
}
```

### Fonctions Critiques

| Fonction | Ligne | Description |
|----------|-------|-------------|
| `_load_conversation_index()` | 2148 | Charge index.json |
| `_save_conversation_index()` | 2164 | Sauvegarde index.json |
| `_make_conv_id()` | 2177 | Génère ID unique (timestamp) |
| `_make_title_from_text()` | 2188 | Titre basique (15 mots max) |
| `_generate_smart_title_from_history()` | 2203 | Titre IA intelligent |
| `_persist_conversation()` | 2541 | Sauvegarde conversation active |
| `_load_conversation()` | 2712 | Charge conversation archivée |
| `_new_conversation()` | 2788 | Démarre nouvelle conversation |

### Système de Titrage Intelligent

**Processus** :
1. **Message 1** : Titre basique (15 premiers mots)
2. **Message 2** : Trigger génération IA asynchrone
3. **Génération** : Résumé 3-7 mots via Archiviste Controller
4. **Update** : Mise à jour index + fichier conversation

**Fonctions** :
- Trigger : `_schedule_smart_title_generation()` (ligne 2258)
- Async : `_generate_smart_title_async()` (ligne 2277)
- Manuel : `_regenerate_title_manual()` (ligne 2372)

### Mémorisation Conversations

**Workflow** :
1. Génération résumé via Archiviste : `_generate_conversation_summary()` (3384)
2. Mémorisation dans FAISS : `_memorize_conversation()` (3450)
3. Flag dans index : `_mark_conversation_memorized()` (3497)

**Utilitaires** :
- Check : `_is_conversation_memorized()` (3505)
- Count : `_count_memorized_conversations()` (3511)
- List : `_get_memorized_conversations_list()` (3517)
- Update : `_update_memorized_conversation()` (3531)
- Delete : `_delete_memorized_conversation()` (3553)

---

## 🧠 SYSTÈME DE MÉMOIRE

### Architecture Hybride
- **SQLite** : `data/memory/memory.db` (metadata, texte)
- **FAISS** : `data/memory/memory.faiss` (vecteurs embeddings)
- **Backup** : `data/memory/backup/` (rotation 10 fichiers)

### Tables SQLite

**memories**
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    title TEXT,
    summary TEXT,
    text_original TEXT,
    valence INTEGER,
    score_impact REAL,
    lesson TEXT,
    created_at TEXT,
    metadata JSON
)
```

### Souvenirs Fondateurs
**Fichier** : `data/instructions_defaults.json → souvenirs_fondateurs`

Liste IDs souvenirs à **toujours** injecter (haute importance).

### Fonction Injection
**Dans** : `_send_chat_message()` ligne ~5920

**Process** :
1. Recherche vectorielle FAISS (query = message utilisateur)
2. Récupération top 3-5 souvenirs
3. Déduplication (injection_deduplicator.py)
4. Formatting :
   - Score > 95 : `[MÉMOIRE À HAUT IMPACT | Texte original]`
   - Score ≤ 95 : `Note de l'Archiviste : [Synthèse]`
5. Injection dans prompt système

### Fonction Mémorisation
**Trigger** : Phrases magiques utilisateur
- "il faut que je me souvienne de ça: [texte]"
- "mémorise ça: [texte]"

**Process** : Ligne 5724-5780 dans `_send_chat_message()`
1. Extraction texte (regex)
2. Génération metadata via Archiviste Controller
3. Génération embedding via Embedding Controller
4. Insertion SQLite + FAISS

---

## 🔌 EXTENSIONS

### Architecture Modulaire

Toutes les extensions suivent le pattern :
```
extensions/[nom]/
├── __init__.py          # Point d'entrée API publique
├── core.py              # Logique métier
├── ui_components.py     # Interface NiceGUI (optionnel)
└── config.py            # Configuration (optionnel)
```

### Cognitive Mirror (Introspection)

**Dossier** : `extensions/cognitive_mirror/`

**Fonction init** : `_ensure_cognitive_mirror()` (ligne 840)

**API Publique** :
```python
initialize_cognitive_mirror(deps)  # Initialisation
get_cognitive_mirror()             # Récupère instance
is_enabled()                       # Check activation
check_magic_phrases(text, source)  # Détection phrases
trigger_introspection_sync()       # Lance introspection
```

**Phrases Magiques IA** :
- "il faut que je réfléchisse"
- "il faut que tu réfléchisses" (utilisateur)

**Intégration** :
- Detection phrases: `_message()` ligne 1610-1706
- Callbacks: `_on_introspection_message_callback()` (739)
- Synthesis: `_on_synthesis_ready()` (724)

### Perception (Vision Webcam)

**Fichiers** :
- `extensions/perception_ui.py` (Interface)
- `extensions/perception_agent.py` (Backend OpenCV)

**API Publique** :
```python
from extensions.perception_ui import get_perception_ui

perception_ui.start_perception()   # Démarre webcam
perception_ui.stop_perception()    # Arrête webcam
perception_ui.capture_for_chat()   # Snapshot pour IA
perception_ui.is_enabled           # État activation
```

**Phrases Magiques IA** : **⭐ RÉCEMMENT AJOUTÉ**
- Activation : "il faut que je te vois", "je veux te voir"
- Désactivation : "je n'ai plus besoin de te voir", "je ferme ma vision"

**Intégration** :
- Detection phrases: `_message()` ligne **1708-1777**
- Capture auto: `_send_chat_message()` ligne 5360
- Page dédiée: `perception_page()` ligne 6671

**Configuration** :
- Resolution: 640x480 (Normal), 720p/1080p (Chirurgical)
- FPS: 15-30 (configurable)
- Chronophotography: 2-20 images, 14 layouts

### Journal de Bord

**Dossier** : `extensions/journal_de_bord/`

**Fonction init** : `_initialize_journal_extension()` (ligne 1248)

**API Publique** :
```python
from extensions.journal_de_bord import get_journal_extension

journal.create_entry(content, metadata)
journal.get_entries(date)
journal.search_entries(query)
journal.generate_summary(period)
```

**Phrases Magiques** :
- "consulte le journal du [YYYY-MM-DD]"
- "montre le contexte d'hier"
- "résume la semaine"

**Injection Contexte** :
- Hook injection matinal automatique
- Fonction: `_inject_journal_context()` (ligne 1329)

### Biographie Profil

**Dossier** : `extensions/biographie_profil/`

**Fonction init** : `_initialize_biography_extension()` (ligne 1207)

**API Publique** :
```python
from extensions.biographie_profil import get_biography_extension

bio.get_profile(first_name)
bio.update_profile(first_name, data)
bio.generate_volume2(first_name)  # Narratif
```

**Phrases Magiques IA** :
- "il faut que je consulte la biographie de [prénom]"

**Intégration** :
- Detection phrases: `_message()` ligne 1580-1608
- Injection auto: Détection prénom première mention
- Button header: `_create_header_biography_button_inline()` (1441)

### Temporal Guardian

**Dossier** : `extensions/temporal_guardian/`

**Fonction init** : `_ensure_temporal_guardian()` (ligne 480)

**Responsabilités** :
- Injection horodatage dans prompt
- Calcul délais entre messages
- Détection fatigue/disponibilité utilisateur
- Instructions temporelles pour IA

**Injection** : Automatique dans prompt système (via injection_deduplicator)

### Web Navigator

**Dossier** : `extensions/web_navigator/`

**Fonction getter** : `get_web_navigator_instance()` (ligne 223)

**API Publique** :
```python
web_nav.search_web(query)
web_nav.search_news(query)
web_nav.search_images(query)
```

**Phrases Magiques IA** :
- "il faut que je cherche sur internet [sujet]"
- "actualités sur [sujet]"
- "recherche des images de [description]"

**Commandes** :
- `/web [terme]`
- `/news [sujet]`
- `/image [description]`

---

## 🎨 UI COMPONENTS (INTERFACE)

### Layout Principal

```
main_page()
├── _header()                    # Barre supérieure
│   ├── Logo OGMA
│   ├── Upload fichier
│   ├── Boutons extensions (Journal, Bio)
│   └── Settings/Profile
├── Row (flex)
│   ├── _sidebar()              # Liste conversations (20% width)
│   │   ├── Boutons New/Edit/Delete
│   │   ├── Liste conversations
│   │   └── Bouton phrases magiques (ⓘ)
│   └── Column (80% width)
│       ├── _conversation_history (messages)
│       └── _input_overlay()    # Zone saisie message
└── Styles CSS injection
```

### Header
**Fonction** : `_header()` (ligne 1488)

**Composants** :
- Logo + titre OGMA
- Upload fichier : `_show_file_upload_dialog()` (1167)
- Tabs fichiers actifs : `_update_file_tab_display()` (1103)
- Bouton Journal : `_create_header_journal_button_inline()` (1402)
- Bouton Biographie : `_create_header_biography_button_inline()` (1441)
- Settings modal : `_models_modal()` (3646)
- Profile modal : `_profile_modal()` (4143)

### Sidebar
**Fonction** : `_sidebar()` (ligne 2957)

**Composants** :
- Overlay phrases magiques : `_show_magic_phrases_info()` (ligne ~2960)
- Boutons : New, Edit, Delete conversation
- Liste conversations : Render dynamique avec index
- Filtres : Date, mémorisation
- Context menu : Edit title, Memorize, Delete

**Sections Overlay Phrases Magiques** :
- 📖 Journal de Bord
- 👤 Biographie Profil
- 🧠 Miroir Cognitif
- 💾 Mémorisation
- 📚 Conversations Archivées
- 🌐 Recherche Internet
- **👁️ Perception Visuelle (IA)** ← Ajouté récemment (ligne ~3088)

### Input Overlay
**Fonction** : `_input_overlay()` (ligne 6617)

**Composants** :
- Textarea message (auto-resize)
- Bouton micro (audio recording)
- Bouton send
- Bouton Perception (ouvrir page)
- Bouton stop (génération IA)

**Audio Integration** :
- Start recording : `_start_audio_recording()` (6557)
- Stop → transcription → insertion texte

---

## ✨ MAGIC PHRASES SYSTEM

### Architecture

**Détection en 2 Phases** :

1. **Phrases Utilisateur** : Dans `_send_chat_message()` ligne 4981
2. **Phrases IA** : Dans `_message()` ligne 1559 (quand `role == 'assistant'`)

### Protection Historique
**Module** : `magic_phrase_guard.py`

**API** :
```python
should_process_magic_phrase(message_data, extension_name) → bool
```

**Critères de blocage** :
- Flag `from_history` dans metadata
- Mode loading actif (chargement conversation)

### Caviarder (Strip)
**Fonction** : `_strip_magic_phrases()` ligne ~5500

**Patterns supprimés de l'affichage** :
- "il faut que je me souvienne de ça: [texte]"
- "mémorise ça: [texte]"
- "il faut que je te vois"
- "je veux te voir"
- "je n'ai plus besoin de te voir"
- "je ferme ma vision"
- "je coupe ma caméra"

### Extraction Mémorisation
**Fonction** : `_extract_magic_memories()` ligne ~5450

**Patterns extraits** :
```python
patterns = [
    r"il\s*faut\s*que\s*je\s*me\s*souvienne\s*de\s*(?:ça|ca)\s*[:\-]\s*(.+)",
    r"m[ée]morise(?:s)?\s*(?:ça|ca)\s*[:\-]\s*(.+)"
]
```

### Liste Complète Phrases Magiques

| Phrase | Type | Extension | Ligne Détection |
|--------|------|-----------|-----------------|
| "il faut que je me souvienne de ça: [texte]" | USER | Memory | 5724 |
| "mémorise ça: [texte]" | USER | Memory | 5724 |
| "il faut que je réfléchisse" | IA | Cognitive Mirror | 1620 |
| "il faut que tu réfléchisses" | USER | Cognitive Mirror | 5045 |
| "il faut que je te vois" | IA | Perception | 1708 |
| "je veux te voir" | IA | Perception | 1708 |
| "je n'ai plus besoin de te voir" | IA | Perception | 1740 |
| "je ferme ma vision" | IA | Perception | 1740 |
| "il faut que je consulte la biographie de [prénom]" | IA | Biography | 1580 |
| "consulte le journal du [date]" | USER | Journal | Handler spécifique |
| "il faut que je cherche sur internet [sujet]" | IA | Web Navigator | Handler spécifique |

---

## 🎤 AUDIO SYSTEM

### Managers
**Wrapper** : `audio_manager_wrapper.py`  
**Core** : `audio_manager.py`

### STT (Speech-to-Text)

**Engines Supportés** :
- OpenAI Whisper (API)
- Vosk (local)
- Azure Speech

**Workflow** :
1. Utilisateur clique micro
2. `_start_audio_recording()` (ligne 6557)
3. Recording démarre (AudioManager)
4. Utilisateur clique stop
5. Transcription → insertion textarea
6. Message envoyé normalement

### TTS (Text-to-Speech)

**Engines Supportés** :
- ElevenLabs (API)
- Azure Speech (API)
- gTTS (Google Text-to-Speech)
- pyttsx3 (local)

**Auto-speak** : Configuration dans settings
- Lecture automatique réponses IA
- Voice ID configurable par engine

---

## 🪟 MODALS & DIALOGS

### Settings Modal
**Fonction** : `_models_modal()` (ligne 3646)

**Sections** :
- Chat API (IA principale)
- Reasoning API (Archiviste)
- Embedding API (FAISS)
- Audio (STT/TTS)
- Extensions (Cognitive Mirror, etc.)

**Fonctions Support** :
- `_list_models()` (4345) : Liste modèles provider
- `_test_connection()` (4370) : Test connexion API
- `_check_global_ia_status()` (4395) : Status tous providers
- `_refresh_models_ui()` (4557) : Update UI après changement

### Profile Modal
**Fonction** : `_profile_modal()` (ligne 4143)

**Gestion** :
- Profils multiples (user_name, ai_name, relationship)
- Switch profil actif
- Creation/edition/suppression profils
- Sauvegarde dans settings.json

### Image Generation Modal
**Fonction** : `_image_modal()` (ligne 3650)

**Extensions Support** :
- Text2Img extension
- Configuration provider images (Stability, DALL-E, etc.)

### Conversation Summary Edit
**Fonction** : `_edit_summary_popup()` (ligne 3631)

**UI** : `_create_edit_interface()` (3566)
- Edit titre conversation
- Edit résumé mémorisation
- Update mémoire FAISS

---

## 🌐 ROUTES & PAGES

### Routing NiceGUI

```python
@ui.page('/')
def main_page():
    # Page principale chat

@ui.page('/perception')
def perception_page():
    # Page dédiée Perception (popup)
```

### Main Page
**Fonction** : `main_page()` (ligne 7270)

**Initialisation** :
1. CSS injection (dark theme custom)
2. `_sidebar()` - Liste conversations
3. `_header()` - Barre supérieure
4. Chat container (`_chat_inner`)
5. `_input_overlay()` - Zone saisie
6. Render historique : `_render_full_history()`

### Perception Page
**Fonction** : `perception_page()` (ligne 6671)

**Mode** : Popup window 440×440px

**Composants** :
- Stream vidéo webcam (canvas)
- Contrôles FPS (slider 5-30)
- Résolution (select 640x480, 720p, 1080p)
- Bouton capture manuelle
- Chronophotographie (2-20 images, 14 layouts)
- Bouton fermer (retour OGMA)

**Storage** : Position/taille popup sauvegardée localStorage

---

## 🛠️ UTILITAIRES

### Formatage & Parsing

| Fonction | Ligne | Description |
|----------|-------|-------------|
| `format_size()` | 82 | Octets → KB/MB/GB |
| `_format_datetime()` | 2821 | ISO → format lisible |
| `_parse_thinking_format()` | 2835 | Extrait <thinking> |
| `_parse_introspection_format()` | 2917 | Extrait <subconscience> |
| `_truncate_filename()` | 1071 | Limite longueur nom fichier |
| `_get_file_icon()` | 1077 | Icône selon extension |

### Backend Mapping

| Fonction | Ligne | Description |
|----------|-------|-------------|
| `_map_backend_for_controller()` | 310 | Uniformise noms backends |
| `_ensure_backends()` | 268 | Init API/Ollama/GGUF/Kobold |

### Helpers Conversation

| Fonction | Ligne | Description |
|----------|-------|-------------|
| `_make_conv_id()` | 2177 | ID timestamp unique |
| `_make_title_from_text()` | 2188 | Titre basique 15 mots |
| `_generate_smart_title_from_history()` | 2203 | Titre IA intelligent |

### Notification Safe
**Fonction** : `_notify_safe()` (ligne 1057)

Wrapper `ui.notify()` avec protection crash client déconnecté.

---

## 🔗 POINTS D'INJECTION (HOOKS)

### 1. Prompt Système (System Prompt)

**Emplacement** : `_send_chat_message()` ligne ~5900

**Injections** :
1. **Instructions de base** (settings.json → prompts.instructions)
2. **Ego Prompt** (data/ego_prompt.txt ou ego_prompt_synthesized.json)
3. **Temporal Guardian** (contexte temporel + horodatage)
4. **Journal Context** (entrées du jour si extension active)
5. **Souvenirs FAISS** (top 3-5 + souvenirs fondateurs)
6. **Perception** (image base64 si capture active)

**Déduplication** : Module `injection_deduplicator.py` évite doublons

### 2. Fonction `_message()` (Rendu Messages)

**Emplacement** : Ligne 1559

**Hooks Extensions** :
1. **Biography** (1580-1608) : Détection "consulte biographie [prénom]"
2. **Cognitive Mirror** (1610-1706) : Détection "il faut que je réfléchisse"
3. **Perception** (1708-1777) : Détection "il faut que je te vois"

**Pattern Async** :
```python
async def trigger_action():
    await asyncio.sleep(0.3)  # Délai affichage message
    # Action (activation extension, etc.)

asyncio.create_task(trigger_action())
```

### 3. Header Buttons (Injection Boutons)

**Journal** :
- `_inject_journal_header_button()` (1295)
- `_create_header_journal_button_inline()` (1402)

**Biography** :
- `_create_header_biography_button_inline()` (1441)

### 4. Sidebar Info Overlay

**Fonction** : `_show_magic_phrases_info()` (dans `_sidebar()` ligne ~2960)

**Sections** :
- 📖 Journal de Bord (phrases + descriptions)
- 👤 Biographie Profil
- 🧠 Miroir Cognitif
- 💾 Mémorisation
- 📚 Conversations Archivées
- 🌐 Recherche Internet
- 👁️ Perception Visuelle (IA)

**Ajout Extension** :
```python
# Dans _sidebar() après section Web Navigator
ui.separator()
ui.label('🔧 Nouvelle Extension')
new_extension_phrases = [...]
for phrase, desc in new_extension_phrases:
    # Rendu UI phrase + description
```

### 5. Callbacks Cognitive Mirror

**Synthesis Ready** : `_on_synthesis_ready()` (724)
- Appelé quand introspection termine
- Affiche synthèse dans chat

**Message Callback** : `_on_introspection_message_callback()` (739)
- Stream messages Luna↔Archiviste
- Update widget markdown temps réel

**Message Ready** : `_on_message_ready()` (771)
- Callback générique messages streaming

---

## 📊 MÉTRIQUES FICHIER

| Métrique | Valeur |
|----------|--------|
| **Lignes totales** | 7724 |
| **Fonctions** | ~120 |
| **Classes** | 1 (_Dummy) |
| **Imports** | 45+ modules |
| **Extensions intégrées** | 6 (Cognitive Mirror, Perception, Journal, Bio, Temporal, Web) |
| **Managers** | 8 (Settings, Memory, Audio, API, Ollama, GGUF, Kobold, Embedding) |
| **UI Components** | 15+ (Header, Sidebar, Input, Modals, etc.) |
| **Magic Phrases** | 11+ patterns |

---

## 🎯 ZONES CRITIQUES REFACTORING

### 1. `_send_chat_message()` (Ligne 4981-6557)
**Taille** : ~1576 lignes ❌  
**Responsabilités** : TROP (20+)

**À Extraire** :
- [ ] Détection phrases magiques utilisateur
- [ ] Injection prompt système
- [ ] Mémorisation automatique
- [ ] Perception capture
- [ ] Gestion streaming
- [ ] Callbacks audio
- [ ] Error handling

**Suggestion** : Créer `message_handler.py` avec classes dédiées

### 2. `_message()` (Ligne 1559-2113)
**Taille** : ~554 lignes ❌  
**Responsabilités** : Rendu + Hooks extensions

**À Extraire** :
- [ ] Hooks extensions (Biography, Cognitive, Perception)
- [ ] Parsing thinking/introspection
- [ ] Edit mode
- [ ] Badges system

**Suggestion** : Créer `message_renderer.py` + `extension_hooks.py`

### 3. `_sidebar()` (Ligne 2957-3384)
**Taille** : ~427 lignes ❌  
**Responsabilités** : UI + Logic conversations

**À Extraire** :
- [ ] Overlay phrases magiques (déjà extraction possible → `magic_phrases_overlay.py`)
- [ ] Conversation list rendering
- [ ] Context menu actions

**Suggestion** : Créer `sidebar_components.py`

### 4. Modals (Lignes 3646-4345)
**Taille** : ~699 lignes  
**Suggestion** : Créer `ogma_modals_refactored.py` (fichier déjà existe mais incomplet)

### 5. Backend Functions (Lignes 4345-4699)
**Taille** : ~354 lignes  
**Suggestion** : Créer `backend_communication.py`

---

## 🗂️ STRUCTURE PROPOSÉE POST-REFACTORING

```
ogma_ng_refactored.py (< 2000 lignes)
├── Imports & Config (100)
├── Global State Management (200)
├── Routing & Pages (300)
└── Main Run Function (50)

modules/
├── managers/
│   ├── lazy_initializers.py       # Tous les _ensure_*()
│   ├── memory_integration.py      # Injection souvenirs
│   └── backend_manager.py         # Communication APIs
├── ui/
│   ├── header.py                  # _header() + boutons
│   ├── sidebar.py                 # _sidebar() + conversations
│   ├── message_renderer.py        # _message() rendering
│   ├── input_overlay.py           # Zone saisie
│   └── modals.py                  # Settings, Profile, Image
├── conversation/
│   ├── persistence.py             # Save/Load conversations
│   ├── title_generation.py       # Smart titles
│   └── summarization.py          # Résumés + mémorisation
├── message/
│   ├── handler.py                 # _send_chat_message() logique
│   ├── streaming.py               # Gestion streams IA
│   ├── magic_phrases.py           # Détection + extraction
│   └── injection.py               # Prompt system injection
├── extension_hooks/
│   ├── cognitive_mirror_hooks.py  # Hooks introspection
│   ├── perception_hooks.py        # Hooks vision
│   ├── biography_hooks.py         # Hooks profils
│   └── journal_hooks.py           # Hooks journal
└── utils/
    ├── formatters.py              # Format size, dates, etc.
    ├── parsers.py                 # Thinking, introspection
    └── notifications.py           # _notify_safe()
```

---

## 📌 POINTS D'ATTENTION REFACTORING

### 1. Variables Globales
**Problème** : 40+ variables globales interdépendantes

**Solutions** :
- [ ] Créer classe `OgmaState` singleton
- [ ] Encapsuler état dans dataclasses
- [ ] Utiliser context managers

### 2. Couplage Extensions
**Problème** : Extensions importées directement dans ogma_ng.py

**Solutions** :
- [ ] Système de registry extensions
- [ ] Découverte dynamique (scan dossier extensions/)
- [ ] Interface commune Extension Protocol

### 3. UI State Management
**Problème** : État UI dispersé (widgets globaux)

**Solutions** :
- [ ] Classe UIComponents centralisée
- [ ] Reactive state management
- [ ] Separation of concerns (UI vs Logic)

### 4. Async/Await Patterns
**Problème** : Mélange sync/async functions

**Solutions** :
- [ ] Standardiser toutes les I/O en async
- [ ] Créer wrappers sync pour callbacks NiceGUI
- [ ] Documenter async boundaries

### 5. Error Handling
**Problème** : Try/except dispersés, pas de logging structuré

**Solutions** :
- [ ] Logger centralisé (module `logging`)
- [ ] Exception hierarchy custom
- [ ] Error recovery strategies documentées

---

## 📚 DÉPENDANCES EXTERNES

### Packages Python Critiques
```
nicegui                 # Framework UI
openai                  # API OpenAI/compatible
anthropic               # API Anthropic Claude
mistralai               # API Mistral
google-generativeai     # API Gemini
faiss-cpu               # Index vectoriel
sqlite3                 # Base données (stdlib)
opencv-python           # Webcam Perception
numpy                   # Arrays (OpenCV)
pillow                  # Images
```

### Fichiers Configuration
```
data/settings.json               # Config principale
data/ego_prompt.txt              # Prompt identité IA
data/ego_prompt_synthesized.json # Ego structuré
data/conversations/index.json    # Index conversations
data/memory/memory.db            # SQLite mémoire
data/memory/memory.faiss         # Index FAISS
data/instructions_defaults.json  # Defaults système
```

---

## 🔍 INDEX RAPIDE FONCTIONS

**Navigation rapide par catégorie :**

### Initialisation
- `_ensure_settings_manager()` → 239
- `_ensure_memory_manager()` → 322
- `_ensure_chat_controller()` → 931
- `_ensure_archiviste_controller()` → 1025
- `_ensure_cognitive_mirror()` → 840
- `_ensure_temporal_guardian()` → 480

### Conversation
- `_load_conversation()` → 2712
- `_save_conversation()` → 2541 (_persist_conversation)
- `_new_conversation()` → 2788
- `_generate_smart_title()` → 2203

### Mémoire
- `_retrieve_liberating_memory()` → 173
- Injection souvenirs → `_send_chat_message()` ~5920
- Mémorisation → `_send_chat_message()` ~5724

### Messages
- `_message()` → 1559 (rendu UI)
- `_send_chat_message()` → 4981 (handler principal)
- `_parse_thinking_format()` → 2835
- `_strip_magic_phrases()` → ~5500

### UI
- `main_page()` → 7270
- `_header()` → 1488
- `_sidebar()` → 2957
- `_input_overlay()` → 6617
- `perception_page()` → 6671

### Extensions
- Biography init → 1207
- Journal init → 1248
- Cognitive hooks → 1610-1706
- Perception hooks → 1708-1777

### Modals
- Settings → 3646
- Profile → 4143
- Image Gen → 3650

---

**FIN DE LA CARTOGRAPHIE**

*Document généré le 25 octobre 2025*  
*Version OGMA : 2.0*  
*Auteur : Système de cartographie automatique*

---

## 🎯 PROCHAINES ÉTAPES REFACTORING

1. ✅ **Cartographie complète** (CE DOCUMENT)
2. ⏳ **Analyse dépendances** (graphe imports)
3. ⏳ **Plan découpage** (modules cibles)
4. ⏳ **Tests unitaires** (coverage critique)
5. ⏳ **Migration progressive** (module par module)
6. ⏳ **Validation fonctionnelle** (non-régression)

**Estimation** : 15-20 heures de refactoring structuré  
**Risque** : Moyen (avec tests + validation continue)  
**Bénéfice** : Maintenabilité ×5, Évolutivité ×10
