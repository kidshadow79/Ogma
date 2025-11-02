"""
OGMA UI CONVERSATIONS - Module UI pour Conversations & Sidebar
Extrait depuis ogma_ng.py (Phase Découpage Scénario A - Nov 2025)

Responsabilités:
- Affichage messages (_message)
- Édition messages (load_message_for_edit)
- Gestion conversations (index, load, save, persist)
- Sidebar complète avec actions
- Memory UI (mémorisation conversations)
- Modals (Models, Image generation)

IMPORTANT: Ce module doit être importé APRÈS ogma_ng.py (pas de problème car ogma_ng est le point d'entrée)
"""

from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
import asyncio
import re
import uuid
from datetime import datetime

# NiceGUI
try:
    from nicegui import ui
except ImportError:
    ui = None  # type: ignore

# === IMPORTS MODULES OGMA ===
from utils.message_parsers import parse_thinking_format, parse_introspection_format
from utils.formatting_utils import format_datetime, format_size, truncate_filename, get_file_icon
from conversations import load_conversation_index, save_conversation_index
from conversations import make_conv_id, make_title_from_text

# === CONSTANTES ===
DATA_DIR = Path('data')  # Dossier data pour conversations


# === HELPER POUR LAZY IMPORT ===
def _get_ogma():
    """Import paresseux pour éviter import circulaire"""
    import ogma_ng
    return ogma_ng

def activate_loading_mode():
    """Wrapper pour activate_loading_mode depuis magic_phrase_guard"""
    from magic_phrase_guard import activate_loading_mode as _activate
    _activate()

def deactivate_loading_mode():
    """Wrapper pour deactivate_loading_mode depuis magic_phrase_guard"""
    from magic_phrase_guard import deactivate_loading_mode as _deactivate
    _deactivate()

def _notify_safe(message: str, type: str = 'info') -> None:
    """Wrapper pour _notify_safe depuis ogma_ng"""
    try:
        _get_ogma()._notify_safe(message, type)
    except Exception:
        # Fallback si _notify_safe n'existe pas
        if ui:
            ui.notify(message, type=type)

def _ensure_settings_manager():
    """Wrapper pour _ensure_settings_manager depuis ogma_ng"""
    return _get_ogma()._ensure_settings_manager()

def _get_cognitive_mirror_available() -> bool:
    """Helper pour récupérer COGNITIVE_MIRROR_AVAILABLE depuis ogma_ng"""
    try:
        return _get_ogma().COGNITIVE_MIRROR_AVAILABLE
    except AttributeError:
        return False

def _memorization_popup(conv_id: str, conv_title: str):
    """Wrapper pour _memorization_popup depuis ogma_ng"""
    _get_ogma()._memorization_popup(conv_id, conv_title)

def _ensure_archiviste_controller():
    """Wrapper pour _ensure_archiviste_controller depuis ogma_ng"""
    return _get_ogma()._ensure_archiviste_controller()

def _ensure_memory_manager():
    """Wrapper pour _ensure_memory_manager depuis ogma_ng"""
    return _get_ogma()._ensure_memory_manager()

def _ensure_chat_controller():
    """Wrapper pour _ensure_chat_controller depuis ogma_ng"""
    return _get_ogma()._ensure_chat_controller()

def _ensure_embedding_controller():
    """Wrapper pour _ensure_embedding_controller depuis ogma_ng"""
    return _get_ogma()._embedding_controller

def _ensure_audio_manager():
    """Wrapper thread-safe pour _audio_manager depuis ogma_ng"""
    return _get_ogma()._audio_manager

def _get_conv_index():
    """Wrapper thread-safe pour _conv_index depuis ogma_ng"""
    return _get_ogma()._conv_index

def _get_chat_history():
    """Wrapper thread-safe pour _chat_history depuis ogma_ng"""
    return _get_ogma()._chat_history

def _get_current_conversation_id():
    """Wrapper thread-safe pour _current_conversation_id depuis ogma_ng"""
    return _get_ogma()._current_conversation_id

def _try_restore_index_from_backup() -> bool:
    """
    Tente de restaurer l'index depuis le backup le plus récent.
    Retourne True si restauration réussie, False sinon.
    """
    try:
        import json
        from pathlib import Path
        
        conv_dir = DATA_DIR / 'conversations'
        # Chercher tous les backups index_backup_*.json
        backups = list(conv_dir.glob('index_backup_*.json'))
        
        if not backups:
            print(f"[CONV-INDEX-RESTORE] ⚠️ Aucun backup trouvé")
            return False
        
        # Trier par date (nom contient timestamp) - le plus récent en premier
        backups.sort(reverse=True)
        
        # Essayer les backups du plus récent au plus ancien
        for backup_path in backups:
            try:
                content = backup_path.read_text(encoding='utf-8-sig').strip()
                if not content or content == '{}':
                    print(f"[CONV-INDEX-RESTORE] ⏭️  {backup_path.name} vide, ignoré")
                    continue
                
                data = json.loads(content)
                
                # Vérifier format valide
                if isinstance(data, dict) and 'conversations' in data:
                    conversations = data.get('conversations', {})
                else:
                    conversations = data if isinstance(data, dict) else {}
                
                if len(conversations) == 0:
                    print(f"[CONV-INDEX-RESTORE] ⏭️  {backup_path.name} aucune conversation, ignoré")
                    continue
                
                # BACKUP VALIDE TROUVÉ !
                _get_ogma()._conv_index = conversations
                print(f"[CONV-INDEX-RESTORE] ✅ Restauré depuis {backup_path.name}")
                print(f"[CONV-INDEX-RESTORE] 📊 {len(conversations)} conversations récupérées")
                
                # Sauvegarder dans index.json
                idx_path = conv_dir / 'index.json'
                payload = {"conversations": conversations}
                idx_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f"[CONV-INDEX-RESTORE] 💾 index.json restauré")
                
                return True
                
            except Exception as e:
                print(f"[CONV-INDEX-RESTORE] ❌ Erreur lecture {backup_path.name}: {e}")
                continue
        
        print(f"[CONV-INDEX-RESTORE] ⚠️ Aucun backup valide trouvé sur {len(backups)} fichiers")
        return False
        
    except Exception as e:
        print(f"[CONV-INDEX-RESTORE] ❌ Erreur restauration: {e}")
        return False

# === VARIABLES GLOBALES IMPORTÉES DEPUIS OGMA_NG ===
# Note: Ces variables sont définies dans ogma_ng.py qui est le point d'entrée
# L'import circulaire est résolu car ogma_ng est toujours chargé en premier
# Elles seront déclarées "global" dans les fonctions qui les utilisent

# Liste des variables globales utilisées (référence pour documentation):
# - _get_ogma()._chat_history, _get_ogma()._chat_history_ui, _chat_inner
# - _get_ogma()._current_conversation_id, _conv_index
# - _get_ogma()._sidebar_render_cb, _sidebar_container
# - _chat_controller, _archiviste_controller, _memory_manager, _settings_manager
# - _get_ogma()._editing_message_index, _biography_available
# - _is_speech_active, _stt_manager, _tts_manager
# - etc.

# Ces variables seront accessibles via "import ogma_ng" ou directement
# selon les besoins de chaque fonction

# === FONCTIONS EXTRAITES D'OGMA_NG.PY ===

def _message(role: str, content: str, badges: Optional[List[str]] = None, message_index: Optional[int] = None):
    # Simple rendu de message avec classes CSS
    try:
        cls = 'message-system'
        if role == 'user':
            cls = 'message-user'
        elif role == 'assistant':
            cls = 'message-ai'
        with ui.element('div').classes('message-container'):
            with ui.element('div').classes(cls):
                if role == 'assistant':
                    # Parser le format thinking si présent (importé depuis utils.message_parsers)
                    thinking_content, main_content = parse_thinking_format(content)

                    # 📖 BIOGRAPHIE PROFIL: Détection phrases magiques Luna dans les réponses
                    biography_context_to_inject = ""
                    try:
                        if _get_ogma()._biography_available and main_content:
                            # 🛡️ MAGIC PHRASE GUARD: Vérifier si message historique
                            from magic_phrase_guard import should_process_magic_phrase

                            # Récupérer métadonnées du message actuel
                            current_message_data = {}
                            if message_index is not None and message_index < len(_get_ogma()._chat_history_ui):
                                current_message_data = _get_ogma()._chat_history_ui[message_index]

                            # Vérifier si traitement autorisé (message temps réel)
                            if should_process_magic_phrase(current_message_data, "BIOGRAPHIE"):
                                from extensions.biographie_profil import get_biography_magic_phrases
                                biography_magic = get_biography_magic_phrases()

                                if biography_magic:
                                    # Détecter phrases magiques Luna (consultation)
                                    luna_magic_response = biography_magic._handle_luna_magic_phrases(main_content)
                                    if luna_magic_response:
                                        biography_context_to_inject = f"\n\n{luna_magic_response}"
                                        print(f"[BIOGRAPHY-EXTENSION] 🔍 Phrase magique Luna détectée - contexte ajouté")

                    except Exception as e:
                        print(f"[BIOGRAPHY-EXTENSION] ERROR Erreur détection phrase magique Luna: {e}")

                    # 🧠 COGNITIVE MIRROR v2.0: Détection phrases magiques IA pour introspection
                    try:
                        if _get_cognitive_mirror_available() and main_content:
                            from extensions.cognitive_mirror import is_enabled, check_magic_phrases

                            if is_enabled():
                                # 🛡️ MAGIC PHRASE GUARD: Vérifier si message historique
                                from magic_phrase_guard import should_process_magic_phrase

                                # Récupérer métadonnées du message actuel
                                current_message_data = {}
                                if message_index is not None and message_index < len(_get_ogma()._chat_history_ui):
                                    current_message_data = _get_ogma()._chat_history_ui[message_index]

                                # Vérifier si traitement autorisé (message temps réel)
                                if should_process_magic_phrase(current_message_data, "INTROSPECTION"):
                                    # Vérifier si Luna a utilisé une phrase magique d'introspection
                                    magic_type = check_magic_phrases(main_content, source="ia")

                                    if magic_type == "trigger":
                                        print(f"[INTROSPECTION] 🧠 Phrase magique IA détectée: déclenchement différé d'introspection")

                                        # Programmer déclenchement introspection après affichage message
                                        async def trigger_delayed_introspection():
                                            try:
                                                # Petite pause pour permettre l'affichage du message
                                                await asyncio.sleep(0.5)

                                                # Construire contexte pour introspection
                                                from utils import get_ego_prompt

                                                try:
                                                    current_ego_prompt = get_ego_prompt()
                                                except:
                                                    current_ego_prompt = "Ego prompt non disponible"

                                                # NOUVEAU: Récupération identités dynamiques
                                                from identity_manager import get_current_identities
                                                identities = get_current_identities()

                                                chat_hist = _get_chat_history()
                                                extended_history = chat_hist[-20:] if len(chat_hist) > 20 else chat_hist

                                                conversation_context = {
                                                    'user_message': f"[Auto-déclenchement suite à phrase magique IA]",
                                                    'chat_history': extended_history,
                                                    'user_identity': identities['user_identity'],
                                                    'ego_prompt': current_ego_prompt,
                                                    'main_ai_identity': identities['main_ai_identity'],
                                                    'relationship_context': identities['relationship_context']
                                                }

                                                # Lancer introspection
                                                from extensions.cognitive_mirror import get_introspection
                                                introspection_core = get_introspection()

                                                if introspection_core:
                                                    print(f"[INTROSPECTION] 🚀 Lancement introspection différée...")

                                                    # Créer la boîte thinking pour l'introspection différée
                                                    global _introspection_box_content, _introspection_md_widget
                                                    _introspection_box_content = []

                                                    with _get_ogma()._chat_inner:
                                                        with ui.expansion().classes('thinking-expansion') as introspection_box:
                                                            introspection_box.props('label=""')
                                                            with introspection_box.add_slot('header'):
                                                                ui.html('<span style="color: rgba(255, 200, 100, 0.7); font-size: 12px; font-style: italic;">🧠 introspection ia-principale-archiviste [auto-déclenchée]</span>')

                                                            _introspection_md_widget = ui.markdown("_Dialogue en cours..._")
                                                            _introspection_md_widget.style(
                                                                'color: rgba(255, 255, 255, 0.85); '
                                                                'font-size: 13px; '
                                                                'line-height: 1.5; '
                                                                'margin: 0; '
                                                                'padding: 8px 0; '
                                                                'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'
                                                            )
                                                            _introspection_md_widget.classes('introspection-dialogue')

                                                    introspection_result = await introspection_core.trigger_introspection_sync(
                                                        user_message="[Auto-introspection déclenchée par phrase magique IA]",
                                                        conversation_context=conversation_context
                                                    )

                                                    if introspection_result.get("success"):
                                                        final_response = introspection_result.get("final_response", "")
                                                        print("[INTROSPECTION] ✅ Auto-introspection complétée")

                                                        # Afficher la réponse finale dans la conversation
                                                        if final_response:
                                                            with _get_ogma()._chat_inner:
                                                                _message('assistant', final_response)

                                                            msg = {'role': 'assistant', 'content': final_response}
                                                            _get_ogma()._chat_history.append(msg)
                                                            _get_ogma()._chat_history_ui.append(msg)
                                                    else:
                                                        print("[INTROSPECTION] ❌ Échec auto-introspection")
                                                else:
                                                    print("[INTROSPECTION] ❌ Core introspection non disponible")

                                            except Exception as e:
                                                print(f"[INTROSPECTION] ❌ Erreur auto-introspection: {e}")

                                        # Programmer l'exécution différée
                                        asyncio.create_task(trigger_delayed_introspection())
                                    
                    except Exception as e:
                        print(f"[INTROSPECTION] ERROR Erreur détection phrase magique IA: {e}")

                    # 👁️ PERCEPTION: Détection phrases magiques IA pour auto-activation/désactivation
                    try:
                        from extensions.perception_ui import get_perception_ui
                        perception_ui = get_perception_ui()

                        if perception_ui and main_content:
                            # 🛡️ MAGIC PHRASE GUARD: Vérifier si message historique
                            from magic_phrase_guard import should_process_magic_phrase

                            # Récupérer métadonnées du message actuel
                            current_message_data = {}
                            if message_index is not None and message_index < len(_get_ogma()._chat_history_ui):
                                current_message_data = _get_ogma()._chat_history_ui[message_index]

                            # Vérifier si traitement autorisé (message temps réel)
                            if should_process_magic_phrase(current_message_data, "PERCEPTION"):
                                # Patterns d'activation IA: "il faut que je te vois", "je veux te voir", "il faut que je vois"
                                activation_patterns = [
                                    r"il\s+faut\s+que\s+je\s+(?:te\s+)?vois",
                                    r"je\s+veux\s+te\s+voir",
                                    r"il\s+faut\s+que\s+je\s+vois"
                                ]
                                
                                # Patterns de désactivation IA: "je n'ai plus besoin de te voir", "je peux arrêter de te regarder"
                                deactivation_patterns = [
                                    r"je\s+n'ai\s+plus\s+besoin\s+de\s+te\s+voir",
                                    r"je\s+(?:peux|vais)\s+arrêter\s+de\s+te\s+(?:voir|regarder)",
                                    r"je\s+ferme\s+(?:ma\s+)?vision",
                                    r"je\s+coupe\s+(?:ma\s+)?caméra"
                                ]
                                
                                is_activation_trigger = any(re.search(pattern, main_content, re.IGNORECASE) for pattern in activation_patterns)
                                is_deactivation_trigger = any(re.search(pattern, main_content, re.IGNORECASE) for pattern in deactivation_patterns)
                                
                                if is_activation_trigger and not perception_ui.is_enabled:
                                    print("[PERCEPTION] 👁️ Phrase magique IA d'activation détectée - démarrage webcam")
                                    
                                    # Programmer l'activation différée (après affichage message)
                                    async def trigger_perception_activation():
                                        try:
                                            await asyncio.sleep(0.3)  # Pause pour affichage du message
                                            perception_ui.start_perception()
                                            ui.notify('👁️ Perception activée par Luna - Webcam démarrée', type='positive', position='top')
                                            print("[PERCEPTION] ✅ Webcam activée suite à phrase magique IA")
                                        except Exception as e:
                                            print(f"[PERCEPTION] ❌ Erreur activation différée: {e}")
                                    
                                    asyncio.create_task(trigger_perception_activation())
                                
                                elif is_deactivation_trigger and perception_ui.is_enabled:
                                    print("[PERCEPTION] 🛑 Phrase magique IA de désactivation détectée - arrêt webcam")
                                    
                                    # Programmer la désactivation différée
                                    async def trigger_perception_deactivation():
                                        try:
                                            await asyncio.sleep(0.3)
                                            perception_ui.stop_perception()
                                            ui.notify('🛑 Perception désactivée par Luna - Webcam arrêtée', type='info', position='top')
                                            print("[PERCEPTION] ✅ Webcam désactivée suite à phrase magique IA")
                                        except Exception as e:
                                            print(f"[PERCEPTION] ❌ Erreur désactivation différée: {e}")
                                    
                                    asyncio.create_task(trigger_perception_deactivation())
                            
                            else:
                                print("[PERCEPTION] 🛡️ Message historique - phrase magique IA ignorée")

                    except Exception as e:
                        print(f"[PERCEPTION] ERROR Erreur détection phrase magique IA: {e}")

                    # Ajouter le contexte biographique au contenu principal si disponible
                    if biography_context_to_inject:
                        main_content += biography_context_to_inject

                    # Afficher la partie thinking si elle existe (dans un cadre dépliant)
                    if thinking_content:
                        global _thinking_css_injected
                        
                        # Injecter le CSS personnalisé pour les dialogues intérieurs
                        # Force l'injection à chaque fois pour s'assurer que le CSS s'applique
                        ui.add_head_html('''
                        <style>
                        /* CSS spécifique pour les dialogues Subconscience - Force l'application */
                        .subconscience-dialogue .q-expansion-item__content,
                        .subconscience-content {
                            font-size: 12px !important;
                            font-style: italic !important;
                            color: rgba(255, 255, 255, 0.8) !important;
                            line-height: 1.4 !important;
                        }
                        /* Force style sur tous les éléments du dialogue intérieur */
                        .subconscience-content *,
                        .subconscience-dialogue .q-expansion-item__content *,
                        .subconscience-dialogue .q-expansion-item__content div,
                        .subconscience-dialogue .q-expansion-item__content p,
                        .subconscience-dialogue .q-expansion-item__content span,
                        .subconscience-dialogue .q-expansion-item__content strong,
                        .subconscience-dialogue .q-expansion-item__content em {
                            font-size: 12px !important;
                            font-style: italic !important;
                            color: rgba(255, 255, 255, 0.8) !important;
                            line-height: 1.4 !important;
                        }
                        .thinking-expansion .q-expansion-item__header {
                            background: rgba(255, 255, 255, 0.05) !important;
                            border-radius: 6px !important;
                            padding: 6px 10px !important;
                            margin-bottom: 6px !important;
                            border-left: 3px solid rgba(79, 172, 254, 0.4) !important;
                            min-height: 32px !important;
                            flex-direction: row-reverse !important;
                        }
                        .thinking-expansion .q-expansion-item__header:hover {
                            background: rgba(255, 255, 255, 0.05) !important;
                        }
                        .thinking-expansion .q-expansion-item__header .q-item__label,
                        .thinking-expansion .q-expansion-item__header .q-item__section,
                        .thinking-expansion .q-expansion-item__header span,
                        .thinking-expansion .q-expansion-item__header {
                            color: rgba(255, 255, 255, 0.7) !important;
                            font-size: 14px !important;
                            font-style: italic !important;
                            font-weight: 400 !important;
                        }
                        .thinking-expansion .q-expansion-item__content {
                            background: rgba(255, 255, 255, 0.02) !important;
                            border-radius: 0 0 6px 6px !important;
                            padding: 6px 10px !important;
                            margin-bottom: 8px !important;
                            border-left: none !important;
                        }
                        .thinking-expansion .q-expansion-item__icon {
                            display: block !important;
                            color: rgba(79, 172, 254, 0.6) !important;
                            font-size: 16px !important;
                            order: -1 !important;
                            margin-right: 8px !important;
                            margin-left: 0 !important;
                        }
                        .thinking-expansion .q-expansion-item {
                            margin: 0 !important;
                        }
                        </style>
                        ''')
                        _thinking_css_injected = True
                        
                        with ui.expansion().classes('thinking-expansion') as expansion:
                            # Customiser le titre avec du HTML inline pour forcer l'italique
                            expansion.props(f'label=""')
                            with expansion.add_slot('header'):
                                ui.html('<span style="color: rgba(255, 255, 255, 0.5); font-size: 12px; font-style: italic; font-weight: 400;">réflexion</span>')
                            try:
                                thinking_md = ui.markdown(thinking_content)
                                thinking_md.style(
                                    'color: rgba(255, 255, 255, 0.7); '
                                    'background: transparent; '
                                    'font-size: 12px; '
                                    'font-style: italic; '
                                    'line-height: 1.2; '
                                    'margin: 0; '
                                    'padding: 4px 0;'
                                )
                            except Exception:
                                thinking_lbl = ui.label(thinking_content)
                                thinking_lbl.style(
                                    'color: rgba(255, 255, 255, 0.7); '
                                    'font-size: 12px; '
                                    'font-style: italic; '
                                    'line-height: 1.2; '
                                    'margin: 0; '
                                    'padding: 4px 0;'
                                )

                    # Parser le format introspection depuis le contenu restant après thinking
                    # Importé depuis utils.message_parsers
                    current_content = main_content if thinking_content else content
                    introspection_content, final_content = parse_introspection_format(current_content)
                    
                    # Afficher la partie introspection si elle existe (dans un cadre dépliant orange)
                    if introspection_content:
                        # Injecter le CSS spécifique pour introspection
                        ui.add_head_html('''
                        <style>
                        /* CSS spécifique pour les expansions Introspection */
                        .introspection-expansion {
                            margin: 8px 0 !important;
                            border-radius: 6px !important;
                            background: rgba(255, 140, 0, 0.05) !important;
                            border: 1px solid rgba(255, 140, 0, 0.2) !important;
                        }
                        .introspection-expansion .q-expansion-item__header {
                            padding: 8px 12px !important;
                            min-height: 32px !important;
                        }
                        .introspection-expansion .q-expansion-item__content {
                            padding: 8px 12px !important;
                            font-size: 12px !important;
                            font-style: italic !important;
                            color: rgba(255, 255, 255, 0.8) !important;
                            line-height: 1.4 !important;
                            background: rgba(255, 140, 0, 0.03) !important;
                        }
                        .introspection-expansion .q-expansion-item__content * {
                            font-size: 12px !important;
                            font-style: italic !important;
                            color: rgba(255, 255, 255, 0.8) !important;
                        }
                        .introspection-header {
                            color: rgba(255, 140, 0, 0.8) !important;
                            font-size: 12px !important;
                            font-style: italic !important;
                            font-weight: 400 !important;
                        }
                        </style>
                        ''')
                        
                        with ui.expansion().classes('introspection-expansion') as introspection_expansion:
                            introspection_expansion.props(f'label=""')
                            with introspection_expansion.add_slot('header'):
                                ui.html('<span class="introspection-header">introspection</span>')
                            try:
                                introspection_md = ui.markdown(introspection_content)
                                introspection_md.style(
                                    'color: rgba(255, 255, 255, 0.8); '
                                    'background: transparent; '
                                    'font-size: 12px; '
                                    'font-style: italic; '
                                    'line-height: 1.4; '
                                    'margin: 0; '
                                    'padding: 4px 0;'
                                )
                            except Exception:
                                introspection_lbl = ui.label(introspection_content)
                                introspection_lbl.style(
                                    'color: rgba(255, 255, 255, 0.8); '
                                    'font-size: 12px; '
                                    'font-style: italic; '
                                    'line-height: 1.4; '
                                    'margin: 0; '
                                    'padding: 4px 0;'
                                )
                    
                    # Afficher le contenu principal
                    display_content = final_content if introspection_content else current_content
                    # Le markdown rend mieux les retours à la ligne / listes; fallback label si indisponible
                    try:
                        md = ui.markdown(display_content)
                        md.style(
                            'color: var(--text-offwhite); '
                            'background: transparent; '
                            'font-size: 16px; '
                            'line-height: 1.3; '
                            'margin: 0; '
                            'padding: 0;'
                        )
                    except Exception:
                        lbl = ui.label(display_content)
                        lbl.style(
                            'color: var(--text-offwhite); '
                            'font-size: 16px; '
                            'line-height: 1.3; '
                            'margin: 0; '
                            'padding: 0;'
                        )
                    
                    # Bouton TTS pour les réponses de l'assistant - Option A : Toggle Simple
                    if not hasattr(_message, '_tts_button_states'):
                        _message._tts_button_states = {}
                    
                    button_id = f"tts-{id(content)}"
                    
                    def speak_message():
                        try:
                            # Récupérer l'état actuel du bouton
                            is_playing = _message._tts_button_states.get(button_id, False)
                            
                            if is_playing:  # STOP - Arrêter la lecture
                                print("[TTS] ⏹️ STOP - Arrêt de la lecture demandé")
                                audio_mgr = _ensure_audio_manager()
                                if audio_mgr and hasattr(audio_mgr, 'stop_speaking'):
                                    success = audio_mgr.stop_speaking()
                                    if success:
                                        ui.notify("🔇 Lecture arrêtée", type='info')
                                    else:
                                        ui.notify("⚠️ Impossible d'arrêter la lecture", type='warning')
                                else:
                                    ui.notify("❌ Audio manager non disponible", type='negative')
                                
                                _message._tts_button_states[button_id] = False
                                print("[TTS] ⏹️ État mis à jour : STOP")
                                
                            else:  # PLAY - Démarrer la lecture
                                print(f"[TTS] ▶️ PLAY - Démarrage lecture: {content[:50]}...")
                                audio_mgr = _ensure_audio_manager()
                                if audio_mgr and hasattr(audio_mgr, 'speak'):
                                    import asyncio
                                    # Nettoyer le contenu pour la synthèse
                                    clean_content = content.replace('*', '').replace('**', '').replace('#', '').replace('`', '')
                                    _message._tts_button_states[button_id] = True
                                    
                                    # Notification immédiate
                                    ui.notify("🔊 Lecture en cours...", type='info')
                                    
                                    def audio_task():
                                        """Tâche audio synchrone avec wrapper TTS sans conflit"""
                                        try:
                                            # Le nouveau wrapper retourne bool directement (pas async)
                                            audio_mgr = _ensure_audio_manager()
                                            success = audio_mgr.speak(clean_content) if audio_mgr else False
                                            if success:
                                                print("[TTS] ✅ Synthèse réussie")
                                            else:
                                                print("[TTS] ⚠️ Synthèse en mode fallback")
                                        except Exception as e:
                                            print(f"[TTS] ❌ Erreur pendant la lecture: {e}")
                                            # Pas de ui.notify ici (thread background)
                                        finally:
                                            # Remettre à PLAY quand terminé
                                            _message._tts_button_states[button_id] = False
                                            print("[TTS] ✅ Lecture terminée - État remis à PLAY")
                                    
                                    # Lancer dans un thread séparé pour éviter blocage UI
                                    import threading
                                    thread = threading.Thread(target=audio_task, daemon=True)
                                    thread.start()
                                    print(f"[TTS] ▶️ Thread créé pour: {clean_content[:30]}...")
                                else:
                                    print("[TTS] ❌ Audio manager non disponible")
                                    ui.notify("❌ Audio manager non disponible", type='negative')
                                    
                        except Exception as e:
                            print(f"[TTS] ❌ ERROR: {e}")
                            ui.notify(f"❌ Erreur TTS: {str(e)[:50]}...", type='negative')
                            _message._tts_button_states[button_id] = False
                    
                    # Vérifier si TTS est activé dans les paramètres
                    try:
                        sm = _ensure_settings_manager()
                        tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
                        auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
                        
                        # N'afficher le bouton que si la lecture automatique n'est PAS activée
                        if tts_enabled and _ensure_audio_manager() and not auto_speak:
                            with ui.row().classes('gap-2 mt-2'):
                                # Bouton Play permanent - clic = toggle play/stop
                                ui.button("▶", on_click=speak_message).classes('tts-button').tooltip(
                                    'Écouter cette réponse (clic = play/stop)'
                                )
                                
                        elif tts_enabled and auto_speak:
                            # Afficher un petit indicateur que la lecture automatique est active
                            with ui.row().classes('gap-2 mt-2'):
                                ui.label('▶ Auto').classes('text-xs text-muted').style(
                                    'color: rgba(255, 255, 255, 0.6); '
                                    'font-size: 12px; '
                                    'font-family: monospace;'
                                ).tooltip('Lecture automatique activée')
                                
                    except Exception as e:
                        print(f"[TTS] ❌ Erreur config TTS: {e}")
                    
                else:
                    lbl = ui.label(content)
                    if role == 'user':
                        # Priorité maximale contre styles internes de composants
                        lbl.style('color: var(--text-offwhite); font-size: 16px;')

                # Badges additionnels (ex: "mémorisé")
                try:
                    if badges:
                        with ui.row().classes('gap-1 mt-1'):
                            for b in badges:
                                ui.label(b).style('font-size: 12px; color: #9EF0A7; background: rgba(158,240,167,0.12); border: 1px solid rgba(158,240,167,0.65); border-radius: 6px; padding: 2px 6px;')
                except Exception:
                    pass

            # Bouton edit SOUS la bulle pour messages user (aligné à droite)
            if role == 'user' and message_index is not None:
                with ui.row().classes('gap-2').style('margin-top: 4px; justify-content: flex-end;'):
                    ui.button("✎", on_click=lambda idx=message_index, txt=content: load_message_for_edit(txt, idx)) \
                        .props('flat dense color=grey-6') \
                        .style('''
                            font-size: 12px;
                            min-width: 20px;
                            padding: 0;
                            opacity: 0.5;
                        ''') \
                        .tooltip('Modifier ce message')
    except Exception as e:
        print(f"[ERROR] Erreur création message {role}: {e}")
        # PROTECTION ANTI-CRASH: Vérifier si c'est une erreur de client supprimé
        error_msg = str(e).lower()
        if "deleted" in error_msg or "client" in error_msg:
            print(f"[UI-PROTECTION] ⚠️ Élément UI supprimé détecté - rechargement interface...")
            # Ne pas planter, laisser NiceGUI se reconnecter
            try:
                # Force refresh de l'interface si possible
                ui.run_javascript('setTimeout(() => window.location.reload(), 100);')
            except:
                pass
        # Fallback simple si l'UI ne peut pas être créée
        pass


def load_message_for_edit(original_content: str, message_index: int):
    """
    Charge un message dans l'input field pour édition

    Args:
        original_content: Texte original du message
        message_index: Index du message dans _chat_history
    """

    try:
        # Stocker l'index pour que _send_chat_message sache qu'on édite
        _get_ogma()._editing_message_index = message_index

        # 🛡️ MAGIC PHRASE GUARD: Retirer from_history (message devient "vivant")
        from magic_phrase_guard import unmark_message_as_historical

        if message_index < len(_get_ogma()._chat_history_ui):
            _get_ogma()._chat_history_ui[message_index] = unmark_message_as_historical(_get_ogma()._chat_history_ui[message_index])
            print(f"[EDIT-MESSAGE] 🔄 Message #{message_index} démarqué - devient éditable")

        # Charger le texte dans l'input
        input_field = _get_ogma()._input_field
        if input_field:
            input_field.value = original_content
            ui.notify('✎ Message chargé - Modifiez et envoyez', type='info', position='top')
            print(f"[EDIT-MESSAGE] 📝 Message #{message_index} chargé dans l'input pour édition")
        else:
            print(f"[EDIT-MESSAGE] ❌ Input field non disponible")

    except Exception as e:
        print(f"[EDIT-MESSAGE] ❌ Erreur chargement message: {e}")
        import traceback
        traceback.print_exc()


def _load_conversation_index() -> Dict[str, Dict]:
    """Charge data/conversations/index.json si présent."""
    try:
        idx_path = DATA_DIR / 'conversations' / 'index.json'
        if idx_path.exists():
            import json
            # Lire avec utf-8-sig pour gérer le BOM automatiquement
            content = idx_path.read_text(encoding='utf-8-sig').strip()
            
            # Gérer fichier vide ou corrompu - TENTER RESTAURATION BACKUP
            if not content:
                print(f"[CONV-INDEX] ⚠️ Fichier index.json vide, tentative restauration backup...")
                backup_restored = _try_restore_index_from_backup()
                if backup_restored:
                    return _get_ogma()._conv_index
                # Pas de backup valide - initialiser vide SANS sauvegarder
                print(f"[CONV-INDEX] ⚠️ Aucun backup valide, index vide (manuel: python repair_conversation_index.py)")
                _get_ogma()._conv_index = {}
                return _get_ogma()._conv_index
            
            data = json.loads(content)
            # Support ancien format {'conversations': {...}} et nouveau format direct {...}
            if isinstance(data, dict) and 'conversations' in data:
                _get_ogma()._conv_index = data.get('conversations', {})
            else:
                _get_ogma()._conv_index = data or {}
            print(f"[CONV-INDEX] ✅ Index chargé: {len(_get_ogma()._conv_index)} conversations")
        else:
            _get_ogma()._conv_index = {}
            print(f"[CONV-INDEX] ⚠️ Fichier index.json introuvable: {idx_path}")
    except Exception as e:
        print(f"[CONV-INDEX] ❌ Erreur chargement index: {e}")
        # TENTER RESTAURATION BACKUP AVANT RÉINITIALISATION
        backup_restored = _try_restore_index_from_backup()
        if backup_restored:
            print(f"[CONV-INDEX] ✅ Index restauré depuis backup")
            return _get_ogma()._conv_index
        # Pas de backup - initialiser vide SANS sauvegarder
        print(f"[CONV-INDEX] ⚠️ Aucun backup, index vide (manuel: python repair_conversation_index.py)")
        _get_ogma()._conv_index = {}
    return _get_ogma()._conv_index


def _save_conversation_index() -> Tuple[bool, str]:
    """
    Sauvegarde l'index des conversations sur disque.
    Crée automatiquement un backup avant sauvegarde (rotation 5 backups max).
    """
    try:
        import json
        from datetime import datetime
        
        idx_path = DATA_DIR / 'conversations' / 'index.json'
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        
        # PROTECTION: Backup automatique AVANT sauvegarde
        if idx_path.exists():
            try:
                # Lire l'ancien index pour backup
                old_content = idx_path.read_text(encoding='utf-8-sig').strip()
                if old_content and old_content != '{}':
                    # Créer backup avec timestamp
                    backup_name = f"index_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = idx_path.parent / backup_name
                    backup_path.write_text(old_content, encoding='utf-8')
                    
                    # Rotation: garder max 5 backups les plus récents
                    backups = sorted(idx_path.parent.glob('index_backup_*.json'), reverse=True)
                    for old_backup in backups[5:]:  # Supprimer au-delà de 5
                        old_backup.unlink()
                        print(f"[CONV-INDEX-SAVE] 🗑️ Ancien backup supprimé: {old_backup.name}")
                    
                    print(f"[CONV-INDEX-SAVE] 💾 Backup créé: {backup_name}")
            except Exception as e:
                print(f"[CONV-INDEX-SAVE] ⚠️ Erreur création backup (non bloquant): {e}")
        
        # Sauvegarder le nouvel index
        payload = {"conversations": _get_conv_index()}
        idx_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return True, 'Index sauvegardé.'
    except Exception as e:
        return False, f'Erreur sauvegarde index: {e}'


def _make_conv_id() -> str:
    """Crée un identifiant unique horodaté pour une conversation."""
    try:
        import datetime, random
        ts = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        suf = hex(random.randint(0, 0xFFFF))[2:]
        return f"{ts}_{suf}"
    except Exception:
        return str(uuid.uuid4())


def _make_title_from_text(text: str) -> str:
    """Génère un titre inspiré du premier message + horodatage court."""
    try:
        import datetime
        t = (text or '').strip().splitlines()[0]
        # nettoie espaces et réduit
        t = re.sub(r"\s+", " ", t)
        if len(t) > 48:
            t = t[:48].rstrip() + '…'
        stamp = datetime.datetime.now().strftime('%d/%m %H:%M')
        return f"{t or 'Conversation'} — {stamp}"
    except Exception:
        return 'Conversation'


async def _generate_smart_title_from_history() -> str:
    """Génère un titre intelligent basé sur les 5 premières interactions."""
    try:
        import datetime
        from conversation_summarizer import summarizer
        
        # Récupère les 5 premières interactions (10 messages max: 5 user + 5 assistant)
        relevant_messages = []
        user_count = 0
        
        for msg in _get_ogma()._chat_history:
            if msg.get('role') in ('user', 'assistant'):
                relevant_messages.append(msg)
                if msg.get('role') == 'user':
                    user_count += 1
                    if user_count >= 5:  # Stop après 5 interactions utilisateur
                        break
        
        if len(relevant_messages) < 3:  # Pas assez de contenu
            return _make_title_from_text(_get_ogma()._chat_history[0].get('content', '') if _get_ogma()._chat_history else '')
        
        # Génère un résumé concis pour le titre
        title_prompt = """Génère un titre court (maximum 40 caractères) qui résume le sujet principal de cette conversation. 
        Le titre doit être informatif et concis, sans ponctuation finale.
        
        Conversation:
        """ + "\n".join([f"{m['role']}: {m['content'][:200]}" for m in relevant_messages])
        
        # Utilise le système de résumé existant
        if hasattr(summarizer, '_api_mgr') and summarizer._api_mgr:
            try:
                response = await summarizer._api_mgr.get_chat_completion_async([
                    {'role': 'user', 'content': title_prompt}
                ])
                
                if response and 'choices' in response:
                    smart_title = response['choices'][0]['message']['content'].strip()
                    # Nettoie et limite le titre
                    smart_title = smart_title.replace('"', '').replace("'", "")
                    if len(smart_title) > 40:
                        smart_title = smart_title[:37] + '…'
                    
                    # Ajoute l'horodatage
                    stamp = datetime.datetime.now().strftime('%d/%m %H:%M')
                    return f"{smart_title} — {stamp}"
            except Exception as e:
                print(f"Erreur génération titre intelligent: {e}")
        
        # Fallback : titre basique si l'API échoue
        return _make_title_from_text(relevant_messages[0].get('content', '') if relevant_messages else '')
        
    except Exception:
        return 'Conversation'


def _schedule_smart_title_generation(conv_id: str):
    """
    Génère un titre intelligent via l'Archiviste après 5 interactions
    """
    try:
        conv_index = _get_conv_index()
        chat_history = _get_chat_history()
        if conv_id in conv_index and len(chat_history) >= 10:  # 5 interactions = 10 messages
            print("BRAIN [SMART-TITLE] Génération titre intelligent via Archiviste...")
            import asyncio
            asyncio.create_task(_generate_smart_title_async(conv_id))
        else:
            # Reset du flag si pas assez d'interactions
            conv_index = _get_conv_index()
            if conv_id in conv_index:
                _get_ogma()._conv_index[conv_id]['smart_title_pending'] = False
    except Exception as e:
        print(f"ERROR [SMART-TITLE] Erreur programmation titre: {e}")
        conv_index = _get_conv_index()
        if conv_id in conv_index:
            _get_ogma()._conv_index[conv_id]['smart_title_pending'] = False


async def _generate_smart_title_async(conv_id: str):
    """Génère un titre intelligent en utilisant l'Archiviste"""
    try:
        
        archiviste = _ensure_archiviste_controller()
        if not archiviste:
            print("WARN [SMART-TITLE] Archiviste non disponible")
            return
            
        # Récupérer les premiers messages pour contexte
        recent_messages = [m for m in _get_ogma()._chat_history[-10:] if m.get('role') in ('user', 'assistant')]
        
        if len(recent_messages) < 4:
            return
            
        # Construire le contexte pour l'Archiviste
        context = ""
        for msg in recent_messages:
            role = "USER Utilisateur" if msg['role'] == 'user' else "🌙 Luna"
            # Tronquer le contenu
            content = msg['content'][:200] if len(msg['content']) > 200 else msg['content']
            context += f"{role}: {content}...\n\n"
        
        prompt = f"""Analyse cette conversation et génère un titre concis qui résume le VRAI sujet discuté entre l'utilisateur et Luna.

IGNORE complètement :
- Les instructions techniques
- Les métadonnées temporelles  
- Les préfixes d'injection
- Les balises système

CONCENTRE-TOI uniquement sur le contenu conversationnel authentique.

Conversation:
{context}

Génère un titre descriptif de 3-8 mots maximum.
Réponds UNIQUEMENT avec le titre, sans guillemets."""

        messages = [{"role": "user", "content": prompt}]
        
        response, error = await archiviste.call_chat_api(
            messages=messages,
            max_tokens=50,
            temperature=0.3,  # Plus déterministe pour les titres
            is_json=False
        )
        
        if error or not response:
            print(f"ERROR [SMART-TITLE] Échec Archiviste: {error}")
            return
            
        # Extraire le titre
        if isinstance(response, dict) and 'content' in response:
            title = response['content'].strip()
        elif isinstance(response, str):
            title = response.strip()
        else:
            print(f"ERROR [SMART-TITLE] Format réponse inattendu: {type(response)}")
            return
            
        # Nettoyer le titre
        title = title.replace('"', '').replace("'", '').strip()
        if len(title) > 60:
            title = title[:57] + "..."
            
        if title and len(title) > 3:
            # Mettre à jour le titre dans l'index
            conv_index = _get_conv_index()
            if conv_id in conv_index:
                old_title = _get_ogma()._conv_index[conv_id]['title']
                _get_ogma()._conv_index[conv_id]['title'] = title
                _get_ogma()._conv_index[conv_id]['smart_title_pending'] = False
                _get_ogma()._conv_index[conv_id]['auto_title'] = False
                
                # Sauvegarder l'index
                _save_conversation_index()
                
                print(f"OK [SMART-TITLE] Titre mis à jour: '{old_title}' → '{title}'")
                
                # Notifier l'interface si possible
                try:
                    _notify_safe(f"EDIT Titre intelligent: {title}", type='info')
                except:
                    pass
        else:
            print("WARN [SMART-TITLE] Titre généré vide ou trop court")
            
    except Exception as e:
        print(f"ERROR [SMART-TITLE] Erreur génération: {e}")
    finally:
        # Reset du flag en cas d'erreur
        conv_index = _get_conv_index()
        if conv_id in conv_index:
            _get_ogma()._conv_index[conv_id]['smart_title_pending'] = False


async def _regenerate_title_manual(conv_id: str) -> bool:
    """Régénère manuellement le titre d'une conversation via l'IA principale."""
    try:
        print(f"[MANUAL-TITLE] SEARCH Début régénération pour conversation: {conv_id}")
        
        if conv_id not in _get_conv_index():
            print(f"[MANUAL-TITLE] ERROR Conversation {conv_id} non trouvée dans l'index")
            return False
            
        # Charger la conversation pour analyser le contenu
        conv_path = DATA_DIR / 'conversations' / f'{conv_id}.json'
        if not conv_path.exists():
            print(f"[MANUAL-TITLE] ERROR Fichier conversation non trouvé: {conv_path}")
            return False
            
        print(f"[MANUAL-TITLE] PAGE Chargement du fichier: {conv_path}")
        import json
        conv_data = json.loads(conv_path.read_text(encoding='utf-8'))
        
        # Prendre les 5 dernières interactions (max 10 messages)
        relevant_messages = [msg for msg in conv_data if msg.get('role') in ('user', 'assistant')][-10:]
        print(f"[MANUAL-TITLE] STATS {len(relevant_messages)} messages trouvés pour analyse")
        
        if len(relevant_messages) < 2:
            print(f"[MANUAL-TITLE] ERROR Pas assez de messages ({len(relevant_messages)}) pour générer un titre")
            return False
        
        # Construire le contexte
        context = ""
        for msg in relevant_messages:
            role = "Utilisateur" if msg['role'] == 'user' else "Luna"
            content = msg['content'][:150] if len(msg['content']) > 150 else msg['content']
            context += f"{role}: {content}...\n"
        
        print(f"[MANUAL-TITLE] EDIT Contexte construit: {len(context)} chars")
        print(f"[MANUAL-TITLE] EDIT Aperçu contexte: {context[:200]}...")
        
        # Prompt pour l'IA principale
        prompt = f"""Génère un titre court et précis (3-7 mots) qui résume le sujet principal de cette conversation.

Conversation:
{context}

Réponds UNIQUEMENT avec le titre, sans guillemets ni ponctuation finale."""

        print(f"[MANUAL-TITLE] AI Appel à l'IA principale...")
        # Utiliser l'IA principale (chat_controller)
        ctrl = _ensure_chat_controller()
        messages = [{"role": "user", "content": prompt}]
        
        response, error = await ctrl.call_chat_api(
            messages=messages,
            max_tokens=30,
            context_length=512,
            temperature=0.2,
            is_json=False
        )
        
        print(f"[MANUAL-TITLE] 📤 Réponse IA: '{response}', Erreur: '{error}'")
        
        if error or not response:
            print(f"ERROR [MANUAL-TITLE] Échec IA principale: {error}")
            return False
        
        # Nettoyer et valider le titre
        title = str(response).strip().replace('"', '').replace("'", '')
        if len(title) > 50:
            title = title[:47] + "..."
        
        print(f"[MANUAL-TITLE] 🧹 Titre nettoyé: '{title}' (longueur: {len(title)})")
        
        if len(title) > 3:
            # Mettre à jour le titre
            old_title = _get_ogma()._conv_index[conv_id]['title']
            _get_ogma()._conv_index[conv_id]['title'] = title
            _get_ogma()._conv_index[conv_id]['auto_title'] = False
            
            _save_conversation_index()
            
            print(f"OK [MANUAL-TITLE] Titre régénéré: '{old_title}' → '{title}'")
            _notify_safe(f"UPDATE Nouveau titre: {title}", type='positive')
            
            # Mettre à jour la sidebar avec la conversation modifiée
            if _get_ogma()._sidebar_render_cb:
                print(f"[MANUAL-TITLE] UPDATE Rafraîchissement sidebar pour: {conv_id}")
                _get_ogma()._sidebar_render_cb(conv_id)
            else:
                print(f"[MANUAL-TITLE] WARN Pas de callback sidebar disponible")
                
            return True
            
        return False
        
    except Exception as e:
        print(f"ERROR [MANUAL-TITLE] Erreur régénération: {e}")
        _notify_safe("ERROR Erreur lors de la régénération du titre", type='negative')
        return False



async def _check_progressive_summarization():
    """Vérifie si une résumisation progressive doit être déclenchée"""
    try:
        from conversation_summarizer import summarizer

        # Filtrer les messages utilisateur/assistant
        valid_messages = [m for m in _get_ogma()._chat_history if m.get('role') in ('user', 'assistant')]
        message_count = len(valid_messages)

        # Vérifier si on doit résumer
        if summarizer.should_summarize(message_count):
            print(f"BRAIN [SUMMARIZER] Déclenchement résumisation progressive ({message_count} messages)")

            # Protection anti-crash: timeout et gestion d'erreurs robuste
            try:
                # Timeout de 30 secondes pour éviter les blocages
                summaries, recent_messages = await asyncio.wait_for(
                    summarizer.optimize_conversation_history(valid_messages),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                print(f"ERROR [SUMMARIZER] Timeout après 30s - abandon résumisation")
                return  # Abandon en cas de timeout
            except Exception as summarizer_error:
                print(f"ERROR [SUMMARIZER] Erreur pendant résumisation: {summarizer_error}")
                return  # Abandon en cas d'erreur

            if summaries:
                # Remplacer l'historique IA par les résumés + messages récents
                original_count = len(valid_messages)

                # Reconstruire l'historique IA avec résumés + messages récents
                new_history = []

                # Préserver les messages système en début
                for msg in _get_ogma()._chat_history:
                    if msg.get('role') == 'system':
                        new_history.append(msg)
                    else:
                        break

                # Ajouter les résumés comme messages système
                for i, summary in enumerate(summaries):
                    from datetime import datetime
                    new_history.append({
                        'role': 'system',
                        'content': f"[RÉSUMÉ #{i+1}] {summary}",
                        'is_summary': True,
                        'timestamp': datetime.now().isoformat()
                    })

                # Ajouter les messages récents
                new_history.extend(recent_messages)

                # ✅ NOUVEAU : Remplacer UNIQUEMENT l'historique IA
                # L'historique UI (_chat_history_ui) reste INTACT avec tous les messages originaux
                _get_ogma()._chat_history[:] = new_history

                reduction = original_count - len(recent_messages)
                print(f"OK [SUMMARIZER] Historique IA optimisé: {reduction} messages → {len(summaries)} résumés")
                print(f"STATS [SUMMARIZER] IA - Avant: {original_count} messages, Après: {len(recent_messages)} + {len(summaries)} résumés")
                print(f"INFO [SUMMARIZER] UI - Historique complet préservé: {len(_get_ogma()._chat_history_ui)} messages")

    except Exception as e:
        print(f"ERROR [SUMMARIZER] Erreur résumisation progressive: {e}")


def _persist_conversation(initial_text_for_title: Optional[str] = None) -> None:
    """Sauvegarde l'historique courant dans data/conversations/<id>.json et met à jour l'index."""
    try:
        # Assure l'ID et l'entrée d'index
        current_id = _get_current_conversation_id()
        if not current_id:
            _get_ogma()._current_conversation_id = _make_conv_id()
        cid = _get_current_conversation_id()
        # Met à jour/Crée l'entrée index
        from datetime import datetime
        now_iso = datetime.now().isoformat(timespec='seconds')
        conv_index = _get_conv_index()
        if cid not in conv_index:
            title = _make_title_from_text(initial_text_for_title or '')
            _get_ogma()._conv_index[cid] = {
                'id': cid,
                'title': title,
                'created': now_iso,
                'updated': now_iso,
                'message_count': len(_get_ogma()._chat_history_ui),  # ✅ Utiliser _chat_history_ui
                'auto_title': True,
                'smart_title_pending': False,
            }
        else:
            _get_ogma()._conv_index[cid]['updated'] = now_iso
            _get_ogma()._conv_index[cid]['message_count'] = len(_get_ogma()._chat_history_ui)  # ✅ Utiliser _chat_history_ui

            # 🆕 NOUVEAU: Marque pour génération d'un titre intelligent après 5 interactions
            user_messages = len([m for m in _get_ogma()._chat_history_ui if m.get('role') == 'user'])  # ✅ Utiliser _chat_history_ui
            if (_get_ogma()._conv_index[cid].get('auto_title', True) and
                user_messages >= 5 and
                not _get_ogma()._conv_index[cid].get('smart_title_pending', False)):

                _get_ogma()._conv_index[cid]['smart_title_pending'] = True
                # Planifie la génération du titre intelligent de manière asynchrone
                from nicegui_client_guard import safe_timer_callback
                ui.timer(0.1, safe_timer_callback(lambda: _schedule_smart_title_generation(cid)), once=True)
            # Ne change pas le titre automatiquement si déjà défini par l'utilisateur
        # Écrit le fichier JSON d'historique - SEULS les échanges utilisateur/assistant
        path = DATA_DIR / 'conversations' / f'{cid}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        import json

        # ✅ SAUVEGARDER _chat_history_ui (historique complet) au lieu de _chat_history (résumé)
        payload = []
        for m in _get_ogma()._chat_history_ui:
            role = m.get('role')
            content = m.get('content')
            
            # Ne conserver que user et assistant (exclure system, memories, injections, etc.)
            if role in ('user', 'assistant') and isinstance(content, str):
                # Pour l'utilisateur, garder le contenu original avec marqueurs temporels
                # (ne plus utiliser display_content pour préserver l'horodatage)
                payload.append({
                    'role': role, 
                    'content': content,
                    # Optionnel: ajouter metadata utile
                    'timestamp': m.get('timestamp'),
                    'memorized': m.get('memorized', False)
                })
        
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        _save_conversation_index()
        # Rafraîchit la barre latérale si disponible
        try:
            if _get_ogma()._sidebar_render_cb:
                _get_ogma()._sidebar_render_cb(_current_conversation_id)
        except Exception:
            pass
    except Exception as e:
        _notify_safe(f"Erreur sauvegarde conversation: {e}", 'warning')


async def _maybe_update_conv_title() -> None:
    """Après au moins 2 messages (user+assistant), proposer un titre contextualisé (IA → fallback heuristique)."""
    try:
        if _get_ogma()._title_updating:
            return
        cid = _get_ogma()._current_conversation_id
        if not cid or cid not in _get_ogma()._conv_index:
            return
        entry = _get_ogma()._conv_index[cid]
        if not entry.get('auto_title', True):
            return
        # Compter messages significatifs
        msgs = [m for m in _get_ogma()._chat_history if m.get('role') in ('user','assistant') and isinstance(m.get('content'), str)]
        if len(msgs) < 2:
            return
        _get_ogma()._title_updating = True
        # Préparer un corpus compact (derniers 6 messages max)
        recent = msgs[-6:]
        def _compact_text(s: str, max_len: int = 220) -> str:
            s = re.sub(r"\s+", " ", s or '').strip()
            return s if len(s) <= max_len else (s[:max_len].rstrip() + '…')
        convo = "\n".join(f"- {m['role']}: {_compact_text(m['content'])}" for m in recent)

        # Appel IA (Archiviste si dispo sinon Chat)
        title_resp: Optional[str] = None
        try:
            ctrl = _ensure_archiviste_controller() or _ensure_chat_controller()
            sys_prompt = (
                "Tu es un assistant qui génère des titres courts et précis. "
                "Donne un seul titre en français qui résume le sujet de la conversation ci-dessous. "
                "Contraintes: 5 à 8 mots, pas de guillemets, pas d'émojis, pas de point final, pas de salutations."
            )
            user_prompt = f"Conversation (du plus ancien au plus récent):\n{convo}\n\nTitre:"
            messages = [
                { 'role': 'system', 'content': sys_prompt },
                { 'role': 'user', 'content': user_prompt },
            ]
            reply, err = await ctrl.call_chat_api(messages=messages, max_tokens=64, context_length=1024, temperature=0.2, is_json=False)
            if not err and reply:
                title_resp = str(reply).strip()
        except Exception:
            title_resp = None

        # Nettoyage et fallback
        def _cleanup_title(t: str) -> str:
            t = t.strip().strip('"\'\u201c\u201d')  # guillemets
            t = re.sub(r"[\s\.\!\?]+$", "", t)  # ponctuation finale
            t = re.sub(r"\s+", " ", t)
            # clamp longueur
            if len(t) > 64:
                t = t[:64].rstrip() + '…'
            return t or 'Conversation'

        def _heuristic_title() -> str:
            # Retire salutations communes et prend un fragment significatif
            txt = " ".join(m.get('content','') for m in recent)
            txt = re.sub(r"\b(salut|bonjour|bonsoir|coucou|hello|hi)\b[\,\!\s]*", " ", txt, flags=re.IGNORECASE)
            txt = re.sub(r"\b(comment ça va|ça va|tu vas bien|vous allez bien)\b[\?\!\s]*", " ", txt, flags=re.IGNORECASE)
            txt = re.sub(r"\s+", " ", txt).strip()
            if len(txt) > 56:
                txt = txt[:56].rstrip() + '…'
            import datetime as _dt
            stamp = _dt.datetime.now().strftime('%d/%m %H:%M')
            return f"{txt or 'Conversation'} — {stamp}"

        new_title = None
        if title_resp:
            new_title = _cleanup_title(title_resp)
        if not new_title or new_title.lower() in ('titre', 'conversation'):
            new_title = _heuristic_title()

        # Appliquer et sauvegarder
        if new_title and isinstance(new_title, str):
            entry['title'] = new_title
            entry['auto_title'] = False  # fige le titre proposé
            _save_conversation_index()
            try:
                if _get_ogma()._sidebar_render_cb:
                    _get_ogma()._sidebar_render_cb(_current_conversation_id)
            except Exception:
                pass
    finally:
        _get_ogma()._title_updating = False


def _render_full_history():
    """Ré-affiche l'historique courant dans la zone de conversation."""
    if _get_ogma()._chat_inner is None:
        return
    with _get_ogma()._chat_inner:
        _get_ogma()._chat_inner.clear()
        # ✅ UTILISER _chat_history_ui pour l'affichage (historique complet sans résumés)
        for i, m in enumerate(_get_ogma()._chat_history_ui):
            badges = ['mémorisé'] if m.get('memorized') else None
            _message(m.get('role', 'system'), m.get('content', ''), badges, message_index=i)


def _load_conversation(conv_id: str):
    """Charge une conversation depuis data/conversations/<id>.json et l'affiche."""

    # 🛡️ MAGIC PHRASE GUARD: Importer module protection
    from magic_phrase_guard import activate_loading_mode, deactivate_loading_mode_delayed, mark_message_as_historical

    try:
        # 🛡️ PROTECTION 1: Activer flag temporel
        activate_loading_mode()

        path = DATA_DIR / 'conversations' / f'{conv_id}.json'
        if not path.exists():
            _notify_safe("Conversation introuvable", 'warning')
            deactivate_loading_mode()  # Désactiver en cas d'erreur
            return

        import json
        raw = json.loads(path.read_text(encoding='utf-8'))
        new_hist: List[Dict] = []

        for msg in raw:
            role = msg.get('role')
            content = msg.get('content')
            display_content = msg.get('display_content')  # Préserver display_content
            memorized = msg.get('memorized', False)

            if role in ('user', 'assistant', 'system') and isinstance(content, str):
                entry = {'role': role, 'content': content, 'memorized': memorized}
                if display_content:  # Si display_content existe, l'inclure
                    entry['display_content'] = display_content

                # 🛡️ PROTECTION 2: Marquer message comme historique
                entry = mark_message_as_historical(entry)

                new_hist.append(entry)

        # 📚 NOUVELLE FONCTIONNALITÉ: Préparer la conversation pour injection différée
        # Au lieu d'injecter immédiatement, on prépare pour injection au prochain message
        _loaded_conversation = new_hist.copy()
        _loaded_conversation_filename = f"{conv_id}.json"
        _conversation_context_injected = False  # Réinitialiser le flag pour la nouvelle conversation
        _orchestration_injected = False  # Réinitialiser le flag d'orchestration cognitive

        # Mettre à jour les deux historiques et afficher (pour lecture seulement)
        _get_ogma()._chat_history = new_hist.copy()  # Pour l'IA (peut être résumé)
        _get_ogma()._chat_history_ui = new_hist.copy()  # Pour l'UI (toujours complet)
        _get_ogma()._current_conversation_id = conv_id
        _render_full_history()

        # Informer l'utilisateur que la conversation est prête mais pas encore injectée
        from datetime import datetime

        # Extraire la date de création depuis le nom du fichier (format: YYYY-MM-DD_HH-MM-SS)
        try:
            date_part = conv_id.split('_')[0]  # 2025-09-19
            time_part = conv_id.split('_')[1].replace('-', ':')  # 17:46:36
            conversation_date = f"{date_part} à {time_part}"
        except:
            conversation_date = "date inconnue"

        # Log de debug
        print(f"[CONVERSATION-LOAD] ✅ Conversation {conv_id} chargée ({len(new_hist)} messages marqués from_history)")
        print(f"[CONVERSATION-LOAD] 📅 Date: {conversation_date}, Flag injection: {_conversation_context_injected}")

        # Note: Pas de notification frontend pour éviter l'encombrement visuel
        # La conversation est chargée silencieusement pour navigation read-only

        # 🛡️ PROTECTION 1: Désactiver flag temporel après délai sécurité
        asyncio.create_task(deactivate_loading_mode_delayed())

    except Exception as e:
        _notify_safe(f"Erreur chargement conversation: {e}", 'negative')
        # 🛡️ Sécurité: désactiver flag même en cas d'erreur
        deactivate_loading_mode()


def _new_conversation():
    """Réinitialise l'historique pour démarrer une nouvelle conversation."""

    # 🛡️ MAGIC PHRASE GUARD: S'assurer que flag temporel est désactivé
    from magic_phrase_guard import deactivate_loading_mode
    deactivate_loading_mode()

    _get_ogma()._chat_history = []
    _get_ogma()._chat_history_ui = []
    _get_ogma()._current_conversation_id = None

    # 📚 Nettoyer le contexte de conversation chargée
    _loaded_conversation = None
    _loaded_conversation_filename = None
    _conversation_context_injected = False  # Réinitialiser le flag
    _orchestration_injected = False  # Réinitialiser le flag d'orchestration cognitive

    # 📖 BIOGRAPHIE PROFIL: Réinitialiser les noms injectés pour nouvelle conversation
    try:
        if _get_ogma()._biography_available:
            from extensions.biographie_profil import get_biography_magic_phrases
            biography_magic = get_biography_magic_phrases()
            if biography_magic:
                biography_magic.reset_conversation()
                print(f"[BIOGRAPHY-EXTENSION] 🔄 Injection automatique réinitialisée pour nouvelle conversation")
    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ERROR Erreur reset conversation: {e}")

    print(f"[NEW-CONVERSATION] 🆕 Nouvelle conversation démarrée - Protection phrases magiques réinitialisée")

    _render_full_history()

# NOTA: _format_datetime extrait vers utils/formatting_utils.py
# NOTA: _parse_thinking_format extrait vers utils/message_parsers.py
# NOTA: _parse_introspection_format extrait vers utils/message_parsers.py

def _sidebar():
    """Barre latérale listant les conversations (type ChatGPT)."""
    # Charger l'index depuis le disque au démarrage
    _load_conversation_index()
    with ui.element('aside').classes('sidebar'):
        # Actions disponibles dans l'entête
        def do_rename():
            cid = _get_ogma()._current_conversation_id
            if not cid or cid not in _get_ogma()._conv_index:
                _notify_safe('Aucune conversation sélectionnée.', 'warning')
                return
            d = ui.dialog()
            with d, ui.card().classes('popup-content'):
                ui.label('Renommer la conversation').classes('popup-title')
                new_title = ui.input(label='Nouveau titre', value=_get_ogma()._conv_index[cid].get('title', '')).classes('form-input')
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=d.close).classes('action-button')
                    def _apply():
                        title = (new_title.value or '').strip() or 'Sans titre'
                        _get_ogma()._conv_index[cid]['title'] = title
                        _get_ogma()._conv_index[cid]['auto_title'] = False
                        ok, msg = _save_conversation_index()
                        _notify_safe(msg, 'positive' if ok else 'warning')
                        d.close()
                        try:
                            if _get_ogma()._sidebar_render_cb:
                                _get_ogma()._sidebar_render_cb(cid)
                            else:
                                render_items(cid)
                        except Exception:
                            render_items(cid)
                    ui.button('Renommer', on_click=_apply).classes('send-button')
            d.open()

        def do_delete():
            cid = _get_ogma()._current_conversation_id
            if not cid or cid not in _get_ogma()._conv_index:
                _notify_safe('Aucune conversation sélectionnée.', 'warning')
                return
            d = ui.dialog()
            with d, ui.card().classes('popup-content'):
                ui.label('Supprimer la conversation ?').classes('popup-title')
                ui.label("Cette action est définitive.").classes('text-muted')
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=d.close).classes('action-button')
                    def _apply_delete():
                        try:
                            # Supprimer la mémoire associée si elle existe
                            if _is_conversation_memorized(cid):
                                _delete_memorized_conversation(cid)
                            
                            path = DATA_DIR / 'conversations' / f'{cid}.json'
                            if path.exists():
                                path.unlink()
                            _get_ogma()._conv_index.pop(cid, None)
                            ok, msg = _save_conversation_index()
                            _notify_safe(msg, 'positive' if ok else 'warning')
                            d.close()
                            _new_conversation()
                            try:
                                if _get_ogma()._sidebar_render_cb:
                                    _get_ogma()._sidebar_render_cb(None)
                                else:
                                    render_items(None)
                            except Exception:
                                render_items(None)
                        except Exception as e:
                            _notify_safe(f'Erreur suppression: {e}', 'negative')
                    ui.button('Supprimer', on_click=_apply_delete).classes('send-button')
            d.open()

        def _show_magic_phrases_info():
            """Affiche l'overlay d'information sur les phrases magiques"""
            with ui.dialog() as magic_dialog, ui.card().style('''
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid var(--accent-gold);
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                border-radius: 12px;
                min-width: 600px;
                max-width: 800px;
                max-height: 80vh;
                overflow-y: auto;
                color: var(--text-primary);
            '''):
                # Header
                ui.label('ℹ️ Phrases Magiques OGMA').style('''
                    font-size: 20px;
                    font-weight: bold;
                    color: var(--accent-gold);
                    margin-bottom: 16px;
                    text-align: center;
                ''')

                ui.separator().style('background: var(--accent-gold); opacity: 0.3; margin: 16px 0;')

                # 📖 Journal de Bord
                ui.label('📖 Journal de Bord').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                journal_phrases = [
                    # Phrases UTILISATEUR
                    ("consulte le journal du [date YYYY-MM-DD]", "Affiche les entrées du journal pour une date précise"),
                    ("consulte le journal d'hier / d'aujourd'hui / de lundi", "Affiche les entrées du journal pour une date relative"),
                    ("consulte le journal de la semaine", "Affiche les entrées de la semaine en cours"),
                    ("montre le contexte du [date] / d'hier", "Affiche le contexte formaté d'une journée"),
                    ("journal recherche [terme]", "Recherche un terme dans toutes les entrées du journal"),
                    ("résume la semaine du [date]", "Génère un résumé des entrées de la semaine"),
                    ("résume le mois [YYYY-MM]", "Génère un résumé des entrées du mois"),
                    ("sauvegarde la conversation dans le journal", "Crée une entrée manuelle depuis la conversation actuelle"),
                    ("ouvre le journal d'hier / d'aujourd'hui", "Ouvre l'interface journal pour une date"),
                    ("journal affiche [filtre]", "Affiche entrées filtrées par critère"),
                    # Phrases IA (automatiques)
                    ("Injection automatique contexte matinal", "Luna reçoit automatiquement le journal du jour au premier message"),
                ]
                for phrase, description in journal_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 👤 Biographie Profil
                ui.label('👤 Biographie Profil').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                bio_phrases = [
                    ("il faut que je consulte la biographie de [prénom]", "L'IA consulte automatiquement la biographie d'une personne (phrase IA uniquement)"),
                    ("complète ma biographie / complète ma bio", "Génère le Volume 2 narratif de votre biographie"),
                    ("mets à jour ma biographie", "Régénère votre profil biographique avec les nouveaux souvenirs"),
                    ("enrichis mon profil", "Enrichit votre profil avec l'analyse des conversations récentes"),
                    ("Détection automatique prénom", "Injection automatique de la biographie lors de la première mention d'un prénom connu"),
                ]
                for phrase, description in bio_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 🧠 Cognitive Mirror (Introspection)
                ui.label('🧠 Miroir Cognitif (Introspection)').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                mirror_phrases = [
                    # Phrases UTILISATEUR (commandes directes)
                    ("il faut que tu réfléchisses", "Déclenche immédiatement une session d'introspection (prioritaire)"),
                    ("lance une introspection", "Démarre une phase de réflexion intérieure avec le subconscient"),
                    ("déclenche une introspection", "Active la conversation entre l'IA et son subconscient"),
                    ("active la subconscience", "Démarre le monitoring d'inactivité et l'introspection automatique"),
                    ("réfléchis en profondeur", "Lance une analyse métacognitive approfondie"),
                    ("arrête de réfléchir", "Interrompt l'introspection - L'IA génère organiquement une synthèse"),
                    ("stop la réflexion", "Termine la réflexion - Synthèse organique générée par l'IA"),
                    # Phrases IA (auto-déclenchement)
                    ("il faut que je réfléchisse sur : [thème]", "Luna démarre auto-introspection sur un sujet (phrase IA)"),
                    # UI
                    ("Bouton ⏹ dans zone introspection", "Arrêt d'urgence avec génération organique de synthèse"),
                    ("Déclenchement automatique inactivité", "Introspection automatique après période sans interaction"),
                ]
                for phrase, description in mirror_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 💾 Mémorisation
                ui.label('💾 Mémorisation').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                memory_phrases = [
                    # Phrases IA (Luna mémorise)
                    ("il faut que je me souvienne de ça: [texte]", "Luna mémorise explicitement un élément important (phrase IA)"),
                    # Phrases UTILISATEUR
                    ("mémorise ça: [texte]", "Commande utilisateur pour sauvegarder un souvenir avec haute importance"),
                    ("mémorises ça: [texte]", "Variante impérative pour mémorisation"),
                    ("souviens-toi de ça: [texte]", "Commande utilisateur pour créer un souvenir mémorable"),
                    ("je vais mémoriser [texte]", "Mémorisation différée par l'utilisateur"),
                    ("je dois mémoriser [texte]", "Mémorisation prioritaire par l'utilisateur"),
                    ("lis le souvenir [usr-xxx...]", "Affiche le contenu complet d'un souvenir par son ID"),
                    ("consulte le souvenir [usr-xxx...]", "Charge et affiche un souvenir spécifique depuis la base"),
                ]
                for phrase, description in memory_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 📚 Conversations Archivées
                ui.label('📚 Conversations Archivées').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                archive_phrases = [
                    ("va lire la conversation [nom.json]", "Charge une conversation archivée pour consultation"),
                    ("lis la conversation [nom]", "Affiche le contenu d'une conversation sauvegardée"),
                    ("charge la conversation [nom]", "Ouvre une conversation depuis l'historique archivé"),
                    ("ouvre la conversation [nom]", "Accède à une conversation enregistrée"),
                ]
                for phrase, description in archive_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 🌐 Recherche Internet (Web Navigator)
                ui.label('🌐 Recherche Internet').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                web_phrases = [
                    # Commandes UTILISATEUR slash
                    ("/web [terme]", "Recherche web générale avec Serper API"),
                    ("/news [sujet]", "Recherche d'actualités récentes"),
                    ("/image [description]", "Recherche d'images avec description"),
                    # Phrases UTILISATEUR naturelles
                    ("cherche sur internet [terme]", "Phrase naturelle pour recherche web"),
                    ("recherche sur le web [sujet]", "Demande de recherche en langage naturel"),
                    ("trouve sur internet [information]", "Recherche d'information spécifique"),
                    ("regarde sur google [terme]", "Recherche via phrase familière"),
                    ("actualités sur [sujet]", "Recherche de news sur un sujet précis"),
                    ("recherche des images de [description]", "Recherche d'images descriptive"),
                    # Phrases IA (auto-déclenchement)
                    ("il faut que je recherche sur le net", "Luna auto-déclenche recherche web (phrase IA)"),
                    ("il faut que je cherche sur internet", "Auto-recherche par Luna dans ses réponses (phrase IA)"),
                    ("je dois vérifier sur le web", "Vérification automatique par Luna (phrase IA)"),
                ]
                for phrase, description in web_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 👁️ Perception Visuelle (Webcam)
                ui.label('👁️ Perception Visuelle').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                perception_phrases = [
                    # Phrases IA (Luna active/désactive webcam)
                    ("il faut que je te vois", "Luna active automatiquement la webcam pour vous voir (phrase IA)"),
                    ("je veux te voir", "Luna démarre la perception visuelle en temps réel (phrase IA)"),
                    ("il faut que je vois", "Luna active l'extension Perception pour vision webcam (phrase IA)"),
                    ("je n'ai plus besoin de te voir", "Luna désactive la webcam automatiquement (phrase IA)"),
                    ("je peux arrêter de te voir", "Luna coupe la perception visuelle (phrase IA)"),
                    ("je ferme ma vision", "Luna termine la session de perception (phrase IA)"),
                    # Phrases UTILISATEUR (commandes directes)
                    ("active la webcam", "Commande utilisateur pour démarrer perception visuelle"),
                    ("désactive la webcam", "Commande utilisateur pour arrêter perception visuelle"),
                    # Triggers automatiques
                    ("Détection automatique demande visuelle", "Si Luna a besoin de voir, elle active automatiquement"),
                ]
                for phrase, description in perception_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 🎨 Génération Images
                ui.label('🎨 Génération Images').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                image_phrases = [
                    ("je dois créer une image de : [description]", "Luna génère une image via Pollinations.AI (réponse IA)"),
                    ("il faut que je crée une image de : [description]", "Variante phrase magique génération image (réponse IA)"),
                    ("je vais créer une image de : [description]", "Variante phrase magique génération image (réponse IA)"),
                    ("je dois générer une image de : [description]", "Variante phrase magique génération image (réponse IA)"),
                ]
                for phrase, description in image_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 💭 Souvenirs Contextuels
                ui.label('💭 Souvenirs Contextuels').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                recall_phrases = [
                    # Phrases UTILISATEUR (expressions temporelles)
                    ("il y a [X] jours / [X] semaines", "Recherche souvenirs par période relative (ex: il y a 3 jours)"),
                    ("hier / avant-hier / aujourd'hui", "Recherche souvenirs par date simple"),
                    ("la semaine dernière / cette semaine", "Recherche souvenirs par période nommée"),
                    ("le mois dernier / il y a [X] mois", "Recherche souvenirs du mois précédent ou relatif"),
                    ("quand on a parlé de [sujet]", "Recherche souvenirs par conversation thématique"),
                    ("tu te souviens de [événement]", "Trigger recherche mémorielle contextuelle"),
                    ("tu te rappelles quand [contexte]", "Recherche souvenir par contexte événementiel"),
                    ("notre conversation sur [thème]", "Recherche discussions passées par sujet"),
                    ("ce qu'on a dit sur [sujet]", "Recherche contenu conversationnel thématique"),
                    ("rappelle-moi ce que [contexte]", "Demande explicite rappel mémoriel"),
                    # Détection automatique
                    ("Injection automatique souvenirs pertinents", "Système injecte souvenirs contextuels selon requête temporelle"),
                ]
                for phrase, description in recall_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.2; margin: 16px 0;')

                # 📝 Éditeur Docs
                ui.label('📝 Éditeur Docs').style('font-size: 16px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                filewriter_phrases = [
                    # Commande UTILISATEUR slash
                    ("/doc [titre document]", "Commande slash pour créer un document markdown"),
                    # Phrases UTILISATEUR naturelles
                    ("crée un document markdown sur [sujet]", "Génération document .md avec titre et contenu"),
                    ("écris un fichier markdown qui [description]", "Création fichier .md selon spécification"),
                    ("rédige un .md sur [thème]", "Génération document markdown thématique"),
                    ("fais-moi un fichier markdown pour [usage]", "Création document .md avec usage précis"),
                    ("génère un document markdown de [type]", "Production automatique document .md typé"),
                    ("écris un .md qui [objectif]", "Création fichier avec objectif défini"),
                    # Détection automatique
                    ("Détection automatique demande .md", "Système détecte intention création document et propose génération"),
                ]
                for phrase, description in filewriter_phrases:
                    with ui.row().style('margin: 6px 0; gap: 8px;'):
                        ui.label('•').style('color: var(--accent-gold); font-weight: bold;')
                        ui.label(f'"{phrase}"').style('font-family: monospace; color: #f5f5dc;')
                    ui.label(f'   → {description}').style('color: #999; font-size: 12px; margin-left: 20px;')

                ui.separator().style('background: var(--accent-gold); opacity: 0.3; margin: 16px 0;')

                # Note explicative
                ui.label('💡 Note').style('font-size: 14px; font-weight: bold; color: var(--accent-gold); margin-top: 12px;')
                ui.label('Les phrases magiques sont détectées automatiquement dans vos messages. Utilisez-les en langage naturel pour déclencher des fonctionnalités avancées d\'OGMA sans passer par l\'interface.').style('color: #ccc; font-size: 13px; line-height: 1.6;')

                # Bouton fermer
                ui.button('Fermer', on_click=lambda: magic_dialog.close()).classes('send-button').style('margin-top: 16px; width: 100%;')

            magic_dialog.open()

        with ui.element('div').classes('sidebar-header').style('display: flex; align-items: center; gap: 8px; justify-content: space-between;'):
            # Groupe de boutons à gauche
            with ui.element('div').style('display: flex; gap: 8px;'):
                ui.button(icon='add', on_click=_new_conversation).classes('header-btn')
                ui.button(icon='edit', on_click=do_rename).classes('header-btn')
                ui.button(icon='delete', on_click=do_delete).classes('header-btn')

            # Bouton info à l'extrême droite
            ui.button('ⓘ', on_click=_show_magic_phrases_info).props('flat dense').style('''
                font-size: 18px;
                color: white !important;
                min-width: 24px;
                padding: 4px;
                opacity: 0.7;
                background: transparent !important;
            ''').tooltip('Phrases magiques OGMA')
        list_container = ui.element('div').classes('sidebar-list').style(
            'max-height: 70vh; overflow-y: auto; overflow-x: hidden; border-right: 1px solid var(--border-color, #333);'
        )
        def render_items(active_id: Optional[str] = None):
            list_container.clear()
            with list_container:
                try:
                    items = sorted(_get_conv_index().values(), key=lambda x: x.get('created', ''), reverse=True)
                except Exception:
                    items = list(_get_conv_index().values())
                for item in items:
                    cid = item.get('id')
                    if not cid:
                        continue
                    title = (item.get('title') or cid)[:120]
                    
                    # Préparer les données pour le tooltip
                    created = item.get('created', '')
                    updated = item.get('updated', '')
                    
                    def _on_click(conv_id=cid):
                        _load_conversation(conv_id)
                        try:
                            if _get_ogma()._sidebar_render_cb:
                                _get_ogma()._sidebar_render_cb(conv_id)
                            else:
                                render_items(conv_id)
                        except Exception:
                            render_items(conv_id)
                    
                    row = ui.element('div').classes('sidebar-item')
                    if active_id and cid == active_id:
                        row.classes(add='active')
                    # NE PAS ajouter row.on('click') ici - on va gérer les clics spécifiquement
                    
                    # Créer le tooltip avec la méthode NiceGUI native
                    created = item.get('created', '')
                    updated = item.get('updated', '')
                    tooltip_lines = []
                    
                    if created:
                        # format_datetime importé depuis utils.formatting_utils
                        tooltip_lines.append(f"Créé : {format_datetime(created)}")
                    if updated and updated != created:
                        tooltip_lines.append(f"Modifié : {format_datetime(updated)}")
                    
                    if tooltip_lines:
                        tooltip_text = " | ".join(tooltip_lines)  # Une seule ligne séparée par |
                        row.tooltip(tooltip_text)
                    
                    with row:
                        # Container flex pour icône + titre
                        with ui.row().classes('items-center gap-2 w-full'):
                            # Icône de mémorisation - zone cliquable indépendante
                            is_memorized = _is_conversation_memorized(cid)
                            
                            def _on_memorize_click(conv_id=cid, conv_title=title):
                                if _is_conversation_memorized(conv_id):
                                    # Conversation déjà mémorisée → la supprimer
                                    _delete_memorized_conversation(conv_id)
                                    _mark_conversation_memorized(conv_id, False)
                                    _trigger_memory_update()  # Actualiser la liste des mémoires
                                    # Recharger la sidebar pour mettre à jour l'icône
                                    if _get_ogma()._sidebar_render_cb:
                                        _get_ogma()._sidebar_render_cb(_get_ogma()._current_conversation_id)
                                    ui.notify(f'💔 Conversation "{conv_title}" supprimée de la mémoire', type='info')
                                else:
                                    # Vérifier la limite de 15 conversations mémorisées
                                    memorized_count = _count_memorized_conversations()
                                    if memorized_count >= 15:
                                        ui.notify('WARN Limite de 15 conversations mémorisées atteinte. Supprimez-en une avant d\'en ajouter.', type='warning')
                                    else:
                                        _memorization_popup(conv_id, conv_title)
                            
                            # Style et symbole selon l'état : normale (gris) ou mémorisée (cercle orange)
                            if is_memorized:
                                memory_symbol = '●'  # Cercle plein orange
                                icon_style = (
                                    'padding: 4px; min-width: 20px; height: 20px; border-radius: 4px; '
                                    'background: rgba(128, 128, 128, 0.2); border: 1px solid #666; color: #FF8C00 !important;'
                                )
                            else:
                                memory_symbol = '○'  # Cercle vide gris
                                icon_style = (
                                    'padding: 4px; min-width: 20px; height: 20px; border-radius: 4px; '
                                    'background: rgba(128, 128, 128, 0.2); border: 1px solid #666; color: #888888 !important;'
                                )
                            
                            memory_btn = ui.button(memory_symbol, on_click=_on_memorize_click).style(icon_style)
                            memory_btn.props('dense flat')
                            
                            # 🆕 NOUVEAU: Bouton pour copier le nom du fichier JSON
                            def _on_copy_filename(conv_id=cid):
                                filename = f"{conv_id}.json"
                                # Copie dans le presse-papiers (si possible) et affiche notification
                                try:
                                    # Tentative de copie dans le clipboard via JS
                                    ui.run_javascript(f'''
                                        navigator.clipboard.writeText("{filename}").then(() => {{
                                            console.log("Nom de fichier copié: {filename}");
                                        }}).catch(err => {{
                                            console.log("Échec copie clipboard:", err);
                                        }});
                                    ''')
                                    ui.notify(f'CLIPBOARD Copié: {filename}', type='positive')
                                except Exception:
                                    # Fallback: juste afficher le nom
                                    ui.notify(f'PAGE Nom du fichier: {filename}', type='info')
                            
                            copy_btn_style = (
                                'padding: 2px; min-width: 16px; height: 16px; border-radius: 50%; '
                                'background: transparent; border: none; color: #888888 !important; '
                                'font-size: 14px; line-height: 1;'
                            )
                            copy_btn = ui.button('•', on_click=_on_copy_filename).style(copy_btn_style)
                            copy_btn.props('dense flat')
                            copy_btn.tooltip(f'Copier le nom du fichier: {cid}.json')
                            
                            # UPDATE NOUVEAU: Bouton pour régénérer le titre via IA
                            def _on_regenerate_title(conv_id=cid):
                                print(f"[DEBUG-TITLE] UPDATE Bouton rafraîchissement cliqué pour conversation: {conv_id}")
                                
                                # Version simplifiée sans safe_timer_callback à cause des erreurs NiceGUI
                                async def do_regenerate():
                                    try:
                                        print(f"[DEBUG-TITLE] INIT Début régénération titre pour: {conv_id}")
                                        success = await _regenerate_title_manual(conv_id)
                                        if not success:
                                            print(f"[DEBUG-TITLE] ERROR Échec régénération pour: {conv_id}")
                                            _notify_safe("WARN Impossible de régénérer le titre", type='warning')
                                        else:
                                            print(f"[DEBUG-TITLE] OK Succès régénération pour: {conv_id}")
                                            # Forcer le rafraîchissement avec un petit délai
                                            import asyncio
                                            await asyncio.sleep(0.2)  # Petit délai pour que l'index soit bien sauvé
                                            if _get_ogma()._sidebar_render_cb:
                                                print(f"[DEBUG-TITLE] UPDATE Rafraîchissement sidebar forcé")
                                                _get_ogma()._sidebar_render_cb(conv_id)
                                    except Exception as e:
                                        print(f"[DEBUG-TITLE] ERROR Erreur dans do_regenerate: {e}")
                                        _notify_safe(f"ERROR Erreur: {e}", type='negative')
                                
                                # Utiliser directement asyncio au lieu de safe_timer_callback
                                import asyncio
                                asyncio.create_task(do_regenerate())
                            
                            refresh_btn_style = (
                                'padding: 2px; min-width: 18px; height: 18px; border-radius: 50%; '
                                'background: transparent; border: none; '
                                'color: #888888 !important; font-size: 13px; line-height: 1; '
                                'transition: all 0.2s ease; box-shadow: none;'
                            )
                            refresh_btn = ui.button('↻', on_click=_on_regenerate_title).style(refresh_btn_style)
                            refresh_btn.props('dense flat')
                            refresh_btn.tooltip('Régénérer le titre automatiquement')
                            
                            # Titre de la conversation - zone cliquable pour ouvrir la conversation
                            title_label = ui.label(title).classes('sidebar-item-title flex-1 cursor-pointer')
                            title_label.on('click', _on_click)
        # Expose render callback pour mises à jour temps réel
        def _cb(active_id: Optional[str] = None):
            # Recharger l'index depuis disque pour afficher les nouvelles conversations
            _load_conversation_index()
            render_items(active_id)
        _get_ogma()._sidebar_render_cb = _cb
        render_items(_get_ogma()._current_conversation_id)

        # Footer: uniquement pour l'espacement
        with ui.element('div').classes('sidebar-footer'):
            pass  # Garde la structure pour l'espacement


# ==============================================================================
# MÉMORISATION DES CONVERSATIONS
# ==============================================================================

async def _generate_conversation_summary(conversation_id: str) -> Optional[str]:
    """Génère un résumé de 150 mots max d'une conversation via l'IA."""
    try:
        # Charger la conversation
        from utils import load_conversation
        history = load_conversation(conversation_id)
        if not history:
            return None
        
        # Construire le texte de la conversation
        conversation_text = []
        for msg in history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if content.strip():
                conversation_text.append(f"{role.upper()}: {content}")
        
        if not conversation_text:
            return None
        
        full_text = "\n\n".join(conversation_text)
        
        # Utiliser l'IA pour générer le résumé
        ctrl = _ensure_chat_controller()
        if not ctrl:
            return None
        
        prompt = f"""Génère un résumé structuré de cette conversation en 150 mots maximum.

Format attendu :
**Sujet principal :** [theme principal]
**Points clés :** [liste des points importants]
**Contexte :** [informations contextuelles importantes]

Conversation à résumer :
{full_text}

IMPORTANT : Reste factuel, concis et limite-toi à 150 mots maximum."""

        messages = [{'role': 'user', 'content': prompt}]
        summary, error = await ctrl.call_chat_api(
            messages=messages, 
            max_tokens=300, 
            context_length=4096,  # Contexte suffisant pour analyser la conversation
            temperature=0.3, 
            is_json=False
        )
        
        if error:
            print(f"[CONV-SUMMARY] Erreur génération résumé: {error}")
            return None
        
        # Sécuriser contre les réponses non-string
        if summary:
            if isinstance(summary, list):
                summary = str(summary[0]) if len(summary) > 0 else ""
            elif not isinstance(summary, str):
                summary = str(summary)
            return summary.strip()
        return None
        
    except Exception as e:
        print(f"[CONV-SUMMARY] Exception: {e}")
        return None


async def _memorize_conversation(conversation_id: str, summary: str) -> bool:
    """Mémorise le résumé d'une conversation dans le système FAISS."""
    try:
        mm = _ensure_memory_manager()
        if not mm:
            return False
        
        # Créer ID mémoire unique
        memory_id = f"conv-{conversation_id}"
        
        # Préparer le contenu enrichi pour la mémoire
        from utils import load_conversations_index
        index = load_conversations_index()
        conv_data = index.get('conversations', {}).get(conversation_id, {})
        
        title = conv_data.get('title', conversation_id)
        created = conv_data.get('created', '')
        
        enriched_content = f"""RÉSUMÉ DE CONVERSATION
Titre: {title}
Date: {created[:10] if created else 'inconnue'}
ID: {conversation_id}

{summary}"""
        
        # Mémoriser avec scoring IA Principale
        chat_ctrl = _ensure_chat_controller()
        success = await mm.add_memory(
            memory_id, 
            enriched_content,
            chat_controller=chat_ctrl,
            conversation_context=f"Résumé de conversation avec {len(conv_data.get('messages', []))} messages",
            interlocutor="Yohan"
        )
        
        if success:
            # Marquer la conversation comme mémorisée dans l'index
            _mark_conversation_memorized(conversation_id, True)
            print(f"[CONV-MEMORY] Conversation {conversation_id} mémorisée")
        
        return success
        
    except Exception as e:
        print(f"[CONV-MEMORY] Erreur mémorisation: {e}")
        return False


def _mark_conversation_memorized(conversation_id: str, memorized: bool):
    """Marque une conversation comme mémorisée dans l'index."""
    conv_index = _get_conv_index()
    if conversation_id in conv_index:
        _get_ogma()._conv_index[conversation_id]['memorized'] = memorized
        _save_conversation_index()


def _is_conversation_memorized(conversation_id: str) -> bool:
    """Vérifie si une conversation est déjà mémorisée."""
    return _get_conv_index().get(conversation_id, {}).get('memorized', False)


def _count_memorized_conversations() -> int:
    """Compte le nombre total de conversations mémorisées."""
    return sum(1 for conv in _get_ogma()._conv_index.values() if conv.get('memorized', False))


def _get_memorized_conversations_list() -> list[tuple[str, str]]:
    """Retourne la liste des conversations mémorisées avec leur date."""
    memorized = []
    for conv_id, conv_data in _get_ogma()._conv_index.items():
        if conv_data.get('memorized', False):
            created = conv_data.get('created', '')
            memorized.append((conv_id, created))
    
    # Trier par date de création (plus ancien en premier)
    memorized.sort(key=lambda x: x[1])
    return memorized


async def _update_memorized_conversation(conversation_id: str, summary: str) -> bool:
    """Met à jour une conversation déjà mémorisée."""
    try:
        mm = _ensure_memory_manager()
        if not mm:
            return False
        
        memory_id = f"conv-{conversation_id}"
        
        # Supprimer l'ancienne version
        success = mm.delete_memory(memory_id)
        if success:
            # Ajouter la nouvelle version
            return await _memorize_conversation(conversation_id, summary)
        
        return False
        
    except Exception as e:
        print(f"[CONV-UPDATE] Erreur mise à jour: {e}")
        return False


def _delete_memorized_conversation(conversation_id: str):
    """Supprime une conversation mémorisée du système FAISS."""
    try:
        mm = _ensure_memory_manager()
        if mm:
            memory_id = f"conv-{conversation_id}"
            mm.delete_memory(memory_id)
            _mark_conversation_memorized(conversation_id, False)
            print(f"[CONV-DELETE] Mémoire de conversation {conversation_id} supprimée")
    except Exception as e:
        print(f"[CONV-DELETE] Erreur suppression: {e}")


def _create_edit_interface(dialog, conversation_id: str, title: str, summary: str):
    """Crée l'interface d'édition du résumé dans un dialog donné."""
    print(f"[DEBUG] Création interface édition pour {conversation_id}")
    
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(600px, 90vw); max-height: 80vh;'):
        ui.label('Édition du résumé').classes('popup-title')
        ui.label(f'Conversation: {title}').classes('text-sm text-muted mb-4')
        
        # Zone de texte pour le résumé
        summary_input = ui.textarea(
            'Résumé (150 mots max)', 
            value=summary,
        ).classes('w-full').style('min-height: 200px;')
        
        # Compteur de mots
        word_count = ui.label('').classes('text-xs text-muted')
        
        def update_word_count():
            words = len(summary_input.value.split()) if summary_input.value else 0
            word_count.text = f'{words}/150 mots'
            if words > 150:
                word_count.classes(remove='text-muted', add='text-red-400')
            else:
                word_count.classes(remove='text-red-400', add='text-muted')
        
        summary_input.on('input', update_word_count)
        update_word_count()
        
        async def finalize_memorization():
            if not summary_input.value.strip():
                ui.notify('Le résumé ne peut pas être vide', type='negative')
                return
            
            words = len(summary_input.value.split())
            if words > 150:
                ui.notify('Le résumé dépasse 150 mots', type='negative')
                return
            
            ui.notify('Mémorisation en cours...', type='info')
            
            try:
                print(f"[DEBUG] Tentative mémorisation conversation {conversation_id}")
                success = await _memorize_conversation(conversation_id, summary_input.value.strip())
                print(f"[DEBUG] Résultat mémorisation: {success}")
                
                if success:
                    ui.notify('OK Conversation mémorisée avec succès', type='positive')
                    dialog.close()
                    # Rafraîchir la sidebar pour mettre à jour l'icône
                    if _get_ogma()._sidebar_render_cb:
                        _get_ogma()._sidebar_render_cb(_get_ogma()._current_conversation_id)
                    # Actualiser la liste des mémoires si ouverte
                    _trigger_memory_update()
                else:
                    ui.notify('ERROR Erreur lors de la mémorisation (voir logs)', type='negative')
                    
            except Exception as e:
                print(f"[DEBUG] Exception mémorisation: {e}")
                ui.notify(f'ERROR Erreur: {e}', type='negative')
        
        with ui.row().classes('justify-end gap-2 mt-4'):
            ui.button('Annuler', on_click=dialog.close).classes('action-button')
            ui.button('Mémoriser', on_click=finalize_memorization).classes('send-button')


def _edit_summary_popup(conversation_id: str, title: str, summary: str):
    """Popup d'édition du résumé avant validation finale."""
    print(f"[DEBUG] _edit_summary_popup appelée pour {conversation_id}")
    dialog = ui.dialog()
    _create_edit_interface(dialog, conversation_id, title, summary)
    print(f"[DEBUG] Ouverture popup d'édition pour {conversation_id}")
    dialog.open()


def _status_dot(initial='var(--text-muted)'):
    el = ui.element('div').style(f'width:10px; height:10px; border-radius:50%; background:{initial}; border:1px solid var(--border-color);')
    return el


# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _models_modal(*args, **kwargs):
    """DÉPLACÉE: Redirige vers ogma_modals._models_modal()"""
    from ogma_modals import _models_modal as moved_func
    return moved_func(*args, **kwargs)
def _image_modal():
    """Fenêtre de configuration de la génération d'images via extension text2img"""
    d = ui.dialog()
    sm = _ensure_settings_manager()

    # Charger config actuelle
    img_config = sm.settings.get('image_generation', {
        'enabled': False,
        'default_width': 1024,
        'default_height': 1024,
        'save_images': True,
        'ai_can_see_images': False
    })

    with d, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 680px; max-height: 85vh; overflow-y: auto;'):
        ui.label('🎨 Génération d\'Images (Text2Image)').classes('popup-title')
        ui.label('Configuration de la génération d\'images via Pollinations.AI (Stable Diffusion)').classes('text-muted mb-4')

        with ui.column().classes('gap-4 w-full'):
            # Section activation
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label('Activation').classes('font-semibold mb-2')
                enabled_check = ui.checkbox(
                    'Activer la génération d\'images',
                    value=img_config.get('enabled', False)
                ).classes('mb-2')
                ui.label('Permet à Luna de créer des images via la phrase-clé "je dois créer une image de :"').classes('text-sm text-gray-400')

            # Section résolution
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label('Résolution par défaut').classes('font-semibold mb-2')

                with ui.row().classes('gap-4 items-center'):
                    width_input = ui.number(
                        'Largeur',
                        value=img_config.get('default_width', 1024),
                        min=256,
                        max=2048,
                        step=64
                    ).classes('flex-1')
                    ui.label('×').classes('text-xl')
                    height_input = ui.number(
                        'Hauteur',
                        value=img_config.get('default_height', 1024),
                        min=256,
                        max=2048,
                        step=64
                    ).classes('flex-1')

                ui.label('Résolutions recommandées: 1024×1024 (carré), 1920×1080 (paysage), 1080×1920 (portrait)').classes('text-sm text-gray-400 mt-2')

            # Section modèle et filtres
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label('Modèle et filtres').classes('font-semibold mb-2')

                # Sélection du modèle
                model_select = ui.select(
                    label='Modèle',
                    options=['flux', 'turbo'],
                    value=img_config.get('model', 'flux')
                ).classes('mb-2')
                ui.label('Flux: Haute qualité (recommandé) | Turbo: Plus rapide').classes('text-sm text-gray-400 mb-3')

                # Filtre NSFW
                safe_check = ui.checkbox(
                    'Filtre NSFW (contenu adulte bloqué)',
                    value=img_config.get('safe_mode', True)
                ).classes('mb-2')
                ui.label('⚠️ Recommandé: ACTIVER pour filtrer le contenu inapproprié').classes('text-sm text-yellow-400')

            # Section sauvegarde
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label('Sauvegarde').classes('font-semibold mb-2')

                save_check = ui.checkbox(
                    'Sauvegarder les images générées',
                    value=img_config.get('save_images', True)
                ).classes('mb-2')
                ui.label('Les images seront sauvegardées dans data/generated_images/').classes('text-sm text-gray-400')

            # Section vision IA
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label('Vision IA (Expérimental)').classes('font-semibold mb-2')

                vision_check = ui.checkbox(
                    'Luna peut voir ses créations',
                    value=img_config.get('ai_can_see_images', False)
                ).classes('mb-2')
                ui.label('⚠️ Fonctionnalité incomplète - Luna pourra analyser les images qu\'elle génère').classes('text-sm text-yellow-400')

            # Comment ça fonctionne
            with ui.card().classes('q-dark p-4').style('background: rgba(212, 175, 55, 0.1); border-left: 3px solid #d4af37;'):
                ui.label('💡 Comment ça fonctionne').classes('font-semibold mb-3').style('color: #d4af37;')

                steps = [
                    ('1️⃣', 'Utilisateur active la génération via Paramètres > Image'),
                    ('2️⃣', 'IA principale dit "je dois créer une image de : un chat cosmique"'),
                    ('3️⃣', 'Système détecte la phrase magique'),
                    ('4️⃣', 'Extension text2img génère l\'image via Perchance (Stable Diffusion)'),
                    ('5️⃣', 'Backend sauvegarde dans data/generated_images/'),
                    ('6️⃣', 'Interface affiche l\'image inline dans le chat'),
                    ('7️⃣', 'IA principale peut voir le résultat dans le chat')
                ]

                for emoji, text in steps:
                    with ui.row().classes('gap-2 items-start mb-1'):
                        ui.label(emoji).classes('text-base')
                        ui.label(text).classes('text-sm text-gray-300')

            # Informations API
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label('ℹ️ Informations Backend').classes('font-semibold mb-2')
                ui.label('Provider: Pollinations.AI (gratuit, illimité)').classes('text-sm text-gray-400')
                ui.label('Modèles: Flux (qualité) / Turbo (rapide)').classes('text-sm text-gray-400')
                ui.label('Filtre NSFW: Configurable (recommandé: activé)').classes('text-sm text-gray-400')
                ui.label('Aucune clé API requise').classes('text-sm text-green-400')

        # Boutons d'action
        with ui.row().classes('gap-2 mt-4 justify-end w-full'):
            ui.button('Annuler', on_click=d.close).classes('action-button')

            def save_config():
                # Construire nouvelle config
                new_config = {
                    'enabled': enabled_check.value,
                    'default_width': int(width_input.value),
                    'default_height': int(height_input.value),
                    'model': model_select.value,
                    'safe_mode': safe_check.value,
                    'save_images': save_check.value,
                    'ai_can_see_images': vision_check.value
                }

                # Sauvegarder
                sm.settings['image_generation'] = new_config
                sm.save_settings()

                # Réinitialiser l'extension text2img avec les nouveaux paramètres
                from extensions.text2img import initialize_text2img
                if new_config['enabled']:
                    initialize_text2img(sm)

                ui.notify('✅ Configuration sauvegardée', type='positive')
                d.close()

            ui.button('Sauvegarder', on_click=save_config).classes('primary-action-button')

    return d


# Fonction _perception_modal supprimée - l'overlay a été remplacé par :
# - Section simple dans les paramètres généraux
# - Utilisation directe de _perception_settings_modal pour le bouton header


# FONCTION DÉPLACÉE - Voir ogma_tts_config.py
# _render_tts_config: 604 lignes déplacées vers ogma_tts_config.py pour spécialisation


def _show_data_cleanup_dialog_OLD_SUPPRIMEE():
    """Affiche le dialogue de nettoyage des données avec sélection granulaire"""
    
    cleanup_dialog = ui.dialog()
    selected_categories = {}
    confirmation_input = None
    delete_button = None
    
    def validate_deletion():
        """Valide les conditions pour activer la suppression"""
        if not confirmation_input or not delete_button:
            print("[DEBUG-CLEANUP] Éléments manquants:", f"input={confirmation_input is not None}, button={delete_button is not None}")
            return
        
        expected_code = "DELETE-ALL-OGMA-DATA"
        code_valid = confirmation_input.value == expected_code
        
        # Debug des checkboxes
        checkbox_states = {}
        for cat, cb in selected_categories.items():
            if cb:
                checkbox_states[cat] = cb.value
        
        has_selection = any(checkbox_states.values())
        
        print(f"[DEBUG-CLEANUP] Code: '{confirmation_input.value}' == '{expected_code}' = {code_valid}")
        print(f"[DEBUG-CLEANUP] Checkboxes: {checkbox_states}")
        print(f"[DEBUG-CLEANUP] Sélection: {has_selection}")
        
        should_enable = code_valid and has_selection
        delete_button.enabled = should_enable
        
        print(f"[DEBUG-CLEANUP] Bouton activé: {delete_button.enabled}")
        
        # Forcer une mise à jour visuelle
        try:
            delete_button.update()
        except:
            pass
    
    def show_backup_list():
        """Affiche la liste des sauvegardes disponibles pour restauration"""
        backup_dialog = ui.dialog()
        
        with backup_dialog, ui.card().classes('w-full max-w-lg'):
            ui.label('SAVE Sauvegardes Disponibles').classes('text-lg font-bold mb-4')
            
            # Rechercher les sauvegardes
            backup_base_dir = Path('backups')
            if backup_base_dir.exists():
                backups = sorted([d for d in backup_base_dir.iterdir() if d.is_dir()], 
                               key=lambda x: x.stat().st_mtime, reverse=True)
                
                if backups:
                    for backup_dir in backups[:10]:  # Limiter à 10 sauvegardes récentes
                        backup_name = backup_dir.name
                        backup_date = datetime.fromtimestamp(backup_dir.stat().st_mtime).strftime('%d/%m/%Y %H:%M')
                        
                        # Calculer la taille
                        try:
                            backup_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                            size_text = format_size(backup_size)
                        except:
                            size_text = "Taille inconnue"
                        
                        with ui.row().classes('w-full items-center justify-between mb-2'):
                            with ui.column().classes('flex-grow'):
                                ui.label(backup_name).classes('font-semibold')
                                ui.label(f'{backup_date} • {size_text}').classes('text-sm text-muted')
                            
                            ui.button(
                                '↩️ Restaurer', 
                                on_click=lambda bd=backup_dir: restore_backup(bd, backup_dialog)
                            ).classes('bg-green-600 hover:bg-green-700 text-white')
                else:
                    ui.label('Aucune sauvegarde trouvée').classes('text-muted text-center')
            else:
                ui.label('Dossier de sauvegarde inexistant').classes('text-muted text-center')
            
            ui.button('Fermer', on_click=backup_dialog.close).classes('bg-gray-500 text-white mt-4 w-full')
        
        backup_dialog.open()
    
    def restore_backup(backup_dir, backup_dialog):
        """Restaure une sauvegarde sélectionnée"""
        try:
            ui.notify('Restauration en cours...', type='info')
            
            # Supprimer les données actuelles
            data_dir = Path('data')
            if data_dir.exists():
                shutil.rmtree(data_dir)
            
            # Restaurer depuis la sauvegarde
            backup_data_dir = backup_dir / 'data'
            if backup_data_dir.exists():
                shutil.copytree(backup_data_dir, data_dir)
                ui.notify('OK Restauration réussie!', type='positive', timeout=5000)
                ui.notify('UPDATE Redémarrez OGMA pour prendre en compte les changements', type='info', timeout=8000)
            else:
                ui.notify('ERROR Sauvegarde corrompue - dossier data manquant', type='negative')
            
            backup_dialog.close()
            cleanup_dialog.close()
            if refresh_callback:
                refresh_callback()
                
        except Exception as e:
            ui.notify(f'ERROR Erreur restauration: {e}', type='negative', timeout=5000)
    
    async def execute_cleanup():
        """Exécute le nettoyage avec feedback"""
        try:
            # Collecter les catégories sélectionnées
            selected = [cat for cat, cb in selected_categories.items() if cb.value]

            if not selected:
                ui.notify('Aucune catégorie sélectionnée', type='warning')
                return

            ui.notify('Création de la sauvegarde...', type='info')

            # Créer une sauvegarde
            backup_dir = cleaner.create_backup()
            ui.notify(f'Sauvegarde créée: {backup_dir.name}', type='positive')

            # IMPORTANT: Fermer MemoryManager AVANT la suppression pour libérer le verrou sur memories.db
            if 'memory' in selected:
                ui.notify('Fermeture du système de mémoire...', type='info')
                close_memory_manager()
                print("[CLEANUP] MemoryManager fermé avant suppression")

                # Attendre que Windows libère complètement les verrous de fichier
                import asyncio
                await asyncio.sleep(2.0)
                print("[CLEANUP] Attente de 2s pour libération des verrous Windows")

            # Exécuter la suppression
            ui.notify('Suppression en cours...', type='info')
            deletion_log = cleaner.delete_selected_data(
                categories=selected,
                confirmation_code=confirmation_input.value if confirmation_input else ""
            )

            # Réinitialiser MemoryManager si la mémoire a été supprimée
            if 'memory' in selected:
                ui.notify('Réinitialisation du système de mémoire...', type='info')
                init_memory_manager()
                print("[CLEANUP] MemoryManager réinitialisé avec une base vierge")

            # Vérifier le résultat
            verification = cleaner.verify_clean_state()

            if verification['all_clean']:
                ui.notify('OK Nettoyage terminé avec succès!', type='positive', timeout=5000)
                ui.notify('SUCCESS OGMA a maintenant un profil vierge', type='positive', timeout=5000)
            else:
                ui.notify('WARN Nettoyage partiellement réussi', type='warning', timeout=3000)

            # Fermer le dialogue et rafraîchir
            cleanup_dialog.close()
            if refresh_callback:
                refresh_callback()

        except Exception as e:
            ui.notify(f'ERROR Erreur lors du nettoyage: {e}', type='negative', timeout=5000)
    
    with cleanup_dialog, ui.card().classes('w-full max-w-3xl').style('max-height: 80vh; overflow-y: auto; padding: 24px;'):
        ui.label('🗑️ Nettoyage des Données OGMA').classes('text-2xl font-bold mb-2')
        ui.label('Suppression sécurisée pour créer un profil vierge').classes('text-lg text-muted mb-6')
        
        # Zone d'avertissement proéminente SANS CADRE
        ui.label('WARN ATTENTION - SUPPRESSION IRRÉVERSIBLE').classes('text-2xl font-bold text-red-600 mb-3')
        ui.label('Cette action supprimera définitivement les données sélectionnées.').classes('text-lg text-red-700 mb-2')
        ui.label('OK Une sauvegarde automatique sera créée avant suppression.').classes('text-lg text-green-600 mb-6')
        
        # Sélection des catégories - SANS CADRES
        ui.label('CLIPBOARD Sélectionnez les données à supprimer:').classes('text-xl font-bold mb-4')
        
        categories_config = {
            'memory': {
                'icon': 'BRAIN',
                'title': 'Mémoire complète de Luna',
                'files': f"{analysis['memory'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['memory'].get('total_size', 0)),
                'details': f"• {analysis['memory'].get('memory_count', 0)} souvenirs stockés\n• Base de données SQLite\n• Index vectoriel FAISS\n• Fichiers de sauvegarde",
                'warning': 'WARN SUPPRIME TOUS LES SOUVENIRS DE LUNA'
            },
            'conversations': {
                'icon': '💬',
                'title': 'Historique complet des conversations',
                'files': f"{analysis['conversations'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['conversations'].get('total_size', 0)),
                'details': f"• {analysis['conversations'].get('conversation_count', 0)} conversations\n• Fichiers JSON d'historique\n• Index des conversations",
                'warning': 'WARN SUPPRIME TOUT L\'HISTORIQUE DE CHAT'
            },
            'ego_data': {
                'icon': 'MASK',
                'title': 'Données de personnalité et ego',
                'files': f"{analysis['ego_data'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['ego_data'].get('total_size', 0)),
                'details': "• Fichier ego_prompt.txt\n• Archives de personnalité\n• Contexte persistant",
                'warning': 'WARN SUPPRIME LA PERSONNALITÉ DE LUNA'
            },
            'temp_files': {
                'icon': '🗑️',
                'title': 'Fichiers temporaires et cache',
                'files': f"{analysis['temp_files'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['temp_files'].get('total_size', 0)),
                'details': "• Fichiers .tmp et .bak\n• Caches système\n• Logs temporaires",
                'warning': 'OK Nettoyage sûr (aucune perte de données importantes)'
            }
        }
        
        for category, config in categories_config.items():
            if analysis.get(category, {}).get('file_count', 0) > 0:
                # Checkbox avec label enrichi - SANS CADRE
                with ui.row().classes('w-full items-start mb-6'):
                    checkbox = ui.checkbox('').classes('mt-1')
                    selected_categories[category] = checkbox
                    # N'ajouter l'événement qu'après avoir créé tous les éléments
                    
                    with ui.column().classes('flex-grow ml-4'):
                        # Titre avec icône
                        ui.label(f"{config['icon']} {config['title']}").classes('text-lg font-bold mb-2')
                        
                        # Informations sur les fichiers
                        ui.label(f"STATS {config['files']} • {config['size']}").classes('text-base text-blue-600 mb-2')
                        
                        # Détails
                        for detail_line in config['details'].split('\n'):
                            ui.label(detail_line).classes('text-sm text-muted')
                        
                        # Avertissement
                        warning_color = 'text-red-600 font-bold' if 'WARN' in config['warning'] else 'text-green-600 font-semibold'
                        ui.label(config['warning']).classes(f'text-base {warning_color} mt-2')
                
                ui.separator().classes('my-2')
        
        # Section sauvegarde et restauration
        ui.label('SAVE Gestion des Sauvegardes').classes('text-xl font-bold mt-6 mb-4')
        
        with ui.column().classes('w-full mb-6'):
            ui.label('Avant suppression, une sauvegarde complète sera automatiquement créée.').classes('text-base text-muted mb-3')
            ui.button(
                'CLIPBOARD Voir et Restaurer les Sauvegardes',
                on_click=show_backup_list
            ).classes('bg-blue-600 hover:bg-blue-700 text-white text-lg px-6 py-3 w-full font-semibold')
        
        # Code de confirmation
        ui.separator().classes('my-6')
        ui.label('LOCK Confirmation de Sécurité').classes('text-xl font-bold mb-4')
        ui.label('Pour confirmer cette action irréversible, tapez exactement:').classes('text-base mb-2')
        ui.label('DELETE-ALL-OGMA-DATA').classes('text-lg font-mono bg-gray-100 p-2 rounded border-l-4 border-red-500 mb-4')
        
        confirmation_input = ui.input('Code de confirmation').classes('w-full text-lg')
        # N'ajouter l'événement qu'après avoir créé le bouton
        
        # Boutons d'action
        ui.separator().classes('my-6')
        with ui.row().classes('w-full justify-between'):
            ui.button(
                'ERROR Annuler',
                on_click=cleanup_dialog.close
            ).classes('bg-gray-500 hover:bg-gray-600 text-white text-lg px-8 py-3')
            
            delete_button = ui.button(
                '🗑️ SUPPRIMER DÉFINITIVEMENT',
                on_click=execute_cleanup
            ).classes('bg-red-600 hover:bg-red-700 text-white text-lg px-8 py-3 font-bold')
            delete_button.enabled = False
        
        # MAINTENANT connecter tous les événements après avoir créé tous les éléments
        def setup_validation():
            """Configure la validation avec des références stables"""
            
            # Sauvegarder les références pour éviter les problèmes de closure
            input_ref = confirmation_input
            button_ref = delete_button
            categories_ref = dict(selected_categories)
            
            def stable_validate():
                """Validation avec références stables"""
                if not input_ref or not button_ref:
                    print("[DEBUG-CLEANUP] Références manquantes")
                    return
                
                expected_code = "DELETE-ALL-OGMA-DATA"
                code_valid = input_ref.value == expected_code
                
                # Vérification explicite des checkboxes
                checkbox_states = {}
                for cat, cb in categories_ref.items():
                    if cb and hasattr(cb, 'value'):
                        checkbox_states[cat] = cb.value
                    else:
                        checkbox_states[cat] = False
                
                has_selection = any(checkbox_states.values())
                should_enable = code_valid and has_selection
                
                print(f"[DEBUG-CLEANUP] Input: '{input_ref.value}'")
                print(f"[DEBUG-CLEANUP] Code valide: {code_valid}")  
                print(f"[DEBUG-CLEANUP] États checkboxes: {checkbox_states}")
                print(f"[DEBUG-CLEANUP] A une sélection: {has_selection}")
                print(f"[DEBUG-CLEANUP] Doit activer: {should_enable}")
                
                button_ref.enabled = should_enable
                
                # Notification visuelle pour debug
                status = "ACTIVÉ" if should_enable else "GRISÉ"
                print(f"[DEBUG-CLEANUP] Bouton {status}")
            
            # Événements avec références stables
            input_ref.on('input', stable_validate)
            
            for category, checkbox in categories_ref.items():
                if checkbox:
                    print(f"[DEBUG-CLEANUP] Connecter {category}")
                    checkbox.on('change', stable_validate)
            
            # Timer de validation continue
            ui.timer(1.0, stable_validate)
            
            # Validation initiale
            print("[DEBUG-CLEANUP] === VALIDATION INITIALE ===")
            stable_validate()
        
        # Délai pour s'assurer que tout est créé
        ui.timer(0.2, setup_validation, once=True)
    
    cleanup_dialog.open()


def _profile_modal():
    d = ui.dialog()
    
    def refresh_content():
        """Rafraîchit dynamiquement le contenu du modal."""
        # Vider le contenu dynamique et le recréer
        dynamic_content.clear()
        
        with dynamic_content:
            sm = _ensure_settings_manager()
            
            # === SECTION DEBUG ===
            ui.label('SEARCH Options de Debug').classes('text-lg font-medium mb-2')
            
            # Affichage injections Archiviste
            debug_archiviste = sm.settings.get('debug', {}).get('show_archiviste_injection', False)
            
            def on_debug_archiviste_change(e):
                if 'debug' not in sm.settings:
                    sm.settings['debug'] = {}
                sm.settings['debug']['show_archiviste_injection'] = e.value
                sm.save_settings()
                ui.notify('Paramètre debug sauvegardé', type='positive')
            
            ui.checkbox(
                'Afficher les injections de contexte de l\'Archiviste dans le chat',
                value=debug_archiviste,
                on_change=on_debug_archiviste_change
            ).classes('mb-2')
            
            ui.label('Quand activé, vous verrez les notes de contexte injectées par l\'Archiviste en tant que messages système dans la conversation.').classes('text-xs text-muted mb-4')
            
            # === TRANSCRIPTION AUDIO ===
            ui.separator().classes('my-4')
            ui.label('Transcription et Auto-envoi').classes('text-lg font-medium mb-2')
            
            audio_auto_send = sm.settings.get('audio', {}).get('auto_send', False)
            
            def on_audio_auto_send_change(e):
                if 'audio' not in sm.settings:
                    sm.settings['audio'] = {}
                sm.settings['audio']['auto_send'] = e.value
                sm.save_settings()
                ui.notify('Paramètre audio sauvegardé', type='positive')
            
            ui.checkbox(
                'Envoi automatique après transcription vocale',
                value=audio_auto_send,
                on_change=on_audio_auto_send_change
            ).classes('mb-2')
            
            ui.label('Quand activé, les messages transcrits sont automatiquement envoyés sans appuyer sur Entrée.').classes('text-xs text-muted mb-4')
            
            # === PERFORMANCES GPU ===
            ui.separator().classes('my-4')
            ui.label('🎮 Performances GPU').classes('text-lg font-medium mb-2')
            
            # Paramètre GPU pour reconnaissance d'images
            gpu_accel_enabled = not sm.settings.get('other_backends', {}).get('ollama', {}).get('low_vram', True)
            
            def on_gpu_accel_change(e):
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'ollama' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['ollama'] = {}
                
                # Inverse la logique : coché = utiliser GPU (low_vram=False)
                sm.settings['other_backends']['ollama']['low_vram'] = not e.value
                sm.save_settings()
                
                status = "activée" if e.value else "désactivée"
                ui.notify(f'Accélération GPU {status}', type='positive')
                
                # Reconfigurer Ollama si nécessaire
                global _chat_api
                if _chat_api and hasattr(_chat_api, 'configure_ollama_gpu'):
                    _chat_api.configure_ollama_gpu(not e.value)
            
            ui.checkbox(
                'Utiliser la puissance GPU pour la reconnaissance d\'images',
                value=gpu_accel_enabled,
                on_change=on_gpu_accel_change
            ).classes('mb-2')
            
            ui.label('Recommandé pour les cartes graphiques avec plus de 8GB de VRAM (RTX 4070, RTX 5070Ti, etc.)').classes('text-xs text-muted mb-4')
            
            # === TEXT-TO-SPEECH ===
            ui.separator().classes('my-4')
            ui.label('SPEAKER Text-to-Speech').classes('text-lg font-medium mb-2')
            
            # Activation TTS
            tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
            
            def on_tts_enabled_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['enabled'] = e.value
                sm.save_settings()
                
                audio_mgr = _ensure_audio_manager()
                if audio_mgr and hasattr(audio_mgr, 'set_tts_settings'):
                    audio_mgr.set_tts_settings(enabled=e.value)
                
                status = "activé" if e.value else "désactivé"
                ui.notify(f'TTS {status}', type='positive')
                
                # Rafraîchir le contenu pour montrer/cacher les options TTS
                refresh_content()
            
            ui.checkbox(
                'Activer la synthèse vocale',
                value=tts_enabled,
                on_change=on_tts_enabled_change
            ).classes('mb-3')
            
            if tts_enabled:
                # Mode automatique
                auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
                
                def on_auto_speak_change(e):
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['auto_speak'] = e.value
                    sm.save_settings()
                    ui.notify(f'Lecture automatique {"activée" if e.value else "désactivée"}', type='positive')
                
                ui.checkbox(
                    'Lecture automatique des réponses IA',
                    value=auto_speak,
                    on_change=on_auto_speak_change
                ).classes('mb-3')
                
                ui.label('Quand activé, l\'IA parlera automatiquement ses réponses sans cliquer sur SPEAKER.').classes('text-xs text-muted mb-4')
                
                # Sélection du moteur TTS
                current_engine = sm.settings.get('tts', {}).get('engine', 'system')
                print(f"[DEBUG-TTS] Valeur current_engine depuis settings: '{current_engine}'")
                
                def on_engine_change(e):
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['engine'] = e.value
                    sm.save_settings()
                    
                    # Reconfigurer l'audio manager
                    audio_mgr = _ensure_audio_manager()
                    if audio_mgr:
                        audio_mgr.configure_tts_engine(e.value)
                    
                    ui.notify(f'Moteur changé: {e.value}', type='positive')
                    print(f"[DEBUG-TTS] Changement moteur vers: {e.value}")
                    
                    # Rafraîchir le contenu pour afficher les bonnes options
                    try:
                        refresh_content()
                        print(f"[DEBUG-TTS] Rafraîchissement terminé pour: {e.value}")
                    except Exception as ex:
                        print(f"[DEBUG-TTS] Erreur rafraîchissement: {ex}")
                        ui.notify(f'Erreur rafraîchissement: {ex}', type='negative')
                
                engine_options = {
                    'system': '🖥️ Système (Windows SAPI/pyttsx3)',
                    'google': 'WEB Google Cloud TTS',
                    'elevenlabs': '🎙️ ElevenLabs',
                    'azure': '☁️ Azure AI Speech',
                    'gtts': '🆓 Google TTS (Offline)',
                    'edge_tts': 'WEB Microsoft Edge TTS (Gratuit)'
                }
                
                ui.select(
                    label='Moteur de synthèse vocale',
                    options=engine_options,
                    value=current_engine,
                    on_change=on_engine_change
                ).classes('mb-4')
                
                # Configuration spécifique au moteur sélectionné
                print(f"[DEBUG-TTS] Appel _render_tts_config avec: '{current_engine}'")
                _render_tts_config(current_engine, sm, refresh_content)
            

            
            # === BOUTONS D'ACTION ===
            ui.separator().classes('my-4')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Rafraîchir', on_click=refresh_content).classes('bg-blue-500 text-white')
                ui.button('Fermer', on_click=d.close).classes('bg-gray-500 text-white')
    
    with d, ui.card().classes('w-full max-w-4xl mx-auto').style('min-height: 400px; max-height: 80vh; overflow-y: auto;'):
        ui.label('⚙️ Configuration OGMA').classes('text-xl font-bold mb-4')
        
        # Conteneur dynamique pour le contenu
        dynamic_content = ui.column().classes('w-full')
        
        # Charger le contenu initial
        refresh_content()
    
    return d


# ---- Helpers dynamiques: modèles et tests ----
async def _list_models(backend_type: str, provider: Optional[str], api_key: Optional[str]) -> Tuple[List[str], Optional[str]]:
    _ensure_backends()
    assert _api_mgr is not None and _ollama_mgr is not None and _gguf_mgr is not None and _kobold_mgr is not None
    try:
        if backend_type == 'API':
            provider_val = provider or 'Aucun'
            if provider_val == 'Aucun':
                return [], "Aucun fournisseur API sélectionné."
            models, api_err = await _api_mgr.list_models(api_key, provider_val)
            return models, api_err
        elif backend_type == 'Ollama':
            models = await _ollama_mgr.list_models()
            return models, None
        elif backend_type == 'GGUF':
            models = _gguf_mgr.list_models()
            return models, None
        elif backend_type == 'KoboldCpp':
            models = await _kobold_mgr.list_models()
            return models, None
        else:
            return [], f"Type de backend inconnu: {backend_type}"
    except Exception as e:
        return [], f"Erreur lors de la récupération des modèles: {str(e)}"


async def _test_connection(backend_type: str, provider: Optional[str], api_key: Optional[str], service_url: Optional[str] = None) -> Tuple[bool, str]:
    _ensure_backends()
    assert _api_mgr is not None and _ollama_mgr is not None and _gguf_mgr is not None and _kobold_mgr is not None
    try:
        if backend_type == 'API':
            provider_val = provider or 'Aucun'
            if provider_val == 'Aucun':
                return False, "Aucun fournisseur API sélectionné."
            return await _api_mgr.test_connection(api_key, provider_val)
        elif backend_type == 'Ollama':
            return await _ollama_mgr.test_connection(service_url)
        elif backend_type == 'GGUF':
            return _gguf_mgr.test_connection()
        elif backend_type == 'KoboldCpp':
            return await _kobold_mgr.test_connection(service_url)
        else:
            return False, f"Type de backend inconnu: {backend_type}"
    except Exception as e:
        return False, f"Erreur lors du test de connexion: {str(e)}"






async def _check_global_ia_status() -> Dict[str, Dict[str, Any]]:
    """Vérifie l'état de configuration et de disponibilité des 3 IAs principales.
    
    Returns:
        Dict avec clés 'chat', 'archiviste', 'embeddings', chacune contenant:
        - 'configured': bool (modèle sélectionné)
        - 'available': bool (connexion OK)
        - 'model_name': str (nom du modèle actuel)
        - 'backend': str (type de backend)
    """
    sm = _ensure_settings_manager()
    status = {}
    
    # Sections de configuration correspondantes
    sections = {
        'chat': 'chat_api',
        'archiviste': 'reasoning_api', 
        'embeddings': 'embedding_api'
    }
    
    for ia_name, config_key in sections.items():
        config = sm.settings.get(config_key, {})
        
        # Utiliser la même logique que les contrôleurs pour déterminer le backend actif
        backend = config.get('backend_type', 'API')
        if ia_name == 'embeddings' and backend not in ['API', 'Ollama', 'GGUF']:
            backend = 'API'  # Les embeddings ne supportent que API, Ollama, GGUF
        
        # Déterminer le modèle configuré selon la même logique qu'OGMA
        model_name = "Aucun modèle"
        configured = False
        
        if backend == 'API':
            provider = config.get('provider', 'Aucun')
            api_model = config.get('api_model', '') or config.get('model', '')  # Fallback compatibilité
            api_key = config.get('api_key', '')
            
            if provider != 'Aucun' and api_model and api_key:
                model_name = f"{provider}:{api_model}"
                configured = True
            elif provider != 'Aucun' and api_key:
                model_name = f"{provider}:Clé API configurée"
                configured = True
                
        elif backend == 'Ollama':
            ollama_model = config.get('ollama_model', '')
            if ollama_model:
                model_name = f"Ollama:{ollama_model}"
                configured = True
                
        elif backend == 'GGUF':
            gguf_model = config.get('gguf_model', '')
            if gguf_model:
                # Extraire juste le nom du fichier sans le chemin
                import os
                filename = os.path.basename(gguf_model) if gguf_model else 'Aucun'
                model_name = f"GGUF:{filename}"
                configured = True
                
        elif backend == 'KoboldCpp':
            kobold_url = config.get('kobold_url', 'http://localhost:5001')
            model_name = f"KoboldCpp:{kobold_url}"
            configured = True  # KoboldCpp utilise le modèle chargé sur le serveur
        
        # Tester la disponibilité si configuré
        available = False
        if configured:
            try:
                if backend == 'API':
                    provider = config.get('provider')
                    api_key = config.get('api_key', '')
                    if provider and api_key:  # S'assurer qu'on a les infos nécessaires
                        models, err = await _list_models(backend, provider, api_key)
                        available = (err is None) and bool(models)
                    else:
                        available = False
                elif backend == 'GGUF':
                    # Pour GGUF, utiliser test_connection qui vérifie si le modèle est chargé
                    available, status_msg = await _test_connection(backend, None, None)
                elif backend in ['Ollama', 'KoboldCpp']:
                    service_url = None
                    if backend == 'Ollama':
                        service_url = config.get('ollama_url', 'http://localhost:11434')
                    elif backend == 'KoboldCpp':
                        service_url = config.get('kobold_url', 'http://localhost:5001')
                    
                    models, err = await _list_models(backend, None, None)
                    available = (err is None) and bool(models or backend in ['KoboldCpp'])
            except Exception as e:
                print(f"[STATUS-CHECK] Erreur vérification {ia_name} ({backend}): {e}")
                available = False
        
        # Log pour debug
        print(f"[STATUS-CHECK] {ia_name.upper()}: backend={backend}, configured={configured}, available={available}, model={model_name}")
        
        status[ia_name] = {
            'configured': configured,
            'available': available,
            'model_name': model_name,
            'backend': backend
        }
    
    return status


async def _update_ia_status_indicators():
    """Met à jour les indicateurs d'état IA dans le header principal."""
    global _ia_status_indicators
    
    if not _ia_status_indicators:
        return  # Indicateurs pas encore créés
    
    try:
        status = await _check_global_ia_status()
        
        for ia_name, ia_data in status.items():
            dot_key = f"{ia_name}_dot"
            model_key = f"{ia_name}_model"
            
            if ia_name == 'chat':
                dot_key = 'chat_dot'
                model_key = 'chat_model'
            elif ia_name == 'archiviste':
                dot_key = 'archiviste_dot'
                model_key = 'archiviste_model'
            elif ia_name == 'embeddings':
                dot_key = 'embeddings_dot'
                model_key = 'embeddings_model'
            
            # Mettre à jour le voyant (vert si configuré ET disponible, rouge sinon)
            if dot_key in _ia_status_indicators:
                dot_el = _ia_status_indicators[dot_key]
                is_ok = ia_data['configured'] and ia_data['available']
                color = '#16a34a' if is_ok else '#dc2626'  # Vert si OK, rouge sinon
                try:
                    dot_el.style(f'background: {color};')
                except Exception as e:
                    print(f"[STATUS-UPDATE] Erreur mise à jour voyant {dot_key}: {e}")
            
            # Mettre à jour le nom du modèle
            if model_key in _ia_status_indicators:
                model_el = _ia_status_indicators[model_key]
                model_name = ia_data['model_name'] if ia_data['configured'] else 'Aucun modèle'
                try:
                    model_el.text = model_name
                    # Couleur différente selon l'état
                    if ia_data['configured'] and ia_data['available']:
                        model_el.style('color: #16a34a;')  # Vert si tout OK
                    elif ia_data['configured']:
                        model_el.style('color: #f59e0b;')  # Orange si configuré mais pas disponible
                    else:
                        model_el.style('color: var(--text-muted);')  # Gris si pas configuré
                except Exception as e:
                    print(f"[STATUS-UPDATE] Erreur mise à jour modèle {model_key}: {e}")
    
    except Exception as e:
        print(f"[STATUS-UPDATE] Erreur générale mise à jour indicateurs: {e}")


# ---- GESTION DES NOTIFICATIONS ----


def _refresh_models_ui(section: str, backend_select, provider_select, model_select, api_key_input, service_url_input=None):
    """Rafraîchit la liste des modèles pour une section (chat/arch/embed)."""
    async def _do():
        backend = backend_select.value if hasattr(backend_select, 'value') else backend_select
        provider = provider_select.value if provider_select and hasattr(provider_select, 'value') else None
        api_key = api_key_input.value if api_key_input and hasattr(api_key_input, 'value') else None
        # Appliquer l'URL du service si fournie (Ollama/Kobold)
        if service_url_input:
            try:
                url_el = service_url_input()
                url_val = url_el.value if hasattr(url_el, 'value') else None
            except Exception:
                url_val = None
            if url_val:
                if backend == 'Ollama':
                    _ensure_backends(); assert _ollama_mgr is not None
                    _ollama_mgr.api_url = url_val.rstrip('/')
                elif backend == 'KoboldCpp':
                    _ensure_backends(); assert _kobold_mgr is not None
                    _kobold_mgr.api_url = url_val.rstrip('/')
        import uuid
        call_id = str(uuid.uuid4())[:8]
        models, err = await _list_models(backend, provider, api_key)
        if models:
            pass
        if err:
            _notify_safe(err, type='warning')
        if models is not None:
            # Déduplication et tri simple
            opts = sorted(list({m for m in models if isinstance(m, str)}))
            
            if hasattr(model_select, 'options'):
                if hasattr(model_select.options, 'clear'):
                    model_select.options.clear()
                model_select.options = opts
                if hasattr(model_select, 'update'):
                    model_select.update()
            else:
                pass
        # Tenter de sélectionner le modèle sauvegardé si présent
        saved_model = None
        try:
            sm = _ensure_settings_manager()
            section_key = {'chat': 'chat_api', 'arch': 'reasoning_api', 'embed': 'embedding_api'}.get(section)
            sec = sm.settings.get(section_key, {}) if section_key else {}
            if backend == 'API':
                saved_model = sec.get('api_model')
            elif backend == 'Ollama':
                saved_model = sec.get('ollama_model')
            elif backend == 'GGUF':
                saved_model = sec.get('gguf_model')
        except Exception:
            saved_model = None
        if opts:
            if saved_model and saved_model in opts:
                model_select.value = saved_model
            elif model_select.value in opts:
                # Garder la valeur courante si encore valide
                model_select.value = model_select.value
            else:
                model_select.value = opts[0]
        else:
            model_select.value = None
        _notify_safe(f'{len(opts)} modèle(s) chargé(s).', type=('positive' if opts else 'warning'))
    return _do


def _test_connection_ui(section: str, backend_select, provider_select, api_key_input, service_url_input=None):
    """Teste rapidement la connexion: API list_models, Ollama/GGUF/Kobold health."""
    async def _do():
        backend = backend_select.value if hasattr(backend_select, 'value') else backend_select
        provider = provider_select.value if provider_select and hasattr(provider_select, 'value') else None
        # Appliquer l'URL du service si fournie (Ollama/Kobold)
        if service_url_input:
            try:
                url_el = service_url_input()
                url_val = url_el.value if hasattr(url_el, 'value') else None
            except Exception:
                url_val = None
            if url_val:
                if backend == 'Ollama':
                    _ensure_backends(); assert _ollama_mgr is not None
                    _ollama_mgr.api_url = url_val.rstrip('/')
                elif backend == 'KoboldCpp':
                    _ensure_backends(); assert _kobold_mgr is not None
                    _kobold_mgr.api_url = url_val.rstrip('/')
        try:
            if backend == 'API':
                _notify_safe('Test: récupération de la liste des modèles...', type='info')
                # Utiliser la clé saisie si dispo
                api_key = api_key_input.value if api_key_input and hasattr(api_key_input, 'value') else None
                if not api_key:
                    sm = _ensure_settings_manager()
                    key_map = {
                        'chat': sm.settings.get('chat_api', {}).get('api_key', ''),
                        'arch': sm.settings.get('reasoning_api', {}).get('api_key', ''),
                        'embed': sm.settings.get('embedding_api', {}).get('api_key', ''),
                    }
                    api_key = key_map.get(section, '')
                models, err = await _list_models('API', provider, api_key)
                if err:
                    _notify_safe(f'Échec: {err}', type='warning')
                else:
                    _notify_safe(f'OK: {len(models)} modèles disponibles.', type='positive')
            elif backend in ['Ollama', 'GGUF', 'KoboldCpp']:
                models, err = await _list_models(backend, None, None)
                if err:
                    _notify_safe(f'Échec: {err}', type='warning')
                else:
                    _notify_safe('OK: service disponible.', type='positive')
            else:
                _notify_safe('Backend non supporté.', type='warning')
        except Exception as e:
            _notify_safe(f'Erreur: {e}', type='warning')
    return _do


def _init_models_ui(section: str, backend_select, provider_select, model_select, api_key_input, api_zone, ollama_zone, ollama_model_select, gguf_zone, gguf_model_select, kobold_zone, ollama_url_input=None, kobold_url_input=None):
    """Initialise la visibilité et essaie de précharger des modèles pour chaque zone."""
    from nicegui_client_guard import safe_async_timer_callback
    
    # Visibilité initiale
    backend = backend_select.value
    if api_zone is not None: api_zone.visible = (backend == 'API')
    if ollama_zone is not None: ollama_zone.visible = (backend == 'Ollama')
    if gguf_zone is not None: gguf_zone.visible = (backend == 'GGUF')
    if kobold_zone is not None: kobold_zone.visible = (backend == 'KoboldCpp')
    # Préchargement modèle selon backend
    if backend == 'API':
        cb = _refresh_models_ui(section, backend_select, provider_select, model_select, api_key_input)
        ui.timer(0.01, safe_async_timer_callback(lambda: asyncio.create_task(cb())), once=True)
    elif backend == 'Ollama':
        cb = _refresh_models_ui(section, backend_select, None, ollama_model_select, None, service_url_input=(lambda: ollama_url_input) if ollama_url_input else None)
        ui.timer(0.01, safe_async_timer_callback(lambda: asyncio.create_task(cb())), once=True)
    elif backend == 'GGUF':
        cb = _refresh_models_ui(section, backend_select, None, gguf_model_select, None)
        ui.timer(0.01, safe_async_timer_callback(lambda: asyncio.create_task(cb())), once=True)
    elif backend == 'KoboldCpp':
        # Rien à charger; juste valider service au besoin
        pass


async def _handle_conversation_commands(text: str) -> bool:
    """
    Gère les commandes spéciales pour accéder aux conversations archivées
    Retourne True si une commande a été traitée, False sinon
    """
    global _loaded_conversation, _loaded_conversation_filename
    text_lower = text.lower().strip()
    
    # Debug: vérifier si les imports fonctionnent
    try:
        # Test des imports
        if not hasattr(archive, 'load_conversation'):
            _notify_safe("ERROR Module archive non initialisé correctement", 'negative')
            return True
    except NameError:
        _notify_safe("ERROR Module archive non trouvé - réinitialisation nécessaire", 'negative')
        return True
    
    # SEARCH DÉTECTION LANGAGE NATUREL pour lecture de conversation
    natural_patterns = [
        r'va lire\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'lis\s+(?:moi\s+)?(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'charge\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'ouvre\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'accède\s+à\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)'
    ]
    
    for pattern in natural_patterns:
        match = re.search(pattern, text_lower)
        if match:
            filename = match.group(1).strip()
            if not filename.endswith('.json'):
                filename += '.json'
            
            _notify_safe(f"SEARCH Détection automatique: chargement de {filename}", 'info')
            
            try:
                conversation = await archive.load_conversation(filename)
                if conversation:
                    # Charger la conversation dans le contexte global pour l'IA
                    _loaded_conversation = conversation
                    _loaded_conversation_filename = filename
                    
                    await _display_conversation_as_attachment(filename, conversation)
                    
                    # L'IA va maintenant traiter la demande avec la conversation chargée
                    # On ne return pas True pour laisser l'IA répondre
                    return False  # Continue vers l'IA avec le contexte chargé
                else:
                    _notify_safe(f"ERROR Conversation non trouvée: {filename}", 'negative')
                    return True
            except Exception as e:
                _notify_safe(f"ERROR Erreur lors du chargement: {str(e)}", 'negative')
                return True
    
    # Commande: "lis conversation [nom_fichier]"
    if text_lower.startswith('lis conversation '):
        try:
            filename = text[len('lis conversation '):].strip()
            if not filename.endswith('.json'):
                filename += '.json'
            
            _notify_safe(f"SEARCH Chargement de la conversation: {filename}", 'info')
            conversation = await archive.load_conversation(filename)
            if conversation:
                # Charger la conversation dans le contexte global pour l'IA
                _loaded_conversation = conversation
                _loaded_conversation_filename = filename
                
                await _display_archived_conversation(filename, conversation)
                _notify_safe(f"OK Conversation chargée dans le contexte de l'IA. Tu peux maintenant lui poser des questions dessus.", 'positive')
            else:
                _notify_safe(f"ERROR Conversation non trouvée: {filename}", 'negative')
        except Exception as e:
            _notify_safe(f"ERROR Erreur lors du chargement: {str(e)}", 'negative')
        return True
    
    # Commande: "cherche "[terme]" dans conversations"
    if 'cherche ' in text_lower and ' dans conversations' in text_lower:
        # Extraire le terme de recherche
        start = text_lower.find('cherche ') + len('cherche ')
        end = text_lower.find(' dans conversations')
        search_term = text[start:end].strip().strip('"\'')
        
        if search_term:
            results = await archive.search_conversations(search_term)
            await _display_search_results(search_term, results)
        else:
            _notify_safe("ERROR Terme de recherche vide", 'negative')
        return True
    
    # Commande: "résumé conversation [nom_fichier]"
    if text_lower.startswith('résumé conversation ') or text_lower.startswith('resume conversation '):
        prefix_len = len('résumé conversation ') if 'résumé' in text_lower else len('resume conversation ')
        filename = text[prefix_len:].strip()
        if not filename.endswith('.json'):
            filename += '.json'
        
        conversation = await archive.load_conversation(filename)
        if conversation:
            summary = await summarizer.create_summary(conversation)
            if summary:
                await _display_conversation_summary(filename, summary)
            else:
                _notify_safe("ERROR Impossible de créer le résumé", 'negative')
        else:
            _notify_safe(f"ERROR Conversation non trouvée: {filename}", 'negative')
        return True
    
    # Commande: "liste conversations" ou "conversations disponibles"
    if any(cmd in text_lower for cmd in ['liste conversations', 'conversations disponibles', 'voir conversations']):
        await _display_available_conversations()
        return True
    
    # Commande: "vider conversation" ou "clear conversation"
    if any(cmd in text_lower for cmd in ['vider conversation', 'clear conversation', 'vider contexte conversation']):
        if _loaded_conversation:
            old_filename = _loaded_conversation_filename
            _loaded_conversation = None
            _loaded_conversation_filename = None
            _notify_safe(f"OK Conversation '{old_filename}' retirée du contexte de l'IA", 'positive')
        else:
            _notify_safe("ℹ️ Aucune conversation n'est actuellement chargée dans le contexte", 'info')
        return True
    
    return False


async def _display_conversation_as_attachment(filename: str, conversation: List[Dict]):
    """
    Affiche une conversation chargée comme une pièce jointe dans l'interface
    Réutilise le système existant de _active_file_data
    """
    global _active_file_data
    
    # Créer un résumé de la conversation pour l'affichage
    conversation_summary = f"📚 Conversation archivée: {filename}\n"
    conversation_summary += f"STATS {len(conversation)} messages\n\n"
    
    # Ajouter les premiers messages comme aperçu
    sample_size = min(3, len(conversation))
    for i, msg in enumerate(conversation[:sample_size]):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:100] + ('...' if len(msg.get('content', '')) > 100 else '')
        icon = "USER" if role == 'user' else "🌙" if role == 'assistant' else "AI"
        conversation_summary += f"{icon} {role}: {content}\n\n"
    
    if len(conversation) > sample_size:
        conversation_summary += f"... et {len(conversation) - sample_size} autres messages\n"
    
    # Stocker dans le système de fichier actif pour affichage en pièce jointe
    _active_file_data = {
        'filename': f"📚 {filename}",
        'content': conversation_summary,
        'type': 'conversation',
        'full_conversation': conversation,  # Stockage de la conversation complète
        'conversation_filename': filename
    }
    
    # Déclencher la mise à jour de l'affichage du header avec la pièce jointe
    _update_header_display()
    
    print(f"[CONVERSATION-ATTACHMENT] OK Conversation affichée comme pièce jointe: {filename}")


async def _display_archived_conversation(filename: str, conversation: List[Dict]):
    """Affiche une conversation archivée dans le chat"""
    global _chat_inner
    
    with _get_ogma()._chat_inner:
        ui.html(f"""
        <div class="archived-conversation">
            <div class="system-message">
                📚 <strong>Conversation archivée chargée:</strong> {filename}
                <br>STATS <strong>{len(conversation)} messages</strong>
            </div>
        </div>
        """)
        
        # Afficher un échantillon des messages
        sample_size = min(5, len(conversation))
        for i, msg in enumerate(conversation[:sample_size]):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200] + ('...' if len(msg.get('content', '')) > 200 else '')
            
            icon = "USER" if role == 'user' else "🌙" if role == 'assistant' else "AI"
            ui.html(f"""
            <div class="archived-message">
                <small>{icon} <strong>{role}:</strong> {content}</small>
            </div>
            """)
        
        if len(conversation) > sample_size:
            ui.html(f"<small>... et {len(conversation) - sample_size} autres messages</small>")


async def _display_search_results(search_term: str, results: List[Dict]):
    """Affiche les résultats de recherche dans les conversations"""
    global _chat_inner
    
    with _get_ogma()._chat_inner:
        ui.html(f"""
        <div class="search-results">
            <div class="system-message">
                SEARCH <strong>Recherche:</strong> "{search_term}"
                <br>STATS <strong>{len(results)} résultats trouvés</strong>
            </div>
        </div>
        """)
        
        for result in results:
            conv_info = result['conversation']
            message = result['message']
            content = message.get('content', '')[:300] + ('...' if len(message.get('content', '')) > 300 else '')
            
            ui.html(f"""
            <div class="search-result">
                <div><strong>PAGE {conv_info['title']}</strong></div>
                <div><small>📁 {conv_info['filename']}</small></div>
                <div class="result-content">{content}</div>
            </div>
            """)


async def _display_conversation_summary(filename: str, summary: str):
    """Affiche le résumé d'une conversation"""
    global _chat_inner
    
    with _get_ogma()._chat_inner:
        ui.html(f"""
        <div class="conversation-summary">
            <div class="system-message">
                EDIT <strong>Résumé de:</strong> {filename}
            </div>
            <div class="summary-content">
                {summary}
            </div>
        </div>
        """)


async def _display_available_conversations():
    """Affiche la liste des conversations disponibles"""
    global _chat_inner
    
    conversations = archive.list_conversations()
    
    with _get_ogma()._chat_inner:
        ui.html(f"""
        <div class="available-conversations">
            <div class="system-message">
                📚 <strong>Conversations disponibles:</strong> {len(conversations)}
            </div>
        </div>
        """)
        
        if not conversations:
            ui.html("<div>Aucune conversation archivée trouvée.</div>")
        else:
            for conv in conversations[:10]:  # Limiter à 10
                size_mb = conv['size'] / 1024 / 1024
                ui.html(f"""
                <div class="conversation-item">
                    <div><strong>{conv['title']}</strong></div>
                    <div><small>📁 {conv['filename']} • {size_mb:.1f} MB</small></div>
                    <div><small>DATE {conv['modified']}</small></div>
                </div>
                """)
        
        ui.html("""
        <div class="commands-help">
            <small>
            IDEA <strong>Commandes disponibles:</strong><br>
            • "lis conversation [nom_fichier]" - Charger une conversation dans le contexte IA<br>
            • "cherche '[terme]' dans conversations" - Rechercher dans l'historique<br>
            • "résumé conversation [nom_fichier]" - Créer un résumé<br>
            • "vider conversation" - Retirer la conversation du contexte IA
            </small>
        </div>
        """)

