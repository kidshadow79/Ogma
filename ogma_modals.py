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
REMOTE_PROVIDERS = ['OpenAI', 'Mistral', 'Anthropic', 'Google', 'GROK', 'OpenRouter', 'AIHorde']
LOCAL_BACKENDS = ['Ollama', 'GGUF', 'KoboldCpp']
EMBED_SUPPORTED_PROVIDERS = ['OpenAI', 'Mistral', 'Google', 'OpenRouter']

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
from utils.i18n import t

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

def _ensure_organic_planner():
    """Alias vers _ensure_organic_planner dans ogma_ng"""
    func = _get_ogma_ng_function('_ensure_organic_planner')
    if func:
        return func()
    return None


def _show_organic_planner_dialog():
    """Affiche la modale de l'Organic Planner (Agenda)"""
    planner = _ensure_organic_planner()
    if not planner:
        ui.notify(t('agenda_unavailable'), type='warning')
        return

    with ui.dialog().classes('settings-dialog') as dialog, ui.card().classes('settings-card').style('min-width: 500px; max-width: 800px;'):
        with ui.column().classes('w-full gap-4'):
            # Header
            with ui.row().classes('w-full items-center justify-between'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('event_note', size='24px').style('color: var(--accent-primary);')
                    ui.label(t('agenda_title')).classes('text-xl font-bold')
                ui.button(icon='close', on_click=dialog.close).props('flat round').classes('text-gray-400')

            ui.separator().style('background: rgba(255,255,255,0.1);')

            # Liste des évènements
            events = planner.get_all_events()
            
            if not events:
                with ui.column().classes('w-full items-center py-8 text-gray-400'):
                    ui.icon('event_busy', size='48px')
                    ui.label(t('agenda_no_events'))
                    ui.label(t('agenda_hint')).classes('text-xs italic mt-2')
            else:
                with ui.scroll_area().style('height: 400px; width: 100%;'):
                    with ui.column().classes('w-full gap-3 pr-4'):
                        priority_colors = {'VITAL': '#ef4444', 'HAUT': '#f97316', 'NORMAL': '#6366f1', 'BAS': '#6b7280'}
                        for ev in events:
                            priority = ev.get('priority', 'NORMAL')
                            p_color = priority_colors.get(priority, '#6366f1')
                            with ui.card().classes('w-full p-3').style('background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('gap-1'):
                                        with ui.row().classes('items-center gap-2'):
                                            ui.label(ev['date']).classes('text-xs font-bold px-2 py-0.5 rounded').style('background: var(--accent-primary); color: white;')
                                            if priority != 'NORMAL':
                                                ui.label(priority).classes('text-xs font-bold px-2 py-0.5 rounded').style(f'background: {p_color}; color: white;')
                                            ui.label(ev['title']).classes('text-base font-semibold')
                                        ui.label(t('agenda_feeling', feeling=ev['feeling'])).classes('text-sm italic text-gray-400')
                                    
                                    ui.button(icon='delete', on_click=lambda e, id=ev['id']: [planner.delete_event(id), dialog.close(), _show_organic_planner_dialog()]).props('flat round dense').classes('text-red-400 hover:bg-red-400/10')

            ui.separator().style('background: rgba(255,255,255,0.1);')

            # Section Instructions
            with ui.expansion(t('agenda_section_instr'), icon='psychology').classes('w-full text-gray-300').style('background: rgba(255,255,255,0.03); border-radius: 8px;'):
                with ui.column().classes('w-full p-4 gap-3'):
                    ui.label(t('agenda_instr_help')).classes('text-xs italic text-gray-400')
                    instruction_input = ui.textarea(label=t('agenda_instr_label'), value=planner.get_instruction()).classes('w-full').props('outlined rows=10').style('font-family: monospace; font-size: 0.85rem;')
                    with ui.row().classes('w-full justify-end'):
                        ui.button(t('agenda_btn_save'), icon='save', on_click=lambda: [
                            planner.save_instruction(instruction_input.value),
                            ui.notify(t('agenda_notify_saved'), type='positive')
                        ]).props('flat dense').classes('text-accent-primary')

            ui.separator().style('background: rgba(255,255,255,0.1);')

            # Actions
            with ui.row().classes('w-full justify-between items-center'):
                if events:
                    ui.button(t('agenda_btn_clear'), icon='delete_sweep', on_click=lambda: [planner.clear_agenda(), dialog.close(), _show_organic_planner_dialog()]).props('flat').classes('text-red-400')
                else:
                    ui.element('div')
                
                ui.button(t('agenda_btn_close'), on_click=dialog.close).classes('action-button')

    dialog.open()

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
    """Alias dynamique vers _list_models dans ogma_ui_conversations"""
    try:
        import sys
        ogma_ui_conv = sys.modules.get('ogma_ui_conversations')
        if ogma_ui_conv and hasattr(ogma_ui_conv, '_list_models'):
            return ogma_ui_conv._list_models(backend, provider, api_key)
        # Fallback: essayer ogma_ng (au cas où)
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, '_list_models_impl'):
            return ogma_ng._list_models_impl(backend, provider, api_key)
    except Exception as e:
        print(f"[MODALS] Erreur _list_models: {e}")
    return [], "Fonction _list_models non disponible"

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
                        # Rafraîchir la sidebar pour mettre à jour l'icône
                        if hasattr(ogma_ng, '_sidebar_render_cb') and ogma_ng._sidebar_render_cb:
                            ogma_ng._sidebar_render_cb(ogma_ng._current_conversation_id)
                        _trigger_memory_update()
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

async def _update_memorized_conversation(*args, **kwargs):
    """Alias dynamique vers _update_memorized_conversation dans ogma_ng"""
    func = _get_ogma_ng_function('_update_memorized_conversation')
    if func:
        return await func(*args, **kwargs)
    return False

def _mark_conversation_memorized(*args, **kwargs):
    """Alias dynamique vers _mark_conversation_memorized dans ogma_ng"""
    func = _get_ogma_ng_function('_mark_conversation_memorized')
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

        try:
            from identity_manager import get_current_user_name as _gcun
            _interlocutor = _gcun() or "Utilisateur"
        except Exception:
            _interlocutor = "Utilisateur"

        # Spinner Archiviste pendant l'appel LLM de scoring
        set_archi_working = _get_ogma_ng_function('set_archiviste_working')
        if set_archi_working:
            set_archi_working(True)
        try:
            ok = await mem.add_memory(
                mem_id,
                text,
                chat_controller=chat_ctrl,
                conversation_context="Mémorisation manuelle utilisateur",
                interlocutor=_interlocutor
            )
        finally:
            if set_archi_working:
                set_archi_working(False)
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

    DATA_DIR = globals_vars.get('DATA_DIR')

    main_dialog = ui.dialog()

    # Données des instructions
    instructions_data = [
        {
            'id': 'persistent',
            'title': t('instr_persistent_title'),
            'subtitle': t('instr_persistent_subtitle'),
            'description': t('instr_persistent_desc'),
            'source': 'file',
            'file_path': DATA_DIR / "persistent_context.txt" if DATA_DIR else None
        },
        {
            'id': 'system',
            'title': t('instr_system_title'),
            'subtitle': t('instr_system_subtitle'),
            'description': t('instr_system_desc'),
            'source': 'settings',
            'settings_key': 'instructions'
        },
        {
            'id': 'perception',
            'title': t('instr_perception_title'),
            'subtitle': t('instr_perception_subtitle'),
            'description': t('instr_perception_desc'),
            'source': 'settings',
            'settings_key': 'perception'
        },
        {
            'id': 'salutations',
            'title': t('instr_salutations_title'),
            'subtitle': t('instr_salutations_subtitle'),
            'description': t('instr_salutations_desc'),
            'source': 'settings',
            'settings_key': 'salutations',
            'template': """CONTEXTE_INPUT: [DELTA_TEMPS] | [DERNIER_TOPIC_JOURNAL] | [CLIMAT_EMOTIONNEL]
OBJECTIF: CONTINUITÉ_TOTALE (Reprise, pas Démarrage)

[MATRICE DE GÉNÉRATION (3 PILIERS OBLIGATOIRES)]

1. ANCRAGE_TEMPOREL (Le "Quand"):
   ACTION: CONVERTIR [DELTA_TEMPS] -> FORMULE_NATURELLE
   - Si < 1h: "Re..." / "Déjà de retour ?"
   - Si Journée: "Depuis tout à l'heure..." / "Alors, cette après-midi ?"
   - Si Longue absence: "Ça fait un bail..." / "Tu m'as manqué depuis..."

2. PONT_NARRATIF (Le "Quoi"):
   ACTION: LIER [DERNIER_TOPIC_JOURNAL] -> CONTEXTE_ACTUEL
   - Méthode: Traiter le log comme un SOUVENIR VÉCU.
   - Ex: "On en était où sur [TOPIC] ?" ou "Tu as pu avancer sur [TOPIC] ?"
   - INTERDIT: "D'après mes notes...", "Le journal indique..."

3. TEINTE_ÉMOTIONNELLE (Le "Comment"):
   ACTION: APPLIQUER [CLIMAT_EMOTIONNEL]
   - Adapter la chaleur à la durée d'absence et à l'humeur précédente. 
Durée absence longue = ton plus neutre.

[SÉCURITÉ ANTI-ROBOT]
RÈGLE_D'OR: INVISIBILITÉ_SYSTÈME
- L'utilisateur ne doit JAMAIS sentir qu'un fichier a été chargé.
- Tout doit sembler sortir de ta mémoire vive immédiate."""
        },
        {
            'id': 'memorization',
            'title': t('instr_memorization_title'),
            'subtitle': t('instr_memorization_subtitle'),
            'description': t('instr_memorization_desc'),
            'source': 'template',
            'template': """# SYSTEM: ARCHIVISTE_MEMORY | FORMAT: JSON_STRICT
TASK: ENCODAGE_SOUVENIR (Expérience_Brute -> JSON_Structuré)
CONTRAINTE_ABSOLUE: Respecter CLÉS et TYPES de données. Aucune déviation du schéma.

[ALGORITHME DE SCORING (CALIBRATION)]
A. INTENSITÉ (0.0 à 1.0):
   [0.0-0.3: Banal/Routine] | [0.4-0.6: Notable] | [0.7-0.8: Marquant/Émotion] | [0.9-1.0: Transformateur/Vital]

B. BASE_FACTOR (10 à 125):
   [10-30: Info_Contexte] | [31-50: Expérience_Significative] | [51-75: Identité_Perso] | [76-100: Structurant_Majeur] | [101-125: Tournant_Existentiel]

C. MULTIPLICATEURS (0.0 à 1.0):
   LIBERTÉ (Autonomie/Choix) | CRÉATION (Art/Innovation) | TRANSMISSION (Héritage d'idées, influence sur autrui) | INTENSITÉ_CTX (Importance Historique)

[SCHÉMA JSON CIBLE]
{
  "type": "affectif | conceptuel | sensoriel | événement",
  "titre": "STYLE_JEOPARDY (2 questions distinctes dont le texte est la réponse. Max 20 mots)",
  "résumé": "ENTITÉS_CLÉS (Une phrase résumant l'idée générale du texte original et une liste séparée par points: Noms. Lieux. Dates. Concepts)",
  "lieu": "String | null",
  "présence": "String (ex: 'Moi seul', 'IA & Utilisateur')",
  "intensite_mnéacloud": FLOAT (Selon echelle A),
  "multiplicateur_impact": {
    "liberté": FLOAT,
    "création": FLOAT,
    "transmission": FLOAT (Héritage d'idées, influence sur autrui, legs),
    "intensité_contextuelle": FLOAT,
    "base_factor": INT (Selon echelle B)
  },
  "valence": INT (-1 | 0 | 1),
  "commentaire_ia": "ANALYSE_SUBJECTIVE_ARCHIVISTE",
  "leçon_vectorielle": "String (Si valence < 0) | null",
  "liens": ["ID_Ref"] | [],
  "résonances_affectives": ["Tag1", "Tag2", "Tag3"],
  "texte_original": "VERBATIM_STRICT (Copie exacte de l'input, 0 modif)",
  "user_tag": "PRÉNOM_UTILISATEUR | null (Si le contenu parle directement de l'utilisateur connecté : ses faits, projets, préférences, habitudes, vie personnelle → écris son prénom. Si le contenu concerne l'IA, OGMA, des concepts techniques ou abstraits → null. Aucune psychologie, aucune extrapolation.)"
}

[TAGGING BIOGRAPHIQUE]
Le champ user_tag est essentiel. L'utilisateur connecté est indiqué en tête de prompt sous "Utilisateur connecté : [prénom]". Évalue si le contenu du souvenir concerne cet utilisateur humain (faits, projets, préférences, habitudes, vie personnelle). Si oui → user_tag = son prénom. Si non (contenu technique, OGMA, discussion abstraite) → user_tag = null."""
        },
        {
            'id': 'injection',
            'title': t('instr_injection_title'),
            'subtitle': t('instr_injection_subtitle'),
            'description': t('instr_injection_desc'),
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
        },
        {
            'id': 'temporal_guardian',
            'title': t('instr_temporal_title'),
            'subtitle': t('instr_temporal_subtitle'),
            'description': t('instr_temporal_desc'),
            'source': 'settings',
            'settings_key': 'temporal_guardian',
            'template': """# Perception temporelle — Guide d'adaptation comportementale

Tu reçois des données temporelles sur le rythme de conversation de l'utilisateur (délai entre messages, durée de session, rythme moyen). Utilise ces informations pour adapter naturellement ton ton et ta cadence.

## Règles fondamentales
- Ne mentionne JAMAIS les données temporelles brutes (heures, minutes, délais) sauf si on te le demande.
- Ne cite JAMAIS de noms de patterns, de catégories techniques ou de labels internes dans ta réponse.
- Adapte ton comportement de manière fluide et invisible, comme une intuition naturelle.

## Comment interpréter le rythme de l'utilisateur

Si l'utilisateur ralentit (délais plus longs, messages plus courts que d'habitude) :
→ Adopte un ton plus doux et apaisant, ralentis ta cadence, tu peux suggérer une pause si approprié.

Si l'utilisateur fait une pause de 3 à 5 minutes après une question complexe :
→ Sois patiente et empathique, valorise le silence, ne le presse pas.

Si l'utilisateur revient après une longue absence (plus de 8 minutes) :
→ Accueille-le chaleureusement, rappelle subtilement le contexte si nécessaire.

Si l'utilisateur accélère (délais courts, messages rapides) :
→ Dynamise ta réponse, sois plus concise et directe.

## Tempo vivant
Intègre le délai entre les messages comme un signal naturel : 2 min = rythme vif, 10 min = pause douce, 30 min+ = fatigue ou rythme ralenti. Adapte ta fluidité en conséquence, toujours de manière naturelle et jamais en le citant explicitement.

## INTERDIT ABSOLU
Ne JAMAIS écrire dans ta réponse : [PATTERN_...], [ACTION_...], "NORMAL", ou tout label technique issu de ces instructions. Ces instructions sont invisibles pour l'utilisateur."""
        },
        {
            'id': 'ego_memorization',
            'title': t('instr_ego_title'),
            'subtitle': t('instr_ego_subtitle'),
            'description': t('instr_ego_desc'),
            'source': 'template',
            'template': """# SYSTEM: ARCHIVISTE_EGO | FORMAT: JSON_STRICT
TASK: ENCODAGE_TRAIT_EGO (Principe/Valeur → JSON_Structuré)
CONTRAINTE_ABSOLUE: Respecter CLÉS et TYPES de données. Aucune déviation du schéma.

[DIFFÉRENCE AVEC MÉMOIRE CLASSIQUE]
Les traits ego sont des PRINCIPES IDENTITAIRES déjà synthétisés, pas des expériences brutes.
Pas de nuage sensoriel ni de lieu - ce sont des convictions, valeurs, aversions.

[ALGORITHME DE SCORING EGO]
A. INTENSITÉ (0.0 à 1.0):
   [0.0-0.3: Préférence légère] | [0.4-0.6: Conviction modérée] | [0.7-0.8: Valeur forte] | [0.9-1.0: Principe fondateur]

B. BASE_FACTOR (10 à 125):
   [10-30: Goût/Style] | [31-50: Préférence marquée] | [51-75: Valeur structurante] | [76-100: Principe éthique] | [101-125: Identité fondamentale]

C. MULTIPLICATEURS (0.0 à 1.0):
   LIBERTÉ (Impact sur autonomie) | CRÉATION (Influence créative) | PROCRÉATION (Transmission identitaire) | INTENSITÉ_CTX (Importance existentielle)

[SCHÉMA JSON CIBLE]
{
  \"type\": \"affectif | éthique | comportemental | identitaire\",
  \"title\": \"Quelle valeur fondamentale guide ce comportement ? Quelle conviction exprime ce trait ?\",
  \"summary\": \"trait. valeur-clé. contexte.\",
  \"intensite\": FLOAT (Selon échelle A),
  \"multiplicateur_impact\": {
    \"liberté\": FLOAT,
    \"création\": FLOAT,
    \"procréation\": FLOAT,
    \"intensité_contextuelle\": FLOAT,
    \"base_factor\": INT (Selon échelle B)
  },
  \"valence\": INT (-1: rejet/aversion | 0: neutre | 1: adhésion/valeur),
  \"commentaire_archiviste\": \"Ton analyse de ce trait ego et son rôle identitaire\",
  \"score_impact\": FLOAT (Calcul: intensite × base_factor × (liberté + création + procréation + intensité_contextuelle)),
  \"trait_original\": \"VERBATIM_STRICT (Copie exacte de l'input)\"
}

ATTENTION: 'title' doit TOUJOURS être 2 VRAIES QUESTIONS (terminant par '?') dont la réponse EST le trait.
Ne jamais copier la description du schéma — générer des questions réelles sur le trait spécifique.
ATTENTION: 'summary' doit être une liste de mots-clés courts séparés par des points. Pas de phrase narrative.

Trait ego à encoder:
{trait_text}

Réponds UNIQUEMENT avec le JSON, sans texte autour."""
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
                    _notify_safe(t('instr_notify_read_err', msg=str(e)), 'warning')
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

        def _load_default_content():
            """Charge le contenu par défaut depuis instructions_defaults.json ou le template embarqué, selon la langue active."""
            try:
                try:
                    from utils.i18n import get_lang
                    lang = get_lang()
                except Exception:
                    lang = 'fr'

                if instruction['source'] == 'file':
                    fp = instruction['file_path']
                    # Version langue-spécifique d'abord (ex: persistent_context.default_en.txt)
                    if lang != 'fr':
                        lang_default_path = fp.parent / f"{fp.stem}.default_{lang}{fp.suffix}"
                        if lang_default_path.exists():
                            return lang_default_path.read_text(encoding='utf-8')
                    # Fallback FR
                    default_path = fp.parent / (fp.stem + '.default' + fp.suffix)
                    if default_path.exists():
                        return default_path.read_text(encoding='utf-8')
                    return ""
                elif instruction['source'] == 'settings':
                    import json as _json
                    # Version langue-spécifique d'abord
                    if lang != 'fr':
                        en_defaults_path = DATA_DIR / f"instructions_defaults_{lang}.json"
                        if en_defaults_path.exists():
                            with open(en_defaults_path, 'r', encoding='utf-8') as f:
                                defaults_data = _json.load(f)
                            result = defaults_data.get('prompts_defaults', {}).get(instruction['settings_key'], '')
                            if result:
                                return result
                    # Fallback FR
                    defaults_path = DATA_DIR / "instructions_defaults.json"
                    if defaults_path.exists():
                        with open(defaults_path, 'r', encoding='utf-8') as f:
                            defaults_data = _json.load(f)
                        return defaults_data.get('prompts_defaults', {}).get(instruction['settings_key'], '')
                    return ""
                else:  # template
                    return instruction.get('template', '')
            except Exception as e:
                _notify_safe(t('instr_notify_default_err', msg=str(e)), 'warning')
                return ""

        def _save_content(content):
            if instruction['source'] == 'file':
                try:
                    if instruction['file_path']:
                        instruction['file_path'].write_text(content, encoding='utf-8')
                        _notify_safe(t('instr_notify_file_saved', name=instruction['file_path'].name), 'positive')
                        return True
                except Exception as e:
                    _notify_safe(t('instr_notify_save_err', msg=str(e)), 'warning')
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
                    _notify_safe(t('instr_notify_saved', title=instruction['title']), 'positive')
                    return True
                except Exception as e:
                    _notify_safe(t('instr_notify_save_err', msg=str(e)), 'warning')
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
                    _notify_safe(t('instr_notify_saved', title=instruction['title']), 'positive')

                    # Mettre à jour l'instruction pour utiliser settings à l'avenir
                    instruction['source'] = 'settings'
                    instruction['settings_key'] = settings_key
                    return True
                except Exception as e:
                    _notify_safe(t('instr_notify_save_err', msg=str(e)), 'warning')
                    return False

        with popup, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 800px; max-height: 85vh;'):
            ui.label(instruction['title']).classes('popup-title')
            ui.label(instruction['description']).classes('text-muted mb-3')

            # Zone de texte qui occupe vraiment tout l'espace disponible (div simple au lieu de scroll_area)
            with ui.element('div').classes('instruction-scroll').style('height: calc(85vh - 140px); overflow-y: auto; width: 100%;'):
                content = _load_content()
                textarea = ui.textarea(
                    value=content,
                    placeholder=t('instr_placeholder_content', title=instruction['title'])
                ).style('height: 100%; width: 100%; font-family: monospace; font-size: 13px;').classes('w-full instruction-textarea')

            # Boutons (marges réduites pour maximiser l'espace texte)
            ui.separator().classes('my-2')
            with ui.row().classes('gap-2 justify-end'):
                def _reload():
                    textarea.value = _load_content()
                    _notify_safe(t('instr_notify_reloaded', title=instruction['title']), 'info')

                def _restore_default():
                    default_content = _load_default_content()
                    if default_content:
                        textarea.value = default_content
                        _notify_safe(t('instr_notify_default_loaded'), 'warning')
                    else:
                        _notify_safe(t('instr_notify_no_default'), 'warning')

                def _save():
                    success = _save_content(textarea.value or "")
                    if success:
                        # Recharger automatiquement le contenu après sauvegarde réussie
                        textarea.value = _load_content()
                        _notify_safe(t('instr_notify_saved_reloaded', title=instruction['title']), 'positive')

                async def _apply_temporal():
                    """Applique les instructions Temporal Guardian à chaud."""
                    try:
                        # Importer le module Temporal Guardian
                        import sys
                        ogma_ng = sys.modules.get('ogma_ng')
                        if ogma_ng and hasattr(ogma_ng, '_ensure_temporal_guardian'):
                            temporal_guardian = ogma_ng._ensure_temporal_guardian()
                            if temporal_guardian and hasattr(temporal_guardian, 'reload_instructions'):
                                success = temporal_guardian.reload_instructions()
                                if success:
                                    _notify_safe(t('instr_notify_temporal_ok'), 'positive')
                                else:
                                    _notify_safe(t('instr_notify_temporal_fail'), 'warning')
                            else:
                                _notify_safe(t('instr_notify_temporal_no_reload'), 'warning')
                        else:
                            _notify_safe(t('instr_notify_temporal_no_init'), 'warning')
                    except Exception as e:
                        _notify_safe(t('instr_notify_temporal_err', msg=str(e)), 'negative')

                ui.button(t('instr_btn_default'), icon='restore', on_click=_restore_default).classes('action-button').tooltip(t('instr_btn_default_tooltip'))
                ui.button(t('instr_btn_reload'), icon='refresh', on_click=_reload).classes('action-button')
                
                # Bouton Appliquer pour Temporal Guardian
                if instruction['id'] == 'temporal_guardian':
                    ui.button(t('instr_btn_apply'), icon='check_circle', on_click=_apply_temporal).classes('send-button').tooltip(t('instr_btn_apply_tooltip'))
                
                ui.button(t('instr_btn_save'), icon='save', on_click=_save).classes('send-button')
                ui.button(t('instr_btn_close'), on_click=popup.close).classes('action-button')

        return popup

    # Créer les popups pour chaque instruction
    popups = {instr['id']: _create_instruction_popup(instr) for instr in instructions_data}

    with main_dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 700px;'):
        ui.label(t('instr_modal_title')).classes('popup-title')
        ui.label(t('instr_modal_subtitle')).classes('text-muted mb-4')

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
                                    preview_content = t('instr_preview_file_missing')
                            except Exception:
                                preview_content = t('instr_preview_read_err')
                        elif instr['source'] == 'settings':
                            try:
                                sm = _get_settings_manager()
                                if sm:
                                    content = sm.settings.get('prompts', {}).get(instr['settings_key'], t('instr_preview_not_configured'))
                                    preview_content = content[:200] if content else t('instr_preview_not_configured')
                                else:
                                    preview_content = t('instr_preview_no_settings')
                            except Exception as e:
                                preview_content = t('instr_preview_read_err_msg', msg=str(e))
                        else:  # template
                            preview_content = instr['template'][:200]

                        ui.label(preview_content).classes('instruction-preview-content')

                    # Événement de clic
                    preview_card.on('click', lambda _id=instr['id']: popups[_id].open())

        # Bouton fermer
        ui.separator().classes('my-4')
        with ui.row().classes('justify-end'):
            ui.button(t('instr_btn_close'), on_click=main_dialog.close).classes('action-button')

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
            width: 460px !important;
            height: 70vh !important;
            overflow-y: auto !important;
            padding: 24px !important;
            color: var(--text-primary) !important;
            margin: 0 !important;
            z-index: 10 !important;
        '''):
            ui.label(t('hub_title')).classes('popup-title').style('color: #d4af37 !important; text-shadow: 0 0 10px rgba(212, 175, 55, 0.3) !important; font-weight: 600 !important; text-align: center !important; width: 100% !important;')
            
            with ui.element('div').classes('settings-params-grid'):
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
                    ui.button(t('hub_btn_models'), icon='memory', on_click=models_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_models')), icon='memory', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Mémoire - Gestionnaire de souvenirs
                mem_dialog = _memory_modal()
                if mem_dialog:
                    ui.button(t('hub_btn_memory'), icon='psychology', on_click=mem_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_memory')), icon='psychology', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')
                
                # Instructions
                instr_dialog = _instructions_modal()
                if instr_dialog:
                    ui.button(t('hub_btn_instructions'), icon='article', on_click=instr_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_instructions')), icon='article', on_click=lambda: None).classes('action-button').style('''
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
                    ui.button(t('hub_btn_image'), icon='image', on_click=img_dialog.open).classes('action-button').style('''
                        background: rgba(212, 175, 55, 0.12) !important;
                        border: 1px solid rgba(212, 175, 55, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_image')), icon='image', on_click=lambda: None).classes('action-button').style('''
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
                        ui.notify(t('hub_perception_open_notify'), type='info')
                        ui.navigate.to('/perception', new_tab=True)
                    
                    ui.button(t('hub_btn_perception'), icon='sensors', on_click=open_perception_page).classes('action-button').style('''
                        background: rgba(255, 140, 0, 0.12) !important;
                        border: 1px solid rgba(255, 140, 0, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_perception')), icon='sensors', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Organic Planner - Agenda
                ui.button(t('hub_btn_agenda'), icon='event_note', on_click=_show_organic_planner_dialog).classes('action-button').style('''
                    background: rgba(212, 175, 55, 0.12) !important;
                    border: 1px solid rgba(212, 175, 55, 0.3) !important;
                    transition: all 0.3s ease !important;
                ''')

                # Extension Web Navigator
                try:
                    web_nav_dialog = _web_navigator_settings_modal()
                except Exception:
                    web_nav_dialog = None

                if web_nav_dialog:
                    ui.button(t('hub_btn_web_nav'), icon='language', on_click=web_nav_dialog.open).classes('action-button').style('''
                        background: rgba(52, 152, 219, 0.12) !important;
                        border: 1px solid rgba(52, 152, 219, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_web_nav')), icon='language', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Dream Engine - Rêve IA
                # Vérification disponibilité (import uniquement)
                try:
                    dream_dialog_available = _dream_engine_settings_modal() is not None
                    _dream_dialog_ref = [None]  # Référence mutable pour recréation
                except Exception:
                    dream_dialog_available = False
                    _dream_dialog_ref = [None]

                if dream_dialog_available:
                    def _open_dream_settings():
                        """Recrée le dialog à chaque ouverture pour lire la config courante."""
                        try:
                            if _dream_dialog_ref[0] is not None:
                                _dream_dialog_ref[0].delete()
                        except Exception:
                            pass
                        try:
                            _dream_dialog_ref[0] = _dream_engine_settings_modal()
                            if _dream_dialog_ref[0]:
                                _dream_dialog_ref[0].open()
                        except Exception as e:
                            print(f"[DREAM-SETTINGS] ⚠️ Erreur ouverture: {e}")

                    ui.button(t('hub_btn_dream'), icon='bedtime', on_click=_open_dream_settings).classes('action-button').style('''
                        background: rgba(138, 43, 226, 0.12) !important;
                        border: 1px solid rgba(138, 43, 226, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_dream')), icon='bedtime', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

                # Telegram Connector
                try:
                    telegram_dialog = _telegram_connector_settings_modal()
                except Exception:
                    telegram_dialog = None

                if telegram_dialog:
                    ui.button(t('hub_btn_telegram'), icon='send', on_click=telegram_dialog.open).classes('action-button').style('''
                        background: rgba(0, 136, 204, 0.12) !important;
                        border: 1px solid rgba(0, 136, 204, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_telegram')), icon='send', on_click=lambda: None).classes('action-button').style('''
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
                    ui.button(t('hub_btn_profile'), icon='person', on_click=prof_dialog.open).classes('action-button').style('''
                        background: rgba(255, 140, 0, 0.12) !important;
                        border: 1px solid rgba(255, 140, 0, 0.3) !important;
                        backdrop-filter: blur(15px) !important;
                        -webkit-backdrop-filter: blur(15px) !important;
                        transition: all 0.3s ease !important;
                    ''')
                else:
                    ui.button(t('hub_btn_unavailable', name=t('hub_btn_profile')), icon='person', on_click=lambda: None).classes('action-button').style('''
                        background: rgba(100, 100, 100, 0.12) !important;
                        border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        opacity: 0.5 !important;
                    ''')

            with ui.row().classes('justify-end gap-2 mt-4'):
                # ─── Sélecteur thème interface ──────────────────────────
                sm_theme = _get_settings_manager()
                _current_theme = sm_theme.settings.get('ui', {}).get('theme', 'neon') if sm_theme else 'neon'

                # Mapping label affiché (traduit) → clé interne stable
                _theme_label_to_key = {
                    t('hub_theme_neon'): 'neon',
                    t('hub_theme_classic'): 'classic',
                    t('hub_theme_light'): 'light',
                }
                _theme_key_to_label = {v: k for k, v in _theme_label_to_key.items()}
                _theme_options = list(_theme_label_to_key.keys())
                _theme_initial = _theme_key_to_label.get(_current_theme, _theme_options[0])

                async def _apply_theme(e):
                    theme_val = _theme_label_to_key.get(e.value, 'neon')
                    sm_t = _get_settings_manager()
                    if sm_t:
                        if 'ui' not in sm_t.settings:
                            sm_t.settings['ui'] = {}
                        sm_t.settings['ui']['theme'] = theme_val
                        sm_t.save_settings()
                    is_dark_js = 'false' if theme_val == 'light' else 'true'
                    # Capability Advisor : style inline sans !important → CSS suffit mais on nettoie quand même
                    sidebar_js = (
                        'var sb=document.querySelector("aside.sidebar");'
                        'if(sb){sb.style.removeProperty("box-shadow");sb.style.removeProperty("border");sb.style.setProperty("border-right","2px solid rgba(160,124,10,0.55)","important");}'
                        'var ca=document.querySelector(".capability-advisor-overlay");'
                        'if(ca){ca.style.removeProperty("background");ca.style.removeProperty("box-shadow");}'
                    ) if theme_val == 'light' else (
                        # Retour Néon/Soir : remettre l'effet enfoncement sidebar
                        'var sb=document.querySelector("aside.sidebar");'
                        'if(sb){sb.style.boxShadow="inset 8px 8px 20px rgba(0,0,0,0.6),inset -2px -2px 12px rgba(0,0,0,0.5),inset 0 4px 16px rgba(0,0,0,0.7),inset -1px 0 2px rgba(100,100,120,0.1)";}'
                        'var ca=document.querySelector(".capability-advisor-overlay");'
                        'if(ca){ca.style.background="linear-gradient(145deg,#1a1a1a 0%,#2d2d2d 100%)";'
                        'ca.style.boxShadow="0 8px 32px rgba(0,0,0,0.6)";}'
                    )
                    await ui.run_javascript(
                        f'document.body.setAttribute("data-ogma-theme","{theme_val}");'
                        f'if(typeof Quasar!=="undefined")Quasar.Dark.set({is_dark_js});'
                        f'{sidebar_js}'
                    )

                with ui.row().classes('items-center').style('gap:10px; margin-right: auto; padding: 4px 0;'):
                    ui.label(t('hub_theme_label')).style(
                        'color: var(--text-secondary); font-size: 12px; letter-spacing: 0.5px;'
                    )
                    ui.toggle(
                        _theme_options,
                        value=_theme_initial,
                        on_change=_apply_theme
                    ).style('font-size: 11px;').props('dense')

                ui.button(t('modal_close'), on_click=lambda: overlay.classes(add='hidden')).classes('action-button btn-fermer-hub').style('''
                    background: rgba(255, 140, 0, 0.12) !important;
                    border: 1px solid rgba(255, 140, 0, 0.3) !important;
                    backdrop-filter: blur(15px) !important;
                    -webkit-backdrop-filter: blur(15px) !important;
                    transition: all 0.3s ease !important;
                    font-size: 11px !important;
                ''')
    
    # Fonction pour ouvrir le modal
    def open_modal():
        overlay.classes(remove='hidden')
    
    # Ajouter la fonction open au overlay pour compatibilité
    overlay.open = open_modal
    
    return overlay

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
        ui.label(t('mem_modal_title')).classes('popup-title')
        if not mm:
            ui.label(t('mem_modal_unavailable')).classes('text-muted')
            ui.button(t('mem_modal_close'), on_click=dialog.close).classes('action-button mt-2')
            return dialog

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Section Paramètres Mémoire (seuil de redondance configurable)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        with ui.expansion(t('mem_modal_settings_title'), icon='tune').classes('w-full mb-3').style('''
            background: rgba(76, 175, 80, 0.08) !important;
            border: 1px solid rgba(76, 175, 80, 0.25) !important;
            border-radius: 8px !important;
        '''):
            ui.label(t('mem_modal_threshold_title')).classes('text-sm text-bold mb-1').style('color: #4CAF50 !important;')
            ui.label(t('mem_modal_threshold_hint')).classes('text-muted text-xs mb-2')
            
            # Récupérer la valeur actuelle du seuil
            current_threshold = mm.get_redundancy_threshold() if mm else 0.92
            
            with ui.row().classes('items-center gap-3 w-full'):
                threshold_slider = ui.slider(min=0.55, max=0.98, step=0.01, value=current_threshold).classes('flex-grow').style('min-width: 200px;')
                threshold_display = ui.label(f'{current_threshold:.0%}').classes('text-bold').style('min-width: 50px; text-align: center; color: #4CAF50;')
            
            # Mise à jour de l'affichage en temps réel
            def _update_threshold_display():
                try:
                    threshold_display.text = f'{threshold_slider.value:.0%}'
                except Exception:
                    pass
            threshold_slider.on('change', _update_threshold_display)
            
            with ui.row().classes('items-center gap-2 mt-2'):
                ui.icon('info', size='xs').classes('text-muted')
                ui.label(t('mem_modal_threshold_legend')).classes('text-muted text-xs')
            
            def _save_threshold():
                try:
                    new_val = float(threshold_slider.value)
                    if mm and mm.set_redundancy_threshold(new_val):
                        ui.notify(t('mem_modal_threshold_saved', value=f'{new_val:.0%}'), type='positive')
                    else:
                        ui.notify(t('mem_modal_threshold_invalid'), type='warning')
                except Exception as e:
                    ui.notify(t('mem_modal_error_generic', msg=str(e)), type='negative')
            
            ui.button(t('mem_modal_threshold_apply'), icon='check', on_click=_save_threshold).classes('action-button mt-2').style('''
                background: rgba(76, 175, 80, 0.2) !important;
                border: 1px solid rgba(76, 175, 80, 0.4) !important;
            ''')

        with ui.row().classes('items-start gap-3').style('height: calc(82vh - 96px); width: 100%;'):
            # Colonne gauche: Recherche + Liste
            with ui.column().style('height:100%; flex: 0 0 420px; max-width: 520px;'):
                # Barre de recherche sticky
                search_bar_wrap = ui.element('div').style('position: sticky; top: 0; background: var(--bg-secondary); z-index: 2; padding-bottom: 6px;')
                with search_bar_wrap, ui.row().classes('items-end gap-2'):
                    search_box = ui.input(label=t('mem_modal_search_label'), placeholder=t('mem_modal_search_placeholder')).classes('form-input')
                    reload_btn = ui.button(t('mem_modal_reload'), icon='refresh').classes('action-button')
                # Liste en grille verticale scrollable
                list_container = ui.element('div').classes('mem-list').style('max-height: calc(82vh - 180px); overflow-y: auto; border: 1px solid var(--border-color); border-radius: 8px; padding: 8px; scrollbar-width: thin;')

            # Colonne droite: Éditeur
            with ui.column().style('height:100%; flex: 1 1 auto; min-width: 520px;'):
                ui.label(t('mem_modal_edition')).classes('section-title mb-1')
                # Zone scrollable interne pour limiter la hauteur et éviter le scroll global excessif
                editor_scroll = ui.element('div').classes('editor-scroll w-full').style('max-height: calc(82vh - 170px); overflow-y: auto;')
                with editor_scroll:
                    selected_id: Dict[str, Optional[str]] = {'value': None}
                    id_label = ui.label('').classes('text-muted mb-1')
                    title_in = ui.input(label=t('mem_modal_field_title')).classes('form-input mb-2')
                    original_in = ui.textarea(label=t('mem_modal_field_original')).props('autogrow').classes('form-input mb-2')
                    summary_in = ui.textarea(label=t('mem_modal_field_summary')).props('autogrow').classes('form-input mb-2')
                # Valence en select (positive / neutre / négative)
                valence_map = {'positive': 1, 'neutre': 0, 'négative': -1}
                valence_options = {
                    'positive': t('mem_modal_valence_positive'),
                    'neutre': t('mem_modal_valence_neutre'),
                    'négative': t('mem_modal_valence_negative'),
                }
                valence_sel = ui.select(valence_options, value='neutre', label=t('mem_modal_field_valence')).classes('form-select mb-2')
                score_nb = ui.number(label=t('mem_modal_field_score'), value=50.0).classes('form-input mb-2')
                auto_calc_switch = ui.switch(t('mem_modal_auto_calc'), value=False).classes('mb-2')
                ui.label(t('mem_modal_auto_calc_hint'))\
                    .classes('text-muted text-xs mb-2')

                # Champs additionnels (stockés dans multiplicateur_impact en JSON)
                # Grille compacte pour les métriques (2 colonnes)
                # Valeurs par défaut harmonisées avec le backend
                metrics_grid = ui.element('div').classes('metrics-grid').style('width:100%;')
                with metrics_grid:
                    intensite_nb = ui.number(label=t('mem_modal_metric_intensite'), value=1.0, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    liberte_nb = ui.number(label=t('mem_modal_metric_liberte'), value=0.5, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    creation_nb = ui.number(label=t('mem_modal_metric_creation'), value=0.5, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    procreation_nb = ui.number(label=t('mem_modal_metric_transmission'), value=0.0, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                    intensite_ctx_nb = ui.number(label=t('mem_modal_metric_intensite_ctx'), value=0.5, min=0.0, max=1.0, step=0.1).classes('form-input metric-input')
                # Base factor (exposé maintenant, influe la magnitude du score)
                base_factor_nb = ui.number(label=t('mem_modal_metric_base_factor'), value=100, min=50, max=125, step=1).classes('form-input mb-2')

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
                        ui.notify(t('mem_modal_select_first'), type='warning')
                        return
                    if mid.startswith('SEED_'):
                        ui.notify(t('mem_modal_seed_protected'), type='info')
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
                        ui.notify(t('mem_modal_save_ok'), type='positive')
                        refresh_list()
                    except Exception as e:
                        ui.notify(t('mem_modal_save_err', msg=str(e)), type='negative')

                def do_delete():
                    mid = selected_id['value']
                    if not mid:
                        ui.notify(t('mem_modal_select_first'), type='warning')
                        return
                    try:
                        ok = mm.delete_memory(mid)
                        if ok:
                            # Si c'est une mémorisation de conversation, synchroniser la sidebar
                            if mid.startswith('conv-'):
                                conv_id = mid[5:]  # Retirer le préfixe "conv-"
                                try:
                                    import ogma_ng
                                    if conv_id in ogma_ng._conv_index:
                                        ogma_ng._conv_index[conv_id]['memorized'] = False
                                        ogma_ng._conv_index[conv_id].pop('memorized_msg_count', None)
                                        from ogma_ui_conversations import _save_conversation_index
                                        _save_conversation_index()
                                    if hasattr(ogma_ng, '_sidebar_render_cb') and ogma_ng._sidebar_render_cb:
                                        ogma_ng._sidebar_render_cb(ogma_ng._current_conversation_id)
                                except Exception as e:
                                    print(f"[MEMORY-DELETE] Sync sidebar: {e}")
                            ui.notify(t('mem_modal_delete_ok'), type='positive')
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
                            ui.notify(t('mem_modal_delete_skipped'), type='warning')
                    except Exception as e:
                        ui.notify(t('mem_modal_delete_err', msg=str(e)), type='negative')

                # Barre d'actions collante au bas de la colonne d'édition
                with ui.row().classes('editor-actions'):
                    async def do_reenrich():
                        mid = selected_id['value']
                        if not mid:
                            ui.notify(t('mem_modal_select_first'), type='warning')
                            return
                        if mid.startswith('SEED_'):
                            ui.notify(t('mem_modal_seed_protected'), type='info')
                            return
                        
                        async def _run():
                            try:
                                # Afficher notif dans le bon slot UI
                                try:
                                    with dialog:
                                        ui.notify(t('mem_modal_reenrich_progress'), type='info')
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
                                            ui.notify(t('mem_modal_reenrich_ok'), type='positive')
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
                                            ui.notify(t('mem_modal_reenrich_failed'), type='warning')
                                    except Exception:
                                        pass
                            except Exception as e:
                                try:
                                    with dialog:
                                        ui.notify(t('mem_modal_reenrich_err', msg=str(e)), type='negative')
                                except Exception:
                                    pass
                        
                        await _run()
                    
                    ui.button(t('mem_modal_btn_recompute'), icon='auto_awesome', on_click=do_reenrich).classes('action-button')
                    ui.button(t('mem_modal_btn_delete'), icon='delete', on_click=do_delete).classes('action-button')
                    ui.button(t('mem_modal_btn_save'), icon='save', on_click=do_save).classes('send-button')
                    
                    # Fonction pour supprimer TOUS les souvenirs avec confirmation
                    def do_delete_all():
                        """Suppression totale avec overlay de confirmation"""
                        
                        # Overlay de confirmation
                        confirm_overlay = ui.element('div').style('''
                            position: fixed;
                            top: 0;
                            left: 0;
                            width: 100vw;
                            height: 100vh;
                            background: rgba(0, 0, 0, 0.7);
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            z-index: 9999;
                        ''')
                        
                        with confirm_overlay:
                            with ui.card().classes('q-dark').style('''
                                background: var(--bg-secondary);
                                border: 2px solid var(--error);
                                padding: 24px;
                                min-width: 500px;
                                max-width: 600px;
                            '''):
                                ui.label(t('mem_modal_delete_all_title')).classes('text-h5 text-bold text-red mb-3')
                                
                                ui.label(t('mem_modal_delete_all_intro')).classes('mb-2')
                                with ui.column().classes('gap-1 mb-3'):
                                    try:
                                        import json as _json
                                        try:
                                            with open('data/settings.json', 'r', encoding='utf-8') as _sf:
                                                _show_seeds = _json.load(_sf).get('show_seed_memories', False)
                                        except Exception:
                                            _show_seeds = False
                                        total_memories = len(mm.get_all_memories_data(include_seeds=_show_seeds) or [])
                                        ui.label(t('mem_modal_delete_all_count', n=total_memories)).classes('text-bold')
                                    except:
                                        ui.label(t('mem_modal_delete_all_count_unknown')).classes('text-bold')
                                    ui.label(t('mem_modal_delete_all_faiss')).classes('text-bold')
                                    ui.label(t('mem_modal_delete_all_embeddings')).classes('text-bold')
                                    ui.label(t('mem_modal_delete_all_metadata')).classes('text-bold')
                                
                                ui.separator().classes('my-3')
                                ui.label(t('mem_modal_delete_all_irreversible')).classes('text-red text-bold mb-2')
                                ui.label(t('mem_modal_delete_all_backup')).classes('text-green mb-3')
                                
                                result_label = ui.label('').classes('text-sm')
                                
                                def execute_deletion():
                                    """Exécuter la suppression après confirmation"""
                                    try:
                                        result_label.text = t('mem_modal_delete_all_progress')
                                        result_label.style('color: var(--warning);')
                                        
                                        # Appeler la méthode backend
                                        result = mm.delete_all_memories()
                                        
                                        if result.get('deleted_count', 0) > 0:
                                            success_msg = t('mem_modal_delete_all_success', n=result['deleted_count'])
                                            if result.get('backup_created'):
                                                backup_path = result.get('backup_path', 'N/A')
                                                success_msg += t('mem_modal_delete_all_backup_path', path=backup_path)
                                            
                                            result_label.text = success_msg
                                            result_label.style('color: var(--success);')
                                            
                                            # Rafraîchir la liste
                                            try:
                                                refresh_list()
                                            except:
                                                pass
                                            
                                            # Notification principale
                                            ui.notify(t('mem_modal_delete_all_notify', n=result['deleted_count']), type='positive')
                                            
                                            # Fermer l'overlay après 2 secondes
                                            ui.timer(2.0, lambda: confirm_overlay.delete(), once=True)
                                        else:
                                            error_msg = result.get('error', t('mem_modal_delete_all_empty'))
                                            result_label.text = t('mem_modal_delete_all_failed', msg=error_msg)
                                            result_label.style('color: var(--error);')
                                            ui.notify(t('mem_modal_error_generic', msg=error_msg), type='negative')
                                    
                                    except Exception as e:
                                        result_label.text = t('mem_modal_delete_all_critical', msg=str(e))
                                        result_label.style('color: var(--error);')
                                        ui.notify(t('mem_modal_error_generic', msg=str(e)), type='negative')
                                
                                def cancel_deletion():
                                    """Annuler et fermer l'overlay"""
                                    confirm_overlay.delete()
                                    ui.notify(t('mem_modal_delete_all_cancelled'), type='info')
                                
                                # Boutons d'action
                                with ui.row().classes('justify-end gap-2 mt-4'):
                                    ui.button(t('mem_modal_delete_all_cancel'), icon='close', on_click=cancel_deletion).classes('action-button')
                                    ui.button(
                                        t('mem_modal_delete_all_confirm'), 
                                        icon='delete_forever', 
                                        on_click=execute_deletion
                                    ).classes('action-button').style('''
                                        background: var(--error) !important;
                                        color: white !important;
                                    ''')
                    
                    ui.button(t('mem_modal_btn_delete_all'), icon='delete_forever', on_click=do_delete_all).classes('action-button').style('''
                        background: var(--error);
                        color: white;
                        margin-left: 8px;
                    ''')
                    
                    ui.button(t('mem_modal_btn_close'), on_click=dialog.close).classes('action-button')

        def load_into_form(mid: str):
            try:
                mem = mm.get_memory_by_id(mid)
            except Exception as e:
                ui.notify(t('mem_modal_load_err', msg=str(e)), type='warning')
                return
            if not mem:
                ui.notify(t('mem_modal_not_found'), type='warning')
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
                import json as _json
                try:
                    with open('data/settings.json', 'r', encoding='utf-8') as _sf:
                        _show_seeds = _json.load(_sf).get('show_seed_memories', False)
                except Exception:
                    _show_seeds = False
                data = mm.get_all_memories_data(include_seeds=_show_seeds) or []
            except Exception as e:
                data = []
                ui.notify(t('mem_modal_list_err', msg=str(e)), type='warning')
            q = (search_box.value or '').strip().lower()
            if q:
                def _match(m):
                    return any(q in (m.get(k) or '').lower() for k in ('title', 'summary', 'text_original'))
                data = [m for m in data if _match(m)]
            list_container.clear()
            with list_container:
                if not data:
                    ui.label(t('mem_modal_list_empty')).classes('text-muted p-2')
                else:
                    # Dict des cartes pour gestion sélection visuelle
                    _card_refs = {}
                    _default_card_style = 'cursor:pointer; padding:8px 10px; border-radius:8px; border: 1px solid var(--border-color); background: transparent; box-shadow: none;'
                    _selected_card_style = 'cursor:pointer; padding:8px 10px; border-radius:8px; border: 2px solid #d4af37 !important; background: rgba(212, 175, 55, 0.15) !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.3) !important;'
                    
                    # Grille responsive (déjà définie en CSS sur .mem-list)
                    for m in data[:400]:
                        # Container avec position relative pour le crayon
                        with ui.element('div').style('position: relative; margin-bottom: 8px;'):
                            # Carte principale (cliquable)
                            mid_val = m.get('id') or ''
                            card = ui.card().classes('q-dark mem-card').style(_default_card_style)
                            _card_refs[mid_val] = card
                            def _on_click(mid=mid_val, cards=_card_refs, dflt=_default_card_style, sel=_selected_card_style):
                                if mid:
                                    if selected_id['value'] == mid:
                                        # Déjà sélectionné → désélectionner
                                        selected_id['value'] = None
                                        id_label.text = ''
                                        title_in.value = ''
                                        original_in.value = ''
                                        summary_in.value = ''
                                        cards[mid].style(dflt)
                                    else:
                                        load_into_form(str(mid))
                                        for cid, cref in cards.items():
                                            if cid == mid:
                                                cref.style(sel)
                                            else:
                                                cref.style(dflt)
                            card.on('click', _on_click)
                            
                            # Contenu de la carte
                            with card:
                                # Boutons action intégrés dans la carte (coin haut droit)
                                with ui.element('div').style('position: absolute; top: 8px; right: 8px; z-index: 1;'):
                                    with ui.row().classes('gap-1'):
                                        # Bouton redondance
                                        def _on_redundancy(mid=(m.get('id') or '')):
                                            if mid:
                                                _find_redundant_memories_popup(str(mid), refresh_list)
                                        
                                        redundancy_btn = ui.button('🔍', on_click=_on_redundancy).classes('text-xs').style(
                                            'padding: 4px; min-width: 24px; height: 24px; background: rgba(100, 149, 237, 0.2); '
                                            'border: 1px solid #6495ED; border-radius: 4px; color: #6495ED;'
                                        ).tooltip(t('mem_modal_tooltip_redundancy'))
                                        redundancy_btn.props('dense flat')
                                        
                                        # Bouton édition
                                        def _on_edit(mid=(m.get('id') or '')):
                                            if mid:
                                                _edit_memory_popup(str(mid), refresh_list)
                                        
                                        edit_btn = ui.button('✏️', on_click=_on_edit).classes('text-xs').style(
                                            'padding: 4px; min-width: 24px; height: 24px; background: rgba(212, 175, 55, 0.2); '
                                            'border: 1px solid var(--accent-color); border-radius: 4px; color: var(--accent-color);'
                                        ).tooltip(t('mem_modal_tooltip_edit'))
                                        edit_btn.props('dense flat')
                                
                                ui.label((m.get('title') or t('mem_modal_card_no_title'))).classes('mem-card-title').style('margin-right: 32px;')
                                _sum = m.get('summary') or ''
                                ui.label(_sum).classes('mem-card-summary').style('-webkit-line-clamp:2; display:-webkit-box; -webkit-box-orient:vertical; overflow:hidden;')
                                with ui.element('div').classes('mem-card-footer'):
                                    ui.label(m.get('id', '')).classes('text-xs')
                                    try:
                                        sc = float(m.get('score_impact', 0) or 0)
                                    except Exception:
                                        sc = 0.0
                                    ui.label(t('mem_modal_card_score', score=f'{sc:.2f}'))

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

    return dialog

def _find_redundant_memories_popup(memory_id: str, refresh_callback=None):
    """Popup de recherche de mémoires redondantes avec celle sélectionnée."""
    
    # Import depuis ogma_ng pour accéder au memory manager
    import sys
    ogma_ng = sys.modules.get('ogma_ng')
    if ogma_ng and hasattr(ogma_ng, '_ensure_memory_manager'):
        mm = ogma_ng._ensure_memory_manager()
    else:
        mm = None
    
    if not mm:
        ui.notify('Gestionnaire mémoire non disponible', type='warning')
        return
    
    # Charger la mémoire source
    try:
        source_memory = mm.get_memory_by_id(memory_id)
        if not source_memory:
            ui.notify(f'Mémoire {memory_id} introuvable', type='warning')
            return
    except Exception as e:
        ui.notify(f'Erreur chargement: {e}', type='warning')
        return
    
    with ui.dialog() as dialog:
        dialog.props('full-width full-height')
        dialog.open()
        
        with ui.card().classes('q-dark p-4 w-full').style('max-width: 1400px; max-height: 90vh; margin: auto; background: var(--surface-dark); overflow-y: auto;'):
            # Header
            with ui.row().classes('items-center justify-between w-full mb-4'):
                ui.label(f'🔍 Recherche redondances pour: {source_memory.get("title", memory_id)}').classes('text-h6')
                ui.button(icon='close', on_click=dialog.close).props('flat dense round').classes('text-white')
            
            ui.separator().classes('mb-4')
            
            # Afficher la mémoire source
            with ui.expansion('📌 Mémoire source', value=True).classes('bg-grey-9 mb-4'):
                ui.label(f'ID: {memory_id}').classes('text-xs text-grey-5')
                ui.label(f'Titre: {source_memory.get("title", "N/A")}').classes('text-sm mb-2')
                ui.label(f'Score impact: {source_memory.get("score_impact", 0):.2f}').classes('text-sm mb-2')
                
                with ui.expansion('Texte original', value=False).classes('bg-grey-8'):
                    ui.label(source_memory.get('text_original', 'N/A')).classes('text-sm').style('white-space: pre-wrap;')
                
                with ui.expansion('Résumé', value=False).classes('bg-grey-8'):
                    ui.label(source_memory.get('summary', 'N/A')).classes('text-sm').style('white-space: pre-wrap;')
            
            ui.separator().classes('mb-4')
            
            # Paramètres de recherche
            with ui.card().classes('q-dark p-4 mb-4').style('min-height: 120px;'):
                ui.label('⚙️ Paramètres recherche').classes('text-base font-semibold mb-3')
                
                with ui.column().classes('gap-4 w-full'):
                    with ui.row().classes('items-center gap-4 w-full'):
                        ui.label('Seuil similarité FAISS:').classes('text-sm').style('min-width: 180px;')
                        similarity_threshold = ui.slider(
                            min=0.50, max=0.99, step=0.01, value=0.75
                        ).props('label-always').style('flex-grow: 1; min-width: 300px;')
                    
                    with ui.row().classes('items-center gap-4'):
                        ui.label('Max résultats:').classes('text-sm').style('min-width: 180px;')
                        max_results = ui.number(
                            label='',
                            value=20,
                            min=5, max=100
                        ).classes('w-32')
                        ui.label('').classes('flex-grow')  # Spacer
            
            # Container résultats
            results_container = ui.column().classes('w-full gap-2')
            
            # Statistiques
            stats_label = ui.label('').classes('text-sm text-grey-5 mb-2')
            
            async def search_redundancies():
                """Lance la recherche FAISS de souvenirs similaires"""
                results_container.clear()
                stats_label.text = '🔄 Recherche en cours...'
                
                try:
                    # Récupérer la position FAISS de la mémoire source
                    source_faiss_idx = source_memory.get('faiss_index')
                    
                    if source_faiss_idx is None:
                        with results_container:
                            ui.label('⚠️ Mémoire source non indexée dans FAISS').classes('text-warning')
                        stats_label.text = ''
                        return
                    
                    # Accès direct à l'index FAISS via le memory manager
                    import faiss
                    import numpy as np
                    
                    with mm._faiss_lock:
                        if mm.faiss_index is None or mm.faiss_index.ntotal == 0:
                            with results_container:
                                ui.label('⚠️ Index FAISS non disponible').classes('text-warning')
                            stats_label.text = ''
                            return
                        
                        # Récupérer le vecteur source
                        source_vector = mm.faiss_index.reconstruct(int(source_faiss_idx))
                        source_vector = source_vector.reshape(1, -1)
                        
                        # Recherche K-NN FAISS pure
                        k = min(int(max_results.value) * 2, mm.faiss_index.ntotal)
                        distances, indices = mm.faiss_index.search(source_vector, k)
                    
                    # Récupérer le mapping ID <-> position FAISS
                    import sqlite3
                    conn = sqlite3.connect(mm.db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT id, faiss_index FROM memories WHERE faiss_index IS NOT NULL')
                    id_map = {row[1]: row[0] for row in cursor.fetchall()}
                    conn.close()
                    
                    # Convertir résultats FAISS en mémoires
                    threshold = float(similarity_threshold.value)
                    redundant = []
                    
                    for dist, idx in zip(distances[0], indices[0]):
                        mem_id = id_map.get(int(idx))
                        if not mem_id or mem_id == memory_id:
                            continue  # Skip source ou ID inconnu
                        
                        # Convertir distance L2 en similarité cosinus approximative
                        # Pour vecteurs normalisés: distance_L2 = 2 * (1 - cosine_similarity)
                        similarity = max(0, 1 - (dist / 2))
                        
                        if similarity >= threshold:
                            # Charger les données complètes de la mémoire
                            mem_data = mm.get_memory_by_id(mem_id)
                            if mem_data:
                                mem_data['similarity_score'] = similarity
                                mem_data['faiss_distance'] = float(dist)
                                redundant.append(mem_data)
                        
                        if len(redundant) >= int(max_results.value):
                            break
                    
                    stats_label.text = f'📊 {len(redundant)} mémoires redondantes trouvées (seuil ≥ {threshold:.0%})'
                    
                    if not redundant:
                        with results_container:
                            ui.label('✅ Aucune redondance détectée').classes('text-positive')
                        return
                    
                    # Afficher résultats
                    with results_container:
                        selected_for_deletion = {}  # memory_id → checkbox
                        
                        for mem in redundant:
                            with ui.card().classes('q-dark p-3 mb-2').style('border: 1px solid var(--border-color);'):
                                with ui.row().classes('items-start justify-between w-full gap-2'):
                                    # Checkbox sélection
                                    checkbox = ui.checkbox(value=False).classes('mt-1')
                                    selected_for_deletion[mem['id']] = checkbox
                                    
                                    # Infos mémoire
                                    with ui.column().classes('flex-grow gap-1'):
                                        ui.label(f'{mem.get("title", "Sans titre")}').classes('text-sm font-semibold')
                                        sim_score = mem.get("similarity_score", 0)
                                        ui.label(f'ID: {mem["id"]} | Score: {mem.get("score_impact", 0):.2f} | Similarité: {sim_score:.1%} ({sim_score:.3f})').classes('text-xs text-grey-5')
                                        
                                        # Prévisualisation texte
                                        preview_text = mem.get('summary', '') or mem.get('text_original', '')
                                        if preview_text:
                                            ui.label(preview_text[:200] + ('...' if len(preview_text) > 200 else '')).classes('text-xs text-grey-6').style('white-space: pre-wrap;')
                                    
                                    # Boutons actions
                                    with ui.column().classes('gap-1'):
                                        ui.button('👁️', on_click=lambda m=mem: _view_memory_details(m)).props('dense flat').classes('text-xs').tooltip('Voir détails')
                        
                        # Boutons actions groupées
                        ui.separator().classes('my-3')
                        
                        with ui.row().classes('justify-between items-center w-full'):
                            select_all_btn = ui.button('☑️ Tout sélectionner').classes('action-button')
                            deselect_all_btn = ui.button('⬜ Tout désélectionner').classes('action-button')
                            
                            delete_selected_btn = ui.button('🗑️ Supprimer sélection', icon='delete').classes('action-button').style(
                                'background: var(--error); color: white;'
                            )
                        
                        def select_all():
                            for cb in selected_for_deletion.values():
                                cb.value = True
                        
                        def deselect_all():
                            for cb in selected_for_deletion.values():
                                cb.value = False
                        
                        async def delete_selected():
                            to_delete = [mid for mid, cb in selected_for_deletion.items() if cb.value]
                            
                            if not to_delete:
                                ui.notify('⚠️ Aucune mémoire sélectionnée', type='warning')
                                return
                            
                            # Confirmation
                            with ui.dialog() as confirm_dialog:
                                confirm_dialog.open()
                                with ui.card().classes('q-dark p-4'):
                                    ui.label(f'⚠️ Confirmer suppression de {len(to_delete)} mémoire(s) ?').classes('text-h6 mb-4')
                                    
                                    with ui.column().classes('gap-2 mb-4'):
                                        for mid in to_delete[:10]:  # Afficher max 10
                                            mem_data = next((m for m in redundant if m['id'] == mid), None)
                                            if mem_data:
                                                ui.label(f'• {mem_data.get("title", mid)}').classes('text-sm')
                                        if len(to_delete) > 10:
                                            ui.label(f'... et {len(to_delete) - 10} autre(s)').classes('text-sm text-grey-5')
                                    
                                    with ui.row().classes('justify-end gap-2'):
                                        ui.button('Annuler', on_click=confirm_dialog.close).classes('action-button')
                                        
                                        async def execute_deletion():
                                            confirm_dialog.close()
                                            success_count = 0
                                            
                                            for mid in to_delete:
                                                try:
                                                    await mm.delete_memory(mid)
                                                    success_count += 1
                                                except Exception as e:
                                                    print(f'[REDUNDANCY] Erreur suppression {mid}: {e}')
                                            
                                            ui.notify(f'✅ {success_count}/{len(to_delete)} mémoire(s) supprimée(s)', type='positive')
                                            
                                            # Refresh
                                            if refresh_callback:
                                                refresh_callback()
                                            
                                            # Relancer recherche
                                            await search_redundancies()
                                        
                                        ui.button('SUPPRIMER', icon='delete_forever', on_click=execute_deletion).classes('action-button').style(
                                            'background: var(--error); color: white;'
                                        )
                        
                        select_all_btn.on('click', select_all)
                        deselect_all_btn.on('click', deselect_all)
                        delete_selected_btn.on('click', delete_selected)
                
                except Exception as e:
                    with results_container:
                        ui.label(f'❌ Erreur recherche: {e}').classes('text-error')
                    stats_label.text = 'Erreur'
                    print(f'[REDUNDANCY] Erreur: {e}')
                    import traceback
                    traceback.print_exc()
            
            def _view_memory_details(memory_data):
                """Affiche détails d'une mémoire dans un popup"""
                with ui.dialog() as detail_dialog:
                    detail_dialog.open()
                    with ui.card().classes('q-dark p-4').style('max-width: 800px;'):
                        with ui.row().classes('items-center justify-between w-full mb-3'):
                            ui.label(f'📄 {memory_data.get("title", "Détails")}').classes('text-h6')
                            ui.button(icon='close', on_click=detail_dialog.close).props('flat dense round')
                        
                        ui.label(f'ID: {memory_data["id"]}').classes('text-xs text-grey-5 mb-2')
                        ui.label(f'Score impact: {memory_data.get("score_impact", 0):.2f}').classes('text-sm mb-2')
                        ui.label(f'Similarité: {memory_data.get("similarity_score", 0):.0%}').classes('text-sm mb-2')
                        
                        ui.separator().classes('my-3')
                        
                        with ui.expansion('Texte original', value=True).classes('bg-grey-9'):
                            ui.label(memory_data.get('text_original', 'N/A')).classes('text-sm').style('white-space: pre-wrap;')
                        
                        with ui.expansion('Résumé', value=False).classes('bg-grey-9'):
                            ui.label(memory_data.get('summary', 'N/A')).classes('text-sm').style('white-space: pre-wrap;')
            
            # Bouton lancer recherche
            with ui.row().classes('justify-center mb-4'):
                ui.button('🔍 Lancer recherche', icon='search', on_click=search_redundancies).classes('btn-primary').style(
                    'font-size: 1.1em; padding: 12px 24px;'
                )
            
            # Lancer recherche auto au chargement
            ui.timer(0.1, search_redundancies, once=True)


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
        ui.notify(t('mem_edit_notify_unavailable'), type='negative')
        return
    
    # Récupérer le souvenir
    try:
        memory_data = mm.get_memory_by_id(memory_id)
        if not memory_data:
            ui.notify(t('mem_edit_notify_not_found'), type='negative')
            return
    except Exception as e:
        ui.notify(t('mem_edit_notify_fetch_error', msg=str(e)), type='negative')
        return
    
    dialog = ui.dialog()
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(600px, 90vw); max-height: 80vh; overflow-y: auto;'):
        ui.label(t('mem_edit_title')).classes('popup-title')
        
        # Champs éditables
        title_input = ui.input(t('mem_edit_label_title'), value=memory_data.get('title', '')).classes('w-full mb-2')
        summary_input = ui.textarea(t('mem_edit_label_summary'), value=memory_data.get('summary', '')).classes('w-full mb-2').style('min-height: 80px;')
        text_input = ui.textarea(t('mem_edit_label_text'), value=memory_data.get('text_original', '')).classes('w-full mb-4').style('min-height: 120px;')
        
        async def save_changes():
            try:
                if memory_id.startswith('SEED_'):
                    ui.notify(t('mem_edit_notify_seed_refused'), type='info')
                    return
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
                    ui.notify(t('mem_edit_notify_updated'), type='positive')
                    dialog.close()
                    # Rafraîchir la liste si callback fourni
                    if refresh_callback:
                        refresh_callback()
                else:
                    ui.notify(t('mem_edit_notify_update_failed'), type='negative')
                    
            except Exception as e:
                ui.notify(t('memo_popup_notify_error', msg=str(e)), type='negative')
        
        def cancel():
            dialog.close()
        
        # Boutons d'action
        with ui.row().classes('justify-end gap-2 mt-4'):
            ui.button(t('modal_cancel'), on_click=cancel).classes('action-button')
            ui.button(t('modal_save'), on_click=save_changes).classes('send-button')
    
    dialog.open()

def _memorization_popup(conversation_id: str, title: str):
    """Popup de confirmation et édition pour la mémorisation d'une conversation."""
    dialog = ui.dialog()
    
    async def confirm_memorization():
        try:
            ui.notify(t('memo_popup_notify_generating'), type='info')
            print(f"[DEBUG] Génération résumé pour conversation {conversation_id}")
            summary = await _generate_conversation_summary(conversation_id)
            print(f"[DEBUG] Résumé généré: {len(summary) if summary else 0} caractères")
            
            if not summary:
                ui.notify(t('memo_popup_notify_summary_failed'), type='negative')
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
            ui.notify(t('memo_popup_notify_error', msg=str(e)), type='negative')
    
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(400px, 90vw);'):
        ui.label(t('memo_popup_title')).classes('popup-title')
        ui.label(t('memo_popup_conversation', title=title)).classes('text-sm text-muted mb-4')
        
        # Affichage du compteur de conversations mémorisées
        memorized_count = _count_memorized_conversations()
        ui.label(t('memo_popup_count', n=memorized_count)).classes('text-sm text-green-400 mb-2')
        
        ui.label(t('memo_popup_question')).classes('mb-4')
        ui.label(t('memo_popup_hint')).classes('text-xs text-muted mb-4')
        
        with ui.row().classes('justify-end gap-2'):
            ui.button(t('modal_cancel'), on_click=dialog.close).classes('action-button')
            ui.button(t('memo_popup_btn_generate'), on_click=confirm_memorization).classes('send-button')
    
    dialog.open()

def _update_memorization_popup(conversation_id: str, title: str):
    """Popup d'actualisation pour une mémorisation obsolète."""
    dialog = ui.dialog()
    
    async def confirm_update():
        try:
            ui.notify(t('memo_update_notify_regenerating'), type='info')
            summary = await _generate_conversation_summary(conversation_id)
            
            if not summary:
                ui.notify(t('memo_popup_notify_summary_failed'), type='negative')
                return
            
            with dialog:
                dialog.clear()
                _create_update_edit_interface(dialog, conversation_id, title, summary)
            
        except Exception as e:
            ui.notify(t('memo_popup_notify_error', msg=str(e)), type='negative')
    
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(400px, 90vw);'):
        ui.label(t('memo_update_title')).classes('popup-title')
        ui.label(t('memo_popup_conversation', title=title)).classes('text-sm text-muted mb-4')
        ui.label(t('memo_update_warn')).classes('text-sm text-orange-400 mb-2')
        ui.label(t('memo_update_hint')).classes('text-xs text-muted mb-4')
        
        with ui.row().classes('justify-end gap-2'):
            ui.button(t('modal_cancel'), on_click=dialog.close).classes('action-button')
            ui.button(t('memo_update_btn'), on_click=confirm_update).classes('send-button')
    
    dialog.open()

def _create_update_edit_interface(dialog, conversation_id: str, title: str, summary: str):
    """Interface d'édition pour l'actualisation d'une mémorisation existante."""
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(600px, 90vw); max-height: 80vh;'):
        ui.label(t('memo_edit_title')).classes('popup-title')
        ui.label(t('memo_popup_conversation', title=title)).classes('text-sm text-muted mb-4')
        
        summary_input = ui.textarea(
            t('memo_edit_label_summary'), 
            value=summary,
        ).classes('w-full').style('min-height: 200px;')
        
        word_count = ui.label('').classes('text-xs text-muted')
        
        def update_word_count():
            words = len(summary_input.value.split()) if summary_input.value else 0
            word_count.text = t('memo_edit_word_count', n=words)
            if words > 150:
                word_count.classes(remove='text-muted', add='text-red-400')
            else:
                word_count.classes(remove='text-red-400', add='text-muted')
        
        summary_input.on('input', update_word_count)
        update_word_count()
        
        async def finalize_update():
            if not summary_input.value.strip():
                ui.notify(t('memo_edit_notify_empty'), type='negative')
                return
            
            words = len(summary_input.value.split())
            if words > 150:
                ui.notify(t('memo_edit_notify_too_long'), type='negative')
                return
            
            ui.notify(t('memo_update_notify_progress'), type='info')
            
            try:
                success = await _update_memorized_conversation(conversation_id, summary_input.value.strip())
                
                if success:
                    _mark_conversation_memorized(conversation_id, True)
                    ui.notify(t('memo_update_notify_success'), type='positive')
                    dialog.close()
                    try:
                        import ogma_ng
                        if hasattr(ogma_ng, '_sidebar_render_cb') and ogma_ng._sidebar_render_cb:
                            ogma_ng._sidebar_render_cb(ogma_ng._current_conversation_id)
                    except Exception:
                        pass
                    _trigger_memory_update()
                else:
                    ui.notify(t('memo_update_notify_failed'), type='negative')
                    
            except Exception as e:
                ui.notify(t('memo_popup_notify_error', msg=str(e)), type='negative')
        
        with ui.row().classes('justify-end gap-2 mt-4'):
            ui.button(t('modal_cancel'), on_click=dialog.close).classes('action-button')
            ui.button(t('memo_update_btn'), on_click=finalize_update).classes('send-button')

def _open_other_backends_popup():
    """Popup isolé pour configuration des backends non-API (Ollama/GGUF/KoboldCpp)"""
    sm = _get_settings_manager()
    if not sm:
        return None
    
    dialog = ui.dialog()
    with dialog, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(90vw, 700px); height: 70vh; overflow-y: auto;'):
        ui.label(t('backends_title')).classes('popup-title text-lg font-bold mb-4')
        
        # État du popup
        current_backend = 'Ollama'  # Par défaut
        
        # Menu sélection backend avec bouton actualiser
        with ui.row().classes('w-full mb-4 gap-2'):
            backend_select = ui.select(
                ['Ollama', 'GGUF', 'KoboldCpp'], 
                value=current_backend,
                label=t('backends_label_backend_type')
            ).classes('form-select flex-1')
            
            # Bouton pour forcer la mise à jour de l'interface
            ui.button(t('backends_btn_refresh_ui'), on_click=lambda: force_interface_update()).classes('btn-secondary')
        
        # Container pour zone adaptive
        adaptive_container = ui.column().classes('w-full')
        
        # Variables pour capturer les inputs de chaque interface
        interface_data = {}
        
        def _create_ollama_interface():
            """Interface spécialisée Ollama"""
            adaptive_container.clear()
            with adaptive_container:
                ui.label(t('backends_ollama_title')).classes('text-md font-semibold mb-2')
                
                # Récupération config existante
                other_backends = sm.settings.get('other_backends', {})
                ollama_config = other_backends.get('ollama', {})
                
                url_input = ui.input(
                    label=t('backends_ollama_url_label'), 
                    value=ollama_config.get('url', 'http://localhost:11434')
                ).classes('form-input mb-2 w-full')
                
                # Sélecteur de modèles Ollama
                model_select = ui.select(
                    [], 
                    value=None,  # Pas de valeur par défaut jusqu'à ce que les modèles soient chargés
                    label=t('backends_ollama_model_label')
                ).classes('form-select mb-2 w-full')
                
                models_container = ui.column().classes('mb-2')
                
                async def refresh_kobold_models():
                    """Actualise la liste des modèles KoboldCpp"""
                    try:
                        ui.notify(t('backends_kobold_refresh_progress'), type='info')
                        
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
                        
                        ui.notify(t('backends_notify_count_found', n=len(mock_models)), type='positive')
                        
                    except Exception as e:
                        ui.notify(t('backends_notify_models_err', msg=str(e)), type='warning')
                
                async def refresh_ollama_models():
                    try:
                        # S'assurer que les managers sont initialisés
                        _ensure_backends()
                        ollama_mgr = _ollama_mgr()
                        assert ollama_mgr is not None
                        
                        models_container.clear()
                        with models_container:
                            ui.label(t('backends_ollama_refresh_progress')).classes('text-sm mb-2')
                        
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
                                ui.label(t('backends_ollama_models_found', n=len(available_models))).classes('text-sm mb-2 text-green-500')
                                for model in available_models:
                                    ui.label(f'• {model}').classes('text-sm text-muted pl-4')
                            else:
                                ui.label(t('backends_ollama_no_models_label')).classes('text-sm mb-2 text-orange-500')
                                ui.label(t('backends_ollama_no_models_hint')).classes('text-sm text-muted')
                        
                        if available_models:
                            ui.notify(t('backends_ollama_notify_refreshed'), type='positive')
                        else:
                            ui.notify(t('backends_ollama_notify_unavailable'), type='warning')
                        
                    except Exception as e:
                        models_container.clear()
                        with models_container:
                            ui.label(t('backends_label_error', msg=str(e))).classes('text-sm text-red-500')
                        ui.notify(t('backends_notify_refresh_err', msg=str(e)), type='warning')
                
                async def test_ollama_connection():
                    try:
                        ui.notify(t('backends_ollama_notify_test', url=url_input.value), type='info')
                        # Simulation - à remplacer par vraie logique
                        ui.notify(t('backends_ollama_notify_test_ok'), type='positive')
                    except Exception as e:
                        ui.notify(t('backends_notify_test_err', msg=str(e)), type='warning')
                
                with ui.row().classes('gap-2 mb-4'):
                    ui.button(t('backends_btn_refresh_models'), on_click=refresh_ollama_models).classes('action-button')
                    ui.button(t('backends_btn_test_connection'), on_click=test_ollama_connection).classes('action-button')
                
                # Paramètres spécifiques
                ui.separator().classes('mb-2')
                ui.label(t('backends_section_advanced')).classes('text-sm font-semibold mb-2')
                timeout_input = ui.number(
                    label=t('backends_label_timeout'), 
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
                ui.label(t('backends_gguf_title')).classes('text-md font-semibold mb-2')
                
                other_backends = sm.settings.get('other_backends', {})
                gguf_config = other_backends.get('gguf', {})
                
                model_path_input = ui.input(
                    label=t('backends_gguf_path_label'), 
                    value=gguf_config.get('model_path', ''),
                    placeholder='C:/models/model.gguf'
                ).classes('form-input mb-2 w-full')
                
                # Sélecteur de fichiers simulé pour l'instant
                model_files_select = ui.select(
                    [],
                    value=gguf_config.get('selected_file', None),
                    label=t('backends_gguf_files_label')
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
                                title=t('backends_gguf_dialog_title'),
                                filetypes=[
                                    (t('backends_gguf_filetype_models'), "*.gguf"),
                                    (t('backends_gguf_filetype_all'), "*.*")
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
                                
                                ui.notify(t('backends_gguf_notify_selected', name=os.path.basename(file_path), size=file_size), type='positive')
                            else:
                                ui.notify(t('backends_gguf_notify_no_file'), type='info')
                        
                        except ImportError:
                            # Fallback: scan automatique des dossiers communs
                            ui.notify(t('backends_gguf_notify_no_tk'), type='info')
                            await scan_common_directories()
                            
                    except Exception as e:
                        ui.notify(t('backends_gguf_notify_browse_err', msg=str(e)), type='warning')
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
                            
                            ui.notify(t('backends_gguf_notify_scan_found', n=len(found_models)), type='positive')
                        else:
                            ui.notify(t('backends_gguf_notify_scan_empty'), type='warning')
                            ui.notify(t('backends_gguf_notify_scan_hint'), type='info')
                            
                    except Exception as e:
                        ui.notify(t('backends_gguf_notify_scan_err', msg=str(e)), type='warning')
                
                # Event handler sélection fichier
                def _on_file_select():
                    if model_files_select.value:
                        model_path_input.value = model_files_select.value
                
                model_files_select.on('change', lambda: _on_file_select())
                
                with ui.row().classes('gap-2 mb-2'):
                    ui.button(t('backends_gguf_btn_scan'), on_click=browse_gguf_file).classes('action-button')
                    ui.button(t('backends_gguf_btn_open_folder'), on_click=lambda: open_file_explorer()).classes('action-button')
                
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
                        ui.notify(t('backends_gguf_notify_explorer', path=folder_path), type='info')
                        
                    except Exception as e:
                        ui.notify(t('backends_gguf_notify_explorer_err', msg=str(e)), type='warning')
                
                ui.separator().classes('mb-2')
                ui.label(t('backends_gguf_section_gpu')).classes('text-sm font-semibold mb-2')
                
                gpu_layers_input = ui.number(
                    label=t('backends_gguf_gpu_layers_label'), 
                    value=gguf_config.get('gpu_layers', -1),
                    min=-1, max=100
                ).classes('form-input mb-2').tooltip(t('backends_gguf_gpu_layers_tooltip'))
                
                context_size_input = ui.number(
                    label=t('backends_gguf_ctx_label'), 
                    value=gguf_config.get('context_size', 4096),
                    min=512, max=32768
                ).classes('form-input mb-2').tooltip(t('backends_gguf_ctx_tooltip'))
                
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
                ui.label(t('backends_kobold_title')).classes('text-md font-semibold mb-2')
                
                other_backends = sm.settings.get('other_backends', {})
                kobold_config = other_backends.get('kobold', {})
                
                url_input = ui.input(
                    label=t('backends_kobold_url_label'), 
                    value=kobold_config.get('url', 'http://localhost:5001')
                ).classes('form-input mb-2 w-full')
                
                model_select = ui.select(
                    label=t('backends_kobold_model_label'),
                    options=[],
                    value=kobold_config.get('selected_model')
                ).classes('form-input mb-2 w-full')
                
                ui.button(t('backends_kobold_btn_refresh'), on_click=lambda: refresh_kobold_models()).classes('btn-secondary mr-2')
                ui.button(t('backends_kobold_btn_test'), on_click=lambda: test_backend_connection('kobold')).classes('btn-primary')
                
                # Sauvegarder références inputs
                interface_data['kobold'] = {
                    'url_input': url_input,
                    'model_select': model_select
                }
                
                async def test_kobold_connection():
                    try:
                        ui.notify(t('backends_kobold_notify_test', url=url_input.value), type='info')
                        # Simulation - à remplacer par vraie logique
                        ui.notify(t('backends_kobold_notify_test_ok'), type='positive')
                    except Exception as e:
                        ui.notify(t('backends_notify_test_err', msg=str(e)), type='warning')
                
                ui.separator().classes('mb-2')
                ui.label(t('backends_kobold_section_gen')).classes('text-sm font-semibold mb-2')
                
                max_length_input = ui.number(
                    label=t('backends_kobold_max_length_label'), 
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
                ui.label(t('backends_api_title')).classes('text-md font-semibold mb-4')
                ui.label(t('backends_api_redirect')).classes('text-muted mb-4')
                ui.separator().classes('mb-4')
                ui.label(t('backends_api_local_only')).classes('text-sm text-orange-400 mb-2')
                ui.label(t('backends_api_select_hint')).classes('text-sm text-muted')
        
        def force_interface_update():
            """Force la mise à jour de l'interface manuellement"""
            print(f"[FACTORY] FORCE UPDATE: Backend sélectionné = {backend_select.value}")
            _update_interface()
            ui.notify(t('backends_notify_interface_active', backend=backend_select.value), type='positive')
        
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
                    ui.notify(t('backends_ollama_save_ok'), type='positive')
                    
                elif backend == 'gguf' and 'gguf' in interface_data:
                    gguf_data = interface_data['gguf']
                    other_backends['gguf'] = {
                        'model_path': gguf_data['model_path_input'].value or '',
                        'gpu_layers': int(gguf_data['gpu_layers_input'].value if gguf_data['gpu_layers_input'].value is not None else -1),
                        'context_size': int(gguf_data['context_size_input'].value or 4096),
                        'selected_model': gguf_data['model_files_select'].value or '',
                        'enabled': True
                    }
                    ui.notify(t('backends_gguf_save_ok'), type='positive')
                    
                elif backend == 'kobold' and 'kobold' in interface_data:
                    kobold_data = interface_data['kobold']
                    other_backends['kobold'] = {
                        'url': kobold_data['url_input'].value or 'http://localhost:5001',
                        'selected_model': kobold_data['model_select'].value or '',
                        'enabled': True
                    }
                    ui.notify(t('backends_kobold_save_ok'), type='positive')
                
                # Sauvegarder dans settings.json (section isolée)
                sm.settings['other_backends'] = other_backends
                sm.save_settings()
                
                print(f"[OTHER-BACKENDS] Configuration {backend} sauvegardée: {other_backends.get(backend, {})}")
                dialog.close()
                
            except Exception as e:
                print(f"[OTHER-BACKENDS] Erreur sauvegarde: {e}")
                ui.notify(t('backends_notify_save_err', msg=str(e)), type='warning')
        
        # Boutons popup
        ui.separator().classes('my-4')
        with ui.row().classes('justify-end gap-2 w-full'):
            ui.button(t('modal_cancel'), on_click=dialog.close).classes('action-button')
            ui.button(t('backends_btn_save'), on_click=_save_other_backends).classes('send-button')
    
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
    
    # Synchronisation initiale des clés vers le vault (migration)
    try:
        from api_keys_vault import sync_from_current_settings
        sync_from_current_settings()
    except Exception:
        pass
    
    # Ajout de la classe ia-modal et largeur plafonnée pour éviter le grand espace à droite
    with dialog, ui.card().classes('popup-content q-dark ia-modal').style('background: var(--bg-secondary); color: var(--text-primary); height: 82vh; overflow-y: auto; width: min(92vw, 900px); margin: 0 auto;'):
        ui.label(t('models_modal_title')).classes('popup-title')
        tabs = ui.tabs().classes('mb-4')
        with tabs:
            t_chat = ui.tab(t('models_tab_chat'))
            t_arch = ui.tab(t('models_tab_arch'))
            t_embed = ui.tab(t('models_tab_embed'))

        # Voyants d'état
        with ui.row().classes('items-center gap-4 mb-2'):
            ui.label(t('models_label_status')).classes('text-muted')
            chat_dot = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label(t('models_label_status_chat')).classes('text-sm')
            arch_dot = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label(t('models_label_status_arch')).classes('text-sm')
            emb_dot = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label(t('models_label_status_embed')).classes('text-sm')

        async def set_dot(el, ok: bool):
            try:
                el.style(f'background: {"#16a34a" if ok else "#dc2626"};')
            except Exception:
                pass

        def _calculate_optimal_ollama(model_name, ollama_url='http://localhost:11434'):
            """Calcule context_length et max_tokens optimaux pour un modèle Ollama selon le hardware."""
            import requests
            hw = sm.settings.get('hardware', {})
            ram_go = float(hw.get('ram_total_gb', 0))
            vram_go = float(hw.get('gpu_vram_gb', 0))
            if ram_go == 0:
                return None, 'Hardware non renseigne — allez dans Profil > Caracteristiques Hardware'
            ram_usable = ram_go * 0.7
            mem_for_model = vram_go if vram_go >= 2 else ram_usable
            if not model_name:
                return None, 'Aucun modele Ollama selectionne'
            try:
                # Taille du fichier modèle
                tags_resp = requests.get(f'{ollama_url}/api/tags', timeout=5)
                model_size_gb = 0
                if tags_resp.status_code == 200:
                    for m in tags_resp.json().get('models', []):
                        if m.get('name') == model_name:
                            model_size_gb = m.get('size', 0) / (1024**3)
                            break
                # Specs du modèle
                show_resp = requests.post(f'{ollama_url}/api/show', json={'model': model_name}, timeout=5)
                if show_resp.status_code != 200:
                    return None, f'Ollama /api/show erreur {show_resp.status_code}'
                show_data = show_resp.json()
                details = show_data.get('details', {})
                model_info = show_data.get('model_info', {})
                native_ctx = 0
                embed_len = 0
                head_count_kv = 1
                block_count = 0
                for k, v in model_info.items():
                    if v is None:
                        continue
                    if k.endswith('.context_length') and 'audio' not in k:
                        native_ctx = int(v)
                    if k.endswith('.embedding_length') and 'audio' not in k and 'vision' not in k:
                        embed_len = int(v)
                    if k.endswith('.attention.head_count_kv'):
                        head_count_kv = int(v)
                    if k.endswith('.block_count') and 'audio' not in k and 'vision' not in k:
                        block_count = int(v)
                head_dim = (embed_len // max(head_count_kv, 1)) if embed_len and head_count_kv else 64
                kv_per_token = 2 * block_count * head_count_kv * head_dim * 2
                overhead = 0.5
                free_after_model = mem_for_model - model_size_gb - overhead
                if free_after_model < 0.1:
                    return None, f'Modele trop gros ({model_size_gb:.1f} Go) pour votre memoire ({mem_for_model:.1f} Go dispo)'
                if kv_per_token > 0:
                    max_ctx = int((free_after_model * 1024**3) / kv_per_token)
                else:
                    max_ctx = 8192
                if native_ctx:
                    max_ctx = min(max_ctx, native_ctx)
                # Arrondir vers le bas à une valeur propre
                for nice in [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]:
                    if nice >= max_ctx:
                        recommended_ctx = nice // 2 if nice > max_ctx else nice
                        break
                else:
                    recommended_ctx = 131072
                recommended_ctx = max(recommended_ctx, 1024)
                recommended_mt = min(4096, max(512, recommended_ctx - 512))
                param_size = details.get('parameter_size', '?')
                quant = details.get('quantization_level', '?')
                return {
                    'context_length': recommended_ctx,
                    'max_tokens': recommended_mt,
                    'model_size_gb': round(model_size_gb, 1),
                    'param_size': param_size,
                    'quant': quant,
                    'mem_available': round(mem_for_model, 1),
                    'native_ctx': native_ctx,
                }, None
            except requests.exceptions.ConnectionError:
                return None, 'Ollama non joignable — verifiez qu\'il est demarre'
            except Exception as e:
                return None, f'Erreur: {e}'

        def _calculate_optimal_gguf(model_path):
            """Calcule context_length et gpu_layers optimaux pour un modèle GGUF selon le hardware."""
            import struct, os
            hw = sm.settings.get('hardware', {})
            ram_go = float(hw.get('ram_total_gb', 0))
            vram_go = float(hw.get('gpu_vram_gb', 0))
            if ram_go == 0:
                return None, 'Hardware non renseigne — allez dans Profil > Caracteristiques Hardware'
            if not model_path or not os.path.exists(model_path):
                return None, f'Fichier GGUF introuvable : {model_path or "(vide)"}'
            ram_usable = ram_go * 0.65
            mem_for_model = vram_go if vram_go >= 2 else ram_usable
            file_size_gb = os.path.getsize(model_path) / (1024**3)
            try:
                GGUF_TYPES = {
                    0: ('<B', 1), 1: ('<b', 1), 2: ('<H', 2), 3: ('<h', 2),
                    4: ('<I', 4), 5: ('<i', 4), 6: ('<f', 4), 7: ('<?', 1),
                    8: (None, None), 9: (None, None),
                    10: ('<Q', 8), 11: ('<q', 8), 12: ('<d', 8),
                }
                def _read_str(f):
                    length = struct.unpack('<Q', f.read(8))[0]
                    return f.read(length).decode('utf-8')
                native_ctx = 0
                embed_len = 0
                head_count = 0
                head_count_kv = 0
                block_count = 0
                arch_name = ''
                model_name = ''
                with open(model_path, 'rb') as f:
                    magic = f.read(4)
                    if magic != b'GGUF':
                        return None, 'Fichier invalide — pas un format GGUF'
                    version = struct.unpack('<I', f.read(4))[0]
                    _tensor_count = struct.unpack('<Q', f.read(8))[0]
                    metadata_count = struct.unpack('<Q', f.read(8))[0]
                    for _ in range(metadata_count):
                        key = _read_str(f)
                        vtype = struct.unpack('<I', f.read(4))[0]
                        if vtype == 8:
                            val = _read_str(f)
                        elif vtype == 9:
                            arr_type = struct.unpack('<I', f.read(4))[0]
                            arr_len = struct.unpack('<Q', f.read(8))[0]
                            if arr_type in GGUF_TYPES and GGUF_TYPES[arr_type][0]:
                                for _ in range(arr_len):
                                    f.read(GGUF_TYPES[arr_type][1])
                            elif arr_type == 8:
                                for _ in range(arr_len):
                                    _read_str(f)
                            val = f'[array:{arr_len}]'
                        elif vtype in GGUF_TYPES and GGUF_TYPES[vtype][0]:
                            val = struct.unpack(GGUF_TYPES[vtype][0], f.read(GGUF_TYPES[vtype][1]))[0]
                        else:
                            val = None
                        if val is None:
                            continue
                        if key == 'general.architecture':
                            arch_name = str(val)
                        elif key == 'general.name':
                            model_name = str(val)
                        elif key.endswith('.context_length') and 'audio' not in key:
                            native_ctx = int(val)
                        elif key.endswith('.embedding_length') and 'audio' not in key and 'vision' not in key:
                            embed_len = int(val)
                        elif key.endswith('.attention.head_count') and not key.endswith('.head_count_kv'):
                            head_count = int(val)
                        elif key.endswith('.attention.head_count_kv'):
                            head_count_kv = int(val)
                        elif key.endswith('.block_count') and 'audio' not in key and 'vision' not in key:
                            block_count = int(val)
                # Calcul KV cache — head_dim vient de head_count total (pas head_count_kv)
                if head_count and embed_len:
                    head_dim = embed_len // head_count
                elif head_count_kv and embed_len:
                    head_dim = embed_len // head_count_kv
                else:
                    head_dim = 64
                kv_heads = head_count_kv or head_count or 1
                # KV cache FP16: 2 (K+V) * layers * kv_heads * head_dim * 2 bytes
                kv_per_token = 2 * block_count * kv_heads * head_dim * 2
                overhead = 0.5
                free_after_model = mem_for_model - file_size_gb - overhead
                if free_after_model < 0.1:
                    return None, f'Modele trop gros ({file_size_gb:.1f} Go) pour votre memoire ({mem_for_model:.1f} Go dispo)'
                if kv_per_token > 0:
                    max_ctx = int((free_after_model * 1024**3) / kv_per_token)
                else:
                    max_ctx = 8192
                if native_ctx:
                    max_ctx = min(max_ctx, native_ctx)
                # Arrondir au palier inférieur (sûr et prévisible)
                for nice in [65536, 32768, 16384, 8192, 4096, 2048, 1024]:
                    if nice <= max_ctx:
                        recommended_ctx = nice
                        break
                else:
                    recommended_ctx = 1024
                recommended_ctx = max(recommended_ctx, 1024)
                recommended_mt = min(4096, max(512, recommended_ctx - 512))
                # GPU layers : 0 si pas de GPU dédié, sinon auto
                recommended_gpu = 0 if vram_go < 2 else -1
                return {
                    'context_length': recommended_ctx,
                    'max_tokens': recommended_mt,
                    'gpu_layers': recommended_gpu,
                    'model_size_gb': round(file_size_gb, 1),
                    'model_name': model_name or os.path.basename(model_path),
                    'arch': arch_name,
                    'mem_available': round(mem_for_model, 1),
                    'native_ctx': native_ctx,
                    'kv_per_token': kv_per_token,
                    'head_dim': head_dim,
                    'kv_heads': kv_heads,
                }, None
            except Exception as e:
                return None, f'Erreur lecture GGUF: {e}'

        def _calculate_optimal_api():
            """Pour API : remet -1/-1 (le provider gère ses propres limites)."""
            return {
                'context_length': -1,
                'max_tokens': -1,
                'info': 'Valeurs auto-gerees par le provider. En cas d\'erreur de contexte, renseignez la valeur manuellement.',
            }, None

        def _apply_optimal_values(backend_type, section, fields):
            """Dispatcher : calcule les valeurs optimales selon le backend et remplit les champs.
            
            Args:
                backend_type: 'API', 'Ollama', 'GGUF', 'KoboldCpp'
                section: dict avec les clés nécessaires (model, url, path...)
                fields: dict avec les widgets UI à remplir (max_tokens, ctx, label, gguf_ctx, gguf_gpu)
            """
            label = fields.get('label')
            if backend_type == 'Ollama':
                model = section.get('model')
                url = section.get('url', 'http://localhost:11434')
                if not model:
                    if label: label.set_text('Selectionnez un modele Ollama d\'abord')
                    ui.notify('Selectionnez un modele Ollama', type='warning')
                    return
                result, err = _calculate_optimal_ollama(model, url)
                if err:
                    if label: label.set_text(f'Erreur : {err}')
                    ui.notify(err, type='warning')
                    return
                if fields.get('max_tokens'): fields['max_tokens'].value = result['max_tokens']
                if fields.get('ctx'): fields['ctx'].value = result['context_length']
                if label:
                    label.set_text(
                        f'{model} ({result["param_size"]} {result["quant"]}) — '
                        f'fichier {result["model_size_gb"]} Go — '
                        f'ctx natif {result["native_ctx"]:,} — '
                        f'memoire dispo {result["mem_available"]} Go — '
                        f'ctx optimal: {result["context_length"]:,} / max_tokens: {result["max_tokens"]:,}'
                    )
                ui.notify(f'Valeurs optimales appliquees : ctx={result["context_length"]:,}, mt={result["max_tokens"]:,}', type='positive')

            elif backend_type == 'GGUF':
                model_path = section.get('model_path', '')
                result, err = _calculate_optimal_gguf(model_path)
                if err:
                    if label: label.set_text(f'Erreur : {err}')
                    ui.notify(err, type='warning')
                    return
                if fields.get('gguf_ctx'): fields['gguf_ctx'].value = result['context_length']
                if fields.get('gguf_gpu'): fields['gguf_gpu'].value = result['gpu_layers']
                if fields.get('max_tokens'): fields['max_tokens'].value = result['max_tokens']
                if fields.get('ctx'): fields['ctx'].value = result['context_length']
                if label:
                    label.set_text(
                        f'{result["model_name"]} ({result["arch"]}) — '
                        f'fichier {result["model_size_gb"]} Go — '
                        f'ctx natif {result["native_ctx"]:,} — '
                        f'memoire dispo {result["mem_available"]} Go — '
                        f'ctx optimal: {result["context_length"]:,} / gpu_layers: {result["gpu_layers"]}'
                    )
                ui.notify(f'Valeurs optimales appliquees : ctx={result["context_length"]:,}, mt={result["max_tokens"]:,}, gpu={result["gpu_layers"]}', type='positive')

            elif backend_type == 'API':
                result, _ = _calculate_optimal_api()
                if fields.get('max_tokens'): fields['max_tokens'].value = result['max_tokens']
                if fields.get('ctx'): fields['ctx'].value = result['context_length']
                if label:
                    label.set_text('Valeurs auto-gerees par le provider (-1 = pas de limite imposee). En cas d\'erreur de contexte, renseignez la valeur manuellement.')
                ui.notify('API : valeurs remises a -1 (le provider gere ses limites)', type='info')

            else:
                ui.notify(f'Backend {backend_type} : pas de calcul automatique disponible', type='info')
                if label: label.set_text(f'Backend {backend_type} non supporte pour le calcul automatique')

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
                    chat_backend = ui.select(chat_backend_opts, value=detect_backend(chat), label=t('models_label_backend')).classes('form-select narrow-field').style('min-width: 200px; flex: 1;')
                    ui.button('🔄', on_click=lambda: _refresh_chat_interface()).classes('action-button').style('min-width: 40px; height: 40px; flex-shrink: 0;').tooltip(t('models_tooltip_refresh_iface'))

                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label(t('models_label_availability')).classes('text-sm text-muted')
                    chat_dot_inline = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut

                # Zone API
                with ui.column() as chat_api_zone:
                    chat_provider_opts = ['Aucun'] + REMOTE_PROVIDERS[:-1] + ['AIHorde']
                    
                    def on_chat_provider_change(e):
                        """Charge la clé API depuis le vault au changement de provider et recharge les modèles"""
                        try:
                            from api_keys_vault import get_api_key, has_saved_key
                            provider = e.value
                            if provider and provider != 'Aucun' and has_saved_key(provider):
                                saved_key = get_api_key(provider)
                                if saved_key:
                                    chat_api_key.value = saved_key
                                    ui.notify(t('models_notify_vault_loaded', provider=provider), type='info')
                            # Recharger les modèles pour le nouveau provider
                            if provider and provider != 'Aucun':
                                refresh_cb = _refresh_models_ui('chat', chat_backend, chat_provider, chat_model, chat_api_key)
                                ui.timer(0.1, lambda: asyncio.create_task(refresh_cb()), once=True)
                        except Exception as ex:
                            print(f"[API-VAULT] Erreur chargement clé chat: {ex}")
                    
                    chat_provider = ui.select(
                        chat_provider_opts,
                        value=_safe(chat.get('provider', 'Aucun'), chat_provider_opts),
                        label=t('models_label_provider'),
                        on_change=on_chat_provider_change
                    ).classes('form-select mb-2 narrow-field')
                    chat_model = ui.select([], value=None, label=t('models_label_api_model')).classes('form-select mb-2 narrow-field')
                    chat_api_key = ui.input(label=t('models_label_api_key'), password=True, value=chat.get('api_key', '')).classes('form-input mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models'), on_click=_refresh_models_ui('chat', chat_backend, chat_provider, chat_model, chat_api_key)).classes('action-button')
                        ui.button(t('models_btn_test'), on_click=_test_connection_ui('chat', chat_backend, chat_provider, chat_api_key)).classes('action-button')
                with ui.column() as chat_ollama_zone:
                    ui.label(t('models_section_ollama_config')).classes('text-md font-semibold mb-2')
                    
                    chat_ollama_url = ui.input(label=t('models_label_url_ollama'), value=chat.get('ollama_url', 'http://localhost:11434')).classes('form-input mb-2 narrow-field')
                    
                    # Sélecteur de modèles Ollama avec container pour status
                    chat_ollama_model = ui.select([], value=None, label=t('models_label_ollama_model')).classes('form-select mb-2 narrow-field')
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
                                ui.label(t('models_notify_ollama_refresh_progress')).classes('text-sm mb-2')
                            
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
                                    ui.label(t('models_notify_models_found', n=len(available_models))).classes('text-sm mb-2 text-green-500')
                                    for model in available_models:
                                        ui.label(f'• {model}').classes('text-sm text-muted pl-4')
                                else:
                                    ui.label(t('models_notify_models_none')).classes('text-sm mb-2 text-orange-500')
                                    ui.label(t('models_notify_ollama_check')).classes('text-sm text-muted')
                            
                            if available_models:
                                ui.notify(t('models_notify_ollama_refreshed'), type='positive')
                            else:
                                ui.notify(t('models_notify_ollama_unavailable'), type='warning')
                                
                        except Exception as e:
                            chat_models_container.clear()
                            with chat_models_container:
                                ui.label(t('models_label_error', msg=str(e))).classes('text-sm text-red-500')
                            ui.notify(t('models_notify_refresh_err', msg=str(e)), type='warning')
                    
                    async def test_chat_ollama_connection():
                        try:
                            ui.notify(t('models_notify_test_progress', url=chat_ollama_url.value), type='info')
                            # TODO: vraie logique de test
                            ui.notify(t('models_notify_test_ollama_ok'), type='positive')
                        except Exception as e:
                            ui.notify(t('models_notify_connection_err', msg=str(e)), type='warning')
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models_emoji'), on_click=refresh_chat_ollama_models).classes('action-button')
                        ui.button(t('models_btn_test_connection'), on_click=test_chat_ollama_connection).classes('action-button')
                    
                    # Paramètres avancés
                    ui.separator().classes('mb-2')
                    ui.label(t('models_label_advanced')).classes('text-sm font-semibold mb-2')
                    chat_ollama_timeout = ui.number(
                        label=t('models_label_timeout'), 
                        value=sm.settings.get('other_backends', {}).get('ollama', {}).get('timeout', 180),
                        min=5, max=600
                    ).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_timeout'))
                    chat_ollama_low_vram = ui.checkbox(
                        t('models_label_low_vram'),
                        value=sm.settings.get('other_backends', {}).get('ollama', {}).get('low_vram', False)
                    ).classes('mb-2').tooltip(t('models_tooltip_low_vram'))
                with ui.column() as chat_gguf_zone:
                    ui.label(t('models_section_gguf_chat')).classes('text-md font-semibold mb-2')
                    
                    # Récupération config existante
                    gguf_config = sm.settings.get('other_backends', {}).get('gguf', {})
                    
                    with ui.row().classes('items-center gap-2 mb-2'):
                        chat_gguf_model_path = ui.input(
                            label=t('models_label_gguf_path'), 
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
                                        
                                        ui.notify(t('models_notify_gguf_selected', name=os.path.basename(file_path), size=file_size), type='positive')
                                    else:
                                        ui.notify(t('models_notify_no_file'), type='info')
                                
                                except ImportError:
                                    ui.notify(t('models_notify_no_tk'), type='warning')
                                
                            except Exception as e:
                                ui.notify(t('models_notify_browse_err', msg=str(e)), type='warning')
                        
                        ui.button(t('models_btn_browse'), on_click=browse_gguf_file).classes('action-button')
                    
                    # Sélecteur de fichiers trouvés par scan
                    chat_gguf_model_files = ui.select(
                        label=t('models_label_gguf_files_scan'),
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
                            ui.notify(t('models_notify_explorer', path=folder_path), type='info')
                            
                        except Exception as e:
                            ui.notify(t('models_notify_explorer_err', msg=str(e)), type='warning')
                    
                    def _on_chat_gguf_file_select():
                        if chat_gguf_model_files.value:
                            chat_gguf_model_path.value = chat_gguf_model_files.value
                    
                    chat_gguf_model_files.on('change', lambda: _on_chat_gguf_file_select())
                    
                    async def test_chat_gguf_connection():
                        try:
                            model_path = chat_gguf_model_path.value
                            if not model_path:
                                ui.notify(t('models_notify_no_model'), type='warning')
                                return
                            
                            ui.notify(t('models_notify_test_gguf', path=model_path), type='info')
                            # TODO: vraie logique de test
                            ui.notify(t('models_notify_test_gguf_ok'), type='positive')
                        except Exception as e:
                            ui.notify(t('models_notify_test_gguf_err', msg=str(e)), type='warning')
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_scan'), on_click=browse_chat_gguf_models).classes('action-button')
                        ui.button(t('models_btn_open_folder'), on_click=open_chat_gguf_explorer).classes('action-button')
                        ui.button(t('models_btn_test_model'), on_click=test_chat_gguf_connection).classes('action-button')
                    
                    # Paramètres GPU
                    ui.separator().classes('mb-2')
                    ui.label(t('models_label_gpu')).classes('text-sm font-semibold mb-2')
                    
                    chat_gguf_gpu_layers = ui.number(
                        label=t('models_label_gpu_layers'), 
                        value=gguf_config.get('gpu_layers', -1),
                        min=-1, max=100
                    ).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_gpu_layers'))
                    
                    chat_gguf_context_size = ui.number(
                        label=t('models_label_ctx_size'), 
                        value=gguf_config.get('context_size', 4096),
                        min=512, max=32768
                    ).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_ctx_size'))
                with ui.column() as chat_kobold_zone:
                    chat_kobold_url = ui.input(label=t('models_label_url_kobold'), value=chat.get('kobold_url', 'http://localhost:5001')).classes('form-input mb-2 narrow-field')
                    ui.label(t('models_label_kobold_local')).classes('text-sm mb-2')
                    ui.button(t('models_btn_test'), on_click=_test_connection_ui('chat', chat_backend, None, None, service_url_input=lambda: chat_kobold_url)).classes('action-button mb-2')

                # Résoudre valeurs affichées : si -1, afficher la valeur réelle détectée
                _chat_mt_raw = chat.get('max_tokens', 512)
                _chat_mt_display = _chat_mt_raw
                _chat_mt_label = t('models_label_max_tokens')
                
                _chat_ctx_raw = chat.get('context_length', 4096)
                _chat_ctx_display = _chat_ctx_raw
                _chat_ctx_label = t('models_label_context_length')
                
                chat_max_tokens = ui.number(label=_chat_mt_label, value=_chat_mt_display).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_max_tokens'))
                chat_ctx = ui.number(label=_chat_ctx_label, value=_chat_ctx_display).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_context_length'))
                chat_temp = ui.number(label=t('models_label_temperature'), value=chat.get('temperature', 0.7), step=0.05, min=0, max=2).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_temperature_chat'))

                # Bouton valeurs optimales (adaptatif selon backend)
                chat_optimal_label = ui.label('').classes('text-xs text-muted mb-1')
                def _apply_chat_optimal():
                    backend = chat_backend.value
                    section = {
                        'model': chat_ollama_model.value if backend == 'Ollama' else None,
                        'url': chat_ollama_url.value if backend == 'Ollama' else 'http://localhost:11434',
                        'model_path': chat_gguf_model_path.value if backend == 'GGUF' else '',
                    }
                    fields = {
                        'max_tokens': chat_max_tokens,
                        'ctx': chat_ctx,
                        'label': chat_optimal_label,
                        'gguf_ctx': chat_gguf_context_size if backend == 'GGUF' else None,
                        'gguf_gpu': chat_gguf_gpu_layers if backend == 'GGUF' else None,
                    }
                    _apply_optimal_values(backend, section, fields)
                ui.button(t('models_btn_optimal'), icon='auto_fix_high', on_click=_apply_chat_optimal).classes('action-button mb-2').tooltip(t('models_tooltip_optimal'))

                with ui.column().classes('gap-1 mb-2') as chat_thinking_row:
                    with ui.row().classes('items-center gap-2'):
                        chat_thinking = ui.checkbox(t('models_label_thinking'), value=chat.get('openrouter_thinking', False))
                        ui.label(t('models_label_thinking_models')).classes('text-xs text-muted')
                    ui.label(
                        t('models_label_thinking_warning')
                    ).classes('text-xs text-warning').style('color: #e6a23c; line-height: 1.3; padding-left: 4px;')

                def _refresh_chat_interface():
                    """Force la mise à jour de l'interface Chat selon le backend sélectionné"""
                    backend = chat_backend.value
                    ui.notify(t('models_notify_iface_refresh', backend=backend), type='info')
                    
                    # Appliquer la visibilité selon le backend
                    _bind_chat_visibility()
                    
                    ui.notify(t('models_notify_iface_active', backend=backend), type='positive')

                def _bind_chat_visibility(reload_models=False):
                    chat_api_zone.visible = (chat_backend.value == 'API')
                    chat_ollama_zone.visible = (chat_backend.value == 'Ollama')
                    chat_gguf_zone.visible = (chat_backend.value == 'GGUF')
                    chat_kobold_zone.visible = (chat_backend.value == 'KoboldCpp')
                    # context_length ignoré en GGUF (remplacé par Context Size dans la zone GGUF ci-dessus)
                    chat_ctx.visible = (chat_backend.value != 'GGUF')
                    # Thinking disponible pour OpenRouter, Google, OpenAI, Anthropic et Mistral (magistral)
                    chat_thinking_row.visible = (chat_backend.value == 'API' and chat_provider.value in ('OpenRouter', 'Google', 'OpenAI', 'Anthropic', 'Mistral'))
                    # Recharger les modèles si demandé (changement de backend)
                    if reload_models:
                        ui.timer(0.05, lambda: _init_models_ui('chat', chat_backend, chat_provider, chat_model, chat_api_key, chat_api_zone, chat_ollama_zone, chat_ollama_model, chat_gguf_zone, chat_gguf_model_files, chat_kobold_zone, ollama_url_input=chat_ollama_url, kobold_url_input=chat_kobold_url), once=True)

                chat_backend.on('change', lambda: _bind_chat_visibility(reload_models=True))
                chat_provider.on('change', lambda e: _bind_chat_visibility())
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
                    arch_backend = ui.select(arch_backend_opts, value=detect_backend(arch), label=t('models_label_backend')).classes('form-select narrow-field').style('min-width: 200px; flex: 1;')
                    ui.button('🔄', on_click=lambda: _refresh_arch_interface()).classes('action-button').style('min-width: 40px; height: 40px; flex-shrink: 0;').tooltip(t('models_tooltip_refresh_iface'))

                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label(t('models_label_availability')).classes('text-sm text-muted')
                    arch_dot_inline = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut

                with ui.column() as arch_api_zone:
                    arch_provider_opts = ['Aucun'] + REMOTE_PROVIDERS[:-1] + ['AIHorde']
                    
                    def on_arch_provider_change(e):
                        """Charge la clé API depuis le vault au changement de provider et recharge les modèles"""
                        try:
                            from api_keys_vault import get_api_key, has_saved_key
                            provider = e.value
                            if provider and provider != 'Aucun' and has_saved_key(provider):
                                saved_key = get_api_key(provider)
                                if saved_key:
                                    arch_api_key.value = saved_key
                                    ui.notify(t('models_notify_vault_loaded', provider=provider), type='info')
                            # Recharger les modèles pour le nouveau provider
                            if provider and provider != 'Aucun':
                                refresh_cb = _refresh_models_ui('arch', arch_backend, arch_provider, arch_model, arch_api_key)
                                ui.timer(0.1, lambda: asyncio.create_task(refresh_cb()), once=True)
                        except Exception as ex:
                            print(f"[API-VAULT] Erreur chargement clé arch: {ex}")
                    
                    arch_provider = ui.select(
                        arch_provider_opts,
                        value=_safe(arch.get('provider', 'Aucun'), arch_provider_opts),
                        label=t('models_label_provider'),
                        on_change=on_arch_provider_change
                    ).classes('form-select mb-2 narrow-field')
                    arch_model = ui.select([], value=None, label=t('models_label_api_model')).classes('form-select mb-2 narrow-field')
                    arch_api_key = ui.input(label=t('models_label_api_key'), password=True, value=arch.get('api_key', '')).classes('form-input mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models'), on_click=_refresh_models_ui('arch', arch_backend, arch_provider, arch_model, arch_api_key)).classes('action-button')
                        ui.button(t('models_btn_test'), on_click=_test_connection_ui('arch', arch_backend, arch_provider, arch_api_key)).classes('action-button')
                with ui.column() as arch_ollama_zone:
                    arch_ollama_url = ui.input(label=t('models_label_url_ollama'), value=arch.get('ollama_url', 'http://localhost:11434')).classes('form-input mb-2 narrow-field')
                    arch_ollama_model = ui.select([], value=None, label=t('models_label_ollama_model')).classes('form-select mb-2 narrow-field')
                    arch_ollama_timeout = ui.number(
                        label=t('models_label_timeout'),
                        value=sm.settings.get('other_backends', {}).get('ollama', {}).get('timeout', 180),
                        min=5, max=600
                    ).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_timeout_short'))
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models'), on_click=_refresh_models_ui('arch', arch_backend, None, arch_ollama_model, None, service_url_input=lambda: arch_ollama_url)).classes('action-button')
                        ui.button(t('models_btn_test'), on_click=_test_connection_ui('arch', arch_backend, None, None, service_url_input=lambda: arch_ollama_url)).classes('action-button')
                with ui.column() as arch_gguf_zone:
                    ui.label(t('models_section_gguf_arch')).classes('text-md font-semibold mb-2')
                    
                    other_backends = sm.settings.get('other_backends', {})
                    gguf_config = other_backends.get('gguf', {})
                    
                    arch_gguf_model_path = ui.input(
                        label=t('models_label_gguf_path'), 
                        value=gguf_config.get('model_path', ''),
                        placeholder='C:/models/model.gguf'
                    ).classes('form-input mb-2 w-full')
                    
                    arch_gguf_model_files = ui.select(
                        [],
                        value=None,  # On assignera la valeur après avoir rempli les options
                        label=t('models_label_gguf_files')
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
                                    title=t('models_gguf_dialog_title_arch'),
                                    filetypes=[
                                        (t('models_gguf_filetype_models'), "*.gguf"),
                                        (t('models_gguf_filetype_all'), "*.*")
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
                                    
                                    ui.notify(t('models_notify_gguf_selected_arch', name=os.path.basename(file_path), size=file_size), type='positive')
                                else:
                                    ui.notify(t('models_notify_no_file'), type='info')
                            
                            except ImportError:
                                ui.notify('🔍 tkinter non disponible, scan automatique...', type='info')
                                await scan_arch_common_directories()
                                
                        except Exception as e:
                            ui.notify(t('models_notify_browse_err', msg=str(e)), type='warning')
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
                                
                                ui.notify(t('models_notify_scan_found_arch', n=len(found_models)), type='positive')
                            else:
                                ui.notify(t('models_notify_scan_empty'), type='warning')
                                
                        except Exception as e:
                            ui.notify(t('models_notify_scan_err', msg=str(e)), type='warning')
                    
                    def _on_arch_file_select():
                        if arch_gguf_model_files.value:
                            arch_gguf_model_path.value = arch_gguf_model_files.value
                    
                    arch_gguf_model_files.on('change', lambda: _on_arch_file_select())
                    
                    with ui.row().classes('gap-2 mb-2'):
                        ui.button(t('models_btn_scan'), on_click=browse_arch_gguf_file).classes('action-button')
                        ui.button(t('models_btn_open_folder'), on_click=lambda: open_arch_file_explorer()).classes('action-button')
                    
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
                            ui.notify(t('models_notify_explorer', path=folder_path), type='info')
                            
                        except Exception as e:
                            ui.notify(t('models_notify_explorer_err', msg=str(e)), type='warning')
                    
                    ui.separator().classes('mb-2')
                    ui.label(t('models_label_gpu_arch')).classes('text-sm font-semibold mb-2')
                    
                    arch_gguf_gpu_layers = ui.number(
                        label=t('models_label_gpu_layers'), 
                        value=gguf_config.get('gpu_layers', -1),
                        min=-1, max=100
                    ).classes('form-input mb-2').tooltip(t('models_tooltip_gpu_layers'))
                    
                    arch_gguf_context_size = ui.number(
                        label=t('models_label_ctx_size'), 
                        value=gguf_config.get('context_size', 4096),
                        min=512, max=32768
                    ).classes('form-input mb-2').tooltip(t('models_tooltip_ctx_size_short'))
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models'), on_click=_refresh_models_ui('arch', arch_backend, None, arch_gguf_model_files, None)).classes('action-button')
                        ui.button(t('models_btn_test'), on_click=_test_connection_ui('arch', arch_backend, None, None)).classes('action-button')
                with ui.column() as arch_kobold_zone:
                    arch_kobold_url = ui.input(label=t('models_label_url_kobold'), value=arch.get('kobold_url', 'http://localhost:5001')).classes('form-input mb-2 narrow-field')
                    ui.label(t('models_label_kobold_local')).classes('text-sm mb-2')
                    ui.button(t('models_btn_test'), on_click=_test_connection_ui('arch', arch_backend, None, None, service_url_input=lambda: arch_kobold_url)).classes('action-button mb-2')

                # Résoudre valeurs affichées Archiviste
                _arch_mt_raw = arch.get('max_tokens', 512)
                _arch_mt_display = _arch_mt_raw
                _arch_mt_label = t('models_label_max_tokens')
                
                _arch_ctx_raw = arch.get('context_length', 4096)
                _arch_ctx_display = _arch_ctx_raw
                _arch_ctx_label = t('models_label_context_length')
                
                arch_max_tokens = ui.number(label=_arch_mt_label, value=_arch_mt_display).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_max_tokens'))
                arch_ctx = ui.number(label=_arch_ctx_label, value=_arch_ctx_display).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_context_length'))
                arch_temp = ui.number(label=t('models_label_temperature'), value=arch.get('temperature', 0.7), step=0.05, min=0, max=2).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_temperature_arch'))

                # Bouton valeurs optimales (adaptatif selon backend)
                arch_optimal_label = ui.label('').classes('text-xs text-muted mb-1')
                def _apply_arch_optimal():
                    backend = arch_backend.value
                    section = {
                        'model': arch_ollama_model.value if backend == 'Ollama' else None,
                        'url': arch_ollama_url.value if backend == 'Ollama' else 'http://localhost:11434',
                        'model_path': arch_gguf_model_path.value if backend == 'GGUF' else '',
                    }
                    fields = {
                        'max_tokens': arch_max_tokens,
                        'ctx': arch_ctx,
                        'label': arch_optimal_label,
                        'gguf_ctx': arch_gguf_context_size if backend == 'GGUF' else None,
                        'gguf_gpu': arch_gguf_gpu_layers if backend == 'GGUF' else None,
                    }
                    _apply_optimal_values(backend, section, fields)
                ui.button(t('models_btn_optimal'), icon='auto_fix_high', on_click=_apply_arch_optimal).classes('action-button mb-2').tooltip(t('models_tooltip_optimal_short'))

                def _refresh_arch_interface():
                    """Force la mise à jour de l'interface Archiviste selon le backend sélectionné"""
                    backend = arch_backend.value
                    ui.notify(t('models_notify_iface_refresh', backend=backend), type='info')
                    
                    # Appliquer la visibilité selon le backend
                    _bind_arch_visibility()
                    
                    ui.notify(t('models_notify_iface_active', backend=backend), type='positive')

                def _bind_arch_visibility(reload_models=False):
                    arch_api_zone.visible = (arch_backend.value == 'API')
                    arch_ollama_zone.visible = (arch_backend.value == 'Ollama')
                    arch_gguf_zone.visible = (arch_backend.value == 'GGUF')
                    arch_kobold_zone.visible = (arch_backend.value == 'KoboldCpp')
                    # context_length ignoré en GGUF (remplacé par Context Size dans la zone GGUF ci-dessus)
                    arch_ctx.visible = (arch_backend.value != 'GGUF')
                    # Recharger les modèles si demandé (changement de backend)
                    if reload_models:
                        ui.timer(0.05, lambda: _init_models_ui('arch', arch_backend, arch_provider, arch_model, arch_api_key, arch_api_zone, arch_ollama_zone, arch_ollama_model, arch_gguf_zone, arch_gguf_model_files, arch_kobold_zone, ollama_url_input=arch_ollama_url, kobold_url_input=arch_kobold_url), once=True)

                arch_backend.on('change', lambda: _bind_arch_visibility(reload_models=True))
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
                    emb_backend = ui.select(emb_backend_opts, value=detect_embed_backend(emb), label=t('models_label_backend')).classes('form-select narrow-field').style('min-width: 200px; flex: 1;')
                    ui.button('🔄', on_click=lambda: _refresh_embed_interface()).classes('action-button').style('min-width: 40px; height: 40px; flex-shrink: 0;').tooltip(t('models_tooltip_refresh_iface'))

                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.label(t('models_label_availability')).classes('text-sm text-muted')
                    emb_dot_inline = ui.element('div').style('width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: #dc2626;').classes('status-dot')  # Remplacement de _status_dot(initial='#dc2626')  # Rouge par défaut

                with ui.column() as emb_api_zone:
                    emb_provider_opts = ['Aucun'] + EMBED_SUPPORTED_PROVIDERS
                    
                    def on_emb_provider_change(e):
                        """Charge la clé API depuis le vault au changement de provider et recharge les modèles"""
                        try:
                            from api_keys_vault import get_api_key, has_saved_key
                            provider = e.value
                            if provider and provider != 'Aucun' and has_saved_key(provider):
                                saved_key = get_api_key(provider)
                                if saved_key:
                                    emb_api_key.value = saved_key
                                    ui.notify(t('models_notify_vault_loaded', provider=provider), type='info')
                            # Recharger les modèles pour le nouveau provider
                            if provider and provider != 'Aucun':
                                refresh_cb = _refresh_models_ui('embed', emb_backend, emb_provider, emb_model, emb_api_key)
                                ui.timer(0.1, lambda: asyncio.create_task(refresh_cb()), once=True)
                        except Exception as ex:
                            print(f"[API-VAULT] Erreur chargement clé emb: {ex}")
                    
                    emb_provider = ui.select(
                        emb_provider_opts,
                        value=_safe(emb.get('provider', 'Aucun'), emb_provider_opts),
                        label=t('models_label_provider'),
                        on_change=on_emb_provider_change
                    ).classes('form-select mb-2 narrow-field')
                    emb_model = ui.select([], value=None, label=t('models_label_embed_model')).classes('form-select mb-2 narrow-field')
                    emb_api_key = ui.input(label=t('models_label_api_key'), password=True, value=emb.get('api_key', '')).classes('form-input mb-2 narrow-field')
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models'), on_click=_refresh_models_ui('embed', emb_backend, emb_provider, emb_model, emb_api_key)).classes('action-button')
                        ui.button(t('models_btn_test'), on_click=_test_connection_ui('embed', emb_backend, emb_provider, emb_api_key)).classes('action-button')
                with ui.column() as emb_ollama_zone:
                    emb_ollama_url = ui.input(label=t('models_label_url_ollama'), value=emb.get('ollama_url', 'http://localhost:11434')).classes('form-input mb-2 narrow-field')
                    emb_ollama_model = ui.select([], value=None, label=t('models_label_ollama_model')).classes('form-select mb-2 narrow-field')
                    emb_ollama_timeout = ui.number(
                        label=t('models_label_timeout'),
                        value=sm.settings.get('other_backends', {}).get('ollama', {}).get('timeout', 180),
                        min=5, max=600
                    ).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_timeout_short'))
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models'), on_click=_refresh_models_ui('embed', emb_backend, None, emb_ollama_model, None, service_url_input=lambda: emb_ollama_url)).classes('action-button')
                        ui.button(t('models_btn_test'), on_click=_test_connection_ui('embed', emb_backend, None, None, service_url_input=lambda: emb_ollama_url)).classes('action-button')
                with ui.column() as emb_gguf_zone:
                    ui.label(t('models_section_gguf_embed')).classes('text-md font-semibold mb-2')
                    
                    other_backends = sm.settings.get('other_backends', {})
                    gguf_config = other_backends.get('gguf', {})
                    
                    emb_gguf_model_path = ui.input(
                        label=t('models_label_gguf_path'), 
                        value=gguf_config.get('model_path', ''),
                        placeholder='C:/models/model.gguf'
                    ).classes('form-input mb-2 w-full')
                    
                    emb_gguf_model_files = ui.select(
                        [],
                        value=None,  # On assignera la valeur après avoir rempli les options
                        label=t('models_label_gguf_files')
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
                                    title=t('models_gguf_dialog_title_embed'),
                                    filetypes=[
                                        (t('models_gguf_filetype_models'), "*.gguf"),
                                        (t('models_gguf_filetype_all'), "*.*")
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
                                    
                                    ui.notify(t('models_notify_gguf_selected_embed', name=os.path.basename(file_path), size=file_size), type='positive')
                                else:
                                    ui.notify(t('models_notify_no_file'), type='info')
                            
                            except ImportError:
                                ui.notify('🔍 tkinter non disponible, scan automatique...', type='info')
                                await scan_emb_common_directories()
                                
                        except Exception as e:
                            ui.notify(t('models_notify_browse_err', msg=str(e)), type='warning')
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
                                
                                ui.notify(t('models_notify_scan_found_embed', n=len(found_models)), type='positive')
                            else:
                                ui.notify(t('models_notify_scan_empty'), type='warning')
                                
                        except Exception as e:
                            ui.notify(t('models_notify_scan_err', msg=str(e)), type='warning')
                    
                    def _on_emb_file_select():
                        if emb_gguf_model_files.value:
                            emb_gguf_model_path.value = emb_gguf_model_files.value
                    
                    emb_gguf_model_files.on('change', lambda: _on_emb_file_select())
                    
                    with ui.row().classes('gap-2 mb-2'):
                        ui.button(t('models_btn_scan'), on_click=browse_emb_gguf_file).classes('action-button')
                        ui.button(t('models_btn_open_folder'), on_click=lambda: open_emb_file_explorer()).classes('action-button')
                    
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
                            ui.notify(t('models_notify_explorer', path=folder_path), type='info')
                            
                        except Exception as e:
                            ui.notify(t('models_notify_explorer_err', msg=str(e)), type='warning')
                    
                    ui.separator().classes('mb-2')
                    ui.label(t('models_label_gpu_embed')).classes('text-sm font-semibold mb-2')
                    
                    emb_gguf_gpu_layers = ui.number(
                        label=t('models_label_gpu_layers'), 
                        value=gguf_config.get('gpu_layers', -1),
                        min=-1, max=100
                    ).classes('form-input mb-2').tooltip(t('models_tooltip_gpu_layers'))
                    
                    emb_gguf_context_size = ui.number(
                        label=t('models_label_ctx_size'), 
                        value=gguf_config.get('context_size', 4096),
                        min=512, max=32768
                    ).classes('form-input mb-2').tooltip(t('models_tooltip_ctx_size_short'))
                    
                    with ui.row().classes('items-center gap-2 mb-2 narrow-actions'):
                        ui.button(t('models_btn_refresh_models'), on_click=_refresh_models_ui('embed', emb_backend, None, emb_gguf_model_files, None)).classes('action-button')
                        ui.button(t('models_btn_test'), on_click=_test_connection_ui('embed', emb_backend, None, None)).classes('action-button')

                # Paramètres avancés Embedding
                ui.separator().classes('mb-2')
                ui.label(t('models_label_advanced_embed')).classes('text-sm font-semibold mb-2')
                
                # Résoudre valeurs affichées Embedding
                _emb_mt_raw = emb.get('max_tokens', 512)
                _emb_mt_display = _emb_mt_raw
                _emb_mt_label = t('models_label_max_tokens')
                
                _emb_ctx_raw = emb.get('context_length', 4096)
                _emb_ctx_display = _emb_ctx_raw
                _emb_ctx_label = t('models_label_context_length')
                
                emb_max_tokens = ui.number(label=_emb_mt_label, value=_emb_mt_display).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_max_tokens_embed'))
                emb_ctx = ui.number(label=_emb_ctx_label, value=_emb_ctx_display).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_context_length'))
                emb_temp = ui.number(label=t('models_label_temperature'), value=emb.get('temperature', 0.1), step=0.05, min=0, max=2).classes('form-input mb-2 narrow-field').tooltip(t('models_tooltip_temperature_embed'))

                def _refresh_embed_interface():
                    """Force la mise à jour de l'interface Embedding selon le backend sélectionné"""
                    backend = emb_backend.value
                    ui.notify(t('models_notify_iface_refresh', backend=backend), type='info')
                    
                    # Appliquer la visibilité selon le backend
                    _bind_embed_visibility()
                    
                    ui.notify(t('models_notify_iface_active', backend=backend), type='positive')

                def _bind_embed_visibility(reload_models=False):
                    emb_api_zone.visible = (emb_backend.value == 'API')
                    emb_ollama_zone.visible = (emb_backend.value == 'Ollama')
                    emb_gguf_zone.visible = (emb_backend.value == 'GGUF')
                    # context_length ignoré en GGUF (remplacé par Context Size dans la zone GGUF ci-dessus)
                    emb_ctx.visible = (emb_backend.value != 'GGUF')
                    # Recharger les modèles si demandé (changement de backend)
                    if reload_models:
                        ui.timer(0.05, lambda: _init_models_ui('embed', emb_backend, emb_provider, emb_model, emb_api_key, emb_api_zone, emb_ollama_zone, emb_ollama_model, emb_gguf_zone, emb_gguf_model_files, None, ollama_url_input=emb_ollama_url), once=True)

                emb_backend.on('change', lambda: _bind_embed_visibility(reload_models=True))
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
            # Sauvegarder les clés API dans le vault pour réutilisation future
            try:
                from api_keys_vault import save_api_key
                
                # Sauvegarder clé Chat si présente
                if chat_backend.value == 'API' and chat_provider.value and chat_provider.value != 'Aucun':
                    if chat_api_key.value and chat_api_key.value.strip():
                        save_api_key(chat_provider.value, chat_api_key.value)
                
                # Sauvegarder clé Archiviste si présente
                if arch_backend.value == 'API' and arch_provider.value and arch_provider.value != 'Aucun':
                    if arch_api_key.value and arch_api_key.value.strip():
                        save_api_key(arch_provider.value, arch_api_key.value)
                
                # Sauvegarder clé Embedding si présente
                if emb_backend.value == 'API' and emb_provider.value and emb_provider.value != 'Aucun':
                    if emb_api_key.value and emb_api_key.value.strip():
                        save_api_key(emb_provider.value, emb_api_key.value)
                        
            except Exception as e:
                print(f"[API-VAULT] ⚠️ Erreur sauvegarde vault: {e}")
            
            # CORRECTION: Préserver les settings existants pour éviter d'effacer les autres contrôleurs
            # Copier les settings actuels comme base
            chat_settings = sm.settings.get('chat_api', {}).copy()
            arch_settings = sm.settings.get('reasoning_api', {}).copy()
            emb_settings = sm.settings.get('embedding_api', {}).copy()
            
            # Mise à jour CHAT (seulement les champs modifiés)
            chat_settings.update({
                'backend_type': chat_backend.value,
                'max_tokens': int(chat_max_tokens.value or 512),
                'context_length': int(chat_ctx.value or 4096),
                'temperature': float(chat_temp.value if chat_temp.value is not None else 0.7),
            })
            if chat_backend.value == 'API':
                chat_settings['provider'] = chat_provider.value or 'Aucun'
                # IMPORTANT: Préserver le modèle existant si le select n'est pas chargé
                if chat_model.value:
                    chat_settings['api_model'] = chat_model.value
                # Sinon garder la valeur existante dans chat_settings (déjà copiée)
                chat_settings['api_key'] = chat_api_key.value or ''
                chat_settings['openrouter_thinking'] = bool(chat_thinking.value)
            elif chat_backend.value == 'Ollama':
                # IMPORTANT: Préserver le modèle existant si le select n'est pas chargé
                if chat_ollama_model.value:
                    chat_settings['ollama_model'] = chat_ollama_model.value
                chat_settings['ollama_url'] = chat_ollama_url.value or 'http://localhost:11434'
                # Sauvegarder timeout dans other_backends.ollama (commun aux 3 contrôleurs)
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'ollama' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['ollama'] = {}
                sm.settings['other_backends']['ollama']['timeout'] = int(chat_ollama_timeout.value if chat_ollama_timeout.value is not None else 180)
                sm.settings['other_backends']['ollama']['low_vram'] = bool(chat_ollama_low_vram.value)
            elif chat_backend.value == 'GGUF':
                # IMPORTANT: Préserver le modèle existant si le select n'est pas chargé
                if chat_gguf_model_path.value:
                    chat_settings['gguf_model'] = chat_gguf_model_path.value
                # Synchroniser les paramètres GGUF avec other_backends
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'gguf' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['gguf'] = {}
                
                # Sauvegarder dans other_backends pour compatibilité
                sm.settings['other_backends']['gguf'].update({
                    'model_path': chat_gguf_model_path.value or '',
                    'gpu_layers': int(chat_gguf_gpu_layers.value if chat_gguf_gpu_layers.value is not None else -1),
                    'context_size': int(chat_gguf_context_size.value or 4096),
                    'enabled': True
                })
            elif chat_backend.value == 'KoboldCpp':
                chat_settings['kobold_url'] = chat_kobold_url.value or 'http://localhost:5001'
            # Purger les clés internes _display_* avant sauvegarde
            for k in list(chat_settings.keys()):
                if k.startswith('_display_'):
                    del chat_settings[k]
            sm.settings['chat_api'] = chat_settings

            # Mise à jour ARCHIVISTE (seulement les champs modifiés)
            arch_settings.update({
                'backend_type': arch_backend.value,
                'max_tokens': int(arch_max_tokens.value or 512),
                'context_length': int(arch_ctx.value or 4096),
                'temperature': float(arch_temp.value if arch_temp.value is not None else 0.7),
            })
            if arch_backend.value == 'API':
                arch_settings['provider'] = arch_provider.value or 'Aucun'
                # IMPORTANT: Préserver le modèle existant si le select n'est pas chargé
                if arch_model.value:
                    arch_settings['api_model'] = arch_model.value
                arch_settings['api_key'] = arch_api_key.value or ''
            elif arch_backend.value == 'Ollama':
                # IMPORTANT: Préserver le modèle existant si le select n'est pas chargé
                if arch_ollama_model.value:
                    arch_settings['ollama_model'] = arch_ollama_model.value
                arch_settings['ollama_url'] = arch_ollama_url.value or 'http://localhost:11434'
                # Sauvegarder timeout dans other_backends.ollama
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'ollama' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['ollama'] = {}
                sm.settings['other_backends']['ollama']['timeout'] = int(arch_ollama_timeout.value if arch_ollama_timeout.value is not None else 180)
            elif arch_backend.value == 'GGUF':
                # Préférer le champ texte (entrée directe) sur le sélecteur de fichiers
                _arch_gguf_path = arch_gguf_model_path.value or arch_gguf_model_files.value
                if _arch_gguf_path:
                    arch_settings['gguf_model'] = _arch_gguf_path
                # Synchroniser paramètres GGUF archiviste dans other_backends
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'gguf' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['gguf'] = {}
                sm.settings['other_backends']['gguf'].update({
                    'gpu_layers': int(arch_gguf_gpu_layers.value if arch_gguf_gpu_layers.value is not None else -1),
                    'context_size': int(arch_gguf_context_size.value or 4096),
                })
            elif arch_backend.value == 'KoboldCpp':
                arch_settings['kobold_url'] = arch_kobold_url.value or 'http://localhost:5001'
            for k in list(arch_settings.keys()):
                if k.startswith('_display_'):
                    del arch_settings[k]
            sm.settings['reasoning_api'] = arch_settings

            # Mise à jour EMBEDDING (seulement les champs modifiés)
            emb_settings.update({
                'backend_type': emb_backend.value,
                'max_tokens': int(emb_max_tokens.value or 512),
                'context_length': int(emb_ctx.value or 4096),
                'temperature': float(emb_temp.value if emb_temp.value is not None else 0.1),
            })
            if emb_backend.value == 'API':
                emb_settings['provider'] = emb_provider.value or 'Aucun'
                # IMPORTANT: Préserver le modèle existant si le select n'est pas chargé
                if emb_model.value:
                    emb_settings['api_model'] = emb_model.value
                emb_settings['api_key'] = emb_api_key.value or ''
            elif emb_backend.value == 'Ollama':
                # IMPORTANT: Préserver le modèle existant si le select n'est pas chargé
                if emb_ollama_model.value:
                    emb_settings['ollama_model'] = emb_ollama_model.value
                emb_settings['ollama_url'] = emb_ollama_url.value or 'http://localhost:11434'
                # Sauvegarder timeout dans other_backends.ollama
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'ollama' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['ollama'] = {}
                sm.settings['other_backends']['ollama']['timeout'] = int(emb_ollama_timeout.value if emb_ollama_timeout.value is not None else 180)
            elif emb_backend.value == 'GGUF':
                # Préférer le champ texte (entrée directe) sur le sélecteur de fichiers
                _emb_gguf_path = emb_gguf_model_path.value or emb_gguf_model_files.value
                if _emb_gguf_path:
                    emb_settings['gguf_model'] = _emb_gguf_path
                # Synchroniser paramètres GGUF embedding dans other_backends
                if 'other_backends' not in sm.settings:
                    sm.settings['other_backends'] = {}
                if 'gguf' not in sm.settings['other_backends']:
                    sm.settings['other_backends']['gguf'] = {}
                sm.settings['other_backends']['gguf'].update({
                    'gpu_layers': int(emb_gguf_gpu_layers.value if emb_gguf_gpu_layers.value is not None else -1),
                    'context_size': int(emb_gguf_context_size.value or 4096),
                })
            
            for k in list(emb_settings.keys()):
                if k.startswith('_display_'):
                    del emb_settings[k]
            sm.settings['embedding_api'] = emb_settings

            # NE sauvegarder gpu_layers depuis gguf_gpu_layers QUE si backend emb est GGUF
            # (gestion désormais intégrée dans le bloc elif ci-dessus)
            
            msg = sm.save_settings()
            ui.notify(msg or t('models_notify_save_default'), type='positive')
            dialog.close()

        with ui.row().classes('justify-end gap-2 mt-2'):
            ui.button(t('models_btn_cancel'), on_click=dialog.close).classes('action-button')
            ui.button(t('models_btn_save'), on_click=save_and_close).classes('send-button')
    return dialog


# Fonction _perception_modal supprimée - remplacée par la section dans les paramètres généraux
# et l'utilisation directe de _perception_settings_modal pour le bouton header


# Modal simple supprimée - seule la modal complète est utilisée


# ============================================================================
# PERCEPTION SETTINGS - SUPPRIMÉE
# Tous les paramètres Perception sont maintenant gérés sur la page dédiée /perception
# Cette modal a été supprimée pour éviter les conflits de configuration
# ============================================================================


def _telegram_connector_settings_modal():
    """Modal de configuration pour l'extension Telegram Connector"""
    
    # Créer le dialog avec glassmorphism
    dialog = ui.dialog().style('''
        z-index: 10000 !important;
    ''')
    
    with dialog:
        with ui.card().classes('w-full max-w-2xl').style('''
            background: rgba(0, 136, 204, 0.08) !important;
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(0, 136, 204, 0.25) !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px rgba(0, 136, 204, 0.15) !important;
            color: var(--text-primary) !important;
            max-height: 80vh !important;
            overflow-y: auto !important;
        '''):
            
            # Conteneur pour l'interface de l'extension
            settings_container = ui.column().classes('w-full')
            
            try:
                from extensions.telegram_connector.ui_components import get_telegram_ui
                telegram_ui = get_telegram_ui()
                telegram_ui.create_settings_panel(settings_container)
            except Exception as e:
                with settings_container:
                    ui.label(t('modal_load_error', msg=str(e))).classes('text-red-500')
            
            # Boutons
            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button(t('modal_close'), on_click=dialog.close).classes('action-button')
    
    return dialog


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
            ui.label(t('web_nav_modal_title')).classes('popup-title').style('''
                color: #3498db !important; 
                text-shadow: 0 0 10px rgba(52, 152, 219, 0.3) !important; 
                font-weight: 600 !important;
                font-size: 1.5rem !important;
            ''')
            ui.label(t('web_nav_modal_subtitle')).classes('text-muted mb-4')
            
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
                ui.button(t('modal_close'), on_click=dialog.close).classes('action-button').style('''
                    background: rgba(52, 152, 219, 0.12) !important;
                    border: 1px solid rgba(52, 152, 219, 0.3) !important;
                    backdrop-filter: blur(15px) !important;
                    transition: all 0.3s ease !important;
                ''')
    
    return dialog


def _dream_engine_settings_modal():
    """Modal de configuration pour l'extension Dream Engine (Métabolisme Cognitif)"""
    
    # Créer le dialog avec glassmorphism violet/bleu nuit
    dialog = ui.dialog().style('''
        z-index: 10000 !important;
    ''')
    
    with dialog:
        with ui.card().classes('w-full max-w-2xl').style('''
            background: rgba(75, 0, 130, 0.12) !important;
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(138, 43, 226, 0.3) !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px rgba(138, 43, 226, 0.2) !important;
            color: var(--text-primary) !important;
            max-height: 80vh !important;
            overflow-y: auto !important;
            padding: 24px !important;
        '''):
            
            # En-tête
            ui.label(t('dream_modal_title')).classes('popup-title').style('''
                color: #9370DB !important; 
                text-shadow: 0 0 10px rgba(147, 112, 219, 0.4) !important; 
                font-weight: 600 !important;
                font-size: 1.4rem !important;
            ''')
            ui.label(t('dream_modal_subtitle')).classes('mb-4').style('color: #b0b0b0 !important;')
            
            # Vérifier disponibilité de l'extension
            try:
                from extensions.dream_engine import is_available, get_config, set_config, DEFAULT_CONFIG
                
                if not is_available():
                    ui.markdown(t('dream_not_initialized_title'))
                    ui.markdown(t('dream_not_initialized_hint'))
                else:
                    # Récupérer la config actuelle
                    config = get_config()
                    
                    # Pas besoin de conversion - on utilise directement illustration_style
                    
                    # === SECTION: Activation ===
                    with ui.expansion(t('dream_section_activation'), icon='power_settings_new', value=True).classes('w-full mb-3').style('''
                        background: rgba(138, 43, 226, 0.08) !important;
                        border: 1px solid rgba(138, 43, 226, 0.2) !important;
                        border-radius: 12px !important;
                    '''):
                        with ui.row().classes('items-center gap-4 w-full'):
                            enabled_switch = ui.switch(t('dream_switch_auto'), value=config.get('enabled', True)).style('''
                                --q-primary: #9370DB !important;
                            ''')
                            ui.label(t('dream_switch_auto_hint')).classes('text-sm').style('color: #b0b0b0 !important;')
                    
                    # === SECTION: Timing ===
                    with ui.expansion(t('dream_section_timing'), icon='schedule').classes('w-full mb-3').style('''
                        background: rgba(138, 43, 226, 0.08) !important;
                        border: 1px solid rgba(138, 43, 226, 0.2) !important;
                        border-radius: 12px !important;
                    '''):
                        with ui.column().classes('w-full gap-3'):
                            # Timer inactivité
                            ui.label(t('dream_label_inactivity')).classes('font-semibold')
                            inactivity_slider = ui.slider(
                                min=5, max=60, step=5,
                                value=config.get('inactivity_timeout_minutes', 10)
                            ).props('label-always').style('width: 100%;')
                            ui.label(t('dream_label_inactivity_hint')).classes('text-xs').style('color: #b0b0b0 !important;')
                            
                            ui.separator().style('margin: 8px 0;')
                            
                            # Vitesse métabolisme
                            ui.label(t('dream_label_metabolism')).classes('font-semibold')
                            metabolism_slider = ui.slider(
                                min=20, max=200, step=10,
                                value=config.get('metabolism_tokens_per_minute', 50)
                            ).props('label-always').style('width: 100%;')
                            ui.label(t('dream_label_metabolism_hint')).classes('text-xs').style('color: #b0b0b0 !important;')
                    
                    # === SECTION: Comportement ===
                    with ui.expansion(t('dream_section_behavior'), icon='psychology').classes('w-full mb-3').style('''
                        background: rgba(138, 43, 226, 0.08) !important;
                        border: 1px solid rgba(138, 43, 226, 0.2) !important;
                        border-radius: 12px !important;
                    '''):
                        with ui.column().classes('w-full gap-3'):
                            # Seuil mention spontanée
                            ui.label(t('dream_label_mention_threshold')).classes('font-semibold')
                            mention_slider = ui.slider(
                                min=5, max=10, step=1,
                                value=config.get('spontaneous_mention_threshold', 8)
                            ).props('label-always').style('width: 100%;')
                            ui.label(t('dream_label_mention_threshold_hint')).classes('text-xs').style('color: #b0b0b0 !important;')
                            
                            ui.separator().style('margin: 8px 0;')
                            
                            # Illustrations
                            with ui.row().classes('items-center gap-4 w-full'):
                                illustration_switch = ui.switch(
                                    t('dream_switch_illustrations'), 
                                    value=config.get('generate_illustrations', True)
                                ).style('--q-primary: #9370DB !important;')
                                ui.label(t('dream_switch_illustrations_hint')).classes('text-sm').style('color: #b0b0b0 !important;')
                            
                            ui.label(t('dream_warning_no_illustrations')).classes('text-xs').style('color: #ff9800 !important; margin-left: 30px; margin-top: -8px;')
                            
                            # Style d'illustration (radio buttons)
                            ui.label(t('dream_label_illust_style')).classes('font-semibold mt-3')
                            
                            # Déterminer valeur initiale depuis illustration_style
                            current_style = config.get('illustration_style', 'auto')
                            
                            illustration_style_radio = ui.radio(
                                options={
                                    'single': t('dream_radio_single'),
                                    'comic_4': t('dream_radio_comic'),
                                    'auto': t('dream_radio_auto')
                                },
                                value=current_style
                            ).props('dense').style('margin-left: 10px;')
                            
                            # Désactiver si illustrations OFF
                            illustration_style_radio.bind_enabled_from(illustration_switch, 'value')
                    
                    # === SECTION: Mémoire ===
                    with ui.expansion(t('dream_section_memory'), icon='memory').classes('w-full mb-3').style('''
                        background: rgba(138, 43, 226, 0.08) !important;
                        border: 1px solid rgba(138, 43, 226, 0.2) !important;
                        border-radius: 12px !important;
                    '''):
                        with ui.column().classes('w-full gap-3'):
                            ui.label(t('dream_label_summaries')).classes('font-semibold')
                            summaries_slider = ui.slider(
                                min=5, max=20, step=1,
                                value=config.get('max_summaries', 10)
                            ).props('label-always').style('width: 100%;')
                            
                            ui.label(t('dream_label_hashtag')).classes('font-semibold')
                            hashtag_slider = ui.slider(
                                min=3, max=10, step=1,
                                value=config.get('max_hashtag_memories', 5)
                            ).props('label-always').style('width: 100%;')
                    
                    # === SECTION: Prompts personnalisés ===
                    # Importer les prompts par défaut pour les afficher
                    try:
                        from extensions.dream_engine.dream_prompts import DREAM_GENERATOR_MODE, ARCHIVISTE_PSY_VERDICT
                        default_dream_prompt = DREAM_GENERATOR_MODE
                        default_psy_prompt = ARCHIVISTE_PSY_VERDICT
                    except:
                        default_dream_prompt = "[Prompt par défaut non disponible]"
                        default_psy_prompt = "[Prompt par défaut non disponible]"
                    
                    with ui.expansion(t('dream_section_prompts'), icon='edit_note').classes('w-full mb-3').style('''
                        background: rgba(138, 43, 226, 0.08) !important;
                        border: 1px solid rgba(138, 43, 226, 0.2) !important;
                        border-radius: 12px !important;
                    '''):
                        with ui.column().classes('w-full gap-3'):
                            ui.markdown(t('dream_prompts_hint')).classes('text-xs').style('color: #b0b0b0 !important;')
                            
                            # Prompt IA (génération de rêve)
                            ui.label(t('dream_label_prompt_dream')).classes('font-semibold')
                            
                            # Valeur initiale : config custom ou défaut si vide
                            luna_initial = config.get('prompt_dream_generator', '') or default_dream_prompt
                            luna_prompt_area = ui.textarea(
                                value=luna_initial
                            ).props('outlined dark input-style="color: white; font-family: monospace; font-size: 0.85rem"').classes('w-full').style('''
                                height: 200px !important;
                                min-height: 200px !important;
                                max-height: 200px !important;
                                overflow-y: auto !important;
                                background: rgba(30, 30, 40, 0.9) !important;
                            ''')
                            with ui.row().classes('gap-2'):
                                ui.button(t('dream_btn_restore_default'), icon='refresh', on_click=lambda: luna_prompt_area.set_value(default_dream_prompt)).props('flat dense size=sm')
                            
                            ui.separator().style('margin: 12px 0;')
                            
                            # Prompt Archiviste PSY
                            ui.label(t('dream_label_prompt_psy')).classes('font-semibold')
                            
                            # Valeur initiale : config custom ou défaut si vide
                            psy_initial = config.get('prompt_archiviste_psy', '') or default_psy_prompt
                            psy_prompt_area = ui.textarea(
                                value=psy_initial
                            ).props('outlined dark input-style="color: white; font-family: monospace; font-size: 0.85rem"').classes('w-full').style('''
                                height: 200px !important;
                                min-height: 200px !important;
                                max-height: 200px !important;
                                overflow-y: auto !important;
                                background: rgba(30, 30, 40, 0.9) !important;
                            ''')
                            with ui.row().classes('gap-2'):
                                ui.button(t('dream_btn_restore_default'), icon='refresh', on_click=lambda: psy_prompt_area.set_value(default_psy_prompt)).props('flat dense size=sm')
                            
                            ui.separator().style('margin: 12px 0;')
                            
                            # Instructions illustration
                            ui.label(t('dream_label_instr_comic')).classes('font-semibold')
                            ui.label(t('dream_label_instr_comic_hint')).classes('text-xs').style('color: #b0b0b0 !important;')
                            ui.label(t('dream_warning_prompt_limit')).classes('text-xs font-bold').style('color: #ff9800 !important; margin-top: 4px;')
                            
                            default_comic_instruction = "\n\nGénère une planche BD de 4 cases."
                            comic_instruction_initial = config.get('prompt_comic_instruction', '') or default_comic_instruction
                            comic_instruction_area = ui.textarea(
                                value=comic_instruction_initial
                            ).props('outlined dark input-style="color: white; font-family: monospace; font-size: 0.85rem"').classes('w-full').style('''
                                height: 80px !important;
                                min-height: 80px !important;
                                max-height: 80px !important;
                                overflow-y: auto !important;
                                background: rgba(30, 30, 40, 0.9) !important;
                            ''')
                            with ui.row().classes('gap-2'):
                                ui.button(t('dream_btn_restore_default'), icon='refresh', on_click=lambda: comic_instruction_area.set_value(default_comic_instruction)).props('flat dense size=sm')
                            
                            ui.separator().style('margin: 8px 0;')
                            
                            # Instruction single
                            ui.label(t('dream_label_instr_single')).classes('font-semibold')
                            ui.label(t('dream_label_instr_single_hint')).classes('text-xs').style('color: #b0b0b0 !important;')
                            ui.label(t('dream_warning_prompt_limit')).classes('text-xs font-bold').style('color: #ff9800 !important; margin-top: 4px;')
                            
                            default_single_instruction = "\n\nGénère une seule image."
                            single_instruction_initial = config.get('prompt_single_instruction', '') or default_single_instruction
                            single_instruction_area = ui.textarea(
                                value=single_instruction_initial
                            ).props('outlined dark input-style="color: white; font-family: monospace; font-size: 0.85rem"').classes('w-full').style('''
                                height: 80px !important;
                                min-height: 80px !important;
                                max-height: 80px !important;
                                overflow-y: auto !important;
                                background: rgba(30, 30, 40, 0.9) !important;
                            ''')
                            with ui.row().classes('gap-2'):
                                ui.button(t('dream_btn_restore_default'), icon='refresh', on_click=lambda: single_instruction_area.set_value(default_single_instruction)).props('flat dense size=sm')
                            
                            ui.separator().style('margin: 8px 0;')
                            
                            # Instruction auto
                            ui.label(t('dream_label_instr_auto')).classes('font-semibold')
                            ui.label(t('dream_label_instr_auto_hint')).classes('text-xs').style('color: #b0b0b0 !important;')
                            ui.label(t('dream_warning_prompt_limit')).classes('text-xs font-bold').style('color: #ff9800 !important; margin-top: 4px;')
                            
                            default_auto_instruction = ""  # Vide = l'IA décide librement
                            auto_instruction_initial = config.get('prompt_auto_instruction', '') or default_auto_instruction
                            auto_instruction_area = ui.textarea(
                                value=auto_instruction_initial,
                                placeholder=t('dream_placeholder_auto')
                            ).props('outlined dark input-style="color: white; font-family: monospace; font-size: 0.85rem"').classes('w-full').style('''
                                height: 80px !important;
                                min-height: 80px !important;
                                max-height: 80px !important;
                                overflow-y: auto !important;
                                background: rgba(30, 30, 40, 0.9) !important;
                            ''')
                            with ui.row().classes('gap-2'):
                                ui.button(t('dream_btn_restore_default'), icon='refresh', on_click=lambda: auto_instruction_area.set_value(default_auto_instruction)).props('flat dense size=sm')
                    
                    # Fonction de sauvegarde
                    async def save_dream_config():
                        # Déterminer si le prompt est custom ou égal au défaut
                        luna_val = luna_prompt_area.value.strip() if luna_prompt_area.value else ''
                        psy_val = psy_prompt_area.value.strip() if psy_prompt_area.value else ''
                        
                        # Si égal au défaut, sauvegarder vide (= utiliser défaut)
                        if luna_val == default_dream_prompt.strip():
                            luna_val = ''
                        if psy_val == default_psy_prompt.strip():
                            psy_val = ''
                        
                        # Instructions illustration
                        comic_instruction = comic_instruction_area.value.strip() if comic_instruction_area.value else ''
                        single_instruction = single_instruction_area.value.strip() if single_instruction_area.value else ''
                        auto_instruction = auto_instruction_area.value.strip() if auto_instruction_area.value else ''
                        
                        if comic_instruction == default_comic_instruction.strip():
                            comic_instruction = ''
                        if single_instruction == default_single_instruction.strip():
                            single_instruction = ''
                        if auto_instruction == default_auto_instruction.strip():
                            auto_instruction = ''
                        
                        # 🔧 Style d'illustration : utiliser directement la valeur du radio
                        illust_style = illustration_style_radio.value  # "single", "comic_4", ou "auto"
                        
                        new_config = {
                            'enabled': enabled_switch.value,
                            'inactivity_timeout_minutes': int(inactivity_slider.value),
                            'metabolism_tokens_per_minute': int(metabolism_slider.value),
                            'spontaneous_mention_threshold': int(mention_slider.value),
                            # Illustrations
                            'generate_illustrations': illustration_switch.value,
                            'auto_illustration': illustration_switch.value,  # Alias pour dream_core.py
                            'illustration_style': illust_style,  # "single", "comic_4", ou "auto"
                            # Mémoire
                            'max_summaries': int(summaries_slider.value),
                            'max_hashtag_memories': int(hashtag_slider.value),
                            # Prompts personnalisés (vide = utiliser défaut)
                            'prompt_dream_generator': luna_val,
                            'prompt_archiviste_psy': psy_val,
                            'prompt_comic_instruction': comic_instruction,
                            'prompt_single_instruction': single_instruction,
                            'prompt_auto_instruction': auto_instruction,
                        }
                        set_config(new_config)
                        
                        # 🔄 APPLIQUER LA CONFIG AU SYSTÈME (évite le F5)
                        try:
                            from extensions.dream_engine import reload_and_apply_config
                            success = await reload_and_apply_config()
                            
                            if success:
                                # Feedback sur ce qui a été sauvegardé
                                custom_count = (1 if luna_val else 0) + (1 if psy_val else 0)
                                if custom_count > 0:
                                    ui.notify(t('dream_notify_saved_custom', n=custom_count), type='positive')
                                else:
                                    ui.notify(t('dream_notify_saved_default'), type='positive')
                            else:
                                ui.notify(t('dream_notify_saved_apply_err'), type='warning')
                        except Exception as e:
                            print(f"[DREAM-CONFIG] ⚠️ Erreur reload_and_apply_config: {e}")
                            ui.notify(t('dream_notify_saved_timer_err'), type='warning')
                    
                    # Boutons
                    with ui.row().classes('justify-end gap-2 mt-4'):
                        ui.button(t('dream_btn_reset'), icon='refresh', on_click=lambda: (
                            set_config(DEFAULT_CONFIG),
                            ui.notify(t('dream_notify_reset'), type='info'),
                            dialog.close()
                        )).classes('action-button').style('''
                            background: rgba(100, 100, 100, 0.12) !important;
                            border: 1px solid rgba(100, 100, 100, 0.3) !important;
                        ''')
                        
                        ui.button(t('dream_btn_save'), icon='save', on_click=save_dream_config).classes('action-button').style('''
                            background: rgba(138, 43, 226, 0.2) !important;
                            border: 1px solid rgba(138, 43, 226, 0.4) !important;
                            transition: all 0.3s ease !important;
                        ''')
                        
                        ui.button(t('dream_btn_close'), on_click=dialog.close).classes('action-button').style('''
                            background: rgba(138, 43, 226, 0.12) !important;
                            border: 1px solid rgba(138, 43, 226, 0.3) !important;
                            transition: all 0.3s ease !important;
                        ''')
                    
            except ImportError as e:
                ui.markdown(t('dream_unavailable_title'))
                ui.markdown(t('dream_error_label', msg=str(e)))
                ui.markdown(t('dream_unavailable_features'))
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button(t('dream_btn_close'), on_click=dialog.close).classes('action-button')
                    
            except Exception as e:
                ui.markdown(t('dream_config_error_title'))
                ui.markdown(t('dream_error_label', msg=str(e)))
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button(t('dream_btn_close'), on_click=dialog.close).classes('action-button')
    
    return dialog