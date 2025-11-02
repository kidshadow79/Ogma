# 📊 CARTOGRAPHIE COMPLÈTE OGMA_NG.PY - PLAN DÉCOUPAGE

**Date**: 2 novembre 2025  
**Fichier source**: `ogma_ng.py` (7899 lignes)  
**Objectif**: Diviser en 2-3 fichiers cohérents sans doublons

---

## 🎯 STATISTIQUES GLOBALES

### Taille Actuelle
- **Total**: 7899 lignes
- **Fonctions**: ~100+ fonctions
- **Classes**: 1 (_Dummy)
- **Variables globales**: 30+ variables d'état

### État Actuel Refactoring
- ✅ **Modules créés** (Phase 1 - Nov 2025):
  - `utils/` (328L): formatting, parsers, backend_utils
  - `conversations/` (268L): index, utils, commands
  - `backend/` (297L): communication, ia_status
  - `files/` (167L): file_management
- ✅ **Composants UI externalisés**:
  - `ogma_modals.py`, `ogma_displays.py`, `ogma_config_ui.py`
  - `ogma_tts_config.py`, `ogma_profile.py`, `ogma_headers.py`

---

## 🗺️ CARTOGRAPHIE PAR ZONES FONCTIONNELLES

### **ZONE 1: CORE ORCHESTRATION** (≈2500 lignes)
**Lignes**: 1-700, 4900-6800, 7700-7900

#### Contenu:
- **Imports & Setup** (1-150)
- **Variables globales d'état** (139-180)
  - `_chat_controller`, `_archiviste_controller`, `_embedding_controller`
  - `_memory_manager`, `_settings_mgr`, `_audio_manager`
  - `_chat_history`, `_chat_history_ui`, `_current_conversation_id`
  - `_conv_area`, `_chat_inner`, `_input_field`
  - Extensions: `_temporal_guardian`, `_cognitive_mirror`, etc.

- **Lazy Initializers (`_ensure_*`)** (245-470)
  - `_ensure_settings_manager()`
  - `_ensure_audio_manager()`
  - `_ensure_backends()`
  - `_ensure_memory_manager()` (CRITIQUE - 150 lignes)
  - `_ensure_temporal_guardian()`
  - `_ensure_contextual_recall()`
  - `_ensure_file_writer()`

- **Controllers IA** (985-1110)
  - `_ensure_chat_controller()` (95L)
  - `_ensure_archiviste_controller()` (30L)

- **Fonction CRITIQUE: `_send_chat_message()`** (4900-6800)
  - **1900 LIGNES** - Orchestrateur principal
  - Gère: validation, édition, phrases magiques, mémoire, perception, API calls

- **Entry Points** (7700-7900)
  - `run_ogma()` - Démarrage application
  - `main_page()` - Page principale
  - Aliases fonctions déplacées

#### Dépendances:
- **Fortes**: Variables globales, NiceGUI UI, extensions
- **Lecture**: Tous les modules
- **Écriture**: État global (history, controllers, UI refs)

---

### **ZONE 2: UI & DISPLAY** (≈2200 lignes)
**Lignes**: 1600-2900, 3800-4900

#### Contenu:
- **Message Display** (1600-2150)
  - `_message()` (550L) - Affichage messages avec parsing, badges, édition
  - Parsing thinking/introspection (via `utils.message_parsers`)

- **Edit System** (2155-2190)
  - `load_message_for_edit()`
  - Variable `_editing_message_index`

- **Conversations Management** (2190-2900)
  - `_load_conversation_index()`, `_save_conversation_index()`
  - `_make_conv_id()`, `_make_title_from_text()`
  - `_generate_smart_title_from_history()` (async AI call)
  - `_schedule_smart_title_generation()`
  - `_persist_conversation()` (160L)
  - `_render_full_history()`, `_load_conversation()`, `_new_conversation()`
  - **`_sidebar()`** (630L) - Sidebar complète avec actions

- **Memory Management UI** (3500-3650)
  - `_mark_conversation_memorized()`, `_is_conversation_memorized()`
  - `_delete_memorized_conversation()`
  - `_create_edit_interface()`, `_edit_summary_popup()`

- **Modals UI** (3650-4900)
  - `_status_dot()`, `_models_modal()`
  - `_image_modal()` (160L - text2img configuration)
  - `_profile_modal()` (4144-4558, 415L) - **DÉJÀ EXTERNALISÉ**
  - `_refresh_models_ui()`, `_test_connection_ui()`, `_init_models_ui()`

#### Dépendances:
- **Fortes**: `ui` (NiceGUI), variables globales UI (`_chat_inner`, etc.)
- **Moyennes**: `_settings_mgr`, controllers IA (pour modals)
- **Faibles**: Modules utils, conversations, backend

---

### **ZONE 3: EXTENSIONS & INTEGRATIONS** (≈1500 lignes)
**Lignes**: 700-985, 1240-1530, 6839-7438

#### Contenu:
- **Subconscience Processing** (620-894)
  - `_process_subconscience_messages()` (160L)
  - `_on_synthesis_ready()` (120L)
  - Cognitive Mirror integration

- **Cognitive Mirror** (894-985)
  - `_ensure_cognitive_mirror()` (90L)
  - Callback handling

- **Biography Extension** (1240-1530)
  - `_initialize_biography_extension()` (40L)
  - `_inject_journal_header_button()`
  - Header button creators (inline)

- **Journal Extension** (1290-1530)
  - `_initialize_journal_extension()` (50L)
  - `_inject_journal_context()`
  - Header buttons creation

- **Perception Page** (6839-7438)
  - `perception_page()` (600L) - **PAGE COMPLÈTE SÉPARÉE**
  - Webcam, chronophotographie, settings

#### Dépendances:
- **Fortes**: Extensions externes, variables globales
- **Moyennes**: `_chat_history`, `_cognitive_mirror`
- **Faibles**: UI updates

---

### **ZONE 4: UTILITIES & HELPERS** (≈1700 lignes)
**Lignes**: 200-245, 1111-1240, 2300-2583, 3000-3200, 4865-4900, 6721-6826

#### Contenu:
- **Helpers Locaux** (200-245)
  - `_trigger_memory_update()`, `get_web_navigator_instance()`
  - `_get_current_time()`, `close_memory_manager()`

- **Notification & File Management** (1111-1240)
  - `_notify_safe()` (10L)
  - Constants: `REMOTE_PROVIDERS`, `LOCAL_BACKENDS`
  - File upload: `_update_header_display()`, `_show_file_upload_dialog()`
  - **DÉJÀ EXTRAITS** dans `files/file_management.py`

- **Smart Titling** (2300-2583)
  - Async title generation workflows
  - Conversation summarization hooks

- **Magic Phrases Documentation** (3000-3200)
  - Modal avec toutes les phrases magiques (Journal, Biography, Web, etc.)

- **Archive Display** (4865-4900)
  - `_display_archived_conversation()`, `_display_search_results()`

- **Audio System** (6721-6826)
  - `_start_audio_recording()` (120L)
  - `_input_overlay()` (100L)
  - `_process_pending_notifications()`

#### Dépendances:
- **Variables**: Spécifiques à chaque helper
- **Indépendance**: Plupart peuvent être externalisés

---

## 🔪 PLAN DE DÉCOUPAGE PROPOSÉ

### **SCÉNARIO A: DÉCOUPAGE EN 2 FICHIERS** (Recommandé ⭐)

#### **Fichier 1: `ogma_ng.py` (CORE - 3500L)**
**Responsabilité**: Orchestration principale + État global + Entry points

**Contenu**:
- Imports & Setup
- **TOUTES variables globales d'état** (30+ vars)
- Lazy initializers `_ensure_*()` (indissociables de l'état)
- Controllers IA (`_ensure_chat_controller`, `_ensure_archiviste_controller`)
- **`_send_chat_message()`** (1900L - CŒUR APPLICATIF)
- `run_ogma()`, `main_page()`, `perception_page()`
- Aliases fonctions déplacées (compatibilité)

**Justification**:
- ✅ Garde le **cœur critique** ensemble
- ✅ État global **centralisé** (évite imports circulaires)
- ✅ `_send_chat_message()` trop couplé pour extraction
- ✅ Entry points restent dans fichier principal

**Dépendances sortantes**:
```python
from ogma_ui_conversations import (
    _sidebar, _load_conversation, _new_conversation,
    _persist_conversation, _render_full_history
)
from utils.* (déjà fait)
from conversations.* (déjà fait)
from backend.* (déjà fait)
```

---

#### **Fichier 2: `ogma_ui_conversations.py` (UI - 2500L)**
**Responsabilité**: UI Conversations + Sidebar + Message Display

**Contenu**:
- **Message Display** (550L)
  - `_message()` avec parsing, badges, édition
- **Edit System** (35L)
  - `load_message_for_edit()`, `_editing_message_index`
- **Conversations Management** (1000L)
  - Index management, titling, persistence
  - `_sidebar()` (630L)
  - Load/save conversations
- **Memory UI** (150L)
  - Memorization popups, edit interfaces
- **Modals** (765L)
  - Models, Image generation, Settings

**Justification**:
- ✅ Cohésion fonctionnelle forte (tout UI conversations)
- ✅ Peut importer `ogma_ng` pour accès état global
- ✅ ~2500L réduction significative
- ✅ Pas de dépendances circulaires critiques

**Dépendances entrantes**:
```python
# Imports depuis ogma_ng.py
from ogma_ng import (
    _chat_history, _chat_history_ui, _chat_inner,
    _current_conversation_id, _conv_index,
    _ensure_settings_manager, _ensure_chat_controller,
    _ensure_archiviste_controller, _notify_safe
)
```

---

### **Tailles Finales Scénario A**:
- **`ogma_ng.py`**: ~3500L (-55% depuis 7899L) ✅
- **`ogma_ui_conversations.py`**: ~2500L (nouveau)
- **Modules existants**: ~1900L (utils, conversations, backend, files, modals, etc.)
- **Total projet**: ~7900L (identique, mais mieux organisé)

---

### **SCÉNARIO B: DÉCOUPAGE EN 3 FICHIERS** (Plus complexe ⚠️)

#### **Fichier 1: `ogma_ng.py` (CORE - 3000L)**
Identique Scénario A MAIS sans `perception_page()`

#### **Fichier 2: `ogma_ui_conversations.py` (UI - 2500L)**
Identique Scénario A

#### **Fichier 3: `ogma_perception.py` (PERCEPTION - 600L)**
**Responsabilité**: Page Perception + Audio

**Contenu**:
- `perception_page()` (600L)
- Audio system (`_start_audio_recording`, `_input_overlay`)

**Justification**:
- ✅ Page perception **totalement indépendante**
- ⚠️ Mais seulement 600L (~8% du total)
- ⚠️ Ajoute complexité import (3 fichiers au lieu de 2)

**Dépendances**:
```python
from ogma_ng import _ensure_audio_manager, _ensure_settings_manager
```

---

### **Tailles Finales Scénario B**:
- **`ogma_ng.py`**: ~3000L
- **`ogma_ui_conversations.py`**: ~2500L
- **`ogma_perception.py`**: ~600L
- **Modules existants**: ~1900L
- **Total**: ~8000L (légère augmentation imports)

---

## ⚖️ COMPARAISON SCÉNARIOS

| Critère | Scénario A (2 fichiers) | Scénario B (3 fichiers) |
|---------|-------------------------|-------------------------|
| **Réduction ogma_ng** | 55% (-4400L) | 62% (-4900L) |
| **Complexité imports** | 🟢 FAIBLE | 🟡 MOYENNE |
| **Risque circulaire** | 🟢 FAIBLE | 🟡 MOYEN |
| **Cohésion modules** | 🟢 FORTE | 🟡 MOYENNE |
| **Taille fichiers** | 🟢 Équilibrés | 🟡 Déséquilibrés |
| **Effort implémentation** | 🟢 1-2h | 🟡 2-3h |
| **Tests nécessaires** | 🟢 Modérés | 🟡 Étendus |

---

## 🎯 RECOMMANDATION FINALE

### **SCÉNARIO A (2 FICHIERS)** ⭐ RECOMMANDÉ

**Pourquoi ?**
1. ✅ **55% réduction** ogma_ng.py (7899L → 3500L)
2. ✅ **Découpage cohérent** : Core vs UI Conversations
3. ✅ **Risque minimal** : Pas d'imports circulaires
4. ✅ **Complexité maîtrisée** : Seulement 2 fichiers principaux
5. ✅ **Effort raisonnable** : 1-2h implémentation
6. ✅ **Tailles équilibrées** : 3500L vs 2500L

**Perception** :
- Garde `perception_page()` dans `ogma_ng.py`
- C'est une **page séparée** (600L) mais entry point principal
- Évite fragmentation excessive

---

## 📋 PLAN D'IMPLÉMENTATION (Scénario A)

### **Phase 1: Créer `ogma_ui_conversations.py`** (30 min)

1. Créer fichier avec imports :
```python
from typing import Optional, Dict, List, Tuple
from nicegui import ui
import asyncio
from pathlib import Path

# Imports depuis ogma_ng (état global)
from ogma_ng import (
    _chat_history, _chat_history_ui, _chat_inner, _chat_inner,
    _current_conversation_id, _conv_index, _editing_message_index,
    _ensure_settings_manager, _ensure_chat_controller,
    _ensure_archiviste_controller, _ensure_memory_manager,
    _notify_safe, DATA_DIR
)

# Imports depuis modules utils
from utils.message_parsers import parse_thinking_format, parse_introspection_format
from utils.formatting_utils import format_datetime
from conversations import load_conversation_index, save_conversation_index
```

2. Copier fonctions :
   - `_message()` (1600-2150)
   - `load_message_for_edit()` (2155-2190)
   - Conversations management (2190-2900)
   - Memory UI (3500-3650)
   - Modals (3650-4900)

### **Phase 2: Modifier `ogma_ng.py`** (30 min)

1. Ajouter import :
```python
# Import UI Conversations (après création)
from ogma_ui_conversations import (
    _message, load_message_for_edit,
    _sidebar, _load_conversation, _new_conversation,
    _persist_conversation, _render_full_history,
    _models_modal, _image_modal,
    # ... toutes fonctions UI
)
```

2. **SUPPRIMER** fonctions déplacées (lignes 1600-4900)

3. Garder variables globales d'état (nécessaires pour injection)

### **Phase 3: Résoudre dépendances** (30 min)

1. **Variables globales partagées** :
   - Exporter depuis `ogma_ng.py` :
   ```python
   __all__ = [
       '_chat_history', '_chat_history_ui', '_chat_inner',
       '_current_conversation_id', '_conv_index',
       '_editing_message_index', '_ensure_*', '_notify_safe'
   ]
   ```

2. **Imports circulaires** :
   - `ogma_ui_conversations.py` importe depuis `ogma_ng`
   - `ogma_ng.py` importe depuis `ogma_ui_conversations`
   - ✅ **SAFE** car `ogma_ng` est exécuté en premier (entry point)

3. **Tester** après chaque étape

### **Phase 4: Tests & Validation** (30 min)

1. Test import :
```bash
python -c "import ogma_ng; import ogma_ui_conversations; print('✅ Imports OK')"
```

2. Test fonctionnel :
```bash
python ogma_ng.py
```

3. Vérifier :
   - ✅ Conversations chargent
   - ✅ Messages s'affichent
   - ✅ Sidebar fonctionne
   - ✅ Modals s'ouvrent

---

## 🚨 RISQUES & MITIGATIONS

### **Risque 1: Imports Circulaires**
**Probabilité**: 🟡 MOYENNE  
**Impact**: 🔴 ÉLEVÉ  
**Mitigation**:
- ✅ `ogma_ng.py` est entry point (exécuté en premier)
- ✅ Imports conditionnels si nécessaire
- ✅ Test import avant exécution

### **Risque 2: Variables Globales**
**Probabilité**: 🟢 FAIBLE  
**Impact**: 🟡 MOYEN  
**Mitigation**:
- ✅ Exporter via `__all__`
- ✅ Documenter variables partagées
- ✅ Pas de modification état dans `ogma_ui_conversations`

### **Risque 3: Régression Fonctionnelle**
**Probabilité**: 🟡 MOYENNE  
**Impact**: 🔴 ÉLEVÉ  
**Mitigation**:
- ✅ Tests systématiques après chaque étape
- ✅ Commit Git avant découpage
- ✅ Rollback facile si problème

---

## ✅ VALIDATION FINALE

### **Critères de Succès**:
1. ✅ `ogma_ng.py` réduit à ~3500L (vs 7899L initial)
2. ✅ **ZÉRO doublon** (code supprimé de ogma_ng)
3. ✅ **ZÉRO ligne superflue** ajoutée
4. ✅ Application fonctionnelle (0 régression)
5. ✅ Imports propres (pas de circulaires)

### **Métriques Attendues**:
| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| ogma_ng.py | 7899L | 3500L | **-55%** |
| Total fichiers | ~8000L | ~8000L | 0% (réorganisation) |
| Modules | 8 fichiers | 10 fichiers | +2 |
| Cohésion | 🟡 FAIBLE | 🟢 FORTE | ✅ |

---

## 🎯 PROCHAINE ÉTAPE

**Attendu**: Feu vert Architecte pour **Scénario A (2 fichiers)**

Si validé, je procède immédiatement à l'implémentation en 4 phases (2h total).

**Alternative**: Si vous préférez **Scénario B (3 fichiers)**, je peux adapter le plan.

---

**Document créé**: 2 novembre 2025  
**Version**: 1.0  
**Statut**: ⏳ EN ATTENTE VALIDATION ARCHITECTE
