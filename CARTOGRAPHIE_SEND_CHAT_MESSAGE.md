# 📊 CARTOGRAPHIE COMPLÈTE - `_send_chat_message()`

**Date de cartographie**: 1 novembre 2025  
**Fichier cible**: `ogma_ng.py`  
**Fonction**: `async def _send_chat_message()`

---

## 🎯 STATISTIQUES GLOBALES

| Métrique | Valeur |
|----------|--------|
| **Ligne début** | 5125 |
| **Ligne fin** | 6866 |
| **Taille TOTALE** | **1742 lignes** |
| **Pourcentage fichier** | 21,7% (8042 lignes totales) |
| **Prochaine fonction** | Ligne 6867 |
| **Variables globales** | 7 (_chat_history, _chat_history_ui, _chat_inner, _pending_notifications, _editing_message_index, _pending_behavioral_injections, _journal_preformed_response) |
| **Complexité** | Séquentielle (découpage facilitera) |

---

## 📖 STRUCTURE DÉTAILLÉE PAR BLOCS FONCTIONNELS

### **BLOC 1 - INITIALISATION ET VALIDATION** 
**Lignes 5125-5142 (17 lignes)** - ✅ Extractible facilement

**Responsabilités:**
- Signature fonction (3 paramètres: `input_el`, `text_override`, `skip_history_append`)
- Déclarations globales (7 variables)
- Réinitialisation déduplication session
- Récupération input (text_override OU input_el.value)

**Fonction cible**: `_send_validate_input(input_el, text_override) -> tuple[str, bool]`

**Complexité extraction**: 🟢 FACILE

---

### **BLOC 2 - MODE ÉDITION**
**Lignes 5147-5171 (24 lignes)** - ✅ Extractible facilement

**Responsabilités:**
- Vérification `_editing_message_index is not None`
- Suppression messages après index édité (`_chat_history[:index]`)
- Flag `was_editing = True`
- Reset `_editing_message_index = None`

**Fonction cible**: `_send_handle_edit_mode() -> bool`

**Complexité extraction**: 🟢 FACILE

---

### **BLOC 3 - PHRASES MAGIQUES EXTENSIONS**
**Lignes 5173-5598 (425 lignes)** - ⚠️ MONSTRE à découper en 5 sous-fonctions

#### **3.1 Introspection automatique (Lignes 5173-5201)**
**28 lignes** - Mode "always" cognitive mirror
```python
if COGNITIVE_MIRROR_AVAILABLE and is_enabled():
    mode = introspection_core.config.get('introspection_mode', 'on_demand')
    if mode == 'always':
        is_automatic_introspection = True
```

**Fonction cible**: `_send_check_introspection_auto() -> bool`

---

#### **3.2 Journal de Bord (Lignes 5207-5247)**
**40 lignes** - Détection phrases magiques journal
```python
if _journal_available:
    magic_response = await journal.entry_generator.handle_magic_phrases(text, journal.json_manager)
    if magic_response:
        # Injection réponse prédéfinie
        _journal_preformed_response = magic_response
```

**Fonction cible**: `async _send_check_journal_magic(text: str) -> Optional[str]`

---

#### **3.3 Biographie Profil (Lignes 5249-5325)**
**76 lignes** - Détection + injection automatique
```python
if _biography_available:
    magic_response = await biography_magic.handle_magic_phrases(text, is_ai_message=False)
    if magic_response:
        if response_type == 'display':
            # Afficher et retourner
        elif response_type == 'inject':
            # Stocker pour injection contexte IA
```

**Fonction cible**: `async _send_check_biography_magic(text: str) -> Optional[dict]`

---

#### **3.4 Cognitive Mirror v2.0 (Lignes 5328-5589)**
**261 lignes** - Déclenchement introspection complète
```python
if COGNITIVE_MIRROR_AVAILABLE and is_enabled():
    # Patterns phrases magiques
    is_introspection_trigger = is_magic_phrase_trigger or is_automatic_introspection
    if is_introspection_trigger:
        # 1. Ajouter message utilisateur
        # 2. Afficher message système
        # 3. Construire contexte enrichi
        # 4. Créer boîte thinking
        # 5. Lancer introspection v2.0
        # 6. Afficher réponse finale
        # 7. RETURN (bloquer flux normal)
```

**Fonction cible**: `async _send_handle_introspection_trigger(text: str, is_auto: bool) -> bool`

**Complexité extraction**: 🔴 TRÈS DIFFICILE (261 lignes, logique complexe)

---

#### **3.5 Arrêt réflexion (Lignes 5445-5465)**
**20 lignes** - Stop introspection
```python
stop_introspection_patterns = [r"arrête\s+de\s+réfléchir", ...]
if is_stop_trigger:
    success = cognitive_mirror.stop_reflection_session("user_stop_request")
    _message('system', "🛑 Réflexion interrompue")
    return
```

**Fonction cible**: `async _send_handle_stop_introspection(text: str) -> bool`

---

### **BLOC 4 - MÉMOIRE ET PERCEPTION**
**Lignes 5469-5698 (229 lignes)** - ✅ Extractible en 3 fonctions

#### **4.1 Lecture souvenir par ID (Lignes 5469-5567)**
**98 lignes** - Pattern `usr-xxx`
```python
memory_id_patterns = [r"lis\s+(?:le\s+|ce\s+)?souvenir\s+(usr-[a-f0-9\-]+)", ...]
for pattern in memory_id_patterns:
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        memory_data = _memory_manager.get_memory_by_id(memory_id)
        # Formater et afficher
        return
```

**Fonction cible**: `async _send_handle_memory_id_read(text: str) -> bool`

---

#### **4.2 Perception capture (Lignes 5570-5589)**
**19 lignes** - Capture automatique webcam
```python
if perception_ui.is_enabled and perception_ui.perception_agent:
    perception_image_data = perception_ui.capture_for_chat()
```

**Fonction cible**: `_send_capture_perception() -> Optional[dict]`

---

#### **4.3 Conversations archivées (Lignes 5598-5606)**
**8 lignes** - Commandes consultation
```python
conversation_command_result = await _handle_conversation_commands(text)
if conversation_command_result:
    if input_el and not text_override:
        input_el.value = ''
    return
```

**Fonction cible**: `async _send_handle_conversation_commands(text: str) -> bool`

---

#### **4.4 Cognitive Mirror hook (Lignes 5608-5698)**
**90 lignes** - Diagnostics pré-traitement
```python
cognitive_mirror = _ensure_cognitive_mirror()
# DIAGNOSTIC COMPLET
if cognitive_mirror:
    print(f"Extension activée: {cognitive_mirror.is_enabled}")
    # v2.0: Plus de détection d'inactivité automatique
```

**Fonction cible**: `_send_cognitive_mirror_hook()` (optionnel - peut rester inline)

---

### **BLOC 5 - CONSTRUCTION MESSAGE UTILISATEUR**
**Lignes 5700-5823 (123 lignes)** - ✅ Extractible

**Responsabilités:**
- Extraction phrases magiques mémorisation (`_extract_magic_memories`)
- Mémorisation utilisateur si patterns détectés
- Nettoyage texte (`_strip_magic_phrases`)
- Intégration fichier actif (`_active_file_data`)
- Construction multimodal (texte + images perception/fichier)
- Injection biographique auto-détection

**Fonction cible**: `async _send_build_user_message(text: str, perception_data, active_file) -> tuple[dict, str, bool]`

**Retour**: `(ai_content, cleaned_text, user_memorized)`

**Complexité extraction**: 🟡 MOYEN (gestion multimodal)

---

### **BLOC 6 - HISTORIQUE ET AFFICHAGE UI**
**Lignes 5824-5903 (79 lignes)** - ✅ Extractible

**Responsabilités:**
- Ajout historique (`_chat_history.append`, `_chat_history_ui.append`)
- Persistance conversation (`_persist_conversation`)
- Affichage UI message utilisateur (`_message`)
- Réaffichage complet si premier message OU mode édition
- Scroll automatique JavaScript
- Vider input field

**Fonction cible**: `async _send_append_history_and_display(text: str, cleaned_text: str, user_memorized: bool, was_editing: bool, input_el)`

**Complexité extraction**: 🟡 MOYEN (logique UI conditionnelle)

---

### **BLOC 7 - CONTEXTE MÉMOIRE (FAISS + SQLite)**
**Lignes 5906-5981 (75 lignes)** - ✅ Extractible

**Responsabilités:**
- Diagnostic FAISS si keywords détectés
- Détection demande textes intégraux
- Appel `retrieve_full_texts_context` OU `retrieve_hybrid_optimized`
- Déduplication archiviste (`check_archiviste_injection`)
- Affichage debug injection si activé

**Fonction cible**: `async _send_retrieve_memory_context(text: str) -> tuple[Optional[str], list]`

**Retour**: `(context_note, detailed_memories)`

**Complexité extraction**: 🟡 MOYEN (logique hybride)

---

### **BLOC 8 - TEMPORAL GUARDIAN + ARCHIVISTE**
**Lignes 5983-6060 (77 lignes)** - ✅ Extractible

**Responsabilités:**
- Initialisation Temporal Guardian
- Process message utilisateur (`process_user_message`)
- Analyse avec Archiviste (`analyze_with_archiviste`)
- Génération instruction temporelle
- Affichage debug si activé

**Fonction cible**: `async _send_process_temporal_context(text: str, context_note: str) -> tuple[Optional[str], Optional[str]]`

**Retour**: `(temporal_final_alert, temporal_context_enriched)`

**Complexité extraction**: 🟡 MOYEN

---

### **BLOC 9 - CONSTRUCTION MESSAGES API (INJECTIONS)**
**Lignes 6062-6438 (376 lignes)** - 🔴 MONSTRE à découper en 12 sous-fonctions

#### **9.1 Instructions base + temporel fusionnées (Lignes 6062-6112)**
**50 lignes**
```python
base_instructions = sm.settings.get('prompts', {}).get('instructions', '')
if temporal_final_alert:
    # PRIORITÉ ABSOLUE: Instruction temporelle en tête
    priority_instructions = f"""╔══════════════════════════════════════╗
║           FAST PRIORITÉ ABSOLUE FAST           ║
╚══════════════════════════════════════╝
{temporal_final_alert}
{base_instructions}"""
messages.append({'role': 'system', 'content': priority_instructions})
register_ego_prompt_injection(priority_instructions)
```

---

#### **9.2 Injection perception (Lignes 6115-6132)**
**17 lignes**
```python
has_image = (perception_image_data is not None or ...)
if has_image:
    perception_instructions = sm.settings.get('prompts', {}).get('perception', '')
    messages.append({'role': 'system', 'content': perception_system_msg})
```

---

#### **9.3 Contexte permanent (Lignes 6135-6144)**
**12 lignes**
```python
persistent_context_file = DATA_DIR / "persistent_context.txt"
if persistent_context_file.exists():
    messages.append({'role': 'system', 'content': persistent_content})
```

---

#### **9.4 Injection comportementale (Lignes 6147-6166)**
**20 lignes** - Metacognitive Sensor
```python
if _pending_behavioral_injections:
    for injection_msg in _pending_behavioral_injections:
        if injection_msg.startswith("MEMORY_VECTOR_ID:"):
            memory_content = await _retrieve_liberating_memory(memory_id)
            messages.append({'role': 'system', 'content': f"[SOUVENIR LIBÉRATEUR] {memory_content}"})
        else:
            messages.append({'role': 'system', 'content': injection_msg})
    _pending_behavioral_injections.clear()
```

---

#### **9.5 Temporal Guardian (Lignes 6169-6229)**
**60 lignes** - DOUBLON (déjà traité BLOC 8)
```python
# DOUBLON: Ce code est identique au BLOC 8
# À SUPPRIMER lors du refactoring
```

---

#### **9.6 Contexte Archiviste (Lignes 6232-6241)**
**10 lignes**
```python
if temporal_context_enriched:
    messages.append({'role': 'system', 'content': temporal_context_enriched})
elif context_note:
    messages.append({'role': 'system', 'content': f"Note de l'Archiviste : {context_note}"})
```

---

#### **9.7 Souvenirs détaillés (Lignes 6244-6292)**
**48 lignes**
```python
if detailed_memories:
    memories_text = "Souvenirs détaillés de l'Archiviste :\n"
    for i, mem in enumerate(detailed_memories, 1):
        if mem.get('send_full_text', False):
            # Texte intégral (bypass censure)
        else:
            # Résumé standard
    messages.append({'role': 'system', 'content': memories_text.strip()})
    register_archiviste_injection(memories_text.strip())
```

---

#### **9.8 Injection biographique (Lignes 6295-6300)**
**5 lignes**
```python
if biography_injection_content:
    messages.append({'role': 'system', 'content': biography_injection_content})
```

---

#### **9.9 Historique conversation (Lignes 6303-6382)**
**79 lignes**
```python
for i, m in enumerate(conversation_messages):
    # Support multimodal (images)
    if is_last_user_message_with_file or is_last_user_message_with_perception:
        message_content = [{"type": "text", "text": display_content}, {"type": "image_url", ...}]
    else:
        # Nettoyage balises <introspection>
        content_cleaned = re.sub(r'<introspection>.*?</introspection>', '', content, flags=re.DOTALL)
    messages.append({'role': m['role'], 'content': content_cleaned})
```

---

#### **9.10 Injection conversation chargée (Lignes 6385-6433)**
**68 lignes**
```python
if _loaded_conversation and not _conversation_context_injected:
    # Construire contexte avec historique complet
    conversation_context = f"""--- CONTEXTE : REPRISE DE CONVERSATION ARCHIVÉE ---
    Date: {conversation_date}
    === HISTORIQUE DE LA CONVERSATION ===
    {history}
    === FIN DE L'HISTORIQUE ==="""
    messages[0]['content'] += conversation_context
    _conversation_context_injected = True
```

---

#### **9.11 Injection journal de bord (Lignes 6436-6475)**
**45 lignes**
```python
if not _conversation_context_injected:
    user_name = get_current_user_name()
    if is_main_user:
        journal_context = _inject_journal_context()
        messages[0]['content'] += journal_addon
```

---

#### **9.12 Contextual recall (Lignes 6478-6508)**
**31 lignes**
```python
recall_ext = _ensure_contextual_recall()
if recall_ext:
    recall_context = recall_ext.process_message(text)
    if recall_context:
        messages[0]['content'] += recall_addon
```

---

#### **9.13 Injection émotionnelle Archi_sensor (Lignes 6511-6535)**
**32 lignes**
```python
emotional_injection = await run_archi_sensor_analysis(history, None, archiviste_ctrl, memory_mgr)
if emotional_injection:
    messages[0]['content'] += emotional_addon
```

---

#### **9.14 Orchestration cognitive (Lignes 6538-6620)**
**83 lignes**
```python
if is_new_session:
    orchestration_prompt = sm.settings.get('prompts', {}).get('salutations')
    # Fallback defaults.json ou hardcodé
    messages[0]['content'] += orchestration_prompt
    _orchestration_injected = True
```

---

**Fonction cible BLOC 9**: `async _send_build_api_messages(...) -> list[dict]`

**Complexité extraction**: 🔴 MONSTRE (376 lignes, 14 injections différentes)

**Recommandation**: Découper en sous-fonctions:
- `_send_inject_base_instructions()`
- `_send_inject_perception_instructions()`
- `_send_inject_persistent_context()`
- `_send_inject_behavioral()`
- `_send_inject_archiviste_context()`
- `_send_inject_detailed_memories()`
- `_send_inject_conversation_history()`
- `_send_inject_loaded_conversation()`
- `_send_inject_journal_context()`
- `_send_inject_contextual_recall()`
- `_send_inject_emotional_context()`
- `_send_inject_orchestration()`

---

### **BLOC 10 - DEBUG TEMPORAL + WEB NAVIGATOR PRÉ-CALL**
**Lignes 6623-6667 (45 lignes)** - ✅ Extractible

**Responsabilités:**
- Affichage debug messages envoyés à Luna
- Détection requête internet
- Recherche web enrichissement contexte
- Injection contexte web AVANT message utilisateur

**Fonction cible**: `async _send_enrich_web_context(text: str, messages: list) -> list[dict]`

**Complexité extraction**: 🟢 FACILE

---

### **BLOC 11 - APPEL API IA + HOOKS POST-RÉPONSE**
**Lignes 6669-6738 (70 lignes)** - ✅ Extractible

**Responsabilités:**
- Appel API (`ctrl.call_chat_api`)
- Gestion erreur (affichage + return)
- Hook Cognitive Mirror enrichissement contexte
- Hook Archi_sensor analyse émotionnelle

**Fonction cible**: `async _send_call_ia_and_run_hooks(messages: list, ctrl) -> tuple[Optional[str], Optional[str]]`

**Retour**: `(reply, error)`

**Complexité extraction**: 🟡 MOYEN

---

### **BLOC 12 - TRAITEMENT RÉPONSE IA**
**Lignes 6740-6919 (179 lignes)** - 🔴 Extractible en 6 sous-fonctions

#### **12.1 Mémorisation IA (Lignes 6740-6768)**
**28 lignes**
```python
magic_ai = _extract_magic_memories(reply_text)
if magic_ai:
    for content in magic_ai:
        mem_id = f"ai-{uuid.uuid4()}"
        ok = await mem.add_memory(mem_id, content, chat_controller=_chat_controller, ...)
        _trigger_memory_update()
        ai_memorized = True
```

---

#### **12.2 Ego prompt update (Lignes 6771-6831)**
**60 lignes**
```python
if ego_match := re.search(r'ceci est une part de moi maintenant\s*:\s*(.*?)', reply_text, ...):
    content = ego_match.group(1).strip()
    async def store_ego_trait_async():
        memory_id = await _memory_manager.store_ego_trait(content, ...)
        await organize_ego_prompt_with_ids(_memory_manager)
    asyncio.create_task(store_ego_trait_async())
    _pending_notifications.append((notification_msg, 'positive'))
```

---

#### **12.3 Web Navigator auto-search (Lignes 6834-6916)**
**82 lignes**
```python
if web_nav_ext and web_nav_ext.commands.is_internet_request(reply_text):
    # L'IA demande une recherche
    web_response, web_file_path = await web_nav_ext.commands.process_internet_request(reply_text)
    if web_response:
        # RÉGÉNÉRER la réponse avec contexte web
        regeneration_messages = messages + [web_context_message]
        new_reply, new_err = await ctrl.call_chat_api(regeneration_messages, ...)
        cleaned_reply = new_reply
```

---

#### **12.4 Génération images text2img (Lignes 6919-6939)**
**20 lignes**
```python
if text2img_available():
    text2img_mgr = get_text2img_manager()
    cleaned_reply = await process_image_generation(cleaned_reply, sm, text2img_mgr)
```

---

#### **12.5 Détection heure (Lignes 6942-6945)**
**5 lignes**
```python
if re.search(r'\b(quelle heure|l\'heure|heure est)\b', text.lower()):
    cleaned_reply += f"\n\nTIME Il est actuellement {_get_current_time()}"
```

---

#### **12.6 File Writer .md (Lignes 6948-6966)**
**20 lignes**
```python
file_writer = _ensure_file_writer()
if file_writer:
    saved_path = file_writer.process_response(user_message=text, ai_response=cleaned_reply)
    if saved_path:
        _notify_safe(f"📁 Fichier sauvegardé: {Path(saved_path).name}", 'positive')
```

---

**Fonction cible BLOC 12**: `async _send_process_ia_response(reply: str, text: str, ctrl, messages: list) -> tuple[str, bool]`

**Retour**: `(cleaned_reply, ai_memorized)`

**Complexité extraction**: 🔴 DIFFICILE (179 lignes, 6 traitements différents)

---

### **BLOC 13 - FINALISATION ET AFFICHAGE RÉPONSE**
**Lignes 6969-7046 (77 lignes)** - ✅ Extractible

**Responsabilités:**
- Nettoyage HTML images pour historique (phrase magique préservée)
- Append historique (`_chat_history` vs `_chat_history_ui` séparés)
- Résumisation progressive (`_check_progressive_summarization`)
- Persistance conversation (`_persist_conversation`)
- Titrage contextualisé (`_maybe_update_conv_title`)
- Affichage UI réponse assistante (`_message`)
- TTS auto-speak si activé (threading)
- Scroll automatique JavaScript

**Fonction cible**: `async _send_finalize_and_display(cleaned_reply: str, ai_memorized: bool, history_content: str)`

**Complexité extraction**: 🟡 MOYEN (logique UI + TTS)

---

## 🔪 PLAN DE DÉCOUPAGE CHIRURGICAL

### ⚠️ PRINCIPE: Découpage EN PLACE (pas de modules externes)

Toutes les fonctions privées restent dans **ogma_ng.py** avec prefix `_send_*` pour clarté.

### 📋 ORDRE D'EXTRACTION (du plus simple au plus complexe)

| # | Fonction | Lignes | Complexité | Gain |
|---|----------|--------|------------|------|
| 1 | `_send_validate_input()` | 17 | 🟢 FACILE | -17L |
| 2 | `_send_handle_edit_mode()` | 24 | 🟢 FACILE | -24L |
| 3 | `_send_capture_perception()` | 19 | 🟢 FACILE | -19L |
| 4 | `_send_enrich_web_context()` | 45 | 🟢 FACILE | -45L |
| 5 | `_send_check_journal_magic()` | 40 | 🟢 FACILE | -40L |
| 6 | `_send_call_ia_and_run_hooks()` | 70 | 🟡 MOYEN | -70L |
| 7 | `_send_retrieve_memory_context()` | 75 | 🟡 MOYEN | -75L |
| 8 | `_send_check_biography_magic()` | 76 | 🟡 MOYEN | -76L |
| 9 | `_send_process_temporal_context()` | 77 | 🟡 MOYEN | -77L |
| 10 | `_send_append_history_and_display()` | 79 | 🟡 MOYEN | -79L |
| 11 | `_send_finalize_and_display()` | 77 | 🟡 MOYEN | -77L |
| 12 | `_send_handle_memory_id_read()` | 98 | 🟡 MOYEN | -98L |
| 13 | `_send_build_user_message()` | 123 | 🟡 MOYEN | -123L |
| 14 | `_send_process_ia_response()` | 179 | 🔴 DIFFICILE | -179L |
| 15 | `_send_handle_introspection_trigger()` | 261 | 🔴 TRÈS DIFFICILE | -261L |
| 16 | `_send_build_api_messages()` | 376 | 🔴 MONSTRE | -376L |

**TOTAL**: 1636 lignes extractibles

**ORCHESTRATEUR FINAL**: ~150 lignes (au lieu 1742)

**GAIN NET**: **-1540 lignes** (~19% du fichier ogma_ng.py)

---

## 🎯 ORCHESTRATEUR FINAL CIBLE (~150 lignes)

```python
async def _send_chat_message(input_el=None, text_override: Optional[str] = None, skip_history_append: bool = False):
    """
    Orchestrateur principal chat - VERSION REFACTORÉE
    
    Workflow:
    1. Validation input
    2. Mode édition
    3. Phrases magiques extensions (avec returns prématurés)
    4. Construction message utilisateur
    5. Historique + UI
    6. Contexte mémoire (FAISS + SQLite)
    7. Temporal Guardian
    8. Construction messages API (injections)
    9. Enrichissement web pré-call
    10. Appel IA + hooks
    11. Traitement réponse IA (mémorisation, extensions)
    12. Finalisation + affichage
    """
    global _chat_history, _chat_history_ui, _chat_inner, _pending_notifications
    global _editing_message_index, _pending_behavioral_injections, _journal_preformed_response
    
    # === VALIDATION INPUT ===
    text, should_return = _send_validate_input(input_el, text_override)
    if should_return:
        return
    
    # === MODE ÉDITION ===
    was_editing = _send_handle_edit_mode()
    
    # === PHRASES MAGIQUES EXTENSIONS (returns prématurés) ===
    if await _send_check_journal_magic(text):
        if input_el and not text_override:
            input_el.value = ''
        return
    
    if await _send_check_biography_magic(text):
        if input_el and not text_override:
            input_el.value = ''
        return
    
    is_auto_introspection = _send_check_introspection_auto()
    if await _send_handle_introspection_trigger(text, is_auto_introspection):
        if input_el and not text_override:
            input_el.value = ''
        return
    
    if await _send_handle_stop_introspection(text):
        if input_el and not text_override:
            input_el.value = ''
        return
    
    if await _send_handle_memory_id_read(text):
        if input_el and not text_override:
            input_el.value = ''
        return
    
    if await _send_handle_conversation_commands(text):
        if input_el and not text_override:
            input_el.value = ''
        return
    
    # === CAPTURE PERCEPTION ===
    perception_image_data = _send_capture_perception()
    
    # === CONSTRUCTION MESSAGE UTILISATEUR ===
    ai_content, cleaned_text, user_memorized = await _send_build_user_message(
        text, perception_image_data, _active_file_data
    )
    
    # === HISTORIQUE + AFFICHAGE UI ===
    if not skip_history_append:
        await _send_append_history_and_display(
            text, cleaned_text, user_memorized, was_editing, input_el, text_override
        )
    
    # Vider input
    if input_el and not text_override:
        input_el.value = ''
    
    # === CONTEXTE MÉMOIRE (FAISS + SQLite) ===
    context_note, detailed_memories = await _send_retrieve_memory_context(text)
    
    # === TEMPORAL GUARDIAN ===
    temporal_final_alert, temporal_context_enriched = await _send_process_temporal_context(
        text, context_note
    )
    
    # === CONSTRUCTION MESSAGES API (TOUTES INJECTIONS) ===
    messages = await _send_build_api_messages(
        text=text,
        context_note=context_note,
        temporal_alert=temporal_final_alert,
        temporal_context=temporal_context_enriched,
        detailed_memories=detailed_memories,
        perception_data=perception_image_data,
        active_file=_active_file_data,
        user_message_content=ai_content
    )
    
    # === ENRICHISSEMENT WEB PRÉ-CALL ===
    messages = await _send_enrich_web_context(text, messages)
    
    # === APPEL IA + HOOKS POST-RÉPONSE ===
    ctrl = _ensure_chat_controller()
    reply, err = await _send_call_ia_and_run_hooks(messages, ctrl)
    
    if err:
        if _chat_inner is not None:
            with _chat_inner:
                _message('system', f"[ERREUR] {err}")
        return
    
    if reply is None:
        return
    
    # === TRAITEMENT RÉPONSE IA (Extensions) ===
    cleaned_reply, ai_memorized = await _send_process_ia_response(
        reply, text, ctrl, messages
    )
    
    # === FINALISATION + AFFICHAGE ===
    await _send_finalize_and_display(cleaned_reply, ai_memorized)
```

---

## 📝 NOTES IMPORTANTES

### ⚠️ Variables Globales à Préserver
Ces variables globales sont utilisées partout et **NE DOIVENT PAS** être modifiées lors du refactoring:

```python
global _chat_history                    # Liste messages texte
global _chat_history_ui                 # Liste messages UI (avec HTML)
global _chat_inner                      # Conteneur UI NiceGUI
global _pending_notifications           # Queue notifications
global _editing_message_index           # Index édition message
global _pending_behavioral_injections   # Injections metacognition
global _journal_preformed_response      # Réponse journal prédéfinie
global _active_file_data                # Fichier uploadé actif
global _loaded_conversation             # Conversation chargée
global _conversation_context_injected   # Flag injection contexte
global _orchestration_injected          # Flag orchestration
global _introspection_box_content       # Contenu boîte introspection
global _introspection_md_widget         # Widget markdown introspection
```

### 🔒 Dépendances Critiques

**Managers requis:**
- `_ensure_chat_controller()`
- `_ensure_archiviste_controller()`
- `_ensure_memory_manager()`
- `_ensure_settings_manager()`
- `_ensure_audio_manager()`
- `_ensure_temporal_guardian()`
- `_ensure_cognitive_mirror()`
- `_ensure_contextual_recall()`
- `_ensure_file_writer()`

**Extensions:**
- `_journal_available` + `get_journal()`
- `_biography_available` + `get_biography_magic_phrases()`
- `COGNITIVE_MIRROR_AVAILABLE` + `get_introspection()`
- `text2img_available()` + `get_text2img_manager()`
- `get_web_navigator_instance()`
- `get_perception_ui()`

### 🧪 Tests Requis Après Chaque Extraction

1. **Envoi message simple** → Affichage OK
2. **Phrase magique journal** → Interception OK
3. **Phrase magique introspection** → Dialogue Luna↔Archiviste OK
4. **Message avec image** → Multimodal OK
5. **Édition message** → Suppression historique OK
6. **Mémorisation IA** → Notification + FAISS update OK
7. **Recherche web** → Enrichissement contexte OK
8. **Génération image** → text2img trigger OK

### 🚨 Garde-Fous Anti-Destruction

1. ✅ **Copier code AVANT suppression** (backup clipboard)
2. ✅ **Supprimer IMMÉDIATEMENT après extraction** (ne pas attendre fin)
3. ✅ **Tester après CHAQUE fonction** (pas batch)
4. ✅ **Commit atomique par fonction** (rollback facile)
5. ✅ **Git reset si test échoue** (restauration instantanée)

---

## 📅 HISTORIQUE

| Date | Action | Détails |
|------|--------|---------|
| 2025-11-01 | Cartographie initiale | 1742 lignes identifiées, 16 blocs fonctionnels |
| 2025-11-01 | Plan découpage | 16 fonctions à extraire, ordre prioritaire défini |

---

## 🎯 OBJECTIFS FINAUX

- [x] Cartographie complète fonction _send_chat_message
- [ ] Extraction 16 fonctions (ordre: simple → complexe)
- [ ] Tests validation après chaque extraction
- [ ] Orchestrateur final ~150 lignes
- [ ] Gain net: **-1540 lignes** (~19% fichier)
- [ ] Commit final: "refactor: découpage chirurgical _send_chat_message"

---

**FIN DE LA CARTOGRAPHIE**
