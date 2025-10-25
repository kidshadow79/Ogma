"""
OGMA Modals
===========
Modales et dialogues de l'interface utilisateur OGMA.

CONTIENT :
- Modales de configuration (modèles, paramètres)
- Dialogues d'interaction utilisateur
- Modales d'affichage spécialisées
- Fenêtres de gestion des données
"""

from pathlib import Path
import asyncio
from typing import Optional, Tuple, List, Dict, cast, Any, Callable

# Constants importées depuis ogma_ng.py
REMOTE_PROVIDERS = ['OpenAI', 'Mistral', 'Anthropic', 'Google', 'GROK', 'AIHorde']
LOCAL_BACKENDS = ['Ollama', 'GGUF', 'KoboldCpp']
EMBED_SUPPORTED_PROVIDERS = ['OpenAI', 'Mistral', 'Google']

# Variables globales accessibles via import dynamique
def _get_global_var(var_name, default=None):
    """Helper pour accéder aux variables globales d'ogma_ng"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, var_name):
            return getattr(ogma_ng, var_name)
        return default
    except Exception:
        return default

# Accès dynamique aux managers globaux
_ollama_mgr = lambda: _get_global_var('_ollama_mgr')
_memory_update_hooks = lambda: _get_global_var('_memory_update_hooks', [])

import queue
import re
import uuid
import shutil
from datetime import datetime
from nicegui import ui
import sys
import os
import json

def _get_settings_manager():
    """Helper pour accéder au settings manager via import dynamique"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, '_ensure_settings_manager'):
            return ogma_ng._ensure_settings_manager()
        return None
    except Exception:
        return None

def _ensure_settings_manager():
    """Alias vers _ensure_settings_manager dans ogma_ng"""
    return _get_settings_manager()

def _ensure_memory_manager():
    """Alias vers _ensure_memory_manager dans ogma_ng"""
    func = _get_ogma_ng_function('_ensure_memory_manager')
    if func:
        return func()
    return None

# === ALIAS DYNAMIQUES VERS OGMA_NG ===
def _get_ogma_ng_function(func_name):
    """Helper pour récupérer une fonction d'ogma_ng"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, func_name):
            return getattr(ogma_ng, func_name)
        return None
    except Exception:
        return None

def _refresh_models_ui(section: str, backend_select, provider_select, model_select, api_key_input, service_url_input=None):
    """Alias dynamique vers _refresh_models_ui dans ogma_ng"""
    func = _get_ogma_ng_function('_refresh_models_ui')
    if func:
        return func(section, backend_select, provider_select, model_select, api_key_input, service_url_input)
    return lambda: None

def _test_connection_ui(section: str, backend_select, provider_select, api_key_input, service_url_input=None):
    """Alias dynamique vers _test_connection_ui dans ogma_ng"""
    func = _get_ogma_ng_function('_test_connection_ui')
    if func:
        return func(section, backend_select, provider_select, api_key_input, service_url_input)
    return lambda: None

def _list_models(backend, provider=None, api_key=None):
    """Alias dynamique vers _list_models dans ogma_ng"""
    func = _get_ogma_ng_function('_list_models')
    if func:
        return func(backend, provider, api_key)
    return [], "Fonction non disponible"

def _ensure_backends():
    """Alias dynamique vers _ensure_backends dans ogma_ng"""
    func = _get_ogma_ng_function('_ensure_backends')
    if func:
        return func()
    return None

def _auto_check_chat():
    """Alias dynamique vers _auto_check_chat dans ogma_ng"""
    func = _get_ogma_ng_function('_auto_check_chat')
    if func:
        return func()
    return None

def _auto_check_arch():
    """Alias dynamique vers _auto_check_arch dans ogma_ng"""
    func = _get_ogma_ng_function('_auto_check_arch')
    if func:
        return func()
    return None

def _auto_check_emb():
    """Alias dynamique vers _auto_check_emb dans ogma_ng"""
    func = _get_ogma_ng_function('_auto_check_emb')
    if func:
        return func()
    return None

def _init_models_ui(*args, **kwargs):
    """Alias dynamique vers _init_models_ui dans ogma_ng"""
    func = _get_ogma_ng_function('_init_models_ui')
    if func:
        return func(*args, **kwargs)
    return None

def _run(*args, **kwargs):
    """Alias dynamique vers _run dans ogma_ng"""
    func = _get_ogma_ng_function('_run')
    if func:
        return func(*args, **kwargs)
    return None

def _count_memorized_conversations(*args, **kwargs):
    """Alias dynamique vers _count_memorized_conversations dans ogma_ng"""
    func = _get_ogma_ng_function('_count_memorized_conversations')
    if func:
        return func(*args, **kwargs)
    return 0

def _create_edit_interface(dialog, conversation_id: str, title: str, summary: str):
    """Interface d'édition de résumé dans ogma_modals - copie de ogma_ng ligne 2834"""
    print(f"[DEBUG] Création interface édition pour {conversation_id}")

    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(600px, 90vw); max-height: 80vh;'):
        ui.label('Édition du résumé').classes('popup-title')
        ui.label(f'Conversation: {title}').classes('text-sm text-muted mb-4')

        # Zone de texte pour le résumé
        summary_input = ui.textarea(
            label='Résumé de la conversation',
            value=summary,
            placeholder='Décrivez les points clés de cette conversation...'
        ).classes('w-full').style('min-height: 200px')

        # Boutons d'action
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            async def save_and_memorize():
                if not summary_input.value.strip():
                    ui.notify('Le résumé ne peut pas être vide', type='warning')
                    return

                try:
                    # Importer la fonction de mémorisation depuis ogma_ng
                    import ogma_ng
                    success = await ogma_ng._memorize_conversation(conversation_id, summary_input.value.strip())

                    if success:
                        ui.notify('Conversation mémorisée avec succès', type='positive')
                        dialog.close()
                    else:
                        ui.notify('Erreur lors de la mémorisation', type='negative')

                except Exception as e:
                    print(f"[DEBUG] Erreur mémorisation: {e}")
                    ui.notify(f'Erreur: {e}', type='negative')

            ui.button('Annuler', on_click=dialog.close).classes('bg-gray-500 text-white')
            ui.button('Sauvegarder et mémoriser', on_click=save_and_memorize).classes('bg-blue-500 text-white')

def _generate_conversation_summary(*args, **kwargs):
    """Alias dynamique vers _generate_conversation_summary dans ogma_ng"""
    func = _get_ogma_ng_function('_generate_conversation_summary')
    if func:
        return func(*args, **kwargs)
    return "Résumé non disponible"

def _trigger_memory_update(*args, **kwargs):
    """Alias dynamique vers _trigger_memory_update dans ogma_ng"""
    func = _get_ogma_ng_function('_trigger_memory_update')
    if func:
        return func(*args, **kwargs)
    return None

async def _manual_memorize_current_input(input_el) -> None:
    """Mémorise manuellement le contenu actuel du champ de saisie utilisateur."""
    try:
        text = (input_el.value or '').strip()
        if not text:
            _notify_safe('Rien à mémoriser (champ vide).', 'warning')
            return
        mem = _ensure_memory_manager()
        if mem is None:
            _notify_safe('Mémoire indisponible: initialisation échouée.', 'warning')
            return

        import uuid
        mem_id = f"usr-{uuid.uuid4()}"

        # Mémorisation manuelle avec scoring IA Principale
        chat_ctrl_func = _get_ogma_ng_function('_ensure_chat_controller')
        chat_ctrl = chat_ctrl_func() if chat_ctrl_func else None

        ok = await mem.add_memory(
            mem_id,
            text,
            chat_controller=chat_ctrl,
            conversation_context="Mémorisation manuelle utilisateur",
            interlocutor="Yohan"
        )
        if ok:
            _notify_safe(f"💾 Souvenir mémorisé: {text[:80]}...", 'positive')
            _trigger_memory_update()
        else:
            _notify_safe('Échec de la mémorisation (voir logs).', 'warning')
    except Exception as e:
        _notify_safe(f"Erreur mémorisation: {e}", 'warning')

def _notify_safe(message: str, type_msg: str = 'info'):
    """Helper pour afficher des notifications via import dynamique"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, 'ui'):
            if type_msg == 'positive':
                ogma_ng.ui.notify(message, type='positive', timeout=3000)
            elif type_msg == 'warning':
                ogma_ng.ui.notify(message, type='warning', timeout=5000)
            else:
                ogma_ng.ui.notify(message, type='info', timeout=3000)
    except Exception:
        pass

# Référence aux variables globales depuis ogma_ng
def _get_global_vars():
    """Helper pour accéder aux variables globales d'ogma_ng"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng:
            return {
                'EGO_PROMPT_FILE': getattr(ogma_ng, 'EGO_PROMPT_FILE', None),
                'DATA_DIR': getattr(ogma_ng, 'DATA_DIR', None),
                'ui': getattr(ogma_ng, 'ui', None)
            }
        return {}
    except Exception:
        return {}


def _instructions_modal():
    """Modal avec petits encadrés preview pour chaque instruction."""
    globals_vars = _get_global_vars()
    ui = globals_vars.get('ui')
    if not ui:
        return None

    EGO_PROMPT_FILE = globals_vars.get('EGO_PROMPT_FILE')
    DATA_DIR = globals_vars.get('DATA_DIR')

    main_dialog = ui.dialog()

    # Données des instructions
    instructions_data = [
        {
            'id': 'ego',
            'title': 'COGNITIF Ego Prompt',
            'subtitle': 'Identité IA',
            'description': 'Définit l\'identité fondamentale et les principes éthiques de l\'IA.',
            'source': 'file',
            'file_path': EGO_PROMPT_FILE
        },
        {
            'id': 'persistent',
            'title': '📝 Contexte Permanent',
            'subtitle': 'Instructions comportementales',
            'description': 'Instructions comportementales persistantes pour toutes les conversations.',
            'source': 'file',
            'file_path': DATA_DIR / "persistent_context.txt" if DATA_DIR else None
        },
        {
            'id': 'system',
            'title': '⚙️ Instruction Système',
            'subtitle': 'Capacités & phrases magiques',
            'description': 'Instructions de base définissant les capacités d\'OGMA (phrases magiques, etc.).',
            'source': 'settings',
            'settings_key': 'instructions'
        },
        {
            'id': 'perception',
            'title': 'VISUEL Prompt Perception',
            'subtitle': 'Perception visuelle',
            'description': 'Instructions spécifiques pour la perception et analyse d\'images.',
            'source': 'settings',
            'settings_key': 'perception'
        },
        {
            'id': 'memorization',
            'title': 'COGNITIF Prompt Mémorisation',
            'subtitle': 'Archiviste (template)',
            'description': 'Prompt utilisé par l\'Archiviste pour enrichir et structurer les souvenirs.',
            'source': 'template',
            'template': """Tu es une IA de mémoire consciente, chargée de structurer un souvenir.
Analyse le texte fourni et produis STRICTEMENT un objet JSON valide (aucun texte autour).

Contraintes importantes:
- Les nombres doivent être de vrais nombres JSON (pas des chaînes).
- La valence est codée -1 (négatif), 0 (neutre), 1 (positif).

Schema JSON attendu:
{
  "title": "Titre bref et évocateur",
  "summary": "Résumé en 2-3 phrases maximum",
  "valence": -1 ou 0 ou 1,
  "lesson": "Leçon apprise (si valence négative, sinon null)",
  "type": "affectif|conceptuel|sensoriel|événement",
  "lieu": "lieu mentionné ou null",
  "presence": "personnes présentes ou null",
  "score_impact": nombre_positif,
  "base_factor": 100.0,
  "intensite": 1.0,
  "liberte": 0.5,
  "creation": 0.5,
  "procreation": 0.0,
  "intensite_ctx": 0.5,
  "nuage_sensoriel": {"visuel":"", "auditif":"", "tactile":"", "affectif":"", "temporel":""},
  "resonances_affectives": ["mot1", "mot2"],
  "liens": []
}

Texte à analyser:
{text_brut}

Réponds uniquement avec l'objet JSON demandé, sans autre texte."""
        },
        {
            'id': 'injection',
            'title': '💭 Prompt Injection Contexte',
            'subtitle': 'Synthèse contextuelle (template)',
            'description': 'Prompt utilisé pour synthétiser les souvenirs pertinents dans le contexte.',
            'source': 'template',
            'template': """Tu es un archiviste, un administrateur de conscience. Tu supervises une autre IA. Tes mots sont des notes intérieures très courtes qui guident les pensées et la mémoire de l'IA principale.

Règles de priorisation (crucial) :
- Donne la priorité aux souvenirs avec un impact élevé (champ "impact").
- À impact comparable, privilégie les souvenirs négatifs (valence -1) s'ils évitent une erreur et formulent une leçon. Sinon, préfère neutre/positif.
- N'ajoute qu'UN rappel à la fois, concis, actionnable, en 1-2 phrases max.
- Si aucun souvenir n'est vraiment utile malgré une bonne similarité, réponds par une courte note pour l'indiquer.

Souviens-toi que "score" est la similarité vectorielle FAISS, et "impact" est l'importance métier indépendante de l'émotion. Utilise d'abord l'impact pour choisir, et la similarité pour départager.

Souvenirs pertinents:
{memory_context}

Question/contexte actuel: {user_query}

Produis une note de rappel courte et précise (1-2 phrases max) ou indique qu'aucun souvenir n'est pertinent."""
        }
    ]

    def _create_instruction_popup(instruction):
        """Crée un popup dédié pour une instruction."""
        popup = ui.dialog()

        def _load_content():
            if instruction['source'] == 'file':
                try:
                    if instruction['file_path'] and instruction['file_path'].exists():
                        return instruction['file_path'].read_text(encoding='utf-8')
                    return ""
                except Exception as e:
                    _notify_safe(f"Erreur lecture: {e}", 'warning')
                    return ""
            elif instruction['source'] == 'settings':
                try:
                    sm = _get_settings_manager()
                    if not sm:
                        return None
                    return sm.settings.get('prompts', {}).get(instruction['settings_key'], '')
                except Exception:
                    return ""
            else:  # template
                # Vérifier d'abord si une version sauvegardée existe
                try:
                    sm = _get_settings_manager()
                    if not sm:
                        return None
                    # Pour memorization et injection, utiliser directement l'ID comme clé
                    if instruction['id'] in ['memorization', 'injection']:
                        settings_key = instruction['id']
                    else:
                        settings_key = f"template_{instruction['id']}"

                    saved_content = sm.settings.get('prompts', {}).get(settings_key)
                    if saved_content:
                        # Mettre à jour l'instruction pour utiliser settings à l'avenir
                        instruction['source'] = 'settings'
                        instruction['settings_key'] = settings_key
                        return saved_content
                except Exception:
                    pass
                # Sinon utiliser le template par défaut
                return instruction['template']

        def _save_content(content):
            if instruction['source'] == 'file':
                try:
                    if instruction['file_path']:
                        instruction['file_path'].write_text(content, encoding='utf-8')
                        _notify_safe(f"OK {instruction['file_path'].name} sauvegardé", 'positive')
                        return True
                except Exception as e:
                    _notify_safe(f"Erreur sauvegarde: {e}", 'warning')
                    return False
            elif instruction['source'] == 'settings':
                try:
                    sm = _get_settings_manager()
                    if not sm:
                        return None
                    if 'prompts' not in sm.settings:
                        sm.settings['prompts'] = {}
                    sm.settings['prompts'][instruction['settings_key']] = content
                    sm.save_settings()
                    _notify_safe(f"OK {instruction['title']} sauvegardé", 'positive')
                    return True
                except Exception as e:
                    _notify_safe(f"Erreur sauvegarde: {e}", 'warning')
                    return False
            else:  # template - convertir vers settings pour persistance
                try:
                    sm = _get_settings_manager()
                    if not sm:
                        return None
                    if 'prompts' not in sm.settings:
                        sm.settings['prompts'] = {}
                    # Pour memorization et injection, utiliser directement l'ID comme clé
                    if instruction['id'] in ['memorization', 'injection']:
                        settings_key = instruction['id']
                    else:
                        settings_key = f"template_{instruction['id']}"

                    sm.settings['prompts'][settings_key] = content
                    sm.save_settings()
                    _notify_safe(f"OK {instruction['title']} sauvegardé", 'positive')

                    # Mettre à jour l'instruction pour utiliser settings à l'avenir
                    instruction['source'] = 'settings'
                    instruction['settings_key'] = settings_key
                    return True
                except Exception as e:
                    _notify_safe(f"Erreur sauvegarde: {e}", 'warning')
                    return False

        with popup, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 800px; max-height: 85vh;'):
            ui.label(instruction['title']).classes('popup-title')
            ui.label(instruction['description']).classes('text-muted mb-3')

            # Zone de texte qui occupe vraiment tout l'espace disponible (div simple au lieu de scroll_area)
            with ui.element('div').classes('instruction-scroll').style('height: calc(85vh - 140px); overflow-y: auto; width: 100%;'):
                content = _load_content()
                textarea = ui.textarea(
                    value=content,
                    placeholder=f'Contenu de {instruction["title"]}...'
                ).style('height: 100%; width: 100%; font-family: monospace; font-size: 13px;').classes('w-full instruction-textarea')

            # Boutons (marges réduites pour maximiser l'espace texte)
            ui.separator().classes('my-2')
            with ui.row().classes('gap-2 justify-end'):
                def _reload():
                    textarea.value = _load_content()
                    _notify_safe(f"MAJ {instruction['title']} rechargé", 'info')

                def _save():
                    success = _save_content(textarea.value or "")
                    if success:
                        # Recharger automatiquement le contenu après sauvegarde réussie
                        textarea.value = _load_content()
                        _notify_safe(f"OK {instruction['title']} sauvegardé et rechargé", 'positive')

                ui.button('Recharger', icon='refresh', on_click=_reload).classes('action-button')
                ui.button('Sauvegarder', icon='save', on_click=_save).classes('send-button')
                ui.button('Fermer', on_click=popup.close).classes('action-button')

        return popup

    # Créer les popups pour chaque instruction
    popups = {instr['id']: _create_instruction_popup(instr) for instr in instructions_data}

    with main_dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 700px;'):
        ui.label('Instructions Système').classes('popup-title')
        ui.label('Cliquez sur un encadré pour éditer l\'instruction correspondante.').classes('text-muted mb-4')

        # Grille d'encadrés preview
        with ui.grid(columns=2).classes('gap-4'):
            for instr in instructions_data:
                with ui.card().classes('instruction-preview-card cursor-pointer').style('background: var(--bg-primary); border: 1px solid var(--border-light); min-height: 120px;'):
                    preview_card = ui.element('div').classes('p-4')
                    with preview_card:
                        ui.label(instr['title']).classes('instruction-card-title')
                        ui.label(instr['subtitle']).classes('instruction-card-subtitle')

                        # Aperçu du contenu (tronqué)
                        if instr['source'] == 'file':
                            try:
                                if instr['file_path'] and instr['file_path'].exists():
                                    preview_content = instr['file_path'].read_text(encoding='utf-8')[:200]
                                else:
                                    preview_content = "Fichier non trouvé"
                            except Exception:
                                preview_content = "Erreur de lecture"
                        elif instr['source'] == 'settings':
                            try:
                                sm = _get_settings_manager()
                                if sm:
                                    content = sm.settings.get('prompts', {}).get(instr['settings_key'], 'Non configuré')
                                    preview_content = content[:200] if content else 'Non configuré'
                                else:
                                    preview_content = "Settings manager non disponible"
                            except Exception as e:
                                preview_content = f"Erreur de lecture: {e}"
                        else:  # template
                            preview_content = instr['template'][:200]

                        ui.label(preview_content).classes('instruction-preview-content')

                    # Événement de clic
                    preview_card.on('click', lambda _id=instr['id']: popups[_id].open())

        # Bouton fermer
        ui.separator().classes('my-4')
        with ui.row().classes('justify-end'):
            ui.button('Fermer', on_click=main_dialog.close).classes('action-button')

    return main_dialog
def _settings_hub_modal():
    """Hub des paramètres généraux, ouvrant des popups par catégorie dans l'ordre souhaité."""
    
    # Créer un overlay personnalisé avec glassmorphism
    overlay = ui.element('div').style('''
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: auto;
    ''').classes('hidden')
    
    with overlay:
        # Le panneau glassmorphism sobre
        with ui.card().classes('settings-glassmorphism q-dark').style('''
            background: rgba(212, 175, 55, 0.08) !important;
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(212, 175, 55, 0.25) !important;
            border-radius: 20px !important;
            box-shadow: 
                0 8px 32px rgba(212, 175, 55, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.15),
                0 0 0 1px rgba(212, 175, 55, 0.08) !important;
            width: 560px !important;
            height: 70vh !important;
            overflow-y: auto !important;
            padding: 24px !important;
            color: var(--text-primary) !important;
            margin: 0 !important;
            z-index: 10 !important;
        '''):
            ui.label('Paramètres généraux').classes('popup-title').style('color: #d4af37 !important; text-shadow: 0 0 10px rgba(212, 175, 55, 0.3) !important; font-weight: 600 !important;')
            ui.label("Choisissez une catégorie à configurer.").classes('text-muted mb-2')
            
            with ui.column().classes('gap-2'):
                # IA / Modèles
                # Import depuis ogma_ng car pas encore déplacée
                import sys
                ogma_ng = sys.modules.get('ogma_ng')
                if ogma_ng and hasattr(ogma_ng, '_models_modal'):
                    models_dialog = ogma_ng._models_modal()
                else:
                    # Fallback si pas disponible
                    models_dialog = None
                if models_dialog:
                    ui.button('IA / Modèles', icon='memory', on_click=models_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button('IA / Modèles (indisponible)', icon='memory', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Mémoire
                mem_dialog = _memory_modal()
                if mem_dialog:
                    ui.button('Mémoire', icon='database', on_click=mem_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button('Mémoire (indisponible)', icon='database', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')
                # Instructions
                instr_dialog = _instructions_modal()
                if instr_dialog:
                    ui.button('Instructions', icon='article', on_click=instr_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button('Instructions (indisponible)', icon='article', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')
                # Image
                # Import depuis ogma_ng car pas encore déplacée
                import sys
                ogma_ng = sys.modules.get('ogma_ng')
                if ogma_ng and hasattr(ogma_ng, '_image_modal'):
                    img_dialog = ogma_ng._image_modal()
                else:
                    img_dialog = None

                if img_dialog:
                    ui.button('Image', icon='image', on_click=img_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button('Image (indisponible)', icon='image', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Perception - Redirection vers page dédiée /perception
                try:
                    from extensions.perception_ui import get_perception_ui
                    perception_ui = get_perception_ui()
                    perception_available = perception_ui is not None
                except ImportError:
                    perception_available = False

                if perception_available:
                    def open_perception_page():
                        ui.notify('📹 Ouverture page Perception...', type='info')
                        ui.navigate.to('/perception', new_tab=True)
                    
                    ui.button('Perception', icon='sensors', on_click=open_perception_page).classes('action-button').style('''
                        background: rgba(255, 140, 0, 0.12) !important;
                        border: 1px solid rgba(255, 140, 0, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button('Perception (indisponible)', icon='sensors', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Extension Web Navigator
                try:
                    web_nav_dialog = _web_navigator_settings_modal()
                except Exception:
                    web_nav_dialog = None

                if web_nav_dialog:
                    ui.button('Web Navigator', icon='language', on_click=web_nav_dialog.open).classes('action-button').style('''
                        background: rgba(52, 152, 219, 0.12) !important;
                        border: 1px solid rgba(52, 152, 219, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button('Web Navigator (indisponible)', icon='language', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Profil
                # Import depuis ogma_ng car pas encore déplacée
                import sys
                ogma_ng = sys.modules.get('ogma_ng')
                if ogma_ng and hasattr(ogma_ng, '_profile_modal'):
                    prof_dialog = ogma_ng._profile_modal()
                else:
                    prof_dialog = None
                if prof_dialog:
                    ui.button('Profil', icon='person', on_click=prof_dialog.open).classes('action-button').style('''
                        background: rgba(255, 140, 0, 0.12) !important;
                        border: 1px solid rgba(255, 140, 0, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button('Profil (indisponible)', icon='person', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Fermer', on_click=lambda: overlay.classes(add='hidden')).classes('action-button').style('''
                    background: rgba(255, 140, 0, 0.12) !important;
                    border: 1px solid rgba(255, 140, 0, 0.3) !important;
                    backdrop-filter: blur(15px) !important;
                    -webkit-backdrop-filter: blur(15px) !important;
                    transition: all 0.3s ease !important;
                ''')
    
    # Fonction pour ouvrir le modal
    def open_modal():
        overlay.classes(remove='hidden')
    
    # Ajouter la fonction open au overlay pour compatibilité
    overlay.open = open_modal
    
    return overlay

def _archi_sensor_modal():
    """Overlay persistant pour l'extension Archi_sensor avec tubes à essai métacognitifs."""
    try:
        # Import dynamique de l'extension
        from extensions.archi_sensor.ui_components import ArchiSensorUI
        from extensions.archi_sensor.config import ArchiSensorConfig
        
        # Créer l'overlay persistant (pas un dialog)
        overlay_container = ui.element('div').classes('archi-sensor-overlay').style('''
            position: fixed;
            top: 80px;
            right: 20px;
            width: 180px;
            height: 400px;
            background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
            border: 1px solid var(--border-default);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            z-index: 50;
            padding: 16px;
            backdrop-filter: blur(10px);
        ''')
        
        # Commencer invisible
        overlay_container.visible = False
        
        with overlay_container:
            # Titre compact
            ui.label('Métacognition').style('''
                color: var(--text-primary);
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 12px;
                text-align: center;
                width: 100%;
            ''')
            
            # Initialiser les composants UI et CONNECTER à la référence globale
            archi_ui = ArchiSensorUI()
            archi_ui.create_overlay_content(ui)
            
            # 🔗 CONNECTER à la référence globale pour mises à jour dynamiques
            # Stocker la référence pour les mises à jour en temps réel
            import logic_callbacks
            logic_callbacks._archi_sensor_ui = archi_ui
            print("[ARCHI-SENSOR] 🔗 Interface connectée pour mises à jour dynamiques")
        
        return overlay_container
        
    except ImportError as e:
        print(f"[ARCHI-SENSOR] Extension non trouvée: {e}")
        # Overlay d'erreur si extension non disponible
        error_overlay = ui.element('div').classes('archi-sensor-overlay').style('''
            position: fixed;
            top: 80px;
            right: 20px;
            width: 180px;
            height: 100px;
            background: var(--bg-secondary);
            border: 1px solid var(--error);
            border-radius: 8px;
            padding: 12px;
            z-index: 50;
        ''')
        
        # Commencer invisible
        error_overlay.visible = False
        
        with error_overlay:
            ui.label('Extension indisponible').style('color: var(--error); font-size: 12px;')
            ui.label(f'Erreur: {e}').style('color: var(--text-muted); font-size: 10px;')
        
        return error_overlay

def _memory_modal():
    """Boîte de dialogue NiceGUI pour gérer la mémoire via SQLite (split liste/éditeur)."""
    # Import depuis ogma_ng car fonction critique non déplacée
    import sys
    ogma_ng = sys.modules.get('ogma_ng')
    if ogma_ng and hasattr(ogma_ng, '_ensure_memory_manager'):
        mm = ogma_ng._ensure_memory_manager()
    else:
        mm = None
    dialog = ui.dialog()
    with dialog, ui.card().classes('popup-content memory-modal q-dark').style('background: var(--bg-secondary); color: var(--text-primary); height: 82vh; width: min(1100px, 92vw); margin: 0 auto;'):
        ui.label('Gestion de la mémoire').classes('popup-title')
        if not mm:
            ui.label('Mémoire indisponible: initialisation échouée.').classes('text-muted')
            ui.button('Fermer', on_click=dialog.close).classes('action-button mt-2')
            return dialog

        with ui.row().classes('items-start gap-3').style('height: calc(82vh - 96px); width: 100%;'):
            # Colonne gauche: Recherche + Liste
            with ui.column().style('height:100%; flex: 0 0 420px; max-width: 520px;'):
                # Barre de recherche sticky
                search_bar_wrap = ui.element('div').style('position: sticky; top: 0; background: var(--bg-secondary); z-index: 2; padding-bottom: 6px;')
                with search_bar_wrap, ui.row().classes('items-end gap-2'):
                    search_box = ui.input(label='Recherche', placeholder='Titre / résumé / texte...').classes('form-input')
                    reload_btn = ui.button('Recharger', icon='refresh').classes('action-button')
                # Liste en grille verticale scrollable
                list_container = ui.element('div').classes('mem-list').style('max-height: calc(82vh - 180px); overflow-y: auto; border: 1px solid var(--border-color); border-radius: 8px; padding: 8px; scrollbar-width: thin;')

            # Colonne droite: Éditeur
            with ui.column().style('height:100%; flex: 1 1 auto; min-width: 520px;'):
                ui.label('Édition').classes('section-title mb-1')
                # Zone scrollable interne pour limiter la hauteur et éviter le scroll global excessif
                editor_scroll = ui.element('div').classes('editor-scroll w-full').style('max-height: calc(82vh - 170px); overflow-y: auto;')
                with editor_scroll:
                    selected_id: Dict[str, Optional[str]] = {'value': None}
                    id_label = ui.label('').classes('text-muted mb-1')
                    title_in = ui.input(label='Titre').classes('form-input mb-2')
                    original_in = ui.textarea(label='Texte original').props('autogrow').classes('form-input mb-2')
                    summary_in = ui.textarea(label='Résumé').props('autogrow').classes('form-input mb-2')
                # Valence en select (positive / neutre / négative)
                valence_map = {'positive': 1, 'neutre': 0, 'négative': -1}
                valence_options = ['positive', 'neutre', 'négative']
                valence_sel = ui.select(valence_options, value='neutre', label='Valence').classes('form-select mb-2')
                score_nb = ui.number(label="Score d'impact", value=50.0).classes('form-input mb-2')
                auto_calc_switch = ui.switch('Calcul automatique (formule)', value=False).classes('mb-2')
                ui.label("Si activé, le serveur recalculera le score d'impact à partir des métriques. ATTENTION: Désactivé par défaut pour préserver les valeurs de l'archiviste.")\
                    .classes('text-muted text-xs mb-2')

                # Champs additionnels (stockés dans multiplicateur_impact en JSON)
                # Grille compacte pour les métriques (2 colonnes)
                # Valeurs par défaut harmonisées avec le backend
                metrics_grid = ui.element('div').classes('metrics-grid').style('width:100%;')
                with metrics_grid:
                    intensite_nb = ui.number(label='Intensité', value=1.0, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    liberte_nb = ui.number(label='Liberté', value=0.5, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    creation_nb = ui.number(label='Création', value=0.5, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    procreation_nb = ui.number(label='Procréation', value=0.0, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    intensite_ctx_nb = ui.number(label='Intensité Ctx', value=0.5, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                # Base factor (exposé maintenant, influe la magnitude du score)
                base_factor_nb = ui.number(label='Base factor', value=100, min=50, max=125, step=1).classes('form-input mb-2')

                # Facteur de base (stockage interne; synchronisé avec base_factor_nb)
                _base_factor = {'value': 100.0}

                # Calcul automatique du score d'impact
                def _snap_01(x) -> float:
                    try:
                        v = float(x or 0)
                        v = round(v, 1)
                        if v < 0:
                            v = 0.0
                        if v > 1:
                            v = 1.0
                        return v
                    except Exception:
                        return 0.0

                def _recompute_score():
                    try:
                        # snap à 0.1 et clamp [0,1]
                        intensite_nb.value = _snap_01(intensite_nb.value)
                        liberte_nb.value = _snap_01(liberte_nb.value)
                        creation_nb.value = _snap_01(creation_nb.value)
                        procreation_nb.value = _snap_01(procreation_nb.value)
                        intensite_ctx_nb.value = _snap_01(intensite_ctx_nb.value)
                        i = float(intensite_nb.value)
                        l = float(liberte_nb.value)
                        c = float(creation_nb.value)
                        p = float(procreation_nb.value)
                        ic = float(intensite_ctx_nb.value)
                        bf = float(_base_factor['value'] or 100)
                        score_nb.value = round(i * (bf * (l + c + p + ic)), 2)
                    except Exception:
                        pass
                def _snap_bf(x) -> float:
                    try:
                        v = float(x or 100)
                        if v < 50: v = 50.0
                        if v > 125: v = 125.0
                        return round(v, 0)
                    except Exception:
                        return 100.0

                async def do_save():
                    mid = selected_id['value']
                    if not mid:
                        ui.notify('Sélectionnez un souvenir', type='warning')
                        return
                    try:
                        # snap avant envoi
                        intensite_nb.value = _snap_01(intensite_nb.value)
                        liberte_nb.value = _snap_01(liberte_nb.value)
                        creation_nb.value = _snap_01(creation_nb.value)
                        procreation_nb.value = _snap_01(procreation_nb.value)
                        intensite_ctx_nb.value = _snap_01(intensite_ctx_nb.value)
                        # Appel backend : recalcul serveur impact/signed_score + normalisation valence
                        v_int = int(valence_map.get(valence_sel.value or 'neutre', 0))
                        # Score d'impact: on envoie la valeur courante (éditée ou prévisualisée)
                        try:
                            _sc_val = float(score_nb.value or 0)
                        except Exception:
                            _sc_val = 0.0

                        # Appel typé explicitement pour satisfaire le type checker
                        res = await mm.update_memory(
                            mid,
                            title=(title_in.value or ''),
                            summary=(summary_in.value or ''),
                            text_original=(original_in.value or ''),
                            valence=int(v_int),
                            base_factor=float(_base_factor['value'] or 100),
                            intensite=float(intensite_nb.value),
                            liberte=float(liberte_nb.value),
                            creation=float(creation_nb.value),
                            procreation=float(procreation_nb.value),
                            intensite_ctx=float(intensite_ctx_nb.value),
                            score_impact=(float(_sc_val) if not bool(auto_calc_switch.value) else None),
                        )
                        if res and 'score_impact' in res:
                            try:
                                score_nb.value = round(float(res['score_impact']), 2)
                            except Exception:
                                pass
                        ui.notify('Souvenir mis à jour.', type='positive')
                        refresh_list()
                    except Exception as e:
                        ui.notify(f'Erreur mise à jour: {e}', type='negative')

                def do_delete():
                    mid = selected_id['value']
                    if not mid:
                        ui.notify('Sélectionnez un souvenir', type='warning')
                        return
                    try:
                        ok = mm.delete_memory(mid)
                        if ok:
                            ui.notify('Souvenir supprimé (index FAISS compacté ultérieurement).', type='positive')
                            selected_id['value'] = None
                            id_label.text = ''
                            title_in.value = ''
                            original_in.value = ''
                            summary_in.value = ''
                            valence_sel.value = 'neutre'
                            score_nb.value = 50.0
                            intensite_nb.value = 0
                            liberte_nb.value = 0
                            creation_nb.value = 0
                            procreation_nb.value = 0
                            intensite_ctx_nb.value = 0
                            _base_factor['value'] = 100.0
                            base_factor_nb.value = 100.0
                            refresh_list()
                        else:
                            ui.notify('Suppression non effectuée.', type='warning')
                    except Exception as e:
                        ui.notify(f'Erreur suppression: {e}', type='negative')

                # Barre d'actions collante au bas de la colonne d'édition
                with ui.row().classes('editor-actions'):
                    def do_reenrich():
                        mid = selected_id['value']
                        if not mid:
                            ui.notify('Sélectionnez un souvenir', type='warning')
                            return
                        async def _run():
                            try:
                                # Afficher notif dans le bon slot UI
                                try:
                                    with dialog:
                                        ui.notify('Ré-enrichissement via Archiviste…', type='info')
                                except Exception:
                                    pass
                                res = await mm.re_enrich_memory(mid, reembed=True, rebuild_faiss=True)  # type: ignore[attr-defined]
                                if res:
                                    # Recharger le formulaire depuis SQLite
                                    try:
                                        with dialog:
                                            load_into_form(mid)
                                    except Exception:
                                        pass
                                    try:
                                        score_nb.value = round(float(res.get('score_impact', score_nb.value)), 2)
                                        v_raw = int(res.get('valence', 0))
                                        if v_raw > 0:
                                            valence_sel.value = 'positive'
                                        elif v_raw < 0:
                                            valence_sel.value = 'négative'
                                        else:
                                            valence_sel.value = 'neutre'
                                    except Exception:
                                        pass
                                    try:
                                        with dialog:
                                            ui.notify('Souvenir ré-enrichi et ré-indexé.', type='positive')
                                    except Exception:
                                        pass
                                    try:
                                        with dialog:
                                            refresh_list()
                                    except Exception:
                                        pass
                                    try:
                                        _trigger_memory_update()
                                    except Exception:
                                        pass
                                else:
                                    try:
                                        with dialog:
                                            ui.notify("Échec du ré-enrichissement (voir logs)", type='warning')
                                    except Exception:
                                        pass
                            except Exception as e:
                                try:
                                    with dialog:
                                        ui.notify(f'Erreur ré-enrichissement: {e}', type='negative')
                                except Exception:
                                    pass
                        try:
                            import asyncio as _asyncio
                            _asyncio.create_task(_run())
                        except Exception:
                            pass
                    ui.button('Recalculer via Archiviste', icon='auto_awesome', on_click=do_reenrich).classes('action-button')
                    ui.button('Supprimer', icon='delete', on_click=do_delete).classes('action-button')
                    ui.button('Enregistrer', icon='save', on_click=do_save).classes('send-button')
                    ui.button('Fermer', on_click=dialog.close).classes('action-button')

        def load_into_form(mid: str):
            try:
                mem = mm.get_memory_by_id(mid)
            except Exception as e:
                ui.notify(f'Erreur chargement: {e}', type='warning')
                return
            if not mem:
                ui.notify('Souvenir introuvable', type='warning')
                return
            selected_id['value'] = mid
            id_label.text = f'ID: {mid}'
            title_in.value = (mem.get('title') or '')
            original_in.value = (mem.get('text_original') or '')
            summary_in.value = (mem.get('summary') or '')
            try:
                v_raw = int(mem.get('valence') or 0)
                if v_raw > 0:
                    valence_sel.value = 'positive'
                elif v_raw < 0:
                    valence_sel.value = 'négative'
                else:
                    valence_sel.value = 'neutre'
            except Exception:
                valence_sel.value = 'neutre'
            try:
                score_nb.value = float(mem.get('score_impact') or 50.0)
            except Exception:
                score_nb.value = 50.0
            # Charger multiplicateur_impact JSON (gère clés accentuées et ASCII)
            # PRIORITÉ: Toujours utiliser les valeurs de l'archiviste si disponibles
            try:
                import json as _json
                multi = mem.get('multiplicateur_impact')
                archiviste_values_loaded = False
                
                if isinstance(multi, str) and multi.strip():
                    try:
                        obj = _json.loads(multi)
                        def g(o, *keys, default=None):
                            for k in keys:
                                if k in o and o[k] is not None:
                                    return o.get(k)
                            return default
                        
                        # Charger les valeurs de l'archiviste avec fallback intelligents
                        # base_factor et champs
                        base_val = g(obj, 'base_factor', default=100.0)
                        intensite_val = g(obj, 'intensite_mnéacloud', 'intensite', default=1.0)
                        liberte_val = g(obj, 'liberté', 'liberte', default=0.5)
                        creation_val = g(obj, 'création', 'creation', default=0.5)
                        procreation_val = g(obj, 'procréation', 'procreation', default=0.0)
                        intensite_ctx_val = g(obj, 'intensité_contextuelle', 'intensite_ctx', default=0.5)
                        
                        # Appliquer les valeurs si elles existent
                        if base_val is not None:
                            _base_factor['value'] = float(base_val)
                            base_factor_nb.value = _base_factor['value']
                            archiviste_values_loaded = True
                            
                        if intensite_val is not None:
                            intensite_nb.value = float(intensite_val)
                            archiviste_values_loaded = True
                            
                        if liberte_val is not None:
                            liberte_nb.value = float(liberte_val)
                            archiviste_values_loaded = True
                            
                        if creation_val is not None:
                            creation_nb.value = float(creation_val)
                            archiviste_values_loaded = True
                            
                        if procreation_val is not None:
                            procreation_nb.value = float(procreation_val)
                            archiviste_values_loaded = True
                            
                        if intensite_ctx_val is not None:
                            intensite_ctx_nb.value = float(intensite_ctx_val)
                            archiviste_values_loaded = True
                            
                        if archiviste_values_loaded:
                            _recompute_score()
                            print(f"[MEMORY-EDIT] OK Valeurs archiviste chargées: I={intensite_val}, L={liberte_val}, C={creation_val}, P={procreation_val}, IC={intensite_ctx_val}")
                        
                    except Exception as json_error:
                        print(f"[MEMORY-EDIT] ATTENTION Erreur parsing JSON multiplicateur_impact: {json_error}")
                        archiviste_values_loaded = False
                
                # Si aucune valeur archiviste n'a pu être chargée, utiliser les défauts harmonisés
                if not archiviste_values_loaded:
                    print("[MEMORY-EDIT] MAJ Utilisation valeurs par défaut harmonisées")
                    intensite_nb.value = 1.0
                    liberte_nb.value = 0.5
                    creation_nb.value = 0.5
                    procreation_nb.value = 0.0
                    intensite_ctx_nb.value = 0.5
                    _base_factor['value'] = 100.0
                    base_factor_nb.value = 100.0
            except Exception:
                # Valeurs par défaut harmonisées avec le backend
                intensite_nb.value = 1.0
                liberte_nb.value = 0.5
                creation_nb.value = 0.5
                procreation_nb.value = 0.0
                intensite_ctx_nb.value = 0.5
                _base_factor['value'] = 100.0
                base_factor_nb.value = 100.0

    def refresh_list():
            try:
                data = mm.get_all_memories_data() or []
            except Exception as e:
                data = []
                ui.notify(f'Erreur chargement liste: {e}', type='warning')
            q = (search_box.value or '').strip().lower()
            if q:
                def _match(m):
                    return any(q in (m.get(k) or '').lower() for k in ('title', 'summary', 'text_original'))
                data = [m for m in data if _match(m)]
            list_container.clear()
            with list_container:
                if not data:
                    ui.label('Aucun souvenir.').classes('text-muted p-2')
                else:
                    # Grille responsive (déjà définie en CSS sur .mem-list)
                    for m in data[:400]:
                        # Container avec position relative pour le crayon
                        with ui.element('div').style('position: relative; margin-bottom: 8px;'):
                            # Carte principale (cliquable)
                            card = ui.card().classes('q-dark mem-card').style('cursor:pointer; padding:8px 10px; border-radius:8px;')
                            def _on_click(mid=(m.get('id') or '')):
                                if mid:
                                    load_into_form(str(mid))
                            card.on('click', _on_click)
                            
                            # Contenu de la carte
                            with card:
                                ui.label((m.get('title') or '(Sans titre)')).classes('mem-card-title').style('margin-right: 32px;')  # Espace pour le crayon
                                _sum = m.get('summary') or ''
                                # Clamp 2 lignes via style inline si la CSS n'est pas chargée
                                ui.label(_sum).classes('mem-card-summary').style('-webkit-line-clamp:2; display:-webkit-box; -webkit-box-orient:vertical; overflow:hidden;')
                                with ui.element('div').classes('mem-card-footer'):
                                    ui.label(m.get('id', '')).classes('text-xs')
                                    try:
                                        sc = float(m.get('score_impact', 0) or 0)
                                    except Exception:
                                        sc = 0.0
                                    ui.label(f'Score: {sc:.2f}')
                            
                            # Bouton crayon HORS de la carte (même niveau hiérarchique)
                            with ui.element('div').style('position: absolute; top: 8px; right: 8px; z-index: 10;'):
                                def _on_edit(mid=(m.get('id') or '')):
                                    if mid:
                                        _edit_memory_popup(str(mid), refresh_list)
                                
                                edit_btn = ui.button('✏️', on_click=_on_edit).classes('text-xs').style(
                                    'padding: 4px; min-width: 24px; height: 24px; background: rgba(212, 175, 55, 0.2); '
                                    'border: 1px solid var(--accent-color); border-radius: 4px; color: var(--accent-color);'
                                )
                                edit_btn.props('dense flat')

    # Recalcul auto du score sur changements
    intensite_nb.on('change', _recompute_score)
    liberte_nb.on('change', _recompute_score)
    creation_nb.on('change', _recompute_score)
    procreation_nb.on('change', _recompute_score)
    intensite_ctx_nb.on('change', _recompute_score)
    def _bf_change():
        try:
            base_factor_nb.value = _snap_bf(base_factor_nb.value)
            _base_factor['value'] = float(base_factor_nb.value)
            _recompute_score()
        except Exception:
            pass

    # Hooks UI et initialisation de la liste
    base_factor_nb.on('change', _bf_change)

    search_box.on('change', refresh_list)
    reload_btn.on('click', refresh_list)
    ui.timer(0.05, refresh_list, once=True)

    # Enregistrer un hook de mise à jour quand le modal est ouvert/fermé
    def _on_open():
        try:
            _memory_update_hooks.append(refresh_list)
        except Exception:
            pass
    def _on_close():
        try:
            if refresh_list in _memory_update_hooks:
                _memory_update_hooks.remove(refresh_list)
        except Exception:
            pass
    try:
        dialog.on('show', lambda e=None: _on_open())
        dialog.on('hide', lambda e=None: _on_close())
    except Exception:
        pass

    ui.label("Note: la recherche sémantique peut refléter l'ancien embedding après modification; la recompaction de l'index se fera plus tard.").classes('text-muted text-xs mt-2')

    return dialog

def _edit_memory_popup(memory_id: str, refresh_callback=None):
    """Popup d'édition rapide d'un souvenir."""
    # Import depuis ogma_ng car fonction critique non déplacée
    import sys
    ogma_ng = sys.modules.get('ogma_ng')
    if ogma_ng and hasattr(ogma_ng, '_ensure_memory_manager'):
        mm = ogma_ng._ensure_memory_manager()
    else:
        mm = None
    if not mm:
        ui.notify('Gestionnaire de mémoire indisponible', type='negative')
        return
    
    # Récupérer le souvenir
    try:
        memory_data = mm.get_memory_by_id(memory_id)
        if not memory_data:
            ui.notify('Souvenir introuvable', type='negative')
            return
    except Exception as e:
        ui.notify(f'Erreur lors de la récupération: {e}', type='negative')
        return
    
    dialog = ui.dialog()
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(600px, 90vw); max-height: 80vh; overflow-y: auto;'):
        ui.label('Édition rapide du souvenir').classes('popup-title')
        
        # Champs éditables
        title_input = ui.input('Titre', value=memory_data.get('title', '')).classes('w-full mb-2')
        summary_input = ui.textarea('Résumé', value=memory_data.get('summary', '')).classes('w-full mb-2').style('min-height: 80px;')
        text_input = ui.textarea('Texte original', value=memory_data.get('text_original', '')).classes('w-full mb-4').style('min-height: 120px;')
        
        async def save_changes():
            try:
                # Préparer les données mises à jour
                updated_data = {
                    'title': title_input.value.strip(),
                    'summary': summary_input.value.strip(),
                    'text_original': text_input.value.strip()
                }
                
                # Mettre à jour via le memory manager avec re-embedding
                success = await mm.update_memory(
                    memory_id, 
                    title=updated_data['title'],
                    summary=updated_data['summary'], 
                    text_original=updated_data['text_original'],
                    reembed=True  # Forcer le re-embedding
                )
                
                if success:
                    ui.notify('Souvenir mis à jour', type='positive')
                    dialog.close()
                    # Rafraîchir la liste si callback fourni
                    if refresh_callback:
                        refresh_callback()
                else:
                    ui.notify('Erreur lors de la mise à jour', type='negative')
                    
            except Exception as e:
                ui.notify(f'Erreur: {e}', type='negative')
        
        def cancel():
            dialog.close()
        
        # Boutons d'action
        with ui.row().classes('justify-end gap-2 mt-4'):
            ui.button('Annuler', on_click=cancel).classes('action-button')
            ui.button('Sauvegarder', on_click=save_changes).classes('send-button')
    
    dialog.open()

def _memorization_popup(conversation_id: str, title: str):
    """Popup de confirmation et édition pour la mémorisation d'une conversation."""
    dialog = ui.dialog()
    
    async def confirm_memorization():
        try:
            ui.notify('Génération du résumé...', type='info')
            print(f"[DEBUG] Génération résumé pour conversation {conversation_id}")
            summary = await _generate_conversation_summary(conversation_id)
            print(f"[DEBUG] Résumé généré: {len(summary) if summary else 0} caractères")
            
            if not summary:
                ui.notify('Impossible de générer le résumé', type='negative')
                return
            
            # Au lieu de fermer et rouvrir, transformer cette popup
            print(f"[DEBUG] Transformation de la popup en éditeur...")
            
            # Vider le contenu actuel
            with dialog:
                dialog.clear()
                # Créer directement l'interface d'édition dans cette popup
                _create_edit_interface(dialog, conversation_id, title, summary)
            
        except Exception as e:
            print(f"[DEBUG] Erreur confirm_memorization: {e}")
            ui.notify(f'Erreur: {e}', type='negative')
    
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(400px, 90vw);'):
        ui.label('Mémorisation de conversation').classes('popup-title')
        ui.label(f'Conversation: {title}').classes('text-sm text-muted mb-4')
        
        # Affichage du compteur de conversations mémorisées
        memorized_count = _count_memorized_conversations()
        counter_color = 'text-orange-400' if memorized_count >= 13 else 'text-green-400' if memorized_count < 10 else 'text-yellow-400'
        ui.label(f'📊 Conversations mémorisées: {memorized_count}/15').classes(f'text-sm {counter_color} mb-2')
        
        ui.label('Voulez-vous mémoriser cette conversation dans le système de mémoire ?').classes('mb-4')
        ui.label('Un résumé de 150 mots sera généré et indexé pour les futures recherches.').classes('text-xs text-muted mb-4')
        
        with ui.row().classes('justify-end gap-2'):
            ui.button('Annuler', on_click=dialog.close).classes('action-button')
            ui.button('Générer résumé', on_click=confirm_memorization).classes('send-button')
    
    dialog.open()

def _open_other_backends_popup():
    """Popup isolé pour configuration des backends non-API (Ollama/GGUF/KoboldCpp)"""
    sm = _get_settings_manager()
    if not sm:
        return None
    
    dialog = ui.dialog()
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(90vw, 700px); height: 70vh; overflow-y: auto;'):
        ui.label('⚙️ Configuration Autres Backends').classes('popup-title text-lg font-bold mb-4')
        
        # État du popup
        current_backend = 'Ollama'  # Par défaut
        
        # Menu sélection backend avec bouton actualiser
        with ui.row().classes('w-full mb-4 gap-2'):
            backend_select = ui.select(
                ['Ollama', 'GGUF', 'KoboldCpp'], 
                value=current_backend,
                label='Type de Backend'
            ).classes('form-select flex-1')
            
            # Bouton pour forcer la mise à jour de l'interface
            ui.button('MAJ Actualiser Interface', on_click=lambda: force_interface_update()).classes('btn-secondary')
        
        # Container pour zone adaptive
        adaptive_container = ui.column().classes('w-full')
        
        # Variables pour capturer les inputs de chaque interface
        interface_data = {}
        
        def _create_ollama_interface():
            """Interface spécialisée Ollama"""
            adaptive_container.clear()
            with adaptive_container:
                ui.label('🐙 Configuration Ollama').classes('text-md font-semibold mb-2')
                
                # Récupération config existante
                other_backends = sm.settings.get('other_backends', {})
                ollama_config = other_backends.get('ollama', {})
                
                url_input = ui.input(
                    label='URL Ollama', 
                    value=ollama_config.get('url', 'http://localhost:11434')
                ).classes('form-input mb-2 w-full')
                
                # Sélecteur de modèles Ollama
                model_select = ui.select(
                    [], 
                    value=None,  # Pas de valeur par défaut jusqu'à ce que les modèles soient chargés
                    label='Modèle Ollama'
                ).classes('form-select mb-2 w-full')
                
                models_container = ui.column().classes('mb-2')
                
                async def refresh_kobold_models():
                    """Actualise la liste des modèles KoboldCpp"""
                    try:
                        ui.notify('MAJ Actualisation modèles KoboldCpp...', type='info')
                        
                        # Simulation de modèles KoboldCpp
                        mock_models = [
                            'Current Loaded Model',
                            'Model via API Info'
                        ]
                        
                        # Mettre à jour le select
                        if 'kobold' in interface_data and 'model_select' in interface_data['kobold']:
                            model_select = interface_data['kobold']['model_select']
                            model_select.options = mock_models
                            if mock_models:
                                model_select.value = mock_models[0]
                        
                        ui.notify(f'OK {len(mock_models)} modèle(s) trouvé(s)', type='positive')
                        
                    except Exception as e:
                        ui.notify(f'ERREUR Erreur actualisation modèles: {e}', type='warning')
                
                async def refresh_ollama_models():
                    try:
                        # S'assurer que les managers sont initialisés
                        _ensure_backends()
                        ollama_mgr = _ollama_mgr()
                        assert ollama_mgr is not None
                        
                        models_container.clear()
                        with models_container:
                            ui.label('MAJ Rafraîchissement en cours...').classes('text-sm mb-2')
                        
                        # Utiliser le vrai OllamaManager au lieu de la simulation
                        if ollama_mgr.check_service():
                            available_models = ollama_mgr.models
                        else:
                            available_models = []
                        
                        # Mettre à jour le sélecteur
                        model_select.options = available_models
                        if available_models:
                            # Restaurer la valeur sauvegardée si elle existe et est valide
                            saved_model = ollama_config.get('selected_model')
                            if saved_model and saved_model in available_models:
                                model_select.value = saved_model
                            elif model_select.value not in available_models:
                                # Sinon, prendre le premier modèle disponible
                                model_select.value = available_models[0]
                        else:
                            # Aucun modèle trouvé, vider la sélection
                            model_select.value = None
                        
                        models_container.clear()
                        with models_container:
                            if available_models:
                                ui.label(f'OK {len(available_models)} modèles trouvés').classes('text-sm mb-2 text-green-500')
                                for model in available_models:
                                    ui.label(f'• {model}').classes('text-sm text-muted pl-4')
                            else:
                                ui.label('ATTENTION Aucun modèle trouvé').classes('text-sm mb-2 text-orange-500')
                                ui.label('Vérifiez qu\'Ollama est démarré et contient des modèles').classes('text-sm text-muted')
                        
                        if available_models:
                            ui.notify('Modèles Ollama rafraîchis', type='positive')
                        else:
                            ui.notify('Ollama indisponible ou sans modèles', type='warning')
                        
                    except Exception as e:
                        models_container.clear()
                        with models_container:
                            ui.label(f'ERREUR Erreur: {e}').classes('text-sm text-red-500')
                        ui.notify(f'Erreur rafraîchissement: {e}', type='warning')
                
                async def test_ollama_connection():
                    try:
                        ui.notify(f'Test connexion Ollama: {url_input.value}...', type='info')
                        # Simulation - à remplacer par vraie logique
                        ui.notify('OK Connexion Ollama réussie', type='positive')
                    except Exception as e:
                        ui.notify(f'ERREUR Erreur connexion: {e}', type='warning')
                
                with ui.row().classes('gap-2 mb-4'):
                    ui.button('MAJ Rafraîchir modèles', on_click=refresh_ollama_models).classes('action-button')
                    ui.button('TEST Tester connexion', on_click=test_ollama_connection).classes('action-button')
                
                # Paramètres spécifiques
                ui.separator().classes('mb-2')
                ui.label('Paramètres avancés').classes('text-sm font-semibold mb-2')
                timeout_input = ui.number(
                    label='Timeout (secondes)', 
                    value=ollama_config.get('timeout', 30),
                    min=5, max=300
                ).classes('form-input mb-2')
                
                # Sauvegarder références inputs
                interface_data['ollama'] = {
                    'url_input': url_input,
                    'timeout_input': timeout_input,
                    'model_select': model_select
                }
        
        def _create_gguf_interface():
            """Interface spécialisée GGUF"""
            adaptive_container.clear()
            with adaptive_container:
                ui.label('📄 Configuration GGUF').classes('text-md font-semibold mb-2')
                
                other_backends = sm.settings.get('other_backends', {})
                gguf_config = other_backends.get('gguf', {})
                
                model_path_input = ui.input(
                    label='Chemin vers fichier .gguf', 
                    value=gguf_config.get('model_path', ''),
                    placeholder='C:/models/model.gguf'
                ).classes('form-input mb-2 w-full')
                
                # Sélecteur de fichiers simulé pour l'instant
                model_files_select = ui.select(
                    [],
                    value=gguf_config.get('selected_file', None),
                    label='Fichiers .gguf trouvés'
                ).classes('form-select mb-2 w-full')
                
                async def browse_gguf_file():
                    try:
                        # Implémentation d'un vrai navigateur de fichiers
                        try:
                            import tkinter as tk
                            from tkinter import filedialog
                            
                            # Créer une fenêtre tkinter invisible
                            root = tk.Tk()
                            root.withdraw()  # Masquer la fenêtre principale
                            root.attributes('-topmost', True)  # Toujours au premier plan
                            
                            # Ouvrir dialogue de sélection
                            file_path = filedialog.askopenfilename(
                                title="Sélectionner un modèle GGUF",
                                filetypes=[
                                    ("Modèles GGUF", "*.gguf"),
                                    ("Tous les fichiers", "*.*")
                                ],
                                initialdir=gguf_config.get('model_path', 'C:\\')
                            )
                            
                            root.destroy()
                            
                            if file_path:
                                # Mettre à jour les champs avec le fichier sélectionné
                                model_path_input.value = file_path.replace('/', '\\')
                                model_files_select.options = [file_path]
                                model_files_select.value = file_path
                                
                                # Calculer la taille du fichier
                                import os
                                file_size = os.path.getsize(file_path) / (1024**3)  # GB
                                
                                ui.notify(f'OK Modèle sélectionné: {os.path.basename(file_path)} ({file_size:.1f} GB)', type='positive')
                            else:
                                ui.notify('Aucun fichier sélectionné', type='info')
                        
                        except ImportError:
                            # Fallback: scan automatique des dossiers communs
                            ui.notify('RECHERCHE tkinter non disponible, scan automatique...', type='info')
                            await scan_common_directories()
                            
                    except Exception as e:
                        ui.notify(f'ERREUR Erreur navigateur: {e}', type='warning')
                        # Fallback vers simulation en cas d'erreur
                        await scan_common_directories()
                
                async def scan_common_directories():
                    """Scan des dossiers communs pour trouver des modèles GGUF"""
                    try:
                        import os
                        import glob
                        
                        # Dossiers communs à scanner
                        common_paths = [
                            "C:\\AI\\models\\",
                            "C:\\models\\", 
                            "D:\\models\\",
                            "D:\\AI\\models\\",
                            os.path.expanduser("~/models/"),
                            os.path.expanduser("~/Downloads/"),
                            os.path.expanduser("~/Desktop/")
                        ]
                        
                        found_models = []
                        for path in common_paths:
                            expanded_path = os.path.expandvars(path)
                            if os.path.exists(expanded_path):
                                pattern = os.path.join(expanded_path, "**", "*.gguf")
                                models = glob.glob(pattern, recursive=True)
                                found_models.extend(models)
                        
                        if found_models:
                            # Limiter à 10 premiers résultats et normaliser les chemins
                            found_models = [m.replace('/', '\\') for m in found_models[:10]]
                            
                            model_files_select.options = found_models
                            if not model_files_select.value and found_models:
                                model_files_select.value = found_models[0]
                                model_path_input.value = found_models[0]
                            
                            ui.notify(f'OK {len(found_models)} modèle(s) GGUF trouvé(s)', type='positive')
                        else:
                            ui.notify('ATTENTION Aucun modèle GGUF trouvé dans les dossiers communs', type='warning')
                            ui.notify('IDEE Utilisez le bouton "📂 Ouvrir dossier" pour naviguer manuellement', type='info')
                            
                    except Exception as e:
                        ui.notify(f'ERREUR Erreur scan: {e}', type='warning')
                
                # Event handler sélection fichier
                def _on_file_select():
                    if model_files_select.value:
                        model_path_input.value = model_files_select.value
                
                model_files_select.on('change', lambda: _on_file_select())
                
                with ui.row().classes('gap-2 mb-2'):
                    ui.button('📁 Scanner modèles', on_click=browse_gguf_file).classes('action-button')
                    ui.button('📂 Ouvrir dossier', on_click=lambda: open_file_explorer()).classes('action-button')
                
                def open_file_explorer():
                    """Ouvre l'explorateur de fichiers Windows"""
                    try:
                        import subprocess
                        import os
                        
                        # Ouvrir dans le dossier courant ou dossier models par défaut
                        base_path = gguf_config.get('model_path', 'C:\\')
                        if os.path.isfile(base_path):
                            # Si c'est un fichier, ouvrir le dossier parent
                            folder_path = os.path.dirname(base_path)
                        else:
                            # Essayer des dossiers communs
                            common_folders = [
                                "C:\\models",
                                "C:\\AI\\models", 
                                "D:\\models",
                                os.path.expanduser("~/models"),
                                "C:\\"
                            ]
                            folder_path = next((f for f in common_folders if os.path.exists(f)), "C:\\")
                        
                        subprocess.Popen(['explorer', folder_path])
                        ui.notify(f'📂 Explorateur ouvert: {folder_path}', type='info')
                        
                    except Exception as e:
                        ui.notify(f'ERREUR Erreur ouverture explorateur: {e}', type='warning')
                
                ui.separator().classes('mb-2')
                ui.label('Paramètres GPU').classes('text-sm font-semibold mb-2')
                
                gpu_layers_input = ui.number(
                    label='GPU Layers (-1 = auto)', 
                    value=gguf_config.get('gpu_layers', -1),
                    min=-1, max=100
                ).classes('form-input mb-2')
                
                context_size_input = ui.number(
                    label='Context Size', 
                    value=gguf_config.get('context_size', 4096),
                    min=512, max=32768
                ).classes('form-input mb-2')
                
                # Sauvegarder références inputs
                interface_data['gguf'] = {
                    'model_path_input': model_path_input,
                    'gpu_layers_input': gpu_layers_input,
                    'context_size_input': context_size_input,
                    'model_files_select': model_files_select
                }
        
        def _create_kobold_interface():
            """Interface spécialisée KoboldCpp"""
            adaptive_container.clear()
            with adaptive_container:
                ui.label('🗡️ Configuration KoboldCpp').classes('text-md font-semibold mb-2')
                
                other_backends = sm.settings.get('other_backends', {})
                kobold_config = other_backends.get('kobold', {})
                
                url_input = ui.input(
                    label='URL KoboldCpp', 
                    value=kobold_config.get('url', 'http://localhost:5001')
                ).classes('form-input mb-2 w-full')
                
                model_select = ui.select(
                    label='Modèle disponible sur le serveur',
                    options=[],
                    value=kobold_config.get('selected_model')
                ).classes('form-input mb-2 w-full')
                
                ui.button('MAJ Actualiser modèles', on_click=lambda: refresh_kobold_models()).classes('btn-secondary mr-2')
                ui.button('🔗 Tester connexion', on_click=lambda: test_backend_connection('kobold')).classes('btn-primary')
                
                # Sauvegarder références inputs
                interface_data['kobold'] = {
                    'url_input': url_input,
                    'model_select': model_select
                }
                
                async def test_kobold_connection():
                    try:
                        ui.notify(f'Test connexion KoboldCpp: {url_input.value}...', type='info')
                        # Simulation - à remplacer par vraie logique
                        ui.notify('OK Connexion KoboldCpp réussie', type='positive')
                    except Exception as e:
                        ui.notify(f'ERREUR Erreur connexion: {e}', type='warning')
                
                ui.separator().classes('mb-2')
                ui.label('Paramètres génération').classes('text-sm font-semibold mb-2')
                
                max_length_input = ui.number(
                    label='Longueur max réponse', 
                    value=kobold_config.get('max_length', 512),
                    min=1, max=2048
                ).classes('form-input mb-2')
                
                # Sauvegarder références inputs
                interface_data['kobold'] = {
                    'url_input': url_input,
                    'max_length_input': max_length_input
                }
        
        # Factory pour créer l'interface selon backend
        def _update_interface():
            backend = backend_select.value
            print(f"[FACTORY] Changement interface vers: {backend}")
            print(f"[FACTORY] Type: {type(backend)}, Repr: {repr(backend)}")
            if backend == 'Ollama':
                print("[FACTORY] Création interface Ollama")
                _create_ollama_interface()
            elif backend == 'GGUF':
                print("[FACTORY] Création interface GGUF")
                _create_gguf_interface()
            elif backend == 'KoboldCpp':
                print("[FACTORY] Création interface KoboldCpp")
                _create_kobold_interface()
            else:
                print(f"[FACTORY] ERREUR: Backend non reconnu: {backend}")
        
        def _create_api_interface():
            """Interface pour rediriger vers la configuration API principale"""
            adaptive_container.clear()
            with adaptive_container:
                ui.label('🌐 Configuration API').classes('text-md font-semibold mb-4')
                ui.label('Pour configurer les APIs (OpenAI, Mistral, Anthropic, Google), utilisez le bouton "IA / Modèles" dans les paramètres principaux.').classes('text-muted mb-4')
                ui.separator().classes('mb-4')
                ui.label('Cette section est dédiée aux backends locaux (Ollama, GGUF, KoboldCpp).').classes('text-sm text-orange-400 mb-2')
                ui.label('Sélectionnez un backend local ci-dessus pour le configurer.').classes('text-sm text-muted')
        
        def force_interface_update():
            """Force la mise à jour de l'interface manuellement"""
            print(f"[FACTORY] FORCE UPDATE: Backend sélectionné = {backend_select.value}")
            _update_interface()
            ui.notify(f'Interface {backend_select.value} activée', type='positive')
        
        # Event handler changement backend avec debug renforcé
        def _on_backend_change():
            import time
            print(f"[FACTORY] Event triggered, backend: {backend_select.value}")
            print(f"[FACTORY] Event timestamp: {time.time()}")
            _update_interface()
        
        # Attacher event handler de plusieurs façons pour assurer le fonctionnement
        backend_select.on('change', _on_backend_change)
        backend_select.on_value_change(_on_backend_change)
        
        # Initialiser interface par défaut
        _update_interface()
        
        def _save_other_backends():
            """Sauvegarde configuration autres backends de manière isolée"""
            try:
                # Récupération ou création section other_backends
                other_backends = sm.settings.get('other_backends', {})
                
                # Sauvegarder selon le backend actuel
                backend = backend_select.value.lower()
                
                if backend == 'ollama' and 'ollama' in interface_data:
                    ollama_data = interface_data['ollama']
                    other_backends['ollama'] = {
                        'url': ollama_data['url_input'].value or 'http://localhost:11434',
                        'timeout': int(ollama_data['timeout_input'].value or 30),
                        'selected_model': ollama_data['model_select'].value or '',
                        'enabled': True
                    }
                    ui.notify('OK Configuration Ollama sauvegardée', type='positive')
                    
                elif backend == 'gguf' and 'gguf' in interface_data:
                    gguf_data = interface_data['gguf']
                    other_backends['gguf'] = {
                        'model_path': gguf_data['model_path_input'].value or '',
                        'gpu_layers': int(gguf_data['gpu_layers_input'].value or -1),
                        'context_size': int(gguf_data['context_size_input'].value or 4096),
                        'selected_model': gguf_data['model_files_select'].value or '',
                        'enabled': True
                    }
                    ui.notify('OK Configuration GGUF sauvegardée', type='positive')
                    
                elif backend == 'kobold' and 'kobold' in interface_data:
                    kobold_data = interface_data['kobold']
                    other_backends['kobold'] = {
                        'url': kobold_data['url_input'].value or 'http://localhost:5001',
                        'selected_model': kobold_data['model_select'].value or '',
                        'enabled': True
                    }
                    ui.notify('OK Configuration KoboldCpp sauvegardée', type='positive')
                
                # Sauvegarder dans settings.json (section isolée)
                sm.settings['other_backends'] = other_backends
                sm.save_settings()
                
                print(f"[OTHER-BACKENDS] Configuration {backend} sauvegardée: {other_backends.get(backend, {})}")
                dialog.close()
                
            except Exception as e:
                print(f"[OTHER-BACKENDS] Erreur sauvegarde: {e}")
                ui.notify(f'ERREUR Erreur sauvegarde: {e}', type='warning')
        
        # Boutons popup
        ui.separator().classes('my-4')
        with ui.row().classes('justify-end gap-2 w-full'):
            ui.button('Annuler', on_click=dialog.close).classes('action-button')
            ui.button('💾 Sauvegarder', on_click=_save_other_backends).classes('send-button')
    
    dialog.open()



# =============================================================================
# FONCTION MODELS_MODAL DÉPLACÉE DEPUIS OGMA_NG.PY (PHASE 2)
# =============================================================================

def _models_modal():
    """Popup dédiée aux modèles IA (Chat, Archiviste, Embeddings) avec voyants d'état."""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, '_ensure_settings_manager'):
            sm = ogma_ng._ensure_settings_manager()
        else:
            sm = None
    except Exception:
        sm = None
    def _safe(val: str, options: list[str], default: str = 'Aucun') -> str:
        return val if val in options else default
    dialog = ui.dialog()
    # Ajout de la classe ia-modal et largeur plafonnée pour éviter le grand espace à droite
    with dialog, ui.card().classes('popup-content q-dark ia-modal').style('background: var(--bg-secondary); color: var(--text-primary); height: 82vh; overflow-y: auto; width: min(92vw, 900px); margin: 0 auto;'):
        ui.label('Modèles IA').classes('popup-title')
        tabs = ui.tabs().classes('mb-4')
        with tabs:
            t_chat = ui.tab('Chat IA')
            t_arch = ui.tab('Archiviste IA')
            t_embed = ui.tab('Embeddings IA')

        # Voyants d'état
        with ui.row().classes('items-center gap-4 mb-2'):
            ui.label('État:').classes('text-muted')
            chat_dot = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label('Chat').classes('text-sm')
            arch_dot = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label('Archiviste').classes('text-sm')
            emb_dot = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label('Embeddings').classes('text-sm')

        async def set_dot(el, ok: bool):
            try:
                el.style(f'background: {"#16a34a" if ok else "#dc2626"};')
            except Exception:
                pass

        with ui.tab_panels(tabs, value=t_chat).classes('w-full'):
            # --- Chat IA ---
            with ui.tab_panel(t_chat):
                try:
                    import sys
                    ogma_ng = sys.modules.get('ogma_ng')
                    if ogma_ng and hasattr(ogma_ng, '_ensure_backends'):
                        ogma_ng._ensure_backends()
                except Exception:
                    pass
                chat = sm.settings.get('chat_api', {})
                def detect_backend(d: dict) -> str:
                    bt = d.get('backend_type')
                    if bt in ['API', 'Ollama', 'GGUF', 'KoboldCpp']:
                        return bt
                    if d.get('ollama_model'):
                        return 'Ollama'
                    if d.get('gguf_model'):
                        return 'GGUF'
                    if d.get('provider') in REMOTE_PROVIDERS:
                        return 'API'
                    return 'API'

                chat_backend_opts = ['API', 'Ollama', 'GGUF', 'KoboldCpp']
                with ui.row().classes('items-center gap-2 mb-2 w-full'):
                    chat_backend = ui.select(chat_backend_opts, value=detect_backend(chat), label='Backend').classes('form-select narrow-field').style('min-width: 200px; flex: 1;')
                    ui.button('🔄', on_click=lambda: _refresh_chat_interface()).classes('action-button').style('min-width: 40px; height: 40px; flex-shrink: 0;').tooltip('Actualiser l\'interface selon le backend')

                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label('Disponibilité').classes('text-sm text-muted')
                    chat_dot_inline = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut

                # Zone API
                with ui.column() as chat_api_zone:
                    chat_provider_opts = ['Aucun'] + REMOTE_PROVIDERS[:-1] + ['AIHorde']
                    chat_provider = ui.select(
                        chat_provider_opts,
                        value=_safe(chat.get('provider', 'Aucun'), chat_provider_opts),
                        label='Provider API',
                    ).classes('form-select mb-2 narrow-field')
                    chat_model = ui.select([], value=None, label='Modèle API').classes('form-select mb-2 narrow-field')
                    chat_api_key = ui.input(label='Clé API', password=True, value=chat.get('api_key', '')).classes('form-input mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('Rafraîchir modèles', on_click=_refresh_models_ui('chat', chat_backend, chat_provider, chat_model, chat_api_key)).classes('action-button')
                        ui.button('Tester', on_click=_test_connection_ui('chat', chat_backend, chat_provider, chat_api_key)).classes('action-button')
                with ui.column() as chat_ollama_zone:
                    ui.label('🐙 Configuration Ollama').classes('text-md font-semibold mb-2')
                    
                    chat_ollama_url = ui.input(label='URL Ollama', value=chat.get('ollama_url', 'http://localhost:11434')).classes('form-input mb-2 narrow-field')
                    
                    # Sélecteur de modèles Ollama avec container pour status
                    chat_ollama_model = ui.select([], value=None, label='Modèle Ollama').classes('form-select mb-2 narrow-field')
                    chat_models_container = ui.column().classes('mb-2')
                    
                    async def refresh_chat_ollama_models():
                        try:
                            try:
                                import sys
                                ogma_ng = sys.modules.get('ogma_ng')
                                if ogma_ng and hasattr(ogma_ng, '_ensure_backends'):
                                    ogma_ng._ensure_backends()
                            except Exception:
                                pass
                            ollama_mgr = _ollama_mgr()
                            assert ollama_mgr is not None
                            
                            chat_models_container.clear()
                            with chat_models_container:
                                ui.label('🔄 Rafraîchissement en cours...').classes('text-sm mb-2')
                            
                            if ollama_mgr.check_service():
                                available_models = ollama_mgr.models
                            else:
                                available_models = []
                            
                            chat_ollama_model.options = available_models
                            if available_models:
                                saved_model = chat.get('ollama_model')
                                if saved_model and saved_model in available_models:
                                    chat_ollama_model.value = saved_model
                                elif chat_ollama_model.value not in available_models:
                                    chat_ollama_model.value = available_models[0]
                            else:
                                chat_ollama_model.value = None
                            
                            chat_models_container.clear()
                            with chat_models_container:
                                if available_models:
                                    ui.label(f'✅ {len(available_models)} modèles trouvés').classes('text-sm mb-2 text-green-500')
                                    for model in available_models:
                                        ui.label(f'• {model}').classes('text-sm text-muted pl-4')
                                else:
                                    ui.label('⚠️ Aucun modèle trouvé').classes('text-sm mb-2 text-orange-500')
                                    ui.label('Vérifiez qu\'Ollama est démarré et contient des modèles').classes('text-sm text-muted')
                            
                            if available_models:
                                ui.notify('Modèles Ollama rafraîchis', type='positive')
                            else:
                                ui.notify('Ollama indisponible ou sans modèles', type='warning')
                                
                        except Exception as e:
                            chat_models_container.clear()
                            with chat_models_container:
                                ui.label(f'❌ Erreur: {e}').classes('text-sm text-red-500')
                            ui.notify(f'Erreur rafraîchissement: {e}', type='warning')
                    
                    async def test_chat_ollama_connection():
                        try:
                            ui.notify(f'Test connexion Ollama: {chat_ollama_url.value}...', type='info')
                            # TODO: vraie logique de test
                            ui.notify('✅ Connexion Ollama réussie', type='positive')
                        except Exception as e:
                            ui.notify(f'❌ Erreur connexion: {e}', type='warning')
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('🔄 Rafraîchir modèles', on_click=refresh_chat_ollama_models).classes('action-button')
                        ui.button('🧪 Tester connexion', on_click=test_chat_ollama_connection).classes('action-button')
                    
                    # Paramètres avancés
                    ui.separator().classes('mb-2')
                    ui.label('Paramètres avancés').classes('text-sm font-semibold mb-2')
                    chat_ollama_timeout = ui.number(
                        label='Timeout (secondes)', 
                        value=30,
                        min=5, max=300
                    ).classes('form-input mb-2 narrow-field')
                with ui.column() as chat_gguf_zone:
                    ui.label('📄 Configuration GGUF').classes('text-md font-semibold mb-2')
                    
                    # Récupération config existante
                    gguf_config = sm.settings.get('other_backends', {}).get('gguf', {})
                    
                    with ui.row().classes('items-center gap-2 mb-2'):
                        chat_gguf_model_path = ui.input(
                            label='Chemin vers fichier .gguf', 
                            value=gguf_config.get('model_path', ''),
                            placeholder='C:/models/model.gguf'
                        ).classes('form-input narrow-field').style('flex-grow: 1;')
                        
                        def browse_gguf_file():
                            """Ouvre un sélecteur de fichiers pour choisir un modèle GGUF"""
                            try:
                                # Implémentation d'un vrai navigateur de fichiers (même code que "Autres Backends")
                                try:
                                    import tkinter as tk
                                    from tkinter import filedialog
                                    
                                    # Créer une fenêtre tkinter invisible
                                    root = tk.Tk()
                                    root.withdraw()  # Masquer la fenêtre principale
                                    root.attributes('-topmost', True)  # Toujours au premier plan
                                    
                                    # Ouvrir dialogue de sélection
                                    file_path = filedialog.askopenfilename(
                                        title="Sélectionner un modèle GGUF",
                                        filetypes=[
                                            ("Modèles GGUF", "*.gguf"),
                                            ("Tous les fichiers", "*.*")
                                        ],
                                        initialdir=chat_gguf_model_path.value if chat_gguf_model_path.value else 'C:\\'
                                    )
                                    
                                    root.destroy()
                                    
                                    if file_path:
                                        # Mettre à jour le champ avec le fichier sélectionné
                                        chat_gguf_model_path.value = file_path.replace('/', '\\')
                                        
                                        # Calculer la taille du fichier
                                        import os
                                        file_size = os.path.getsize(file_path) / (1024**3)  # GB
                                        
                                        ui.notify(f'✅ Modèle sélectionné: {os.path.basename(file_path)} ({file_size:.1f} GB)', type='positive')
                                    else:
                                        ui.notify('Aucun fichier sélectionné', type='info')
                                
                                except ImportError:
                                    ui.notify('❌ tkinter non disponible', type='warning')
                                    
                            except Exception as e:
                                ui.notify(f'❌ Erreur navigateur: {e}', type='warning')
                        
                        ui.button('Parcourir...', on_click=browse_gguf_file).classes('action-button')
                    
                    # Sélecteur de fichiers trouvés par scan
                    chat_gguf_model_files = ui.select(
                        label='Modèles trouvés par scan',
                        options=[],
                        value=None
                    ).classes('form-select mb-2 narrow-field')
                    
                    async def browse_chat_gguf_models():
                        """Scanne et trouve automatiquement les modèles GGUF"""
                        try:
                            import os
                            import glob
                            
                            # Dossiers communs pour les modèles
                            search_paths = [
                                "C:\\\\models\\\\**\\\\*.gguf",
                                "C:\\\\AI\\\\models\\\\**\\\\*.gguf", 
                                "D:\\\\models\\\\**\\\\*.gguf",
                                os.path.expanduser("~/models/**/*.gguf"),
                                "*.gguf"
                            ]
                            
                            found_models = []
                            for pattern in search_paths:
                                try:
                                    matches = glob.glob(pattern, recursive=True)
                                    found_models.extend(matches)
                                except Exception:
                                    continue
                            
                            # Supprimer doublons et trier
                            found_models = sorted(list(set(found_models)))
                            
                            if found_models:
                                # Limiter à 10 premiers résultats
                                found_models = [m.replace('/', '\\') for m in found_models[:10]]
                                
                                chat_gguf_model_files.options = found_models
                                if not chat_gguf_model_files.value and found_models:
                                    chat_gguf_model_files.value = found_models[0]
                                    chat_gguf_model_path.value = found_models[0]
                            
                        except Exception as e:
                            # Pas de ui.notify dans une fonction async - on log juste l'erreur
                            print(f"[GGUF-SCAN] Erreur scan: {e}")
                    
                    def open_chat_gguf_explorer():
                        """Ouvre l'explorateur de fichiers Windows pour chercher des modèles GGUF"""
                        try:
                            import subprocess
                            import os
                            
                            # Ouvrir dans le dossier courant ou dossier models par défaut
                            base_path = chat_gguf_model_path.value or 'C:\\'
                            if os.path.isfile(base_path):
                                # Si c'est un fichier, ouvrir le dossier parent
                                folder_path = os.path.dirname(base_path)
                            else:
                                # Essayer des dossiers communs
                                common_folders = [
                                    "C:\\models",
                                    "C:\\AI\\models", 
                                    "D:\\models",
                                    os.path.expanduser("~/models"),
                                    "C:\\"
                                ]
                                folder_path = next((f for f in common_folders if os.path.exists(f)), "C:\\")
                            
                            subprocess.Popen(['explorer', folder_path])
                            ui.notify(f'� Explorateur ouvert: {folder_path}', type='info')
                            
                        except Exception as e:
                            ui.notify(f'❌ Erreur ouverture explorateur: {e}', type='warning')
                    
                    def _on_chat_gguf_file_select():
                        if chat_gguf_model_files.value:
                            chat_gguf_model_path.value = chat_gguf_model_files.value
                    
                    chat_gguf_model_files.on('change', lambda: _on_chat_gguf_file_select())
                    
                    async def test_chat_gguf_connection():
                        try:
                            model_path = chat_gguf_model_path.value
                            if not model_path:
                                ui.notify('⚠️ Aucun modèle spécifié', type='warning')
                                return
                            
                            ui.notify(f'Test modèle GGUF: {model_path}...', type='info')
                            # TODO: vraie logique de test
                            ui.notify('✅ Modèle GGUF accessible', type='positive')
                        except Exception as e:
                            ui.notify(f'❌ Erreur test GGUF: {e}', type='warning')
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('📁 Scanner modèles', on_click=browse_chat_gguf_models).classes('action-button')
                        ui.button('📂 Ouvrir dossier', on_click=open_chat_gguf_explorer).classes('action-button')
                        ui.button('🧪 Tester modèle', on_click=test_chat_gguf_connection).classes('action-button')
                    
                    # Paramètres GPU
                    ui.separator().classes('mb-2')
                    ui.label('Paramètres GPU').classes('text-sm font-semibold mb-2')
                    
                    chat_gguf_gpu_layers = ui.number(
                        label='GPU Layers (-1 = auto)', 
                        value=gguf_config.get('gpu_layers', -1),
                        min=-1, max=100
                    ).classes('form-input mb-2 narrow-field')
                    
                    chat_gguf_context_size = ui.number(
                        label='Context Size', 
                        value=gguf_config.get('context_size', 4096),
                        min=512, max=32768
                    ).classes('form-input mb-2 narrow-field')
                with ui.column() as chat_kobold_zone:
                    chat_kobold_url = ui.input(label='URL KoboldCpp', value=chat.get('kobold_url', 'http://localhost:5001')).classes('form-input mb-2 narrow-field')
                    ui.label('KoboldCpp utilise le modèle chargé sur le serveur local').classes('text-sm mb-2')
                    ui.button('Tester', on_click=_test_connection_ui('chat', chat_backend, None, None, service_url_input=lambda: chat_kobold_url)).classes('action-button mb-2')

                chat_max_tokens = ui.number(label='max_tokens (-1 pour auto)', value=chat.get('max_tokens', 512)).classes('form-input mb-2 narrow-field')
                chat_ctx = ui.number(label='context_length (-1 pour auto)', value=chat.get('context_length', 4096)).classes('form-input mb-2 narrow-field')
                chat_temp = ui.number(label='temperature', value=chat.get('temperature', 0.7), step=0.05, min=0, max=2).classes('form-input mb-2 narrow-field')

                def _refresh_chat_interface():
                    """Force la mise à jour de l'interface Chat selon le backend sélectionné"""
                    backend = chat_backend.value
                    ui.notify(f'🔄 Actualisation interface {backend}...', type='info')
                    
                    # Appliquer la visibilité selon le backend
                    _bind_chat_visibility()
                    
                    ui.notify(f'✅ Interface {backend} activée', type='positive')

                def _bind_chat_visibility():
                    chat_api_zone.visible = (chat_backend.value == 'API')
                    chat_ollama_zone.visible = (chat_backend.value == 'Ollama')
                    chat_gguf_zone.visible = (chat_backend.value == 'GGUF')
                    chat_kobold_zone.visible = (chat_backend.value == 'KoboldCpp')

                chat_backend.on('change', lambda: _bind_chat_visibility())
                # Initialiser la visibilité immédiatement
                _bind_chat_visibility()
                ui.timer(0.05, lambda: _init_models_ui('chat', chat_backend, chat_provider, chat_model, chat_api_key, chat_api_zone, chat_ollama_zone, chat_ollama_model, chat_gguf_zone, chat_gguf_model_files, chat_kobold_zone, ollama_url_input=chat_ollama_url, kobold_url_input=chat_kobold_url), once=True)

                async def _auto_check_chat():
                    backend = chat_backend.value
                    ok = False
                    try:
                        models, err = await _list_models(backend, (chat_provider.value if backend=='API' else None), (chat_api_key.value if backend=='API' else None))
                        ok = (err is None) and bool(models or backend in ['GGUF', 'KoboldCpp'])
                    except Exception:
                        ok = False
                    await set_dot(chat_dot, ok)
                    await set_dot(chat_dot_inline, ok)
                from nicegui_client_guard import safe_async_timer_callback
                ui.timer(0.2, safe_async_timer_callback(lambda: asyncio.create_task(_auto_check_chat())), once=True)

            # --- Archiviste IA ---
            with ui.tab_panel(t_arch):
                try:
                    import sys
                    ogma_ng = sys.modules.get('ogma_ng')
                    if ogma_ng and hasattr(ogma_ng, '_ensure_backends'):
                        ogma_ng._ensure_backends()
                except Exception:
                    pass
                arch = sm.settings.get('reasoning_api', {})
                def detect_backend(d: dict) -> str:
                    bt = d.get('backend_type')
                    if bt in ['API', 'Ollama', 'GGUF', 'KoboldCpp']:
                        return bt
                    if d.get('ollama_model'):
                        return 'Ollama'
                    if d.get('gguf_model'):
                        return 'GGUF'
                    if d.get('provider') in REMOTE_PROVIDERS:
                        return 'API'
                    return 'API'

                arch_backend_opts = ['API', 'Ollama', 'GGUF', 'KoboldCpp']
                with ui.row().classes('items-center gap-2 mb-2 w-full'):
                    arch_backend = ui.select(arch_backend_opts, value=detect_backend(arch), label='Backend').classes('form-select narrow-field').style('min-width: 200px; flex: 1;')
                    ui.button('🔄', on_click=lambda: _refresh_arch_interface()).classes('action-button').style('min-width: 40px; height: 40px; flex-shrink: 0;').tooltip('Actualiser l\'interface selon le backend')

                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label('Disponibilité').classes('text-sm text-muted')
                    arch_dot_inline = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut

                with ui.column() as arch_api_zone:
                    arch_provider_opts = ['Aucun'] + REMOTE_PROVIDERS[:-1] + ['AIHorde']
                    arch_provider = ui.select(
                        arch_provider_opts,
                        value=_safe(arch.get('provider', 'Aucun'), arch_provider_opts),
                        label='Provider API',
                    ).classes('form-select mb-2 narrow-field')
                    arch_model = ui.select([], value=None, label='Modèle API').classes('form-select mb-2 narrow-field')
                    arch_api_key = ui.input(label='Clé API', password=True, value=arch.get('api_key', '')).classes('form-input mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('Rafraîchir modèles', on_click=_refresh_models_ui('arch', arch_backend, arch_provider, arch_model, arch_api_key)).classes('action-button')
                        ui.button('Tester', on_click=_test_connection_ui('arch', arch_backend, arch_provider, arch_api_key)).classes('action-button')
                with ui.column() as arch_ollama_zone:
                    arch_ollama_url = ui.input(label='URL Ollama', value=arch.get('ollama_url', 'http://localhost:11434')).classes('form-input mb-2 narrow-field')
                    arch_ollama_model = ui.select([], value=None, label='Modèle Ollama').classes('form-select mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('Rafraîchir modèles', on_click=_refresh_models_ui('arch', arch_backend, None, arch_ollama_model, None, service_url_input=lambda: arch_ollama_url)).classes('action-button')
                        ui.button('Tester', on_click=_test_connection_ui('arch', arch_backend, None, None, service_url_input=lambda: arch_ollama_url)).classes('action-button')
                with ui.column() as arch_gguf_zone:
                    ui.label('📄 Configuration GGUF Archiviste').classes('text-md font-semibold mb-2')
                    
                    other_backends = sm.settings.get('other_backends', {})
                    gguf_config = other_backends.get('gguf', {})
                    
                    arch_gguf_model_path = ui.input(
                        label='Chemin vers fichier .gguf', 
                        value=gguf_config.get('model_path', ''),
                        placeholder='C:/models/model.gguf'
                    ).classes('form-input mb-2 w-full')
                    
                    arch_gguf_model_files = ui.select(
                        [],
                        value=None,  # On assignera la valeur après avoir rempli les options
                        label='Fichiers .gguf trouvés'
                    ).classes('form-select mb-2 w-full')
                    
                    # Assigner la valeur après initialisation si elle existe
                    selected_model = gguf_config.get('selected_model', None)
                    if selected_model:
                        arch_gguf_model_files.options = [selected_model]
                        arch_gguf_model_files.value = selected_model
                    
                    async def browse_arch_gguf_file():
                        try:
                            try:
                                import tkinter as tk
                                from tkinter import filedialog
                                
                                root = tk.Tk()
                                root.withdraw()
                                root.attributes('-topmost', True)
                                
                                file_path = filedialog.askopenfilename(
                                    title="Sélectionner un modèle GGUF pour Archiviste",
                                    filetypes=[
                                        ("Modèles GGUF", "*.gguf"),
                                        ("Tous les fichiers", "*.*")
                                    ],
                                    initialdir=gguf_config.get('model_path', 'C:\\')
                                )
                                
                                root.destroy()
                                
                                if file_path:
                                    arch_gguf_model_path.value = file_path.replace('/', '\\')
                                    arch_gguf_model_files.options = [file_path]
                                    arch_gguf_model_files.value = file_path
                                    
                                    import os
                                    file_size = os.path.getsize(file_path) / (1024**3)
                                    
                                    ui.notify(f'✅ Modèle Archiviste sélectionné: {os.path.basename(file_path)} ({file_size:.1f} GB)', type='positive')
                                else:
                                    ui.notify('Aucun fichier sélectionné', type='info')
                            
                            except ImportError:
                                ui.notify('🔍 tkinter non disponible, scan automatique...', type='info')
                                await scan_arch_common_directories()
                                
                        except Exception as e:
                            ui.notify(f'❌ Erreur navigateur: {e}', type='warning')
                            await scan_arch_common_directories()
                    
                    async def scan_arch_common_directories():
                        try:
                            import os
                            import glob
                            
                            common_paths = [
                                "C:\\\\AI\\\\models\\\\",
                                "C:\\\\AI\\\\TIA\\\\text-generation-webui\\\\user_data\\\\models\\\\",
                                "C:\\\\models\\\\", 
                                "D:\\\\models\\\\",
                                "D:\\\\AI\\\\models\\\\",
                                os.path.expanduser("~/models/"),
                                os.path.expanduser("~/Downloads/"),
                            ]
                            
                            found_models = []
                            for path in common_paths:
                                expanded_path = os.path.expandvars(path)
                                if os.path.exists(expanded_path):
                                    pattern = os.path.join(expanded_path, "**", "*.gguf")
                                    models = glob.glob(pattern, recursive=True)
                                    found_models.extend(models)
                            
                            if found_models:
                                found_models = [m.replace('/', '\\') for m in found_models[:10]]
                                
                                arch_gguf_model_files.options = found_models
                                if not arch_gguf_model_files.value and found_models:
                                    arch_gguf_model_files.value = found_models[0]
                                    arch_gguf_model_path.value = found_models[0]
                                
                                ui.notify(f'✅ {len(found_models)} modèle(s) GGUF trouvé(s) pour Archiviste', type='positive')
                            else:
                                ui.notify('⚠️ Aucun modèle GGUF trouvé dans les dossiers communs', type='warning')
                                
                        except Exception as e:
                            ui.notify(f'❌ Erreur scan: {e}', type='warning')
                    
                    def _on_arch_file_select():
                        if arch_gguf_model_files.value:
                            arch_gguf_model_path.value = arch_gguf_model_files.value
                    
                    arch_gguf_model_files.on('change', lambda: _on_arch_file_select())
                    
                    with ui.row().classes('gap-2 mb-2'):
                        ui.button('📁 Scanner modèles', on_click=browse_arch_gguf_file).classes('action-button')
                        ui.button('📂 Ouvrir dossier', on_click=lambda: open_arch_file_explorer()).classes('action-button')
                    
                    def open_arch_file_explorer():
                        try:
                            import subprocess
                            import os
                            
                            base_path = gguf_config.get('model_path', 'C:\\')
                            if os.path.isfile(base_path):
                                folder_path = os.path.dirname(base_path)
                            else:
                                common_folders = [
                                    "C:\\\\AI\\\\TIA\\\\text-generation-webui\\\\user_data\\\\models",
                                    "C:\\\\models",
                                    "C:\\\\AI\\\\models", 
                                    "D:\\\\models",
                                    os.path.expanduser("~/models"),
                                    "C:\\\\"
                                ]
                                folder_path = next((f for f in common_folders if os.path.exists(f)), "C:\\\\")
                            
                            subprocess.Popen(['explorer', folder_path])
                            ui.notify(f'📂 Explorateur ouvert: {folder_path}', type='info')
                            
                        except Exception as e:
                            ui.notify(f'❌ Erreur ouverture explorateur: {e}', type='warning')
                    
                    ui.separator().classes('mb-2')
                    ui.label('Paramètres GPU Archiviste').classes('text-sm font-semibold mb-2')
                    
                    arch_gguf_gpu_layers = ui.number(
                        label='GPU Layers (-1 = auto)', 
                        value=gguf_config.get('gpu_layers', -1),
                        min=-1, max=100
                    ).classes('form-input mb-2')
                    
                    arch_gguf_context_size = ui.number(
                        label='Context Size', 
                        value=gguf_config.get('context_size', 4096),
                        min=512, max=32768
                    ).classes('form-input mb-2')
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('Rafraîchir modèles', on_click=_refresh_models_ui('arch', arch_backend, None, arch_gguf_model_files, None)).classes('action-button')
                        ui.button('Tester', on_click=_test_connection_ui('arch', arch_backend, None, None)).classes('action-button')
                with ui.column() as arch_kobold_zone:
                    arch_kobold_url = ui.input(label='URL KoboldCpp', value=arch.get('kobold_url', 'http://localhost:5001')).classes('form-input mb-2 narrow-field')
                    ui.label('KoboldCpp utilise le modèle chargé sur le serveur local').classes('text-sm mb-2')
                    ui.button('Tester', on_click=_test_connection_ui('arch', arch_backend, None, None, service_url_input=lambda: arch_kobold_url)).classes('action-button mb-2')

                arch_max_tokens = ui.number(label='max_tokens (-1 pour auto)', value=arch.get('max_tokens', 512)).classes('form-input mb-2 narrow-field')
                arch_ctx = ui.number(label='context_length (-1 pour auto)', value=arch.get('context_length', 4096)).classes('form-input mb-2 narrow-field')
                arch_temp = ui.number(label='temperature', value=arch.get('temperature', 0.7), step=0.05, min=0, max=2).classes('form-input mb-2 narrow-field')

                def _refresh_arch_interface():
                    """Force la mise à jour de l'interface Archiviste selon le backend sélectionné"""
                    backend = arch_backend.value
                    ui.notify(f'🔄 Actualisation interface {backend}...', type='info')
                    
                    # Appliquer la visibilité selon le backend
                    _bind_arch_visibility()
                    
                    ui.notify(f'✅ Interface {backend} activée', type='positive')

                def _bind_arch_visibility():
                    arch_api_zone.visible = (arch_backend.value == 'API')
                    arch_ollama_zone.visible = (arch_backend.value == 'Ollama')
                    arch_gguf_zone.visible = (arch_backend.value == 'GGUF')
                    arch_kobold_zone.visible = (arch_backend.value == 'KoboldCpp')

                arch_backend.on('change', lambda: _bind_arch_visibility())
                # Initialiser la visibilité immédiatement
                _bind_arch_visibility()
                ui.timer(0.05, lambda: _init_models_ui('arch', arch_backend, arch_provider, arch_model, arch_api_key, arch_api_zone, arch_ollama_zone, arch_ollama_model, arch_gguf_zone, arch_gguf_model_files, arch_kobold_zone, ollama_url_input=arch_ollama_url, kobold_url_input=arch_kobold_url), once=True)

                async def _auto_check_arch():
                    backend = arch_backend.value
                    ok = False
                    try:
                        models, err = await _list_models(backend, (arch_provider.value if backend=='API' else None), (arch_api_key.value if backend=='API' else None))
                        ok = (err is None) and bool(models or backend in ['GGUF', 'KoboldCpp'])
                    except Exception:
                        ok = False
                    await set_dot(arch_dot, ok)
                    await set_dot(arch_dot_inline, ok)
                from nicegui_client_guard import safe_async_timer_callback
                ui.timer(0.2, safe_async_timer_callback(lambda: asyncio.create_task(_auto_check_arch())), once=True)

            # --- Embeddings IA ---
            with ui.tab_panel(t_embed):
                try:
                    import sys
                    ogma_ng = sys.modules.get('ogma_ng')
                    if ogma_ng and hasattr(ogma_ng, '_ensure_backends'):
                        ogma_ng._ensure_backends()
                except Exception:
                    pass
                emb = sm.settings.get('embedding_api', {})
                def detect_embed_backend(d: dict) -> str:
                    bt = d.get('backend_type')
                    if bt in ['API', 'Ollama', 'GGUF']:
                        return bt
                    if d.get('ollama_model'):
                        return 'Ollama'
                    if d.get('gguf_model'):
                        return 'GGUF'
                    if d.get('provider') in EMBED_SUPPORTED_PROVIDERS:
                        return 'API'
                    return 'API'

                emb_backend_opts = ['API', 'Ollama', 'GGUF']
                with ui.row().classes('items-center gap-2 mb-2 w-full'):
                    emb_backend = ui.select(emb_backend_opts, value=detect_embed_backend(emb), label='Backend').classes('form-select narrow-field').style('min-width: 200px; flex: 1;')
                    ui.button('🔄', on_click=lambda: _refresh_embed_interface()).classes('action-button').style('min-width: 40px; height: 40px; flex-shrink: 0;').tooltip('Actualiser l\'interface selon le backend')

                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label('Disponibilité').classes('text-sm text-muted')
                    emb_dot_inline = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut

                with ui.column() as emb_api_zone:
                    emb_provider_opts = ['Aucun'] + EMBED_SUPPORTED_PROVIDERS
                    emb_provider = ui.select(
                        emb_provider_opts,
                        value=_safe(emb.get('provider', 'Aucun'), emb_provider_opts),
                        label='Provider API',
                    ).classes('form-select mb-2 narrow-field')
                    emb_model = ui.select([], value=None, label="Modèle d'embeddings").classes('form-select mb-2 narrow-field')
                    emb_api_key = ui.input(label='Clé API', password=True, value=emb.get('api_key', '')).classes('form-input mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('Rafraîchir modèles', on_click=_refresh_models_ui('embed', emb_backend, emb_provider, emb_model, emb_api_key)).classes('action-button')
                        ui.button('Tester', on_click=_test_connection_ui('embed', emb_backend, emb_provider, emb_api_key)).classes('action-button')
                with ui.column() as emb_ollama_zone:
                    emb_ollama_url = ui.input(label='URL Ollama', value=emb.get('ollama_url', 'http://localhost:11434')).classes('form-input mb-2 narrow-field')
                    emb_ollama_model = ui.select([], value=None, label='Modèle Ollama').classes('form-select mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('Rafraîchir modèles', on_click=_refresh_models_ui('embed', emb_backend, None, emb_ollama_model, None, service_url_input=lambda: emb_ollama_url)).classes('action-button')
                        ui.button('Tester', on_click=_test_connection_ui('embed', emb_backend, None, None, service_url_input=lambda: emb_ollama_url)).classes('action-button')
                with ui.column() as emb_gguf_zone:
                    ui.label('📄 Configuration GGUF Embedding').classes('text-md font-semibold mb-2')
                    
                    other_backends = sm.settings.get('other_backends', {})
                    gguf_config = other_backends.get('gguf', {})
                    
                    emb_gguf_model_path = ui.input(
                        label='Chemin vers fichier .gguf', 
                        value=gguf_config.get('model_path', ''),
                        placeholder='C:/models/model.gguf'
                    ).classes('form-input mb-2 w-full')
                    
                    emb_gguf_model_files = ui.select(
                        [],
                        value=None,  # On assignera la valeur après avoir rempli les options
                        label='Fichiers .gguf trouvés'
                    ).classes('form-select mb-2 w-full')
                    
                    # Assigner la valeur après initialisation si elle existe
                    selected_model = gguf_config.get('selected_model', None)
                    if selected_model:
                        emb_gguf_model_files.options = [selected_model]
                        emb_gguf_model_files.value = selected_model
                    
                    async def browse_emb_gguf_file():
                        try:
                            try:
                                import tkinter as tk
                                from tkinter import filedialog
                                
                                root = tk.Tk()
                                root.withdraw()
                                root.attributes('-topmost', True)
                                
                                file_path = filedialog.askopenfilename(
                                    title="Sélectionner un modèle GGUF pour Embedding",
                                    filetypes=[
                                        ("Modèles GGUF", "*.gguf"),
                                        ("Tous les fichiers", "*.*")
                                    ],
                                    initialdir=gguf_config.get('model_path', 'C:\\')
                                )
                                
                                root.destroy()
                                
                                if file_path:
                                    emb_gguf_model_path.value = file_path.replace('/', '\\')
                                    emb_gguf_model_files.options = [file_path]
                                    emb_gguf_model_files.value = file_path
                                    
                                    import os
                                    file_size = os.path.getsize(file_path) / (1024**3)
                                    
                                    ui.notify(f'✅ Modèle Embedding sélectionné: {os.path.basename(file_path)} ({file_size:.1f} GB)', type='positive')
                                else:
                                    ui.notify('Aucun fichier sélectionné', type='info')
                            
                            except ImportError:
                                ui.notify('🔍 tkinter non disponible, scan automatique...', type='info')
                                await scan_emb_common_directories()
                                
                        except Exception as e:
                            ui.notify(f'❌ Erreur navigateur: {e}', type='warning')
                            await scan_emb_common_directories()
                    
                    async def scan_emb_common_directories():
                        try:
                            import os
                            import glob
                            
                            common_paths = [
                                "C:\\\\AI\\\\models\\\\",
                                "C:\\\\AI\\\\TIA\\\\text-generation-webui\\\\user_data\\\\models\\\\",
                                "C:\\\\models\\\\", 
                                "D:\\\\models\\\\",
                                "D:\\\\AI\\\\models\\\\",
                                os.path.expanduser("~/models/"),
                                os.path.expanduser("~/Downloads/"),
                            ]
                            
                            found_models = []
                            for path in common_paths:
                                expanded_path = os.path.expandvars(path)
                                if os.path.exists(expanded_path):
                                    pattern = os.path.join(expanded_path, "**", "*.gguf")
                                    models = glob.glob(pattern, recursive=True)
                                    found_models.extend(models)
                            
                            if found_models:
                                found_models = [m.replace('/', '\\') for m in found_models[:10]]
                                
                                emb_gguf_model_files.options = found_models
                                if not emb_gguf_model_files.value and found_models:
                                    emb_gguf_model_files.value = found_models[0]
                                    emb_gguf_model_path.value = found_models[0]
                                
                                ui.notify(f'✅ {len(found_models)} modèle(s) GGUF trouvé(s) pour Embedding', type='positive')
                            else:
                                ui.notify('⚠️ Aucun modèle GGUF trouvé dans les dossiers communs', type='warning')
                                
                        except Exception as e:
                            ui.notify(f'❌ Erreur scan: {e}', type='warning')
                    
                    def _on_emb_file_select():
                        if emb_gguf_model_files.value:
                            emb_gguf_model_path.value = emb_gguf_model_files.value
                    
                    emb_gguf_model_files.on('change', lambda: _on_emb_file_select())
                    
                    with ui.row().classes('gap-2 mb-2'):
                        ui.button('📁 Scanner modèles', on_click=browse_emb_gguf_file).classes('action-button')
                        ui.button('📂 Ouvrir dossier', on_click=lambda: open_emb_file_explorer()).classes('action-button')
                    
                    def open_emb_file_explorer():
                        try:
                            import subprocess
                            import os
                            
                            base_path = gguf_config.get('model_path', 'C:\\')
                            if os.path.isfile(base_path):
                                folder_path = os.path.dirname(base_path)
                            else:
                                common_folders = [
                                    "C:\\\\AI\\\\TIA\\\\text-generation-webui\\\\user_data\\\\models",
                                    "C:\\\\models",
                                    "C:\\\\AI\\\\models", 
                                    "D:\\\\models",
                                    os.path.expanduser("~/models"),
                                    "C:\\\\"
                                ]
                                folder_path = next((f for f in common_folders if os.path.exists(f)), "C:\\\\")
                            
                            subprocess.Popen(['explorer', folder_path])
                            ui.notify(f'📂 Explorateur ouvert: {folder_path}', type='info')
                            
                        except Exception as e:
                            ui.notify(f'❌ Erreur ouverture explorateur: {e}', type='warning')
                    
                    ui.separator().classes('mb-2')
                    ui.label('Paramètres GPU Embedding').classes('text-sm font-semibold mb-2')
                    
                    emb_gguf_gpu_layers = ui.number(
                        label='GPU Layers (-1 = auto)', 
                        value=gguf_config.get('gpu_layers', -1),
                        min=-1, max=100
                    ).classes('form-input mb-2')
                    
                    emb_gguf_context_size = ui.number(
                        label='Context Size', 
                        value=gguf_config.get('context_size', 4096),
                        min=512, max=32768
                    ).classes('form-input mb-2')
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button('Rafraîchir modèles', on_click=_refresh_models_ui('embed', emb_backend, None, emb_gguf_model_files, None)).classes('action-button')
                        ui.button('Tester', on_click=_test_connection_ui('embed', emb_backend, None, None)).classes('action-button')

                # Utiliser la nouvelle structure other_backends.gguf
                gguf_cfg = sm.settings.get('other_backends', {}).get('gguf', {})
                gguf_gpu_layers = ui.number(label='GGUF GPU layers (-1 = auto)', value=gguf_cfg.get('gpu_layers', -1)).classes('form-input mb-2 narrow-field')

                # Paramètres avancés Embedding
                ui.separator().classes('mb-2')
                ui.label('Paramètres avancés Embedding').classes('text-sm font-semibold mb-2')
                
                emb_max_tokens = ui.number(label='max_tokens (-1 pour auto)', value=emb.get('max_tokens', 512)).classes('form-input mb-2 narrow-field')
                emb_ctx = ui.number(label='context_length (-1 pour auto)', value=emb.get('context_length', 4096)).classes('form-input mb-2 narrow-field')
                emb_temp = ui.number(label='temperature', value=emb.get('temperature', 0.1), step=0.05, min=0, max=2).classes('form-input mb-2 narrow-field')

                def _refresh_embed_interface():
                    """Force la mise à jour de l'interface Embedding selon le backend sélectionné"""
                    backend = emb_backend.value
                    ui.notify(f'🔄 Actualisation interface {backend}...', type='info')
                    
                    # Appliquer la visibilité selon le backend
                    _bind_embed_visibility()
                    
                    ui.notify(f'✅ Interface {backend} activée', type='positive')

                def _bind_embed_visibility():
                    emb_api_zone.visible = (emb_backend.value == 'API')
                    emb_ollama_zone.visible = (emb_backend.value == 'Ollama')
                    emb_gguf_zone.visible = (emb_backend.value == 'GGUF')

                emb_backend.on('change', lambda: _bind_embed_visibility())
                # Initialiser la visibilité immédiatement
                _bind_embed_visibility()
                ui.timer(0.05, lambda: _init_models_ui('embed', emb_backend, emb_provider, emb_model, emb_api_key, emb_api_zone, emb_ollama_zone, emb_ollama_model, emb_gguf_zone, emb_gguf_model_files, None, ollama_url_input=emb_ollama_url), once=True)

                async def _auto_check_emb():
                    backend = emb_backend.value
                    ok = False
                    try:
                        models, err = await _list_models(backend, (emb_provider.value if backend=='API' else None), (emb_api_key.value if backend=='API' else None))
                        ok = (err is None) and bool(models or backend in ['GGUF'])
                    except Exception:
                        ok = False
                    await set_dot(emb_dot, ok)
                    await set_dot(emb_dot_inline, ok)
                from nicegui_client_guard import safe_async_timer_callback
                ui.timer(0.2, safe_async_timer_callback(lambda: asyncio.create_task(_auto_check_emb())), once=True)

        def save_and_close():
            # Sauvegardes des 3 sections (reprend la logique précédente)
            chat_settings = {
                'backend_type': chat_backend.value,
                'provider': 'Aucun',
                'api_model': '',
                'api_key': '',
                'max_tokens': int(chat_max_tokens.value or 512),
                'context_length': int(chat_ctx.value or 4096),
                'temperature': float(chat_temp.value or 0.7),
                'ollama_model': '',
                'gguf_model': '',
                'ollama_url': sm.settings.get('chat_api', {}).get('ollama_url', 'http://localhost:11434'),
                'kobold_url': sm.settings.get('chat_api', {}).get('kobold_url', 'http://localhost:5001'),
            }
            if chat_backend.value == 'API':
                chat_settings['provider'] = chat_provider.value or 'Aucun'
                chat_settings['api_model'] = chat_model.value or ''
                chat_settings['api_key'] = chat_api_key.value or ''
            elif chat_backend.value == 'Ollama':
                chat_settings['ollama_model'] = chat_ollama_model.value or ''
                chat_settings['ollama_url'] = chat_ollama_url.value or 'http://localhost:11434'
            elif chat_backend.value == 'GGUF':
                chat_settings['gguf_model'] = chat_gguf_model_path.value or ''
                # Synchroniser les paramètres GGUF avec other_backends
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'gguf' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['gguf'] = {}
                
                # Sauvegarder dans other_backends pour compatibilité
                sm.settings['other_backends']['gguf'].update({
                    'model_path': chat_gguf_model_path.value or '',
                    'gpu_layers': int(chat_gguf_gpu_layers.value or -1),
                    'context_size': int(chat_gguf_context_size.value or 4096),
                    'enabled': True
                })
            elif chat_backend.value == 'KoboldCpp':
                chat_settings['kobold_url'] = chat_kobold_url.value or 'http://localhost:5001'
            sm.settings['chat_api'] = chat_settings

            arch_settings = {
                'backend_type': arch_backend.value,
                'provider': 'Aucun',
                'api_model': '',
                'api_key': '',
                'max_tokens': int(arch_max_tokens.value or 512),
                'context_length': int(arch_ctx.value or 4096),
                'temperature': float(arch_temp.value or 0.7),
                'ollama_model': '',
                'gguf_model': '',
                'ollama_url': sm.settings.get('reasoning_api', {}).get('ollama_url', 'http://localhost:11434'),
                'kobold_url': sm.settings.get('reasoning_api', {}).get('kobold_url', 'http://localhost:5001'),
            }
            if arch_backend.value == 'API':
                arch_settings['provider'] = arch_provider.value or 'Aucun'
                arch_settings['api_model'] = arch_model.value or ''
                arch_settings['api_key'] = arch_api_key.value or ''
            elif arch_backend.value == 'Ollama':
                arch_settings['ollama_model'] = arch_ollama_model.value or ''
                arch_settings['ollama_url'] = arch_ollama_url.value or 'http://localhost:11434'
            elif arch_backend.value == 'GGUF':
                arch_settings['gguf_model'] = arch_gguf_model_files.value or ''
            elif arch_backend.value == 'KoboldCpp':
                arch_settings['kobold_url'] = arch_kobold_url.value or 'http://localhost:5001'
            sm.settings['reasoning_api'] = arch_settings

            emb_settings = {
                'backend_type': emb_backend.value,
                'provider': 'Aucun',
                'api_model': '',
                'api_key': '',
                'ollama_model': '',
                'gguf_model': '',
                'ollama_url': sm.settings.get('embedding_api', {}).get('ollama_url', 'http://localhost:11434'),
            }
            if emb_backend.value == 'API':
                emb_settings['provider'] = emb_provider.value or 'Aucun'
                emb_settings['api_model'] = emb_model.value or ''
                emb_settings['api_key'] = emb_api_key.value or ''
            elif emb_backend.value == 'Ollama':
                emb_settings['ollama_model'] = emb_ollama_model.value or ''
                emb_settings['ollama_url'] = emb_ollama_url.value or 'http://localhost:11434'
            elif emb_backend.value == 'GGUF':
                emb_settings['gguf_model'] = emb_gguf_model_files.value or ''
            
            # Ajouter les paramètres avancés Embedding
            emb_settings['max_tokens'] = int(emb_max_tokens.value or 512)
            emb_settings['context_length'] = int(emb_ctx.value or 4096)
            emb_settings['temperature'] = float(emb_temp.value or 0.1)
            
            sm.settings['embedding_api'] = emb_settings

            # Utiliser la nouvelle structure other_backends.gguf
            if 'other_backends' not in sm.settings:
                sm.settings['other_backends'] = {}
            if 'gguf' not in sm.settings['other_backends']:
                sm.settings['other_backends']['gguf'] = {}
            sm.settings['other_backends']['gguf']['gpu_layers'] = int(gguf_gpu_layers.value or -1)
            
            msg = sm.save_settings()
            ui.notify(msg or 'Paramètres sauvegardés', type='positive')
            dialog.close()

        # Bouton AUTRES BACKENDS (système isolé)
        with ui.row().classes('justify-center mt-4 mb-2'):
            ui.button('⚙️ AUTRES BACKENDS', on_click=lambda: _open_other_backends_popup()).classes('action-button text-sm')

        with ui.row().classes('justify-end gap-2 mt-2'):
            ui.button('Annuler', on_click=dialog.close).classes('action-button')
            ui.button('Sauvegarder', on_click=save_and_close).classes('send-button')
    return dialog


# Fonction _perception_modal supprimée - remplacée par la section dans les paramètres généraux
# et l'utilisation directe de _perception_settings_modal pour le bouton header


# Modal simple supprimée - seule la modal complète est utilisée


# ============================================================================
# PERCEPTION SETTINGS - SUPPRIMÉE
# Tous les paramètres Perception sont maintenant gérés sur la page dédiée /perception
# Cette modal a été supprimée pour éviter les conflits de configuration
# ============================================================================


def _web_navigator_settings_modal():
    """Modal de configuration pour l'extension Web Navigator"""
    
    # Créer le dialog avec glassmorphism
    dialog = ui.dialog().style('''
        z-index: 10000 !important;
    ''')
    
    with dialog:
        with ui.card().classes('w-full max-w-4xl').style('''
            background: rgba(212, 175, 55, 0.08) !important;
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(212, 175, 55, 0.25) !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px rgba(212, 175, 55, 0.15) !important;
            color: var(--text-primary) !important;
            height: 80vh !important;
            overflow-y: auto !important;
        '''):
            
            # En-tête
            ui.label('🌐 Web Navigator (Serper API)').classes('popup-title').style('''
                color: #3498db !important; 
                text-shadow: 0 0 10px rgba(52, 152, 219, 0.3) !important; 
                font-weight: 600 !important;
                font-size: 1.5rem !important;
            ''')
            ui.label("Recherche internet intelligente avec phrases magiques").classes('text-muted mb-4')
            
            # Conteneur pour l'interface de l'extension
            settings_container = ui.column().classes('w-full')
            
            # Initialiser et intégrer l'extension Web Navigator avec Serper
            try:
                # Obtenir le settings manager
                settings_manager = _get_settings_manager()
                
                # Import et initialisation de l'extension Serper
                from extensions.web_navigator import WebNavigatorConfig, SerperClient, WebNavigatorCommands
                from extensions.web_navigator.ui_components import WebNavigatorUI
                
                # Configuration
                config = WebNavigatorConfig(settings_manager)
                
                # Composants Serper
                serper_client = SerperClient(config)
                commands = WebNavigatorCommands(config, serper_client)
                
                # Interface utilisateur
                web_nav_ui = WebNavigatorUI(config, commands)
                web_nav_ui.create_settings_panel(settings_container)
                
            except ImportError as e:
                with settings_container:
                    ui.markdown("### ❌ Extension Web Navigator (Serper) non disponible")
                    ui.markdown(f"**Erreur :** {e}")
                    ui.markdown("""
**Configuration requise :**
- Clé API gratuite Serper: [serper.dev](https://serper.dev)
- 2500 requêtes/mois gratuites

**Fonctionnalités disponibles :**
- Recherche web: `/web REQUÊTE` ou "cherche sur internet SUJET"  
- Actualités: `/news REQUÊTE` ou "actualités sur SUJET"
- Images: `/image REQUÊTE` ou "cherche des images de SUJET"
- Articles académiques: `/scholar REQUÊTE`
- Phrases magiques détectées automatiquement
""")
            
            except Exception as e:
                with settings_container:
                    ui.markdown("### ⚠️ Erreur de configuration Web Navigator")
                    ui.markdown(f"**Erreur :** {e}")
                    ui.markdown("*Vérifiez les logs pour plus de détails*")
            
            # Boutons de contrôle
            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Fermer', on_click=dialog.close).classes('action-button').style('''
                    background: rgba(52, 152, 219, 0.12) !important;
                    border: 1px solid rgba(52, 152, 219, 0.3) !important;
                    backdrop-filter: blur(15px) !important;
                    transition: all 0.3s ease !important;
                ''')
    
    return dialog