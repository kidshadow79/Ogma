"""
OGMA NiceGUI (minimal rebase)
Objectif 1: Esthétique type ChatGPT sobre
Objectif 2: Exposer les paramètres IA (providers, modèles, clés, temperature, context_length, max_tokens)
"""

from pathlib import Path
import asyncio
from typing import Optional, Tuple, List, Dict, cast, Any, Callable
import queue
import re
import uuid
import shutil
from datetime import datetime, timedelta

try:
    import importlib
    _ng = importlib.import_module('nicegui')
    _ui = getattr(_ng, 'ui', None)
    _app = getattr(_ng, 'app', None)
except Exception:  # environnement sans NiceGUI installé (lint only)
    _ui = None  # type: ignore
    _app = None  # type: ignore

class _Dummy:
    def __getattr__(self, name):
        return self
    def __call__(self, *args, **kwargs):
        return self
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

# Forcer un type Any pour éviter les erreurs d'analyse lorsque NiceGUI n'est pas présent
ui: Any = _ui if _ui is not None else _Dummy()
app: Any = _app if _app is not None else _Dummy()

# Initialiser la gestion des erreurs NiceGUI AVANT toute utilisation de l'API NiceGUI
if _ui is not None:  # Seulement si NiceGUI est disponible
    try:
        from nicegui_error_handler import initialize_nicegui_error_handling, track_client_activity
        if initialize_nicegui_error_handling():
            print("[NICEGUI] Gestionnaire d'erreurs initialisé")
        else:
            print("[NICEGUI] WARN Erreur initialisation gestionnaire d'erreurs")
    except ImportError:
        print("[NICEGUI] WARN Module gestionnaire d'erreurs non trouvé")
    except Exception as e:
        print(f"[NICEGUI] WARN Erreur initialisation gestionnaire: {e}")

# 🛡️ PROTECTION ANTI-CRASH NICEGUI GLOBALE
def safe_ui_operation(operation_func, *args, **kwargs):
    """
    Wrapper sécurisé pour les opérations NiceGUI
    Évite les crashes par déconnexion client
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["deleted", "client", "belongs"]):
            print(f"[UI-PROTECTION] ⚠️ Opération UI annulée (client déconnecté): {type(e).__name__}")
            return None
        else:
            # Erreur non liée à la déconnexion, la propager
            raise e

from utils import DATA_DIR
from injection_deduplicator import (
    reset_deduplication_session, register_ego_prompt_injection, 
    check_archiviste_injection, register_archiviste_injection,
    get_deduplication_stats
)
from core_logic import SettingsManager, APIManager, OllamaManager, GGUFManager, KoboldManager, AIController, EmbeddingController
from memory_manager import MemoryManager
from audio_manager_wrapper import get_audio_manager
from conversation_summarizer import summarizer, archive
from extensions.temporal_guardian import create_temporal_guardian

# ====== MODULE VOICE CONVERSATION (Janvier 2026) ======
try:
    from modules.voice import VoiceManager, VoiceState, create_voice_indicator, initialize_voice_manager
    VOICE_MODULE_AVAILABLE = True
    print("[VOICE] ✅ Module voice disponible")
except ImportError as e:
    VOICE_MODULE_AVAILABLE = False
    print(f"[VOICE] ⚠️ Module voice non disponible: {e}")

# ====== MODULES REFACTORÉS (Phase 1 - Nov 2025) ======
from utils.formatting_utils import format_size, format_datetime, truncate_filename, get_file_icon
from utils.message_parsers import parse_thinking_format, parse_introspection_format
from utils.backend_utils import map_backend_for_controller
from conversations import (
    load_conversation_index, save_conversation_index,
    make_conv_id, make_title_from_text
)
from conversations.conversation_commands import handle_conversation_commands
from backend import list_models, test_connection, check_global_ia_status, update_ia_status_indicators
from files.file_management import (
    process_uploaded_file, update_header_display, update_file_tab_display,
    remove_active_file, show_file_upload_dialog
)
# ====== FIN MODULES REFACTORÉS ======

# ====== MODULE UI CONVERSATIONS (Scénario A - Nov 2025) ======
# Import des fonctions UI pour conversations, sidebar, modals  
# NOTE: Import circulaire résolu car ogma_ng.py est le point d'entrée
# Les fonctions ont été extraites et NE SONT PLUS définies dans ogma_ng.py
try:
    from ogma_ui_conversations import (
        _message,
        _create_streaming_message,
        _finalize_streaming_message,
        _filter_missing_images,
        load_message_for_edit,
        _sidebar,
        _load_conversation_index,
        _save_conversation_index,
        _load_conversation,
        _new_conversation,
        _persist_conversation,
        _render_full_history,
        _maybe_update_conv_title,
        _generate_smart_title_from_history,
        _schedule_smart_title_generation,
        _generate_smart_title_async,
        _regenerate_title_manual,
        _check_progressive_summarization,
        _make_conv_id,
        _make_title_from_text,
        _generate_conversation_summary,
        _memorize_conversation,
        _mark_conversation_memorized,
        _is_conversation_memorized,
        _count_memorized_conversations,
        _get_memorized_conversations_list,
        _update_memorized_conversation,
        _delete_memorized_conversation,
        _create_edit_interface,
        _edit_summary_popup,
        _display_conversation_as_attachment,
        _display_archived_conversation,
        _display_search_results,
        _display_conversation_summary,
        _display_available_conversations
    )
    _UI_CONVERSATIONS_AVAILABLE = True
    print("[REFACTORING] ✅ Module ogma_ui_conversations chargé (32 fonctions)")
except ImportError as e:
    print(f"[REFACTORING] ⚠️ Module ogma_ui_conversations non disponible: {e}")
    _UI_CONVERSATIONS_AVAILABLE = False
    # Fallback: ces fonctions DOIVENT être disponibles pour que OGMA fonctionne
    raise ImportError(f"CRITIQUE: Module ogma_ui_conversations requis ! {e}")
# ====== FIN MODULE UI CONVERSATIONS ======

# COGNITIVE MIRROR EXTENSION
try:
    from extensions.cognitive_mirror import initialize_cognitive_mirror, get_cognitive_mirror
    COGNITIVE_MIRROR_AVAILABLE = True
    print("[COGNITIVE-MIRROR] OK Extension disponible")
except ImportError as e:
    COGNITIVE_MIRROR_AVAILABLE = False
    print(f"[COGNITIVE-MIRROR] ERROR Extension non disponible: {e}")

# BIOGRAPHIE PROFIL EXTENSION
try:
    from extensions.biographie_profil import initialize_biography_extension, is_available as biography_available, get_biography_ui
    BIOGRAPHY_EXTENSION_AVAILABLE = True
    print("[BIOGRAPHY-EXTENSION] OK Extension disponible")
except ImportError as e:
    BIOGRAPHY_EXTENSION_AVAILABLE = False
    print(f"[BIOGRAPHY-EXTENSION] ERROR Extension non disponible: {e}")

# CAPABILITY ADVISOR EXTENSION
try:
    from extensions.capability_advisor import initialize_capability_advisor, is_available as capability_advisor_available, get_capability_advisor
    CAPABILITY_ADVISOR_AVAILABLE = True
    print("[CAPABILITY-ADVISOR] OK Extension disponible")
except ImportError as e:
    CAPABILITY_ADVISOR_AVAILABLE = False
    print(f"[CAPABILITY-ADVISOR] ERROR Extension non disponible: {e}")

import uuid

# IMPORT DES COMPOSANTS UI DÉPLACÉS (REFACTORING)
try:
    # Imports modulaires depuis les nouveaux fichiers spécialisés
    from ogma_modals import *
    from ogma_displays import *
    from ogma_config_ui import *
    from ogma_tts_config import *
    from ogma_profile import *
    from ogma_headers import *
    # Imports explicites pour fonctions _ (non exportées par import *)
    from ogma_modals import _models_modal, _manual_memorize_current_input, _settings_hub_modal, _list_models, _memorization_popup, _update_memorization_popup
    from ogma_displays import _link_styles
    from ogma_headers import _header
    from ogma_profile import _profile_modal  # Fix: import explicite pour le modal profil
    from ogma_ui_conversations import _update_ia_status_indicators
    # Import module introspection UI (8 déc 2025)
    from ogma_introspection_ui import (
        _process_subconscience_messages,
        _on_synthesis_ready,
        _on_introspection_message_callback,
        _on_message_ready,
        _ensure_cognitive_mirror
    )
    print("[REFACTOR] OK Composants UI importés depuis les modules spécialisés")
except ImportError as e:
    print(f"[REFACTOR] ERREUR import composants UI: {e}")
    # Fallback: continuer sans les composants déplacés

# 🚀 PREANALYSIS OPTIMIZER - Optimisation latence (7 déc 2025)
try:
    from modules.preanalysis_optimizer.integration import (
        trigger_preanalysis_on_typing,
        get_optimized_context_for_message,
        on_conversation_change,
        set_preanalysis_enabled
    )
    PREANALYSIS_AVAILABLE = True
    print("[PREANALYSIS-OPTIMIZER] ✅ Module d'optimisation latence disponible")
except ImportError as e:
    PREANALYSIS_AVAILABLE = False
    print(f"[PREANALYSIS-OPTIMIZER] ⚠️ Module non disponible: {e}")

# 🔧 OGMA CORE MODULE - Structure modulaire (8 déc 2025)
try:
    from modules.ogma_core.compat import sync_globals_to_core, sync_globals_from_core
    from modules.ogma_core import (
        is_extension_available,
        get_available_extensions,
        load_extension,
        get_extension_status,
    )
    # Import des fonctions ensure_* depuis le module centralisé
    from modules.ogma_core.controllers import (
        ensure_settings_manager as _ensure_settings_manager_core,
        ensure_audio_manager as _ensure_audio_manager_core,
        ensure_backends as _ensure_backends_core,
        ensure_memory_manager as _ensure_memory_manager_core,
        ensure_archiviste_controller as _ensure_archiviste_controller_core,
        ensure_embedding_controller as _ensure_embedding_controller_core,
        ensure_chat_controller as _ensure_chat_controller_core,
        ensure_memory_optimizer as _ensure_memory_optimizer_core,
        ensure_temporal_guardian as _ensure_temporal_guardian_core,
        ensure_contextual_recall as _ensure_contextual_recall_core,
        ensure_file_writer as _ensure_file_writer_core,
        ensure_capability_advisor as _ensure_capability_advisor_core,
        ensure_cognitive_mirror as _ensure_cognitive_mirror_core,
        ensure_organic_planner as _ensure_organic_planner_core,
        close_memory_manager as close_memory_manager_core,
        get_web_navigator_instance as get_web_navigator_instance_core,
    )
    OGMA_CORE_AVAILABLE = True
    print("[OGMA-CORE] ✅ Module centralisé disponible")
except ImportError as e:
    OGMA_CORE_AVAILABLE = False
    print(f"[OGMA-CORE] ⚠️ Module non disponible: {e}")
    # Fallback: fonctions vides
    def sync_globals_to_core(g): pass
    def sync_globals_from_core(): return {}


# State minimal
_settings_mgr: Optional[SettingsManager] = None
_api_mgr: Optional[APIManager] = None
_ollama_mgr: Optional[OllamaManager] = None
_gguf_mgr: Optional[GGUFManager] = None
_kobold_mgr: Optional[KoboldManager] = None
_chat_controller: Optional[AIController] = None
_audio_manager = None
_chat_history: List[Dict] = []  # Historique pour l'IA (optimisé avec résumés)
_chat_history_ui: List[Dict] = []  # Historique pour l'interface utilisateur (COMPLET, tous les messages originaux)
_current_conversation_id: Optional[str] = None
_current_user_name: Optional[str] = None  # Session: prénom utilisateur connecté
_user_authenticated: bool = False  # Flag: utilisateur identifié pour cette session
_conv_index: Dict[str, Dict] = {}
_conv_area = None  # conteneur de conversation
_chat_inner = None  # conteneur interne pour les messages (pile verticale)
_input_field = None  # champ de saisie des messages
_archiviste_controller: Optional[AIController] = None
_embedding_controller: Optional[EmbeddingController] = None
_memory_manager: Optional[MemoryManager] = None
_memory_optimizer = None  # Solution A - Archiviste Memory Optimizer (12 nov 2025)
_temporal_guardian = None  # Extension Temporal Guardian
_cognitive_mirror = None   # Extension Cognitive Mirror - Transparence cognitive
_contextual_recall_ext = None  # Extension Contextual Recall - Mémoire conversationnelle
_file_writer_ext = None  # Extension File Writer - Sauvegarde automatique .md
_journal_preformed_response = None  # Réponse journal prête à être injectée
_introspection_box_content = []  # Buffer messages introspection en cours
_voice_manager = None  # Module Voice Conversation (Janvier 2026)
_voice_indicator = None  # Indicateur visuel vocal

# ========== SPINNER IMAGE GENERATION ==========
IMAGE_GEN_SPINNER_HTML = '''
<div style="display:flex;flex-direction:column;align-items:center;margin:16px 0;">
<div style="width:28px;height:28px;border:3px solid #444;border-top:3px solid #f97316;border-radius:50%;animation:ogma-spin 0.8s linear infinite;"></div>
<span style="font-size:11px;color:#888;margin-top:6px;font-style:italic;">création en cours...</span>
</div>
<style>@keyframes ogma-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>
'''

# ========== SPINNER CONVERSATION SEARCH ==========
CONV_SEARCH_SPINNER_HTML = '''
<div style="display:flex;flex-direction:column;align-items:center;margin:16px 0;">
<div style="width:28px;height:28px;border:3px solid #444;border-top:3px solid #E91E63;border-radius:50%;animation:ogma-spin 0.8s linear infinite;"></div>
<span style="font-size:11px;color:#888;margin-top:6px;font-style:italic;">je fouille dans mes souvenirs...</span>
</div>
<style>@keyframes ogma-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>
'''

# ========== SPINNER JAVASCRIPT INJECTION ==========
# Injection directe dans le DOM (ui.markdown.set_content n'affiche pas le HTML brut)
_SPINNER_INJECT_JS_TEMPLATE = (
    "(function(){"
    "if(document.getElementById('ogma-magic-spinner'))return;"
    "if(!document.getElementById('ogma-spin-style')){"
    "var s=document.createElement('style');s.id='ogma-spin-style';"
    "s.textContent='@keyframes ogma-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}';"
    "document.head.appendChild(s);}"
    # Prendre le DERNIER .ogma-streaming-target (le message le plus récent)
    "var all=document.querySelectorAll('.ogma-streaming-target');"
    "var t=all.length>0?all[all.length-1]:null;"
    "if(t){"
    "t.insertAdjacentHTML('afterend',"
    "'<div id=\"ogma-magic-spinner\" style=\"display:flex;flex-direction:column;align-items:center;margin:16px 0;\">'"
    "+'<div style=\"width:28px;height:28px;border:3px solid #444;border-top:3px solid SPINNER_COLOR;border-radius:50%;animation:ogma-spin 0.8s linear infinite;\"></div>'"
    "+'<span style=\"font-size:11px;color:#888;margin-top:6px;font-style:italic;\">SPINNER_LABEL</span></div>'"
    ");}"
    "})();"
)
_SPINNER_REMOVE_JS = "var s=document.getElementById('ogma-magic-spinner');if(s)s.remove();"

def _get_spinner_inject_js(spinner_type='image'):
    """Retourne le JS pour injecter le spinner animé dans le DOM."""
    if spinner_type == 'search':
        color, label = '#E91E63', 'je fouille dans mes souvenirs...'
    else:
        color, label = '#f97316', 'création en cours...'
    return _SPINNER_INJECT_JS_TEMPLATE.replace('SPINNER_COLOR', color).replace('SPINNER_LABEL', label)

# ========== UTILITAIRES COMPRESSION IMAGE ==========
def _get_vision_compression_size() -> int:
    """
    Récupère la taille de compression vision depuis les settings.
    Retourne 0 si pas de compression.
    """
    try:
        sm = _ensure_settings_manager()
        if sm:
            img_config = sm.settings.get('image_generation', {})
            return img_config.get('vision_compression', 400)
    except:
        pass
    return 400  # Défaut: 400x400

def _compress_image_for_vision(base64_data: str, max_tokens: int = 1_500_000) -> str:
    """
    Compresse une image base64 selon le paramètre vision_compression.
    Redimensionne d'abord à la taille max configurée, puis compresse si nécessaire.
    
    Args:
        base64_data: Image en base64 (sans préfixe data:image/...)
        max_tokens: Limite maximale de tokens (fallback si pas de setting)
        
    Returns:
        base64 compressé ou original si pas besoin
    """
    import base64
    from io import BytesIO
    
    # Récupérer la taille max configurée
    max_size = _get_vision_compression_size()
    
    # Si compression désactivée (0), retourner l'original
    if max_size == 0:
        print(f"[VISION-COMPRESS] ⚪ Compression désactivée - image originale")
        return base64_data
    
    try:
        # Vérifier que PIL est disponible
        try:
            from PIL import Image
        except ImportError:
            print("[VISION-COMPRESS] ❌ PIL/Pillow non installé")
            return base64_data
        
        # Décoder base64
        image_bytes = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_bytes))
        
        original_size = f"{image.width}x{image.height}"
        
        # Vérifier si redimensionnement nécessaire
        if image.width <= max_size and image.height <= max_size:
            print(f"[VISION-COMPRESS] ✅ Image {original_size} déjà sous {max_size}px")
            return base64_data
        
        # Calculer nouvelles dimensions en gardant le ratio
        ratio = min(max_size / image.width, max_size / image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        print(f"[VISION-COMPRESS] 🔧 {original_size} → {new_width}x{new_height} (max {max_size}px)")
        
        # Redimensionner avec LANCZOS (haute qualité)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Récupérer la qualité JPEG configurée
        sm = _ensure_settings_manager()
        jpeg_quality = 85  # Défaut
        if sm:
            img_config = sm.settings.get('image_generation', {})
            jpeg_quality = img_config.get('vision_jpeg_quality', 85)
        
        # Convertir en JPEG avec qualité configurée
        output = BytesIO()
        if image.mode in ('RGBA', 'LA', 'P'):
            # Convertir transparence en blanc
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(output, format='JPEG', quality=jpeg_quality, optimize=True)
        compressed_bytes = output.getvalue()
        compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
        
        # Stats
        original_tokens = len(base64_data) * 1.33
        final_tokens = len(compressed_b64) * 1.33
        reduction_pct = (1 - final_tokens / original_tokens) * 100
        print(f"[VISION-COMPRESS] ✅ {original_tokens/1000:.0f}K → {final_tokens/1000:.0f}K tokens (-{reduction_pct:.0f}%)")
        
        return compressed_b64
        
    except Exception as e:
        import traceback
        print(f"[VISION-COMPRESS] ❌ ERREUR: {e}")
        traceback.print_exc()
        return base64_data

def _compress_html_images(html_content: str, max_tokens: int = 400_000) -> str:
    """
    Compresse toutes les images base64 dans du contenu HTML
    
    Args:
        html_content: HTML contenant des <img src="data:image/...;base64,XXX">
        max_tokens: Limite tokens par image (~400K pour rester safe en historique)
        
    Returns:
        HTML avec images compressées
    """
    import re
    import base64
    from io import BytesIO
    
    # Détecter toutes les images base64 dans le HTML (avec tous les attributs)
    pattern = r'<img\s+src="data:image/([^;]+);base64,([^"]+)"([^>]*?)>'
    matches = list(re.finditer(pattern, html_content))
    
    if not matches:
        return html_content  # Pas d'images
    
    print(f"[HTML-COMPRESS] 🖼️ {len(matches)} image(s) détectée(s) dans HTML")
    
    try:
        from PIL import Image
    except ImportError:
        print("[HTML-COMPRESS] ⚠️ PIL absent, images non compressées")
        return html_content
    
    compressed_html = html_content
    
    for i, match in enumerate(matches, 1):
        image_format = match.group(1)  # png, jpeg, etc.
        base64_data = match.group(2)
        
        estimated_tokens = len(base64_data) * 1.33
        print(f"[HTML-COMPRESS] 🔍 Image #{i}: {estimated_tokens/1_000:.0f}K tokens")
        
        if estimated_tokens <= max_tokens:
            print(f"[HTML-COMPRESS] ✅ Image #{i} OK (< {max_tokens/1_000:.0f}K)")
            continue
        
        print(f"[HTML-COMPRESS] 🔧 Compression image #{i}...")
        
        try:
            # Décoder et charger
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Calculer réduction
            reduction_ratio = max_tokens / estimated_tokens
            new_width = int(image.width * (reduction_ratio ** 0.5))
            new_height = int(image.height * (reduction_ratio ** 0.5))
            
            print(f"[HTML-COMPRESS] 📐 {image.width}x{image.height} → {new_width}x{new_height}")
            
            # Redimensionner
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convertir en JPEG qualité 75 (affichage conversation)
            output = BytesIO()
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            image.save(output, format='JPEG', quality=75, optimize=True)
            compressed_bytes = output.getvalue()
            compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
            
            final_tokens = len(compressed_b64) * 1.33
            reduction_pct = (1 - final_tokens / estimated_tokens) * 100
            print(f"[HTML-COMPRESS] ✅ Image #{i}: {final_tokens/1_000:.0f}K tokens (-{reduction_pct:.0f}%)")
            
            # Remplacer dans HTML (forcer JPEG, conserver autres attributs)
            old_img = match.group(0)  # <img src="..." alt="..." style="...">
            other_attrs = match.group(3)  # Les attributs après src (alt, style, etc.)
            new_img = f'<img src="data:image/jpeg;base64,{compressed_b64}"{other_attrs}>'
            compressed_html = compressed_html.replace(old_img, new_img, 1)
            
        except Exception as e:
            print(f"[HTML-COMPRESS] ❌ Erreur image #{i}: {e}")
            # Garder l'original en cas d'erreur
    
    return compressed_html

# ========== FIN UTILITAIRES COMPRESSION IMAGE ==========

_introspection_md_widget = None  # Référence au widget markdown de la boîte
_status_queue: Optional[queue.Queue] = None
_memory_update_hooks: List[Callable[[], None]] = []  # callbacks à appeler après ajout mémoire
_sidebar_render_cb: Optional[Callable[[Optional[str]], None]] = None  # rafraîchisseur de la liste des conversations
_title_updating: bool = False  # évite les mises à jour concurrentes de titre

# Gestion des fichiers
_active_file_data: Optional[Dict] = None  # Données du fichier texte actuel
_active_images: List[Dict] = []  # Liste des images uploadées (max 3)
MAX_IMAGES = 3  # Nombre maximum d'images uploadables simultanément

# ===== REPRÉSENTATION VISUELLE USER/IA POUR I2I =====
_user_representation_active: bool = False  # Bouton User enfoncé
_ia_representation_active: bool = False    # Bouton IA enfoncé
_user_repr_button_ref = None  # Référence UI bouton User
_ia_repr_button_ref = None    # Référence UI bouton IA
_repr_images_for_i2i: List[Dict] = []  # Stockage temporaire avatars HD pour T2I→I2I
_enriched_i2i_prompt: str = ""  # Prompt enrichi composé par vision (bypass regex extraction)
REPR_USER_DIR = Path("data/generated_images/Utilisateur")
REPR_IA_DIR = Path("data/generated_images/IA_Principale")

_loaded_conversation: Optional[List[Dict]] = None  # Conversation actuellement chargée pour l'IA
_loaded_conversation_filename: Optional[str] = None  # Nom du fichier de conversation chargé
_conversation_context_injected: bool = False  # Indique si le contexte a déjà été injecté
_orchestration_injected: bool = False  # Indique si l'orchestration cognitive a été injectée
_thinking_css_injected: bool = False  # Indique si le CSS pour thinking a été injecté
_file_tab_container = None  # Conteneur pour l'onglet de fichier
_header_container = None  # Conteneur du header pour basculer titre/onglet
_ia_status_indicators = {}  # Conteneur pour les indicateurs d'état IA

# Variables globales pour gestion introspection simplifiée
# Plus de système d'accumulation - chaque message a son propre déroulé

# Variable pour l'édition de messages
_editing_message_index = None  # Index du message en cours d'édition

# Messages d'injection comportementale en attente (Extension Metacognitive)
_pending_behavioral_injections = []

# Variable globale pour l'extension Web Navigator (éviter les recréations)
_web_navigator_ext = None

# Variable globale pour l'extension Capability Advisor
_capability_advisor = None

# Variable globale pour l'extension Organic Planner
_organic_planner = None

# Variable globale pour le bouton STOP (reference UI uniquement)
_stop_button_ref = None  # Reference au bouton pour mise a jour visuelle

# Variable globale pour le widget de streaming (pour mise a jour depuis extensions)
_streaming_widget_ref = None  # Widget markdown du message en cours de streaming
_streaming_container_ref = None  # Container AI parent (référence stable pour injection post-streaming)
_streaming_html_ref = None       # Placeholder ui.html() pré-créé pour injection batch grid (set_content fiable)


def get_streaming_widget_ref():
    """Retourne la reference au widget de streaming courant (pour mise a jour depuis extensions)."""
    global _streaming_widget_ref
    return _streaming_widget_ref


async def _retrieve_liberating_memory(memory_id: str) -> Optional[str]:
    """
    OK NOUVEAU: Récupère un souvenir libérateur via ID vectoriel.
    Système similaire à ego_prompt mais pour mémoire émotionnelle.
    """
    global _memory_manager
    
    if not _memory_manager or not memory_id:
        return None
    
    try:
        # Recherche par ID vectoriel dans la base mémoire
        memory_data = _memory_manager.get_memory_by_id(memory_id)
        
        if memory_data:
            # Extraire le contenu émotionnel libérateur
            content = memory_data.get('content', '') or memory_data.get('summary', '')
            if content:
                return f"Tu te souviens: {content}"
        
        # Fallback: recherche alternative par proximité si ID exact non trouvé
        synthesis, fallback_memories = await _memory_manager.retrieve_synthesis_and_memories(
            query_text="expression libre vocabulaire authentique amour",
            k=3,
            top_memories=1
        )
        
        if fallback_memories:
            fallback = fallback_memories[0]
            content = fallback.get('content', '') or fallback.get('summary', '')
            return f"Souvenir similaire: {content}"
        
        return None
        
    except Exception as e:
        print(f"[METACOGNITION] Erreur récupération souvenir {memory_id}: {e}")
        return None


def _trigger_memory_update():
    try:
        for cb in list(_memory_update_hooks):
            try:
                cb()
            except Exception:
                pass
    except Exception:
        pass


# ============================================================================
# FONCTIONS ENSURE_* - WRAPPERS VERS MODULE OGMA_CORE
# Ces fonctions délèguent au module centralisé et synchronisent les globals
# ============================================================================

def get_web_navigator_instance():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _web_navigator_ext
    if OGMA_CORE_AVAILABLE:
        result = get_web_navigator_instance_core()
        _web_navigator_ext = result
        return result
    # Fallback local
    if _web_navigator_ext is None:
        try:
            from extensions.web_navigator import WebNavigatorExtension
            _web_navigator_ext = WebNavigatorExtension()
        except Exception as e:
            print(f"[WEB-NAV] ❌ Erreur: {e}")
    return _web_navigator_ext


def _ensure_settings_manager():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _settings_mgr
    if OGMA_CORE_AVAILABLE:
        result = _ensure_settings_manager_core()
        _settings_mgr = result
        return result
    # Fallback local
    if _settings_mgr is None:
        settings_path = DATA_DIR / 'settings.json'
        _settings_mgr = SettingsManager(settings_path)
    return _settings_mgr


def _ensure_audio_manager():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _audio_manager
    if OGMA_CORE_AVAILABLE:
        result = _ensure_audio_manager_core()
        _audio_manager = result
        # Appliquer la config TTS depuis settings
        _apply_tts_config_from_settings(_audio_manager)
        return result
    # Fallback local
    if _audio_manager is None:
        try:
            _audio_manager = get_audio_manager()
            _audio_manager.initialize_tts()
            # Appliquer la config TTS depuis settings
            _apply_tts_config_from_settings(_audio_manager)
        except Exception as e:
            print(f"[AUDIO] Erreur: {e}")
    return _audio_manager


def _apply_tts_config_from_settings(audio_mgr):
    """Applique la configuration TTS depuis settings.json"""
    if not audio_mgr:
        return
    
    try:
        sm = _ensure_settings_manager()
        if not sm:
            return
        
        tts_settings = sm.settings.get('tts', {})
        engine_type = tts_settings.get('engine', 'system')
        
        print(f"[TTS] Configuration depuis settings: engine={engine_type}")
        
        if engine_type == 'google':
            audio_mgr.configure_tts_engine(
                'google',
                api_key=tts_settings.get('google_api_key'),
                voice=tts_settings.get('google_voice', 'fr-FR-Standard-A')
            )
        elif engine_type == 'elevenlabs':
            eleven_key = tts_settings.get('elevenlabs_api_key')
            eleven_voice = tts_settings.get('elevenlabs_voice_id', 'pNInz6obpgDQGcFmaJgB')
            eleven_model = tts_settings.get('elevenlabs_model', 'eleven_multilingual_v2')
            eleven_stability = tts_settings.get('elevenlabs_stability', 0.5)
            eleven_similarity = tts_settings.get('elevenlabs_similarity', 0.75)
            eleven_style = tts_settings.get('elevenlabs_style', 0.0)
            eleven_speed = tts_settings.get('elevenlabs_speed', 1.0)
            eleven_speaker_boost = tts_settings.get('elevenlabs_speaker_boost', True)
            print(f"[TTS] ElevenLabs: clé={'***' if eleven_key else 'AUCUNE'}, voice={eleven_voice}, model={eleven_model}")
            audio_mgr.configure_tts_engine(
                'elevenlabs',
                api_key=eleven_key,
                voice_id=eleven_voice,
                model=eleven_model,
                stability=eleven_stability,
                similarity=eleven_similarity,
                style=eleven_style,
                speed=eleven_speed,
                speaker_boost=eleven_speaker_boost
            )
        elif engine_type == 'azure':
            audio_mgr.configure_tts_engine(
                'azure',
                api_key=tts_settings.get('azure_api_key'),
                voice=tts_settings.get('azure_voice', 'fr-FR-DeniseNeural'),
                region=tts_settings.get('azure_region', 'westeurope')
            )
        elif engine_type == 'gtts':
            audio_mgr.configure_tts_engine(
                'gtts',
                lang=tts_settings.get('gtts_lang', 'fr')
            )
        elif engine_type == 'edge_tts':
            audio_mgr.configure_tts_engine(
                'edge_tts',
                voice=tts_settings.get('edge_tts_voice', 'fr-FR-DeniseNeural')
            )
        elif engine_type == 'fish_audio':
            fish_key = tts_settings.get('fish_audio_api_key')
            fish_voice = tts_settings.get('fish_audio_voice_id', '')
            fish_model = tts_settings.get('fish_audio_model', 's2-pro')
            fish_latency = tts_settings.get('fish_audio_latency', 'normal')
            fish_chunk = tts_settings.get('fish_audio_chunk_length', 200)
            fish_normalize = tts_settings.get('fish_audio_normalize', True)
            fish_bitrate = tts_settings.get('fish_audio_mp3_bitrate', 128)
            fish_emotion = tts_settings.get('fish_audio_emotion', 'none')
            print(f"[TTS] Fish Audio: cle={'***' if fish_key else 'AUCUNE'}, voice={fish_voice}, model={fish_model}, latency={fish_latency}, emotion={fish_emotion}")
            audio_mgr.configure_tts_engine(
                'fish_audio',
                api_key=fish_key,
                voice_id=fish_voice,
                model=fish_model,
                latency=fish_latency,
                chunk_length=fish_chunk,
                normalize=fish_normalize,
                mp3_bitrate=fish_bitrate,
                emotion=fish_emotion
            )
        elif engine_type == 'cartesia':
            cartesia_key = tts_settings.get('cartesia_api_key')
            cartesia_voice = tts_settings.get('cartesia_voice_id', '')
            cartesia_model = tts_settings.get('cartesia_model', 'sonic-2')
            cartesia_speed = tts_settings.get('cartesia_speed', 1.0)
            cartesia_emotion = tts_settings.get('cartesia_emotion', 'neutral')
            print(f"[TTS] Cartesia: cle={'***' if cartesia_key else 'AUCUNE'}, voice={cartesia_voice}, model={cartesia_model}, speed={cartesia_speed}, emotion={cartesia_emotion}")
            audio_mgr.configure_tts_engine(
                'cartesia',
                api_key=cartesia_key,
                voice_id=cartesia_voice,
                model=cartesia_model,
                speed=cartesia_speed,
                emotion=cartesia_emotion
            )
        elif engine_type == 'hume_ai':
            hume_key = tts_settings.get('hume_ai_api_key')
            hume_voice_name = tts_settings.get('hume_ai_voice_name', '')
            hume_voice_id = tts_settings.get('hume_ai_voice_id', '')
            hume_desc = tts_settings.get('hume_ai_description', '')
            hume_version = tts_settings.get('hume_ai_version', 2)
            voice_info = hume_voice_id or hume_voice_name or 'dynamique'
            print(f"[TTS] Hume AI: clé={'***' if hume_key else 'AUCUNE'}, voice={voice_info}, version=Octave {hume_version}")
            audio_mgr.configure_tts_engine(
                'hume_ai',
                api_key=hume_key,
                voice_name=hume_voice_name,
                voice_id=hume_voice_id,
                description=hume_desc,
                version=hume_version
            )
        elif engine_type == 'conflict_free':
            audio_mgr.configure_tts_engine('conflict_free')
        else:
            audio_mgr.configure_tts_engine('system')
        
        # Appliquer les autres paramètres TTS
        if hasattr(audio_mgr, 'set_tts_settings'):
            audio_mgr.set_tts_settings(
                speed=tts_settings.get('speed', 150),
                volume=tts_settings.get('volume', 0.8),
                enabled=tts_settings.get('enabled', True)
            )
            
    except Exception as e:
        print(f"[TTS] Erreur configuration depuis settings: {e}")


def _ensure_backends():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _api_mgr, _ollama_mgr, _gguf_mgr, _kobold_mgr
    if OGMA_CORE_AVAILABLE:
        result = _ensure_backends_core()
        _api_mgr, _ollama_mgr, _gguf_mgr, _kobold_mgr = result
        return result
    # Fallback local
    if _api_mgr is None:
        _api_mgr = APIManager()
    if _ollama_mgr is None:
        _ollama_mgr = OllamaManager()
    if _gguf_mgr is None:
        _gguf_mgr = GGUFManager()
    if _kobold_mgr is None:
        _kobold_mgr = KoboldManager()
    return _api_mgr, _ollama_mgr, _gguf_mgr, _kobold_mgr


# NOTA: _map_backend_for_controller extrait vers utils/backend_utils.py

def _get_current_time() -> str:
    """Fonction pour que l'IA principale puisse demander l'heure actuelle quand nécessaire."""
    from temporal_injector import TemporalInjector
    temporal_injector = TemporalInjector()
    return temporal_injector.get_current_time()


def _ensure_memory_manager() -> Optional[MemoryManager]:
    """Wrapper: Délègue à ogma_core.controllers"""
    global _memory_manager, _archiviste_controller, _embedding_controller, _status_queue
    if OGMA_CORE_AVAILABLE and _memory_manager is None:
        from modules.ogma_core import globals as g
        result = _ensure_memory_manager_core()
        _memory_manager = result
        _archiviste_controller = g._archiviste_controller
        _embedding_controller = g._embedding_controller
        _status_queue = g._status_queue
        return result
    if _memory_manager is not None:
        return _memory_manager
    # Fallback: initialisation locale si module non disponible
    _ensure_backends()
    sm = _ensure_settings_manager()
    if _status_queue is None:
        _status_queue = queue.Queue()
    # Note: Le fallback complet est dans controllers.py
    print("[MEMORY-MANAGER] ⚠️ Fallback local - utiliser ogma_core pour init complète")
    return None


def _ensure_memory_optimizer():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _memory_optimizer
    if OGMA_CORE_AVAILABLE:
        result = _ensure_memory_optimizer_core()
        _memory_optimizer = result
        return result
    # Fallback local minimal
    if _memory_optimizer is not None:
        return _memory_optimizer
    return None


def _ensure_archiviste_controller():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _archiviste_controller
    if OGMA_CORE_AVAILABLE:
        result = _ensure_archiviste_controller_core()
        _archiviste_controller = result
        # Mettre à jour le Journal si disponible (cas init avec MockArchiviste)
        if result is not None:
            try:
                from extensions.journal_de_bord import update_archiviste, is_available
                if is_available():
                    if update_archiviste(result):
                        print("[JOURNAL-SYNC] ✅ Archiviste mis à jour dans Journal")
            except ImportError:
                pass
            except Exception as e:
                print(f"[ARCHIVISTE] ⚠️ Erreur update journal: {e}")
        return result
    if _archiviste_controller is None:
        _ensure_memory_manager()
    return _archiviste_controller


def _ensure_embedding_controller():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _embedding_controller
    if OGMA_CORE_AVAILABLE:
        result = _ensure_embedding_controller_core()
        _embedding_controller = result
        return result
    if _embedding_controller is None:
        _ensure_memory_manager()
    return _embedding_controller


def close_memory_manager():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _memory_manager
    if OGMA_CORE_AVAILABLE:
        close_memory_manager_core()
        _memory_manager = None
        return
    if _memory_manager is not None:
        try:
            _memory_manager.cleanup()
        except Exception as e:
            print(f"[OGMA] Erreur fermeture: {e}")
        finally:
            _memory_manager = None


def _ensure_temporal_guardian():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _temporal_guardian
    if OGMA_CORE_AVAILABLE:
        result = _ensure_temporal_guardian_core()
        _temporal_guardian = result
        return result
    if _temporal_guardian is not None:
        return _temporal_guardian
    try:
        sm = _ensure_settings_manager()
        temporal_config = sm.settings.get('temporal_guardian', {})
        debug_mode = sm.settings.get('debug', {}).get('show_temporal_debug', False)
        _temporal_guardian = create_temporal_guardian(temporal_config, debug=debug_mode)
    except Exception as e:
        print(f"[OGMA] WARN Erreur Temporal Guardian: {e}")
        _temporal_guardian = create_temporal_guardian(debug=False)
    return _temporal_guardian


def _ensure_contextual_recall():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _contextual_recall_ext
    if OGMA_CORE_AVAILABLE:
        result = _ensure_contextual_recall_core()
        _contextual_recall_ext = result
        return result
    if _contextual_recall_ext is not None:
        return _contextual_recall_ext
    try:
        from extensions.contextual_recall import initialize_recall
        _contextual_recall_ext = initialize_recall(
            conversations_path="data/conversations",
            debug=False
        )
    except Exception as e:
        print(f"[CONTEXTUAL-RECALL] ⚠️ Erreur: {e}")
    return _contextual_recall_ext


def _ensure_file_writer():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _file_writer_ext
    if OGMA_CORE_AVAILABLE:
        result = _ensure_file_writer_core()
        _file_writer_ext = result
        return result
    if _file_writer_ext is not None:
        return _file_writer_ext
    try:
        from extensions.file_writer import initialize_file_writer
        _file_writer_ext = initialize_file_writer(uploads_dir="data/uploads", debug=True)
    except Exception as e:
        print(f"[FILE-WRITER] ⚠️ Erreur: {e}")
    return _file_writer_ext


def _ensure_capability_advisor():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _capability_advisor
    if OGMA_CORE_AVAILABLE:
        result = _ensure_capability_advisor_core()
        _capability_advisor = result
        return result
    if _capability_advisor is not None:
        return _capability_advisor
    if not CAPABILITY_ADVISOR_AVAILABLE:
        return None
    try:
        chat_ctrl = _ensure_chat_controller()
        archi_ctrl = _ensure_archiviste_controller()
        memory_mgr = _ensure_memory_manager()
        if archi_ctrl and memory_mgr:
            from extensions.capability_advisor import initialize_capability_advisor
            _capability_advisor = initialize_capability_advisor(
                chat_controller=chat_ctrl,
                archiviste_controller=archi_ctrl,
                memory_manager=memory_mgr
            )
    except Exception as e:
        print(f"[CAPABILITY-ADVISOR] ❌ Erreur: {e}")
    return _capability_advisor


def _ensure_organic_planner():
    """Wrapper: Délègue à ogma_core.controllers"""
    global _organic_planner
    if OGMA_CORE_AVAILABLE:
        result = _ensure_organic_planner_core()
        _organic_planner = result
        return result
    
    if _organic_planner is not None:
        return _organic_planner
        
    try:
        from extensions.organic_planner import initialize_organic_planner
        chat_ctrl = _ensure_chat_controller()
        archi_ctrl = _ensure_archiviste_controller()
        memory_mgr = _ensure_memory_manager()
        
        _organic_planner = initialize_organic_planner(
            chat_controller=chat_ctrl,
            archiviste_controller=archi_ctrl,
            memory_manager=memory_mgr
        )
    except Exception as e:
        print(f"[ORGANIC-PLANNER] ❌ Erreur: {e}")
    return _organic_planner


def _handle_cognitive_mirror_callback(setting_key: str, new_value):
    """
    Gestionnaire de callbacks de l'extension Cognitive Mirror
    Traite les événements spéciaux comme l'intégration de réflexions
    """
    print(f"[COGNITIVE-MIRROR-CALLBACK] CALL {setting_key} = {new_value}")
    
    try:
        if setting_key == 'integrate_reflection_summary':
            # Intégrer le résumé de réflexion dans le contexte principal
            if isinstance(new_value, str) and new_value.strip():
                print(f"[COGNITIVE-MIRROR] LINK Intégration résumé de réflexion en cours...")
                
                # Créer un message système pour intégrer la réflexion
                integration_message = f"💭 **Résumé de réflexion intégré:**\n\n{new_value.strip()}"
                
                # L'ajouter à l'historique de conversation
                global _chat_history
                if _chat_history is not None:
                    _chat_history.append({
                        "role": "system",
                        "content": integration_message,
                        "timestamp": datetime.now().isoformat(),
                        "type": "reflection_summary"
                    })
                    
                    # Actualiser l'interface pour montrer l'intégration
                    _refresh_ui_after_integration()
                    
                    print(f"[COGNITIVE-MIRROR] OK Résumé de réflexion intégré dans la conversation")
                else:
                    print(f"[COGNITIVE-MIRROR] WARN Aucune conversation active pour intégration")
            else:
                print(f"[COGNITIVE-MIRROR] WARN Résumé vide, intégration ignorée")
                
        elif setting_key == 'force_stop_reflection':
            # Traiter l'arrêt forcé de réflexion si nécessaire
            print(f"[COGNITIVE-MIRROR] 🛑 Arrêt de réflexion traité")
            
        else:
            # Autres paramètres standards
            print(f"[COGNITIVE-MIRROR] ⚙️ Paramètre standard: {setting_key}")
            
    except Exception as e:
        print(f"[COGNITIVE-MIRROR-CALLBACK] ERROR Erreur traitement callback {setting_key}: {e}")
        import traceback
        traceback.print_exc()

def _refresh_ui_after_integration():
    """Actualise l'interface après intégration d'une réflexion"""
    try:
        # Actualiser le rendu des messages si possible
        if 'render_chat_message' in globals():
            # Re-rendre les derniers messages pour inclure l'intégration
            pass
        print(f"[COGNITIVE-MIRROR] UPDATE Interface actualisée après intégration")
    except Exception as e:
        print(f"[COGNITIVE-MIRROR] WARN Erreur actualisation interface: {e}")


# ============================================================
# FONCTIONS INTROSPECTION/COGNITIVE MIRROR EXTRAITES
# Module: ogma_introspection_ui.py (8 déc 2025)
# Fonctions: _process_subconscience_messages, _on_synthesis_ready,
#            _on_introspection_message_callback, _on_message_ready,
#            _ensure_cognitive_mirror
# ============================================================


def _ensure_chat_controller() -> AIController:
    """Wrapper: Délègue à ogma_core.controllers"""
    global _chat_controller
    if OGMA_CORE_AVAILABLE:
        result = _ensure_chat_controller_core()
        _chat_controller = result
        return result
    # Fallback minimal
    _ensure_backends()
    sm = _ensure_settings_manager()
    if _chat_controller is None:
        _chat_controller = AIController('chat', cast(OllamaManager, _ollama_mgr), cast(GGUFManager, _gguf_mgr), cast(KoboldManager, _kobold_mgr))
    chat = sm.settings.get('chat_api', {})
    backend = chat.get('backend_type', 'API')
    ctrl_backend = 'GGUF/llama.cpp' if backend == 'GGUF' else backend
    _chat_controller.set_active_backend(ctrl_backend)
    _chat_controller.max_tokens = int(chat.get('max_tokens', 512))
    _chat_controller.context_length = int(chat.get('context_length', 4096))
    _chat_controller.temperature = float(chat.get('temperature', 0.7))
    if backend == 'API':
        _chat_controller.api_manager.configure(
            chat.get('provider', 'Aucun'), chat.get('api_key', ''), chat.get('api_model', '')
        )
        _chat_controller.api_manager.openrouter_thinking = bool(chat.get('openrouter_thinking', False))
    return _chat_controller


# Note: _ensure_archiviste_controller déjà défini plus haut comme wrapper (ligne ~470)


def _notify_safe(message: str, type: str = 'info', timeout: int = None) -> None:
    """Tente d'afficher une notification; ignore si hors contexte UI (timer/task)."""
    try:
        if timeout is not None:
            ui.notify(message, type=type, timeout=timeout)
        else:
            ui.notify(message, type=type)
    except Exception:
        # Hors slot (timer/task): ignorer la notif, ce n'est pas critique
        pass


# ========================================
# SPINNERS D'ACTIVITÉ IA
# ========================================
def set_ia_working(active: bool = True) -> None:
    """Active/désactive le spinner d'activité de l'IA Principale (jaune)."""
    global _ia_status_indicators
    try:
        spinner = _ia_status_indicators.get('chat_spinner')
        print(f"[SPINNER] 🟡 IA Principale spinner={'ON' if active else 'OFF'} (spinner={spinner is not None})")
        if spinner:
            if active:
                spinner.style('display: inline-block;')
            else:
                spinner.style('display: none;')
            # Force la mise à jour UI immédiate (nécessaire en contexte async)
            spinner.update()
    except Exception as e:
        print(f"[SPINNER] Erreur set_ia_working: {e}")


def set_archiviste_working(active: bool = True) -> None:
    """Active/désactive le spinner d'activité de l'Archiviste (orange)."""
    global _ia_status_indicators
    try:
        spinner = _ia_status_indicators.get('archiviste_spinner')
        print(f"[SPINNER] 🟤 Archiviste spinner={'ON' if active else 'OFF'} (spinner={spinner is not None})")
        if spinner:
            if active:
                spinner.style('display: inline-block;')
            else:
                spinner.style('display: none;')
            # Force la mise à jour UI immédiate (nécessaire en contexte async)
            spinner.update()
        else:
            print(f"[SPINNER] ⚠️ archiviste_spinner non trouvé dans _ia_status_indicators")
    except Exception as e:
        print(f"[SPINNER] Erreur set_archiviste_working: {e}")


REMOTE_PROVIDERS = ['OpenAI', 'Mistral', 'Anthropic', 'Google', 'GROK', 'AIHorde']
LOCAL_BACKENDS = ['Ollama', 'GGUF', 'KoboldCpp']
EMBED_SUPPORTED_PROVIDERS = ['OpenAI', 'Mistral', 'Google']  # Anthropic: pas d'API embeddings à ce jour

# NOTA: _truncate_filename et _get_file_icon extraites vers utils/formatting_utils.py

def _update_header_display():
    """Met à jour l'affichage du header (sans les fichiers actifs)"""
    global _header_container, _active_file_data
    if _header_container is None:
        return
    
    try:
        _header_container.clear()
        
        with _header_container:
            # Le header n'affiche plus les fichiers actifs
            # Ils sont maintenant affichés sous la boîte de messagerie
            pass
    except Exception as e:
        print(f"[ERROR] Erreur update header: {e}")
        # Fallback silencieux si le client n'est plus disponible

def _update_file_tab_display():
    """Met à jour l'affichage de l'onglet fichier sous la boîte de messagerie"""
    global _file_tab_container, _active_file_data, _active_images
    if _file_tab_container is None:
        return
    
    try:
        _file_tab_container.clear()
        
        with _file_tab_container:
            # Affichage des images uploadées (miniatures)
            if _active_images:
                with ui.element('div').classes('images-tab-container').style(
                    'display: flex; gap: 8px; padding: 8px; background: var(--bg-tertiary); '
                    'border-radius: 8px; margin-bottom: 8px; align-items: center; flex-wrap: wrap;'
                ):
                    ui.label(f'🖼️ Images ({len(_active_images)}/{MAX_IMAGES})').style(
                        'color: var(--text-secondary); font-size: 12px; margin-right: 8px;'
                    )
                    
                    for idx, img_data in enumerate(_active_images):
                        with ui.element('div').style(
                            'position: relative; display: inline-block;'
                        ):
                            # Miniature de l'image
                            img_src = f"data:image/png;base64,{img_data.get('data', '')[:100]}..."
                            if img_data.get('data'):
                                img_src = f"data:image/png;base64,{img_data.get('data')}"
                            
                            ui.image(img_src).style(
                                'width: 30px; height: 30px; object-fit: cover; border-radius: 4px; '
                                'border: 1px solid var(--accent-gold);'
                            )
                            
                            # Numéro de l'image
                            ui.label(str(idx + 1)).style(
                                'position: absolute; bottom: 1px; left: 1px; background: rgba(0,0,0,0.7); '
                                'color: white; font-size: 8px; padding: 0px 2px; border-radius: 2px;'
                            )
                            
                            # Bouton supprimer
                            ui.button('✕', on_click=lambda i=idx: _remove_image(i)).style(
                                'position: absolute; top: -4px; right: -4px; width: 12px; height: 12px; '
                                'padding: 0; font-size: 8px; border-radius: 50%; background: #e74c3c; '
                                'color: white; border: none; cursor: pointer; line-height: 12px;'
                            ).props('flat dense')
                    
                    # Bouton ajouter si moins de 3 images
                    if len(_active_images) < MAX_IMAGES:
                        ui.upload(
                            on_upload=_process_uploaded_file,
                            auto_upload=True,
                            max_files=1
                        ).style(
                            'width: 30px; height: 30px;'
                        ).props('accept="image/*" flat dense').classes('add-image-btn')
                        
            # Affichage du fichier texte actif (comportement original)
            elif _active_file_data:
                # Affichage de l'onglet fichier sous la messagerie
                filename = _active_file_data.get('filename', 'Fichier inconnu')
                # Importées depuis utils.formatting_utils
                icon = get_file_icon(filename)
                truncated = truncate_filename(filename)
                
                with ui.element('div').classes('file-tab-container file-tab-bottom'):
                    with ui.element('div').classes('file-tab'):
                        ui.label(f"{icon} {truncated}").classes('file-tab-label')
                        ui.button('✕', on_click=_remove_active_file).classes('file-tab-close')
    except Exception as e:
        print(f"[ERROR] Erreur update file tab: {e}")

def _remove_image(index: int):
    """Supprime une image spécifique de la liste"""
    global _active_images
    if 0 <= index < len(_active_images):
        removed = _active_images.pop(index)
        filename = removed.get('filename', 'unknown')
        print(f"[IMAGES] ❌ Image {index + 1} supprimée: {filename}")
        _update_file_tab_display()
        try:
            ui.notify(f'Image {index + 1} supprimée', type='info')
        except RuntimeError:
            # Le slot parent a été supprimé lors de _update_file_tab_display
            print(f'[INFO] Image {index + 1} supprimée: {filename}')

def _remove_active_file():
    """Supprime le fichier actif (texte) et met à jour l'affichage"""
    global _active_file_data
    _active_file_data = None
    _update_file_tab_display()  # Met à jour l'onglet sous la messagerie
    try:
        ui.notify('Fichier supprimé de la conversation', type='info')
    except:
        print('[INFO] Fichier supprimé de la conversation')

def _clear_all_active_images():
    """Supprime toutes les images actives"""
    global _active_images
    _active_images = []
    _update_file_tab_display()
    try:
        ui.notify('Images supprimées de la conversation', type='info')
    except:
        print('[INFO] Images supprimées de la conversation')

async def _process_uploaded_file(upload_event):
    """Traite un fichier uploadé et l'active dans la conversation"""
    global _active_file_data, _active_images
    
    try:
        # Importer le processeur de fichier
        from extensions.file_processor import process_file
        from pathlib import Path
        import shutil
        
        # Créer un chemin temporaire
        temp_path = Path(DATA_DIR) / "uploads" / f"temp_{uuid.uuid4()}_{upload_event.name}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier temporaire
        with open(temp_path, 'wb') as f:
            f.write(upload_event.content.read())
        
        # Traiter le fichier
        file_data = process_file(temp_path)
        
        if file_data:
            # Vérifier si c'est une image
            is_image = file_data.get('type') == 'image' or file_data.get('base64_image')
            
            if is_image:
                # Mode multi-images pour les images
                if len(_active_images) >= MAX_IMAGES:
                    ui.notify(f'Maximum {MAX_IMAGES} images atteint. Supprimez une image d\'abord.', type='warning')
                    print(f'[WARNING] Maximum {MAX_IMAGES} images déjà uploadées')
                    return
                
                # Ajouter à la liste des images
                _active_images.append(file_data)
                # Différer le refresh pour éviter l'erreur "parent element deleted"
                ui.timer(0.1, lambda: _update_file_tab_display(), once=True)
                print(f'[SUCCESS] Image "{upload_event.name}" ajoutée ({len(_active_images)}/{MAX_IMAGES})')
                ui.notify(f'Image {len(_active_images)}/{MAX_IMAGES} ajoutée', type='positive')
            else:
                # Fichier texte - remplace le précédent comme avant
                _active_file_data = file_data
                ui.timer(0.1, lambda: _update_file_tab_display(), once=True)
                print(f'[SUCCESS] Fichier "{upload_event.name}" ajouté à la conversation')
        else:
            print('[ERROR] Erreur lors du traitement du fichier')
            
    except Exception as e:
        print(f"[ERROR] Erreur upload fichier: {e}")

def _show_file_upload_dialog():
    """Affiche la popup d'upload de fichier"""
    with ui.dialog().classes('popup-overlay') as dialog:
        with ui.card().classes('popup-content'):
            ui.html('<div class="popup-title">📎 Ajouter un fichier</div>')
            
            ui.label('Formats supportés: PDF, DOCX, TXT, MD, JSON, Images (JPG, PNG, WebP, GIF)').classes('text-sm text-gray-400 mb-4')
            
            # Zone d'upload
            with ui.element().style('border: 2px dashed #4a4a4a; border-radius: 8px; padding: 40px; text-align: center; margin: 20px 0;'):
                ui.label('Glissez-déposez votre fichier ici ou cliquez pour sélectionner').classes('text-gray-400')
                upload_area = ui.upload(
                    on_upload=lambda e: _handle_upload_and_close(e, dialog),
                    multiple=False,
                    max_file_size=10*1024*1024  # 10MB max
                ).classes('mt-4')
            
            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Annuler', on_click=dialog.close).classes('action-button')
    
    dialog.open()

async def _handle_upload_and_close(upload_event, dialog):
    """Traite l'upload et ferme le dialog"""
    await _process_uploaded_file_and_close(upload_event, dialog)

async def _process_uploaded_file_and_close(upload_event, dialog):
    """Traite l'upload de façon asynchrone et ferme le dialog"""
    await _process_uploaded_file(upload_event)
    dialog.close()

# ==============================================================================
# EXTENSIONS UI - Importées depuis ogma_extensions_ui.py (REFACTORING)
# ==============================================================================
from ogma_extensions_ui import (
    _initialize_biography_extension,
    _initialize_journal_extension,
    _inject_journal_header_button,
    _inject_journal_context,
    _create_header_journal_button,
    _create_header_journal_button_inline,
    _create_header_biography_button_inline,
    get_biography_available,
    get_journal_available,
    get_journal_instance,
    set_globals as set_extensions_ui_globals,
    BIOGRAPHY_EXTENSION_AVAILABLE as _EXT_BIOGRAPHY_AVAILABLE
)

# JOURNAL DE BORD EXTENSION - Variables globales (synchronisées avec module)
_journal_instance = None
_journal_available = False

# BIOGRAPHIE PROFIL EXTENSION - Variables globales (synchronisées avec module)
_biography_manager = None
_biography_ui = None
_biography_available = False

def _sync_extensions_ui_globals():
    """Synchronise les globals avec le module ogma_extensions_ui"""
    set_extensions_ui_globals(
        _ensure_settings_manager(),
        _memory_manager,
        _chat_controller,
        _archiviste_controller,
        _status_queue
    )

def _status_dot(initial='var(--text-muted)'):
    el = ui.element('div').classes('cyber-dot').style(f'width:10px; height:10px; border-radius:50%; background:{initial}; border:1px solid rgba(0,212,245,0.2);')
    return el


# ==============================================================================
# IMAGE MODAL - Importée depuis ogma_image_config.py (REFACTORING)
# ==============================================================================
from ogma_image_config import _image_modal as _image_modal_impl, set_settings_manager_getter as _set_image_config_sm

# Configurer le getter pour le settings manager
_set_image_config_sm(_ensure_settings_manager)

def _image_modal():
    """Fenêtre de configuration génération d'images - Déléguée au module ogma_image_config.py"""
    return _image_modal_impl()


# Fonction _perception_modal supprimée - l'overlay a été remplacé par :
# - Section simple dans les paramètres généraux
# - Utilisation directe de _perception_settings_modal pour le bouton header


# FONCTION DÉPLACÉE - Voir ogma_tts_config.py
# _render_tts_config: 604 lignes déplacées vers ogma_tts_config.py pour spécialisation


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
    
    print(f"[CONV-CMD] Appel avec texte: '{text[:100]}...'")
    
    # Debug: vérifier si les imports fonctionnent
    try:
        # Test des imports
        if not hasattr(archive, 'load_conversation'):
            print("[CONV-CMD] Erreur: Module archive non initialisé correctement")
            _notify_safe("ERROR Module archive non initialisé correctement", 'negative')
            return True
    except NameError:
        print("[CONV-CMD] Erreur: Module archive non trouvé")
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
    
    print(f"[CONV-CMD] Test {len(natural_patterns)} patterns...")
    for i, pattern in enumerate(natural_patterns):
        match = re.search(pattern, text_lower)
        if match:
            print(f"[CONV-CMD] Pattern {i} MATCH: {pattern}")
            filename = match.group(1).strip()
            if not filename.endswith('.json'):
                filename += '.json'
            
            print(f"[CONV-CMD] Fichier extrait: {filename}")
            _notify_safe(f"SEARCH Détection automatique: chargement de {filename}", 'info')
            
            try:
                print(f"[CONV-CMD] Appel archive.load_conversation('{filename}')...")
                conversation = await archive.load_conversation(filename)
                print(f"[CONV-CMD] Conversation chargée: {conversation is not None}, len={len(conversation) if conversation else 0}")
                
                if conversation:
                    # Charger la conversation dans le contexte global pour l'IA
                    print(f"[CONV-CMD] Mise à jour variables globales...")
                    _loaded_conversation = conversation
                    _loaded_conversation_filename = filename
                    
                    print(f"[CONV-CMD] Appel _display_conversation_as_attachment...")
                    await _display_conversation_as_attachment(filename, conversation)
                    print(f"[CONV-CMD] Affichage terminé, return False (continue vers IA)")
                    
                    # L'IA va maintenant traiter la demande avec la conversation chargée
                    # On ne return pas True pour laisser l'IA répondre
                    return False  # Continue vers l'IA avec le contexte chargé
                else:
                    print(f"[CONV-CMD] Conversation NULL, return True (stop)")
                    _notify_safe(f"ERROR Conversation non trouvée: {filename}", 'negative')
                    return True
            except Exception as e:
                print(f"[CONV-CMD] EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
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


# ================= STOP / INTERRUPTION =================

async def _request_stop():
    """Demande l'arrêt de l'opération en cours (streaming, génération d'image, TTS, etc.)"""
    from stop_signal import request_stop
    request_stop()
    print("[STOP] 🛑 Arrêt demandé par l'utilisateur")
    
    # Stopper le TTS immédiatement
    try:
        from audio_manager_wrapper import get_audio_manager
        audio_mgr = get_audio_manager()
        if audio_mgr:
            if hasattr(audio_mgr, 'stop_speaking'):
                audio_mgr.stop_speaking()
                print("[STOP] ⏹️ TTS stoppé")
            elif hasattr(audio_mgr, 'tts_safe') and audio_mgr.tts_safe:
                audio_mgr.tts_safe.stop_current_speech()
                print("[STOP] ⏹️ TTS stoppé (via tts_safe)")
    except Exception as e:
        print(f"[STOP] ⚠️ Erreur stop TTS: {e}")
    
    try:
        ui.notify('⏹️ Arrêt demandé...', type='warning', timeout=2000)
    except:
        pass
    # Feedback visuel sur le bouton
    if _stop_button_ref:
        try:
            _stop_button_ref.props('color=negative')
            await asyncio.sleep(0.3)
            _stop_button_ref.props('color=')
        except:
            pass


async def _execute_conversation_scanner(user_message: str, keywords: Optional[List[str]] = None) -> Optional[str]:
    """
    🔍 Scanne les conversations récentes pour trouver des keywords
    
    Args:
        user_message: Message de l'utilisateur (pour génération keywords si nécessaire)
        keywords: Liste mots-clés à chercher (optionnel, sinon génération automatique)
        
    Returns:
        Contexte formaté pour injection dans messages système, ou None si pas de résultats
    """
    try:
        from conversation_scanner import search_recent_conversations, format_results_for_injection
        
        # Si pas de keywords fournis, l'IA principale les génère
        if not keywords:
            print("[CONV-SCANNER] 🧠 Génération automatique des keywords...")
            
            keyword_prompt = f"""Analyse cette demande et extrait 2-5 mots-clés pertinents pour chercher dans l'historique de conversations.

Demande utilisateur: "{user_message}"

RÈGLES:
- Noms de personnes en MAJUSCULES (ex: BOB, CASPER)
- Mots-clés précis et courts
- Pas de mots vides (le, la, tu, de, etc)
- Maximum 5 mots-clés

Réponds UNIQUEMENT la liste séparée par des virgules.
Exemple: BOB, vol, PC, Utilisateur"""
            
            controller = _ensure_chat_controller()
            if not controller:
                print("[CONV-SCANNER] ❌ Chat controller non disponible")
                return None
            
            keywords_response, kw_error = await controller.call_chat_api(
                messages=[{'role': 'user', 'content': keyword_prompt}],
                max_tokens=50,
                context_length=controller.context_length if hasattr(controller, 'context_length') else 128000,
                temperature=0.3,  # Précis
                is_json=False
            )
            
            if not keywords_response or kw_error:
                print(f"[CONV-SCANNER] ❌ Erreur génération keywords: {kw_error}")
                return None
            
            # Parser keywords
            keywords = [kw.strip().strip('"\'') for kw in keywords_response.split(',')]
            keywords = [kw for kw in keywords if kw and len(kw) > 1][:5]
            
            if not keywords:
                print("[CONV-SCANNER] ⚠️ Aucun keyword valide généré")
                return None
        
        print(f"[CONV-SCANNER] 🎯 Keywords: {keywords}")
        
        # Rechercher dans les 20 dernières conversations
        results = search_recent_conversations(
            keywords=keywords,
            max_conversations=20,
            context_size=5,  # Contexte élargi (5 messages avant/après)
            max_results=10,
            debug=True
        )
        
        if not results:
            print("[CONV-SCANNER] ⚠️ Aucun résultat trouvé")
            return None
        
        print(f"[CONV-SCANNER] ✅ {len(results)} résultat(s) trouvé(s)")
        
        # Formater pour injection
        search_context = format_results_for_injection(
            results=results,
            keywords=keywords,
            max_results_display=3,
            max_chars_per_message=150
        )
        
        print(f"[CONV-SCANNER] 📝 Contexte généré: {len(search_context)} chars")
        return search_context
    
    except ImportError:
        print("[CONV-SCANNER] ⚠️ Module conversation_scanner non disponible")
        return None
    except Exception as e:
        print(f"[CONV-SCANNER] ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


async def _send_chat_message(input_el=None, text_override: Optional[str] = None, skip_history_append: bool = False):
    global _chat_history, _chat_history_ui, _chat_inner, _pending_notifications, _editing_message_index, _pending_behavioral_injections, _journal_preformed_response, _current_user_name, _user_authenticated, _streaming_widget_ref, _streaming_container_ref, _streaming_html_ref, _active_images, _repr_images_for_i2i, _enriched_i2i_prompt
    import re  # Import au début pour éviter UnboundLocalError
    
    # ═══════════════════════════════════════════════════════════════════
    # FONCTIONS LOCALES D'EXTRACTION (définies tôt pour éviter UnboundLocalError)
    # ═══════════════════════════════════════════════════════════════════
    def _extract_magic_memories(s: str) -> List[str]:
        if not s:
            return []
        patterns = [
            # Texte long ou multi-paragraphes encadré de guillemets (" ou «»)
            r'(?:\*\*|__)?il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*[«"\u201c]([\s\S]+?)[»"\u201d]',
            # Cas standard : contenu court sur une ou quelques lignes (sans guillemets)
            r"(?:\*\*|__)?il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
            r"(?:\*\*|__)?m[ée]morise(?:s)?\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
        ]
        results: List[str] = []
        for pat in patterns:
            found = re.findall(pat, s, flags=re.IGNORECASE | re.DOTALL)
            if found:
                print(f"[MAGIC-DEBUG] Match trouvé avec pattern {pat}: {found}")
            for m in found:
                content = m.strip()
                if content:
                    content = re.sub(r'^[:\-\s\.]+', '', content)
                    content = re.sub(r'(\*\*|__)$', '', content).strip()
                    content = re.sub(r'</?[A-ZÉÈÊa-zéèê_]+>', '', content).strip()
                    if content:
                        results.append(content)
        return results

    def _extract_organic_events(s: str) -> List[Dict]:
        """Extrait les évènements pour l'Organic Planner"""
        if not s:
            return []
        patterns = [
            r"il\s+faut\s+que\s+(?:je|tu)\s+note\s+(?:cet|cette)\s+(?:évènement|evenement)\s*[:\-]\s*(.+?)\s*-\s*(.+?)\s*-\s*(.+?)\s*(?=$|\n|\r)",
            r"(?:note\s+cet\s+évènement|ajoute\s+à\s+l'agenda)\s*[:\-]\s*(.+?)\s*-\s*(.+?)\s*-\s*(.+?)\s*(?=$|\n|\r)"
        ]
        results = []
        seen = set()
        for pattern in patterns:
            matches = re.findall(pattern, s, flags=re.IGNORECASE | re.MULTILINE)
            for m in matches:
                if len(m) == 3:
                    date = m[0].strip()
                    title = m[1].strip()
                    feeling = m[2].strip()
                    key = (date.lower(), title.lower(), feeling.lower())
                    if key not in seen:
                        seen.add(key)
                        results.append({'date': date, 'title': title, 'feeling': feeling})
                    else:
                        print(f"[ORGANIC-PLANNER] Doublon evite: {title} ({date})")
        return results

    def _extract_organic_updates(s: str) -> List[Dict]:
        """Extrait les mises à jour de statut pour l'Organic Planner"""
        if not s:
            return []
        pattern = r"il\s+faut\s+que\s+(?:je|tu)\s+mette\s+à\s+jour\s+(?:l'|cet\s+)(?:évènement|evenement)\s*[:\-]\s*(.+?)\s*-\s*(.+?)\s*(?=$|\n|\r)"
        matches = re.findall(pattern, s, flags=re.IGNORECASE | re.MULTILINE)
        results = []
        for m in matches:
            if len(m) == 2:
                status_raw = m[1].strip().upper()
                status_map = {
                    'TERMINÉ': 'TERMINE', 'TERMINE': 'TERMINE', 'FINI': 'TERMINE', 'COMPLÉTÉ': 'TERMINE',
                    'EN COURS': 'EN_COURS', 'ACTIF': 'EN_COURS',
                    'À FAIRE': 'EN_ATTENTE', 'EN ATTENTE': 'EN_ATTENTE', 'PAS COMMENCÉ': 'EN_ATTENTE'
                }
                status = status_map.get(status_raw, status_raw)
                results.append({'title': m[0].strip(), 'status': status})
        return results

    def _strip_magic_phrases(s: str) -> str:
        if not s:
            return s
        pattern = (
            r"(?:"
            r"(?:\*\*|__)?il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*.+?(?=\n\n|\n\s*\n|$)"
            r"|(?:\*\*|__)?m[ée]morise(?:s)?\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*.+?(?=\n\n|\n\s*\n|$)"
            r"|il\s+faut\s+que\s+(?:je|tu)\s+note\s+(?:cet|cette)\s+(?:évènement|evenement)\s*[:\-]\s*.+?\s*-\s*.+?\s*-\s*.+?(?=$|\n|\r)"
            r"|note\s+cet\s+évènement\s*[:\-]\s*.+?\s*-\s*.+?\s*-\s*.+?(?=$|\n|\r)"
            r"|ajoute\s+à\s+l'agenda\s*[:\-]\s*.+?\s*-\s*.+?\s*-\s*.+?(?=$|\n|\r)"
            r"|il\s+faut\s+que\s+(?:je|tu)\s+mette\s+à\s+jour\s+(?:l'|cet\s+)(?:évènement|evenement)\s*[:\-]\s*.+?\s*-\s*.+?(?=$|\n|\r)"
            r"|il\s+faut\s+que\s+je\s+(?:te\s+)?vois"
            r"|je\s+veux\s+te\s+voir"
            r"|je\s+n'ai\s+plus\s+besoin\s+de\s+te\s+voir"
            r"|je\s+(?:peux|vais)\s+arrêter\s+de\s+te\s+(?:voir|regarder)"
            r"|je\s+ferme\s+(?:ma\s+)?vision"
            r"|je\s+coupe\s+(?:ma\s+)?caméra"
            r")"
        )
        return re.sub(pattern, "", s, flags=re.IGNORECASE).strip()

    # ═══════════════════════════════════════════════════════════════════
    
    # 🛑 STOP: Reset flag à chaque nouveau message
    from stop_signal import reset_stop
    reset_stop()
    
    # 🌙 DREAM ENGINE: Réinitialiser timer inactivité + sursaut si rêve en cours
    _was_dreaming = False  # Flag pour savoir si on vient d'un réveil
    try:
        from extensions.dream_engine import is_dreaming, wake_up, is_available as dream_available
        from extensions.dream_engine.dream_ui import reset_inactivity_timer
        
        if dream_available():
            # Réinitialiser le timer d'inactivité
            reset_inactivity_timer()
            
            # Si l'IA principale rêve, la réveiller (sursaut) et ATTENDRE l'affichage du message de réveil
            if is_dreaming():
                print("[DREAM-ENGINE] ⚡ Sursaut détecté - utilisateur actif!")
                _was_dreaming = True
                wake_result = await wake_up("user_message")
                if wake_result.get('was_dreaming'):
                    duration = wake_result.get('sleep_duration_formatted', 'N/A')
                    print(f"[DREAM-ENGINE] ☀️ l'IA principale réveillée après {duration} de sommeil")
                    # Resynchroniser l'apparence du bouton header
                    try:
                        from extensions.dream_engine.dream_ui import update_dream_header_btn
                        update_dream_header_btn(False)
                    except Exception:
                        pass
                    # Petit délai pour laisser l'UI se mettre à jour (utilise le module global asyncio)
                    await asyncio.sleep(0.5)
    except ImportError:
        pass  # Extension non installée
    except Exception as e:
        print(f"[DREAM-ENGINE] ⚠️ Erreur hook: {e}")
    
    # 📓 JOURNAL: Imports globaux fonction pour éviter UnboundLocalError
    try:
        from extensions.journal_de_bord import hook_message_exchange
        from ogma_extensions_ui import get_journal_available as journal_available_check
    except ImportError as e:
        print(f"[JOURNAL-IMPORT] ⚠️ Import error: {e}")
        hook_message_exchange = None
        journal_available_check = None
    
    # 🛡️ CAPTURE DU CLIENT (Anti Slot Stack Error)
    try:
        client = _chat_inner.client if _chat_inner else None
    except RuntimeError:
        # Client déconnecté - skip envoi message
        print("[CHAT] ℹ️ Client déconnecté - skip envoi message")
        return
    
    # 📋 INITIALISATION DES MESSAGES (Scope global à la fonction)
    messages: List[Dict] = []
    
    # �️ TRACKING ACTIVITÉ: Signaler que l'utilisateur est actif
    try:
        from nicegui import context
        client_id = client.id if client else (context.client.id if hasattr(context, 'client') else None)
        if client_id:
            track_client_activity(client_id)
    except Exception:
        pass  # Silencieux si échec
    
    # �🔇 TTS: Arrêter la lecture en cours si nouveau message
    if _audio_manager:
        try:
            # Arrêter la lecture en cours
            if hasattr(_audio_manager, 'stop_speaking'):
                _audio_manager.stop_speaking()
            # Vider la queue TTS
            if hasattr(_audio_manager, 'tts_safe') and _audio_manager.tts_safe:
                tts = _audio_manager.tts_safe
                # Vider la queue
                while not tts.speech_queue.empty():
                    try:
                        tts.speech_queue.get_nowait()
                    except:
                        break
            # Reset le buffer de streaming
            if hasattr(_audio_manager, 'reset_streaming'):
                _audio_manager.reset_streaming()
            print("[TTS] 🔇 Lecture arrêtée pour nouveau message")
        except Exception as e:
            print(f"[TTS] ⚠️ Erreur arrêt TTS: {e}")
    
    # ✨ COOLDOWN: Incrémenter compteur messages (Option A - 27 nov 2025)
    from injection_deduplicator import increment_message_count
    increment_message_count()
    
    # 🚨 DÉDUPLICATION: Réinitialiser la session si c'est un nouveau chat
    if not _chat_history:
        reset_deduplication_session()
        print(f"[DEDUP] 🔄 Session de déduplication réinitialisée")

    # 🎯 CAPABILITY ADVISOR: Éteindre toutes les LEDs allumées au NOUVEAU message utilisateur
    try:
        advisor = _ensure_capability_advisor()
        print(f"[CAPABILITY-ADVISOR-DEBUG] Advisor instance: {advisor is not None}")
        if advisor and advisor.is_enabled():
            print(f"[CAPABILITY-ADVISOR-DEBUG] Extension activée")
            all_led_states = advisor.led_manager.get_all_led_states()
            print(f"[CAPABILITY-ADVISOR-DEBUG] États LEDs: {all_led_states}")
            active_leds = [cap_id for cap_id, state in all_led_states.items() if state]
            print(f"[CAPABILITY-ADVISOR-DEBUG] LEDs actives trouvées: {active_leds}")
            if active_leds:
                print(f"[CAPABILITY-ADVISOR] 💡 Extinction LEDs actives au message suivant: {active_leds}")
                for cap_id in active_leds:
                    advisor.led_manager.deactivate_led(cap_id)
            else:
                print(f"[CAPABILITY-ADVISOR-DEBUG] Aucune LED active à éteindre")
    except Exception as e:
        print(f"[CAPABILITY-ADVISOR] ⚠️ Erreur extinction LEDs: {e}")
        import traceback
        traceback.print_exc()

    # Utiliser text_override si fourni (pour édition), sinon lire input_el
    if text_override:
        text = text_override.strip()
    elif input_el:
        text = (input_el.value or '').strip()
    else:
        print(f"[SEND-CHAT-DEBUG] Ni input_el ni text_override fournis, return")
        return

    print(f"[SEND-CHAT-DEBUG] _send_chat_message appelée avec: '{text}' (override={text_override is not None}, editing_index={_editing_message_index})")
    if not text:
        print(f"[SEND-CHAT-DEBUG] Texte vide, return")
        return

    # MODE ÉDITION: Si _editing_message_index est défini, on édite un message existant
    was_editing = False
    if _editing_message_index is not None:
        try:
            print(f"[EDIT-MESSAGE] 🔄 MODE ÉDITION DÉTECTÉ - Message #{_editing_message_index}")

            # 1. Supprimer le message édité ET tous ceux après
            _chat_history = _chat_history[:_editing_message_index]
            print(f"[EDIT-MESSAGE] 🗑️ Messages #{_editing_message_index} et suivants supprimés, historique réduit à {len(_chat_history)} messages")

            # 2. Marquer qu'on était en mode édition pour réaffichage complet
            was_editing = True

            # 3. Réinitialiser l'index d'édition
            _editing_message_index = None

            # 4. Continuer avec l'envoi normal du nouveau message
            print(f"[EDIT-MESSAGE] ✅ Passage à l'envoi du nouveau message")

        except Exception as e:
            print(f"[EDIT-MESSAGE] ❌ Erreur édition: {e}")
            import traceback
            traceback.print_exc()
            _editing_message_index = None

    # Variables pour contexte IA enrichi
    is_automatic_introspection = False

    # Mode automatique supprimé (always → autonomous via Capability Advisor)
    is_automatic_introspection = False

    # 🎨 PHRASE MAGIQUE: Restructuration guide i2i
    _i2i_enrich_patterns = [
        "enrichis ton instruction d'image",
        "enrichis ton instruction d image",
        "restructure ton guide i2i",
        "ameliore ton instruction d'image",
        "optimise ton instruction d'image",
    ]
    # Normaliser les apostrophes typographiques vers apostrophes droites pour matching
    _text_lower = text.lower().strip().replace("'", "'").replace("'", "'").replace("`", "'")
    if any(p in _text_lower for p in _i2i_enrich_patterns):
        print(f"[I2I-MAGIC] Phrase magique detectee: restructuration guide i2i")
        try:
            from modules.logic.i2i_lessons import restructure_i2i_guide
            _chat_ctrl = _ensure_chat_controller()
            _sm = _ensure_settings_manager()
            
            # Extraire contexte conversation recent (5 derniers messages)
            _conv_ctx = ""
            if _chat_history and len(_chat_history) > 0:
                recent = _chat_history[-10:]  # 5 paires user/assistant
                _conv_ctx = "\n".join(
                    f"{'User' if m.get('role') == 'user' else 'IA'}: {str(m.get('content', ''))[:200]}"
                    for m in recent if isinstance(m.get('content'), str)
                )
            
            _notify_safe("Restructuration du guide i2i en cours...", 'ongoing', timeout=60)
            result = await restructure_i2i_guide(_chat_ctrl, _sm, _conv_ctx)
            
            if result.get('success'):
                _new_guide = result['new_guide']
                _n_lessons = result['lessons_used']
                _notify_safe(f"Guide i2i restructure ({_n_lessons} lecons integrees)", 'positive', timeout=8)
                # Utiliser le pattern preformed_response (comme journal de bord)
                _journal_preformed_response = (
                    f"**Guide i2i restructure !** ({_n_lessons} lecons integrees)\n\n"
                    f"Le guide a ete reecrit et sauvegarde automatiquement.\n"
                    f"Tu peux le voir dans **Parametres > Image > Guide img2img**.\n\n"
                    f"*Apercu ({len(_new_guide)} chars):*\n```\n{_new_guide[:500]}...\n```"
                )
                print(f"[I2I-MAGIC] Guide restructure avec succes, {_n_lessons} lecons")
            else:
                _err = result.get('error', 'Erreur inconnue')
                _notify_safe(f"{_err}", 'warning', timeout=8)
                _journal_preformed_response = f"Impossible de restructurer le guide: {_err}"
                print(f"[I2I-MAGIC] Echec restructuration: {_err}")
        except Exception as e:
            print(f"[I2I-MAGIC] Erreur restructuration: {e}")
            import traceback
            traceback.print_exc()
            _notify_safe(f"Erreur restructuration: {e}", 'negative', timeout=8)

    # JOURNAL JOURNAL DE BORD: Détection phrases magiques
    # 🔧 FIX: Utiliser get_journal_available() pour récupérer l'état depuis ogma_extensions_ui
    journal_is_available = get_journal_available()
    print(f"[SEND-CHAT-DEBUG] Section journal: _journal_available = {journal_is_available}")
    try:
        if journal_is_available:
            print(f"[SEND-CHAT-DEBUG] Appel journal magic phrases...")
            from extensions.journal_de_bord import get_journal
            journal = get_journal()

            # Vérifier si c'est une phrase magique
            magic_response = await journal.entry_generator.handle_magic_phrases(
                text,
                journal.json_manager
            )
            print(f"[SEND-CHAT-DEBUG] Journal magic_response = {magic_response}")

            if magic_response:
                print(f"[JOURNAL-EXTENSION] SPARKLE Phrase magique traitée")
                print(f"[SEND-CHAT-DEBUG] Journal a intercepté le message, return prématuré")
                # Vérifier si c'est une erreur avant d'afficher
                if magic_response.startswith("ERREUR"):
                    print(f"[JOURNAL-EXTENSION] ERROR dans réponse: {magic_response}")
                    # Ne pas intercepter les erreurs, laisser passer à l'IA normale
                else:
                    # SOLUTION ROBUSTE: Injecter la réponse journal comme réponse IA prédéfinie
                    # au lieu d'essayer de contourner le système d'affichage
                    _journal_preformed_response = magic_response
                    print(f"[JOURNAL-EXTENSION] REDIRECT Réponse sauvegardée pour injection IA")
                    
                    # Continuer le flux normal mais avec réponse prédéfinie
                    # La réponse sera injectée plus tard dans le processus

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur traitement phrase magique: {e}")

    # 📖 BIOGRAPHIE PROFIL: Détection phrases magiques et injection automatique
    # 🔧 FIX: Utiliser get_biography_available() pour récupérer l'état depuis ogma_extensions_ui
    biography_is_available = get_biography_available()
    print(f"[BIOGRAPHY-DEBUG] Début détection phrase magique pour: '{text}'")
    print(f"[BIOGRAPHY-DEBUG] _biography_available = {biography_is_available}")
    try:
        if biography_is_available:
            print(f"[BIOGRAPHY-DEBUG] Extension disponible, import...")
            from extensions.biographie_profil import get_biography_magic_phrases
            biography_magic = get_biography_magic_phrases()
            print(f"[BIOGRAPHY-DEBUG] biography_magic = {biography_magic}")

            if biography_magic:
                print(f"[BIOGRAPHY-DEBUG] Appel handle_magic_phrases...")
                # Vérifier si c'est une phrase magique utilisateur (mise à jour)
                # 🎯 NOUVEAU: Passer _chat_history pour déduplication anti-redondance
                magic_response = await biography_magic.handle_magic_phrases(
                    text, 
                    is_ai_message=False,
                    conversation_history=_chat_history  # Déduplication intelligente
                )
                print(f"[BIOGRAPHY-DEBUG] magic_response = {magic_response}")

                if magic_response:
                    content = magic_response.get('content', '')
                    response_type = magic_response.get('type', 'display')

                    if response_type == 'display':
                        print(f"[BIOGRAPHY-EXTENSION] ✨ Phrase magique utilisateur traitée - affichage")
                        # Afficher la réponse dans le bon contexte UI
                        if _chat_inner is not None:
                            with _chat_inner:
                                _message('assistant', content)
                        if input_el and not text_override:
                            input_el.value = ''
                        return
                    elif response_type == 'inject':
                        print(f"[BIOGRAPHY-EXTENSION] 🔄 Injection automatique biographie détectée")
                        # 🚀 FIX: Stocker directement pour injection dans ai_content (ligne 3648)
                        # Sera utilisé plus bas dans le workflow au lieu de double appel
                        biography_context_early = content

    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ERROR Erreur traitement phrase magique: {e}")

    # 📝 FILE WRITER: Détection précoce demande /doc pour injection instruction markdown
    is_doc_request = False
    try:
        # Utiliser le detector directement pour éviter dépendance à l'initialisation de l'agent
        from extensions.file_writer.request_detector import RequestDetector
        doc_detector = RequestDetector(debug=False)
        detection = doc_detector.detect(text)
        if detection.is_request:
            is_doc_request = True
            print(f"[FILE-WRITER] 📝 Demande /doc détectée (confidence: {detection.confidence}) - instruction markdown sera injectée")
    except Exception as e:
        print(f"[FILE-WRITER] ⚠️ Erreur détection /doc: {e}")

    # 🧠 COGNITIVE MIRROR v2.0: Détection déclenchement introspection
    try:
        print(f"[INTROSPECTION] 🔍 Vérification: '{text[:50]}...' (auto={is_automatic_introspection})")

        if COGNITIVE_MIRROR_AVAILABLE:
            from extensions.cognitive_mirror import is_enabled, get_introspection_config
            
            # Phrases magiques d'introspection (utilisateur) - TOUJOURS vérifier
            introspection_patterns = [
                r"il\s+faut\s+que\s+tu\s+réfléchisses",
                r"lance\s+(?:une\s+)?introspection",
                r"déclenche\s+(?:une\s+)?introspection",
                r"réfléchis\s+(?:en\s+profondeur|à|sur|profondément)?",
                r"introspection"
            ]

            is_magic_phrase_trigger = any(re.search(pattern, text, re.IGNORECASE) for pattern in introspection_patterns)
            
            # Mode on_demand: phrase magique suffit à déclencher
            # Mode always + enabled: déclenche automatiquement
            config = get_introspection_config()
            mode = config.get_introspection_mode() if config else "on_demand"
            extension_on = is_enabled()
            
            # Déclenchement si extension activée ET (Phrase magique OU mode automatique)
            extension_on = is_enabled()
            is_introspection_trigger = extension_on and (is_magic_phrase_trigger or is_automatic_introspection)
            
            print(f"[INTROSPECTION] 📊 Phrase magique: {is_magic_phrase_trigger}, Mode Auto: {is_automatic_introspection}, Extension ON: {extension_on}")

            if is_introspection_trigger:
                trigger_type = "phrase magique" if is_magic_phrase_trigger else "mode automatique"
                print(f"[INTROSPECTION] 🧠 Déclenchement par {trigger_type} - mode introspection v2.1")

                # 1. Ajouter message utilisateur aux deux historiques
                msg = {'role': 'user', 'content': text}
                _chat_history.append(msg)
                _chat_history_ui.append(msg)

                # 2. Afficher message utilisateur
                with _chat_inner:
                    _message('user', text)

                # 3. Afficher message système
                with _chat_inner:
                    _message('system', "🧠 **IA Principale entre en introspection...** Dialogue avec l'Archiviste en cours.")

                # 4. Construire contexte ENRICHI pour introspection
                from utils import get_ego_summary_from_compiled
                
                # Récupérer ego summary depuis ego_compiled.json (système boolean)
                try:
                    current_ego_prompt = get_ego_summary_from_compiled(max_chars=200)
                except Exception as e:
                    print(f"[INTROSPECTION] ⚠️ Erreur récupération ego: {e}")
                    current_ego_prompt = "Ego non disponible"
                
                # NOUVEAU: Récupération identités dynamiques
                from identity_manager import get_current_identities
                identities = get_current_identities()
                
                # Récupérer plus d'historique (20 messages au lieu de 10)
                extended_history = _chat_history[-20:] if len(_chat_history) > 20 else _chat_history
                
                conversation_context = {
                    'user_message': text,
                    'chat_history': extended_history,
                    'user_identity': identities['user_identity'],
                    'ego_prompt': current_ego_prompt,
                    'main_ai_identity': identities['main_ai_identity'],
                    'relationship_context': identities['relationship_context']
                }

                # 5. Créer la boîte thinking AVANT (pour affichage temps réel)
                global _introspection_box_content, _introspection_md_widget
                _introspection_box_content = []

                with _chat_inner:
                    with ui.expansion(value=True).classes('thinking-expansion') as introspection_box:
                        introspection_box.props('label=""')
                        with introspection_box.add_slot('header'):
                            ui.html('<span style="color: rgba(255, 200, 100, 0.7); font-size: 12px; font-style: italic;">🧠 introspection ia-principale-archiviste</span>')

                        _introspection_md_widget = ui.markdown("_Dialogue en cours..._")
                        _introspection_md_widget.style(
                            'color: rgba(255, 255, 255, 0.85); '
                            'font-size: 13px; '
                            'line-height: 1.5; '
                            'margin: 0; '
                            'padding: 8px 0; '
                            'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'
                        )
                        
                        # CSS personnalisé pour formater la conversation introspection
                        ui.add_head_html('''
                        <style>
                        /* Style pour les noms d'intervenants en gras */
                        .introspection-dialogue strong {
                            color: rgba(255, 200, 100, 0.9) !important;
                            font-weight: 600 !important;
                            font-size: 13px !important;
                        }
                        
                        /* Espacement entre les interventions */
                        .introspection-dialogue p {
                            margin-bottom: 8px !important;
                            margin-top: 4px !important;
                        }
                        
                        /* Séparateur entre sections */
                        .introspection-dialogue hr {
                            border: none;
                            height: 1px;
                            background: rgba(255, 255, 255, 0.2);
                            margin: 12px 0;
                        }
                        
                        /* Style général du contenu */
                        .introspection-dialogue {
                            font-style: normal !important;
                        }
                        </style>
                        ''')
                        _introspection_md_widget.classes('introspection-dialogue')

                # 6. Lancer introspection (v2.1 ou v2.0)
                try:
                    from extensions.cognitive_mirror import get_introspection, is_v21
                    introspection_core = get_introspection()
                    
                    if introspection_core:
                        # v2.1 utilise run_introspection, v2.0 utilise trigger_introspection_sync
                        if is_v21():
                            print("[INTROSPECTION] 🚀 Lancement v2.1 (Conscient↔Inconscient)")
                            
                            # Configurer callback pour affichage temps réel
                            dialogue_messages = []
                            
                            def on_introspection_message(step: int, role: str, content: str):
                                """Callback pour afficher les messages en temps réel"""
                                global _introspection_md_widget
                                try:
                                    # La synthèse s'affiche dans la conversation — pas dans la boîte thinking
                                    if role == "synthesis":
                                        return
                                    # Mapper les rôles aux labels
                                    role_labels = {
                                        "main_ai": "🗣️ IA Principale",
                                        "archiviste": "⚔️ Archiviste",
                                        # legacy
                                        "analysis": "🔍 Analyse",
                                        "conscious": "🗣️ IA Principale",
                                        "unconscious": "⚔️ Archiviste",
                                    }
                                    label = role_labels.get(role, role)
                                    
                                    # Ajouter au dialogue
                                    dialogue_messages.append(f"**{label}:**\n{content}")
                                    
                                    # Mettre à jour le widget
                                    if _introspection_md_widget:
                                        full_dialogue = "\n\n---\n\n".join(dialogue_messages)
                                        _introspection_md_widget.set_content(full_dialogue)
                                        print(f"[INTROSPECTION-UI] 📝 Affiché: {role} ({len(content)} chars)")
                                except Exception as e:
                                    print(f"[INTROSPECTION-UI] ⚠️ Erreur affichage: {e}")
                            
                            # Configurer le callback sur le moteur
                            introspection_core.on_message = on_introspection_message
                            
                            introspection_result = await introspection_core.run_introspection(
                                user_message=text,
                                context=conversation_context
                            )
                            
                            # Afficher le dialogue final si pas affiché en temps réel
                            if _introspection_md_widget and introspection_result.get("success"):
                                dialogue_data = introspection_result.get("dialogue", [])
                                if dialogue_data and not dialogue_messages:
                                    # Reconstituer le dialogue depuis les données
                                    formatted_msgs = []
                                    for msg in dialogue_data:
                                        role = msg.get("role", "unknown")
                                        content = msg.get("content", "")
                                        role_labels = {
                                            "main_ai": "🗣️ IA Principale",
                                            "archiviste": "⚔️ Archiviste",
                                            "conscious": "🗣️ IA Principale",
                                            "unconscious": "⚔️ Archiviste",
                                        }
                                        label = role_labels.get(role, role)
                                        formatted_msgs.append(f"**{label}:**\n{content}")
                                    if formatted_msgs:
                                        _introspection_md_widget.set_content("\n\n---\n\n".join(formatted_msgs))
                        else:
                            print("[INTROSPECTION] 🚀 Lancement v2.0 (Legacy)")
                            introspection_result = await introspection_core.trigger_introspection_sync(
                                user_message=text,
                                conversation_context=conversation_context
                            )
                    else:
                        print("[INTROSPECTION] ❌ Core non disponible")
                        introspection_result = {"success": False, "error": "Core non disponible"}

                    if introspection_result.get("success"):
                        final_response = introspection_result.get("final_response", "")
                        print("[INTROSPECTION] ✅ Dialogue complété (affiché en temps réel)")

                        # 7. Afficher UNIQUEMENT la réponse finale utilisateur dans conversation
                        if final_response:
                            with _chat_inner:
                                _message('assistant', final_response)

                            msg = {'role': 'assistant', 'content': final_response}
                            _chat_history.append(msg)
                            _chat_history_ui.append(msg)

                        print("[INTROSPECTION] ✅ Introspection complète affichée")
                        
                        # 🎯 DÉTECTION PHRASES MAGIQUES dans la synthèse d'introspection
                        # La synthesis contient le texte brut complet (INSIGHTS + RÉPONSE + phrase magique)
                        # final_response ne contient que la partie <RÉPONSE> visible utilisateur
                        synthesis_full = introspection_result.get("synthesis", "")
                        # Chercher dans synthesis ET dans final_response (la phrase magique peut être dans les deux)
                        texts_to_scan = [t for t in [synthesis_full, final_response] if t]
                        
                        for scan_text in texts_to_scan:
                            try:
                                # 1. Phrases magiques mémoire
                                magic_ai = _extract_magic_memories(scan_text)
                                if magic_ai:
                                    print(f"[INTROSPECTION-DETECT] ✅ {len(magic_ai)} phrase(s) magique(s) détectée(s)")
                                    mm = _ensure_memory_manager()
                                    if mm:
                                        for content in magic_ai:
                                            try:
                                                print(f"[INTROSPECTION-DETECT] 💾 Mémorisation: '{content[:80]}...'")
                                                mem_id = f"ai-{uuid.uuid4()}"
                                                conv_ctx = "\n".join([f"{msg['role']}: {msg.get('content', '')}" for msg in _chat_history[-3:] if isinstance(msg.get('content'), str)])
                                                set_archiviste_working(True)
                                                ok = await mm.add_memory(
                                                    mem_id,
                                                    content,
                                                    chat_controller=_chat_controller,
                                                    conversation_context=conv_ctx,
                                                    interlocutor="Introspection"
                                                )
                                                set_archiviste_working(False)
                                                if ok:
                                                    print(f"[INTROSPECTION-DETECT] ✅ Mémoire créée: {mem_id}")
                                                    _notify_safe(f"💾 Souvenir mémorisé depuis introspection: {content[:80]}...", 'positive')
                                                    _trigger_memory_update()
                                                else:
                                                    print(f"[INTROSPECTION-DETECT] ⚠️ Échec mémorisation")
                                            except Exception as me:
                                                set_archiviste_working(False)
                                                print(f"[INTROSPECTION-DETECT] ❌ Erreur: {me}")
                                                import traceback
                                                traceback.print_exc()
                                    break  # Trouvé dans ce texte, pas besoin de scanner l'autre
                                
                                # 2. Journal de Bord
                                journal_available = get_journal_available()
                                if journal_available:
                                    try:
                                        from extensions.journal_de_bord import get_journal
                                        journal = get_journal()
                                        journal_magic = await journal.entry_generator.handle_magic_phrases(
                                            scan_text,
                                            journal.json_manager
                                        )
                                        if journal_magic and not journal_magic.startswith("ERREUR"):
                                            print(f"[INTROSPECTION-DETECT] ✅ Journal: phrase magique traitée")
                                    except Exception as je:
                                        print(f"[INTROSPECTION-DETECT] ⚠️ Erreur journal: {je}")
                                
                                # 3. Biographie Profil
                                biography_available = get_biography_available()
                                if biography_available:
                                    try:
                                        from extensions.biographie_profil import get_biography_magic_phrases
                                        biography_magic = get_biography_magic_phrases()
                                        if biography_magic:
                                            bio_response = await biography_magic.handle_magic_phrases(
                                                scan_text,
                                                is_ai_message=True,
                                                conversation_history=_chat_history
                                            )
                                            if bio_response:
                                                print(f"[INTROSPECTION-DETECT] ✅ Biographie: phrase magique traitée")
                                    except Exception as be:
                                        print(f"[INTROSPECTION-DETECT] ⚠️ Erreur biographie: {be}")
                                
                            except Exception as detect_err:
                                print(f"[INTROSPECTION-DETECT] ❌ Erreur détection: {detect_err}")
                                import traceback
                                traceback.print_exc()
                        
                        if not texts_to_scan:
                            print(f"[INTROSPECTION-DETECT] ⚪ Aucun texte à scanner")

                    else:
                        error = introspection_result.get("error", "Erreur inconnue")
                        with _chat_inner:
                            _message('system', f"⚠️ **Introspection échouée:** {error}")
                        print(f"[INTROSPECTION] ❌ Échec: {error}")

                except Exception as e:
                    print(f"[INTROSPECTION] ❌ Exception: {e}")
                    import traceback
                    traceback.print_exc()

                    with _chat_inner:
                        _message('system', f"⚠️ **Erreur introspection:** {str(e)}")

                # 8. CRUCIAL: STOPPER LE FLUX ICI
                if input_el and not text_override:
                    input_el.value = ''

                return  # ← NE PAS CONTINUER vers génération IA principale normale

    except Exception as e:
        print(f"[INTROSPECTION] ERROR: {e}")

    # 🛑 COGNITIVE-MIRROR: Détection phrases magiques utilisateur (arrêt réflexion)
    try:
        cognitive_mirror = _ensure_cognitive_mirror()
        if cognitive_mirror and text:
            # Patterns pour arrêter l'introspection
            stop_introspection_patterns = [
                r"arrête\s+de\s+réfléchir",
                r"arrêt(?:e)?\s+(?:la\s+)?réflexion",
                r"stop\s+(?:la\s+)?réflexion",
                r"arrête\s+(?:la\s+)?subconscience",
                r"arrête\s+(?:l'|la\s+)?introspection",
                r"stop\s+(?:l'|la\s+)?introspection",
                r"cesse\s+de\s+réfléchir",
                r"termine\s+(?:la\s+)?réflexion"
            ]

            is_stop_trigger = any(re.search(pattern, text, re.IGNORECASE) for pattern in stop_introspection_patterns)

            if is_stop_trigger:
                print("[COGNITIVE-MIRROR] 🛑 Phrase magique d'arrêt détectée")

                # Arrêter la réflexion en cours
                success = cognitive_mirror.stop_reflection_session("user_stop_request")

                if success:
                    _message('system', "🛑 **Réflexion interrompue** - L'IA principale arrête sa phase d'introspection sur demande utilisateur")
                    print("[COGNITIVE-MIRROR] OK Réflexion arrêtée via phrase magique utilisateur")
                else:
                    _message('system', "ℹ️ **Aucune réflexion en cours** - Il n'y a pas d'introspection active à arrêter")
                    print("[COGNITIVE-MIRROR] INFO Aucune réflexion en cours à arrêter")

                if input_el and not text_override:
                    input_el.value = ''
                return

    except Exception as e:
        print(f"[COGNITIVE-MIRROR] ERROR Erreur traitement phrase magique arrêt: {e}")

    # 💾 MEMORY: Détection lecture souvenir par ID
    try:
        if _memory_manager and text:
            # Pattern pour lecture directe par ID: "lis le souvenir usr-xxx" ou "consulte souvenir usr-xxx"
            memory_id_patterns = [
                r"lis\s+(?:le\s+|ce\s+)?souvenir\s+(usr-[a-f0-9\-]+)",
                r"consulte\s+(?:le\s+|ce\s+)?souvenir\s+(usr-[a-f0-9\-]+)",
                r"affiche\s+(?:le\s+|ce\s+)?souvenir\s+(usr-[a-f0-9\-]+)",
                r"montre\s+(?:le\s+|ce\s+)?souvenir\s+(usr-[a-f0-9\-]+)",
                r"ouvre\s+(?:le\s+|ce\s+)?souvenir\s+(usr-[a-f0-9\-]+)",
            ]

            for pattern in memory_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    memory_id = match.group(1)
                    print(f"[MEMORY] 🔍 Phrase magique lecture souvenir détectée: {memory_id}")

                    # Récupérer le souvenir par ID
                    memory_data = _memory_manager.get_memory_by_id(memory_id)

                    if memory_data:
                        # Formater le souvenir pour affichage
                        title = memory_data.get('title', 'Sans titre')
                        summary = memory_data.get('summary', '')
                        text_original = memory_data.get('text_original', '')
                        valence = memory_data.get('valence', 'neutre')
                        lesson = memory_data.get('lesson', '')
                        created_at = memory_data.get('created_at', '')
                        score_impact = memory_data.get('score_impact', 0)

                        # Construire la réponse formatée
                        response = f"📖 **Souvenir {memory_id}**\n\n"
                        response += f"**{title}**\n\n"

                        if summary:
                            response += f"**Résumé:** {summary}\n\n"

                        if text_original:
                            response += f"**Contenu original:**\n{text_original}\n\n"

                        response += f"**Valence émotionnelle:** {valence}\n"
                        response += f"**Impact:** {score_impact}\n"

                        if lesson:
                            response += f"**Leçon:** {lesson}\n"

                        if created_at:
                            response += f"**Créé le:** {created_at}\n"

                        print(f"[MEMORY] ✅ Souvenir {memory_id} trouvé et affiché")
                        # Afficher dans le bon contexte UI
                        if _chat_inner is not None:
                            with _chat_inner:
                                _message('assistant', response)
                        else:
                            _message('assistant', response)
                    else:
                        print(f"[MEMORY] ❌ Souvenir {memory_id} non trouvé")
                        # Afficher dans le bon contexte UI
                        if _chat_inner is not None:
                            with _chat_inner:
                                _message('assistant', f"❌ **Souvenir introuvable**\n\nAucun souvenir trouvé avec l'ID `{memory_id}`.")
                        else:
                            _message('assistant', f"❌ **Souvenir introuvable**\n\nAucun souvenir trouvé avec l'ID `{memory_id}`.")

                    if input_el and not text_override:
                        input_el.value = ''
                    return

    except Exception as e:
        print(f"[MEMORY] ERROR Erreur traitement phrase magique lecture souvenir: {e}")

    # 🎥 PERCEPTION: Capture automatique d'image si l'extension est activée
    perception_image_data = None
    try:
        from extensions.perception_ui import get_perception_ui
        perception_ui = get_perception_ui()

        # ✅ CORRECTION: Vérifier si extension démarrée (capture_on_send était obsolète)
        if perception_ui.is_enabled and perception_ui.perception_agent:

            print("[PERCEPTION] 📸 Capture automatique au moment de l'envoi")
            perception_image_data = perception_ui.capture_for_chat()

            if perception_image_data:
                print(f"[PERCEPTION] ✅ Image capturée automatiquement")
            else:
                print(f"[PERCEPTION] ⚠️ Échec capture automatique")
    except Exception as e:
        print(f"[PERCEPTION] ❌ Erreur capture automatique: {e}")

    # � Initialisation des variables temporelles (scope global de la fonction)
    # LOG TEMPOREL: Enregistrer l'heure du message avant tout traitement
    try:
        from extensions.temporal_guardian.temporal_log_builder import register_message_time
        register_message_time()
    except Exception:
        pass
    
    # �📚 NOUVEAU: Détection des commandes de conversation archivée
    conversation_command_result = await _handle_conversation_commands(text)
    if conversation_command_result:
        # La commande a été traitée, vider le champ et arrêter
        if input_el and not text_override:
            input_el.value = ''
        return

    # 🪞 COGNITIVE MIRROR: Hook avant traitement du message utilisateur
    print("🚨 [DEBUG] Hook Cognitive Mirror atteint!")
    print("[COGNITIVE-MIRROR] SEARCH Vérification activation cognitive mirror...")
    try:
        cognitive_mirror = _ensure_cognitive_mirror()
        print(f"🚨 [DEBUG] Cognitive Mirror trouvé: {cognitive_mirror is not None}")
        
        # DIAGNOSTIC COMPLET
        if cognitive_mirror:
            from extensions.cognitive_mirror import is_enabled as cm_is_enabled
            print(f"🚨 [DEBUG] Extension activée: {cm_is_enabled()}")
            print(f"🚨 [DEBUG] Type instance: {type(cognitive_mirror)}")
            print(f"🚨 [DEBUG] ID instance: {id(cognitive_mirror)}")
            
            # Vérifier si c'est une instance IntrospectionCore
            if hasattr(cognitive_mirror, 'parameters'):
                ext_enabled_param = cognitive_mirror.parameters.get('extension_enabled', 'NOT_FOUND')
                print(f"🚨 [DEBUG] Paramètre extension_enabled: {ext_enabled_param}")
            
            # Comparer avec l'instance globale
            from extensions.cognitive_mirror import get_introspection_core
            global_core = get_introspection_core()
            if global_core:
                print(f"🚨 [DEBUG] Instance globale ID: {id(global_core)}")
                print(f"🚨 [DEBUG] Instance globale is_enabled: {cm_is_enabled()}")
                print(f"🚨 [DEBUG] Même instance? {cognitive_mirror is global_core}")
                if hasattr(global_core, 'parameters'):
                    global_ext_enabled = global_core.parameters.get('extension_enabled', 'NOT_FOUND')
                    print(f"🚨 [DEBUG] Instance globale extension_enabled: {global_ext_enabled}")
            
            # v2.0: Plus de détection d'inactivité automatique
            # L'introspection se déclenche seulement par phrases magiques ou mode always
            if cm_is_enabled():
                print("[COGNITIVE-MIRROR] OK Extension v2.0 active - déclenchement à la demande")
            else:
                print("🚨 [DEBUG] Extension OFF - pas de traitement introspection")
        else:
            print("🚨 [DEBUG] Extension non trouvée")
    except Exception as e:
        print(f"[COGNITIVE-MIRROR] ERROR Erreur hook utilisateur: {e}")
        import traceback
        traceback.print_exc()
    
    magic = _extract_magic_memories(text)
    organic_events = _extract_organic_events(text)
    organic_updates = _extract_organic_updates(text)
    user_memorized = False
    
    # Traitement des souvenirs classiques
    if magic:
        mem = _ensure_memory_manager()
        if mem is not None:
            for content in magic:
                try:
                    mem_id = f"usr-{uuid.uuid4()}"
                    # 🌀 SPINNER: Activer le spinner Archiviste pendant l'enrichissement mémoire
                    set_archiviste_working(True)
                    ok = await mem.add_memory(mem_id, content)
                    set_archiviste_working(False)
                    if ok:
                        _notify_safe(f"SAVE Souvenir mémorisé: {content[:80]}...", 'positive')
                        _trigger_memory_update()
                        user_memorized = True
                    else:
                        _notify_safe("Échec de la mémorisation (voir logs)", 'warning')
                except Exception as e:
                    set_archiviste_working(False)
                    _notify_safe(f"Erreur mémorisation: {e}", 'warning')
    
    # Traitement des évènements Organic Planner
    if organic_events:
        planner = _ensure_organic_planner()
        if planner:
            for event in organic_events:
                try:
                    ok = planner.add_event(
                        content=event['title'],
                        target_date=event['date'],
                        emotional_note=event['feeling']
                    )
                    if ok:
                        _notify_safe(f"📅 Évènement noté: {event['title']} ({event['date']})", 'positive')
                        user_memorized = True
                    else:
                        _notify_safe("Échec de l'enregistrement de l'évènement", 'warning')
                except Exception as e:
                    _notify_safe(f"Erreur Organic Planner: {e}", 'warning')
    
    # Traitement des mises à jour Organic Planner
    if organic_updates:
        planner = _ensure_organic_planner()
        if planner:
            for update in organic_updates:
                try:
                    event_data = planner.update_event_status_by_title(
                        title=update['title'],
                        status=update['status']
                    )
                    if event_data:
                        _notify_safe(f"📅 Statut mis à jour: {update['title']} -> {update['status']}", 'positive')
                        
                        # 💾 ARCHIVAGE DANS LA MÉMOIRE SI TERMINÉ
                        if update['status'] == 'TERMINE':
                            mem = _ensure_memory_manager()
                            if mem:
                                memory_content = (
                                    f"Évènement terminé : {event_data['content']} "
                                    f"(Date prévue: {event_data['target_date']}). "
                                    f"Ressenti: {event_data['emotional_note']}"
                                )
                                # Utiliser add_memory pour stockage permanent (SQLite + FAISS)
                                ok_mem = await mem.add_memory(f"plan-{uuid.uuid4()}", memory_content)
                                if ok_mem:
                                    planner.delete_event(event_data['id'])
                                    _notify_safe(f"💾 Archivé dans la mémoire OGMA", 'positive')
                                    _trigger_memory_update()
                        
                        user_memorized = True
                    else:
                        _notify_safe(f"Évènement non trouvé: {update['title']}", 'warning')
                except Exception as e:
                    _notify_safe(f"Erreur Organic Planner Update: {e}", 'warning')
    
    cleaned_text = _strip_magic_phrases(text) or text
    global _active_file_data
    final_message = cleaned_text
    message_content = cleaned_text

    # Construction du message pour l'IA (avec images si disponibles)
    content_parts = [{"type": "text", "text": cleaned_text}]

    # Ajouter image de perception si disponible
    if perception_image_data:
        content_parts.append(perception_image_data)
        print("[PERCEPTION] 🖼️ Image ajoutée au message pour l'IA")

    # Ajouter fichier actif si disponible
    if _active_file_data:
        file_content = _active_file_data.get('content', '')
        filename = _active_file_data.get('filename', 'Fichier')
        file_type = _active_file_data.get('type', 'text')

        if file_type == 'text':
            final_message = f"{cleaned_text}\n\n[Fichier joint: {filename}]\n{file_content}"
        elif file_type == 'image':
            final_message = f"{cleaned_text}\n\n[Image jointe: {filename}]\n[Données image en base64 disponibles pour analyse]"

    # Pour l'IA, utiliser content_parts si on a des images, sinon le texte simple
    ai_content = content_parts if len(content_parts) > 1 else final_message

    # 📖 BIOGRAPHIE PROFIL: Préparation contexte biographique pour injection IA
    biography_context = ""
    try:
        # 🚀 FIX: Utiliser detection déjà effectuée ligne 3169 (évite double appel Archiviste)
        if 'biography_context_early' in locals() and biography_context_early:
            biography_context = f"\n\n{biography_context_early}"
            print(f"[BIOGRAPHY-EXTENSION] 🎯 Injection biographie ajoutée au contexte IA (depuis handle_magic_phrases)")
            
            # 🧠 FLUX COGNITIF - Logger injection biographie AVEC CONTENU
            try:
                from extensions.flux_cognitif import log_cognitive_event
                import re as _re_bio
                
                # Extraire contenu structuré
                match_count = _re_bio.search(r'(\d+)\s+souvenirs? pertinents?', biography_context_early)
                count = int(match_count.group(1)) if match_count else 0
                
                # Extraire les souvenirs (format: "- Titre: ..." ou "• Titre: ...")
                memories_lines = _re_bio.findall(r'[•\-]\s*(.+?)(?:\n|$)', biography_context_early)
                memories_content = []
                for line in memories_lines[:10]:  # Max 10
                    # Nettoyer et limiter longueur
                    clean_line = line.strip()[:80]
                    if clean_line:
                        memories_content.append(f"• {clean_line}")
                
                # Message avec contenu
                if memories_content:
                    content_str = '\n'.join(memories_content)
                    message = f'📖 {count} souvenirs bio:\n{content_str}'
                    if len(memories_lines) > 10:
                        message += f'\n... +{len(memories_lines) - 10} autres'
                else:
                    message = f'Biographie ({count} souvenirs)'
                
                log_cognitive_event('biography', message)
            except Exception as e:
                print(f"[FLUX-COGNITIF] Erreur log bio: {e}")

    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ERROR Erreur préparation contexte biographique: {e}")

    # Ajouter le contexte biographique au message IA si disponible
    if biography_context:
        if isinstance(ai_content, list):
            # Multimodal: ajouter au texte du premier élément
            ai_content[0]["text"] += biography_context
        else:
            # Texte simple: ajouter directement
            ai_content += biography_context

    # === INJECTION PRÉNOM UTILISATEUR (SESSION) ===
    # Ajouter tag [Prénom] au message pour l'IA (pas dans l'affichage UI)
    global _current_user_name
    user_prefix = f"[{_current_user_name}] " if _current_user_name else ""
    
    # Appliquer le préfixe au message final pour l'IA
    if user_prefix:
        if isinstance(ai_content, list):
            # Multimodal: préfixer le texte du premier élément
            ai_content[0]["text"] = user_prefix + ai_content[0]["text"]
        else:
            # Texte simple: préfixer directement
            ai_content = user_prefix + ai_content
        
        # Aussi appliquer à final_message pour stockage historique
        final_message = user_prefix + final_message
        
        print(f"[SESSION] 🏷️ Tag utilisateur ajouté: {user_prefix}")
    # === FIN INJECTION PRÉNOM ===

    # Ajouter à l'historique seulement si pas skip_history_append (édition)
    if not skip_history_append:
        msg = {'role': 'user', 'content': final_message, 'memorized': user_memorized, 'display_content': cleaned_text}
        _chat_history.append(msg)
        _chat_history_ui.append(msg)
        # Persistance: si première interaction, crée ID + titre contextuel
        try:
            if len([m for m in _chat_history if m.get('role') in ('user','assistant')]) == 1:
                _persist_conversation(initial_text_for_title=cleaned_text)
            else:
                _persist_conversation()
        except Exception:
            pass
        if _chat_inner is not None:
            with _chat_inner:
                # Si c'est le premier message OU mode édition, réafficher tout l'historique
                if len(_chat_history) == 1 or was_editing:
                    _chat_inner.clear()
                    # En mode édition, réafficher tous les messages existants avant d'ajouter le nouveau
                    if was_editing:
                        for i, msg in enumerate(_chat_history[:-1]):  # Tous sauf le dernier qu'on vient d'ajouter
                            role = msg.get('role', 'system')
                            content = msg.get('display_content', msg.get('content', ''))
                            badges = ['mémorisé'] if msg.get('memorized', False) else None
                            _message(role, content, badges, message_index=i)

                display_text = cleaned_text
                if _active_file_data:
                    filename = _active_file_data.get('filename', 'Fichier')
                    # Importée depuis utils.formatting_utils
                    icon = get_file_icon(filename)
                    display_text = f"{cleaned_text}\n\n{icon} {filename}"
                _message('user', display_text, ['mémorisé'] if user_memorized else None, message_index=len(_chat_history)-1)
        try:
            ui.run_javascript(r'''
setTimeout(()=>{
    const el = document.querySelector('[data-role="chat-scroll"]');
    if(el){
        // On force le scroll en bas après l'envoi d'un message utilisateur
        el.scrollTop = el.scrollHeight + 1000;
        window.OGMA_autoScroll = true;
        const btn = document.getElementById('scrollBottomBtn');
        if(btn){ btn.style.display = 'none'; }
    }
}, 50);
''')
        except Exception:
            pass

    # Vider input seulement si pas text_override (édition)
    if input_el and not text_override:
        input_el.value = ''

    # Appel backend
    ctrl = _ensure_chat_controller()
    # Contexte mémoire (SQLite/FAISS) — approche hybride: synthèse + souvenirs détaillés
    mem = _ensure_memory_manager()
    context_note = None
    detailed_memories = []
    if mem is not None:
        try:
            # Diagnostic temporaire pour analyser la recherche FAISS
            if "phare" in text.lower():
                print(f"[DEBUG] Diagnostic FAISS pour requête avec 'phare'")
                await mem.diagnose_search_quality(text, k=10)
            
            # Détection de demande de textes intégraux
            fulltext_keywords = ['texte complet', 'texte intégral', 'détails complets', 'raconte-moi plus', 
                               'peux-tu développer', 'plus de détails', 'version complète', 'intégralement',
                               'donne moi le texte', 'montre moi le texte', 'texte original', 'récit complet']
            
            is_fulltext_request = any(keyword in text.lower() for keyword in fulltext_keywords)
            
            print(f"[MEMORY-DETECTION] Requête: '{text}'")
            print(f"[MEMORY-DETECTION] Mots-clés détectés: {[kw for kw in fulltext_keywords if kw in text.lower()]}")
            print(f"[MEMORY-DETECTION] Mode textes intégraux: {is_fulltext_request}")

            # 🔬 DIAGNOSTIC FAISS TEMPORAIRE
            if "date de naissance" in text.lower() or "tu connais ma" in text.lower() or "tu sais" in text.lower():
                print(f"[FAISS-DIAGNOSTIC] 🔬 Lancement diagnostic approfondi k=20...")
                await mem.diagnose_search_quality(text, k=20)

            if is_fulltext_request:
                print(f"[MEMORY-FULLTEXT] 📖 Demande de textes intégraux détectée")
                synthesis, memories = await mem.retrieve_full_texts_context(text, k=5)
            else:
                # ================================================================
                # SMART STOP v2 - OPTIMIZER UNIQUE (13 nov 2025)
                # ================================================================
                print(f"[MEMORY-OPTIMIZER] 🚀 Smart Stop v2 - Workflow optimisé unique")
                optimizer = _ensure_memory_optimizer()
                
                if optimizer:
                    print(f"[MEMORY-OPTIMIZER] 🟢 Optimizer Smart Stop activé")
                    # 🌀 SPINNER: Activer le spinner Archiviste pendant Smart Stop
                    set_archiviste_working(True)
                    try:
                        optimized_ctx = await optimizer.get_optimized_context(
                            message=text,
                            k_personal=5,
                            k_conversation=7
                        )
                        
                        synthesis = optimized_ctx.synthesis
                        memories = optimized_ctx.memories_personal + optimized_ctx.memories_conversation
                        
                        # Log métriques Smart Stop
                        metrics = optimized_ctx.metrics
                        print(f"[MEMORY-OPTIMIZER] ✅ Smart Stop metrics:")
                        print(f"  - Queries: {metrics.get('queries_used', 0)}/{metrics.get('queries_planned', 0)} (économie: {metrics.get('queries_saved', 0)})")
                        print(f"  - Top 2 intégral: {metrics.get('top2_memories', 0)}")
                        print(f"  - Souvenirs total: {len(memories)}")
                        print(f"  - Temps: {metrics.get('latency_ms', 0):.0f}ms")
                        
                        # 🌀 SPINNER: Désactiver après succès
                        set_archiviste_working(False)
                        
                    except Exception as e:
                        set_archiviste_working(False)
                        print(f"[MEMORY-OPTIMIZER] ❌ ERREUR CRITIQUE optimizer: {e}")
                        import traceback
                        traceback.print_exc()
                        # ❌ PLUS DE FALLBACK - Optimizer OBLIGATOIRE
                        synthesis = "Erreur récupération contexte mémoire."
                        memories = []
                else:
                    # ❌ ERREUR: Optimizer indisponible = problème config
                    print(f"[MEMORY-OPTIMIZER] ❌ ERREUR: Optimizer indisponible - Vérifier configuration")
                    synthesis = "Système mémoire indisponible."
                    memories = []
            
            # 🚨 DÉDUPLICATION: Vérifier les redondances avant injection
            if memories:
                memories_preview = str(memories)[:500]  # Aperçu pour analyse
                has_redundancy, exclusion_instruction = check_archiviste_injection(memories_preview)
                
                if has_redundancy:
                    print(f"[DEDUP] ⚠️ Redondances détectées dans les souvenirs Archiviste")
                    print(f"[DEDUP] 📋 Instruction: {exclusion_instruction}")
                    # Ajouter l'instruction de déduplication à la synthèse
                    if synthesis:
                        synthesis = f"{synthesis}\n\n{exclusion_instruction}"
                    else:
                        synthesis = exclusion_instruction
                else:
                    print(f"[DEDUP] ✅ Aucune redondance détectée pour l'Archiviste")
            
            if synthesis and not synthesis.lower().startswith('erreur') and 'aucun souvenir' not in synthesis.lower():
                context_note = synthesis
                detailed_memories = memories
                
                # 🧠 FLUX COGNITIF - Logger souvenirs injectés AVEC CONTENU
                try:
                    from extensions.flux_cognitif import log_cognitive_event
                    memory_count = len(detailed_memories) if detailed_memories else 0
                    
                    # Extraire titres pour affichage
                    memories_content = []
                    for mem in detailed_memories[:10]:  # Max 10 pour lisibilité
                        title = mem.get('title', '?')
                        impact = mem.get('score_impact', 0)
                        memories_content.append(f"• {title} (impact: {impact:.1f})")
                    
                    # Message avec contenu
                    if memories_content:
                        content_str = '\n'.join(memories_content)
                        message = f'📚 {memory_count} souvenirs:\n{content_str}'
                        if memory_count > 10:
                            message += f'\n... +{memory_count - 10} autres'
                    else:
                        message = f'Souvenirs: {memory_count} injectés'
                    
                    log_cognitive_event('archiviste', message)
                except Exception as e:
                    print(f"[FLUX-COGNITIF] Erreur log mémoire: {e}")
                
                # Debug détaillé des souvenirs reçus
                for i, mem in enumerate(detailed_memories, 1):
                    title = mem.get('title', 'N/A')
                    sim = mem.get('similarity_score', 0)
                    impact = mem.get('score_impact', 0)
            else:
                print(f"[DEBUG-INJECTION] Pas de contexte pertinent")
        except Exception as e:
            print(f"[DEBUG-INJECTION] Erreur récupération contexte: {e}")
            context_note = None
            detailed_memories = []

    # Option debug : afficher l'injection de l'Archiviste dans le chat AVANT la réponse IA
    sm = _ensure_settings_manager()
    show_injection = sm.settings.get('debug', {}).get('show_archiviste_injection', False)
    
    
    if show_injection and _chat_inner is not None:
        try:
            with _chat_inner:
                # Afficher la synthèse de l'Archiviste
                if context_note:
                    _message('system', f"BRAIN **Synthèse Archiviste** ({len(context_note)} chars)\n\n{context_note}")
                
                # 3. Afficher les souvenirs détaillés
                if detailed_memories:
                    memories_text = f"📚 **Souvenirs Détaillés** ({len(detailed_memories)} souvenirs)\n\n"
                    for i, mem in enumerate(detailed_memories, 1):
                        memories_text += f"**{i}. {mem.get('title', 'Sans titre')}**\n"
                        memories_text += f"Impact: {mem.get('score_impact', 0)} | Similarité: {mem.get('similarity_score', 0):.2f}\n"
                        memories_text += f"{mem.get('summary', '')}\n"
                        if mem.get('created_at'):
                            memories_text += f"DATE {mem.get('created_at')}\n"
                        memories_text += "\n"
                    
                    _message('system', memories_text.strip())
                
        except Exception as e:
            print(f"[DEBUG-INJECTION] Erreur affichage: {e}")
            # Fallback: afficher via notification
            if context_note:
                ui.notify(f'BRAIN Archiviste: {context_note[:100]}...', type='info')
    elif show_injection:
        print(f"[DEBUG-INJECTION] PROBLÈME: _chat_inner est None - impossible d'afficher dans le chat")
        # Fallback: notification uniquement
        if context_note:
            ui.notify(f'BRAIN Archiviste: {context_note[:100]}...', type='info')

    #  INJECTION PRIORITÉ ABSOLUE: Instructions de base + Instruction temporelle fusionnées
    sm = _ensure_settings_manager()
    base_instructions = sm.settings.get('prompts', {}).get('instructions', '')
    
    # 🧠 COGNITIVE MIRROR: Retirer les instructions d'introspection si l'extension est désactivée
    if COGNITIVE_MIRROR_AVAILABLE:
        from extensions.cognitive_mirror import is_enabled
        if not is_enabled():
            # Retirer le bloc B. >>> [TRIGGER INTROSPECTION] <<<
            # On cherche de "B. >>> [TRIGGER INTROSPECTION]" jusqu'au prochain bloc "[3. LOIS FONDAMENTALES]" ou fin de texte
            base_instructions = re.sub(
                r'B\.\s*>>>\s*\[TRIGGER INTROSPECTION\].*?(?=\[3\. LOIS FONDAMENTALES\]|\Z)', 
                '', 
                base_instructions, 
                flags=re.DOTALL | re.IGNORECASE
            )
            print("[INTROSPECTION] ✂️ Instructions d'introspection retirées du prompt (extension OFF)")
    
    # 🧠 EGO SELECTOR: Remplacer ego_prompt statique par sélection intelligente
    print("[EGO-INJECT] 🔍 Vérification injection ego prompt...")
    ego_injection = None
    
    # Variables pour résultats parallèles
    parallel_archiviste_directive = None  # Directive conscience critique Archiviste
    unified_capability = None  # Résultat Capability du Unified Meta-Analyzer
    
    # 🚀 PREANALYSIS: Utiliser contexte optimisé si disponible (gain ~250ms + nouveaux gains)
    if PREANALYSIS_AVAILABLE:
        try:
            memory_mgr = _ensure_memory_manager()
            archiviste_ctrl = _ensure_archiviste_controller()
            
            # Appel optimizer avec tous les paramètres (exécution parallèle)
            # 🌀 SPINNER: Activer le spinner Archiviste pendant l'analyse parallèle
            set_archiviste_working(True)
            # Passer les titres + extrait contenu des souvenirs pour informer le Meta-Analyzer
            _memory_titles_for_meta = [
                f"{m.get('title', '')[:60]} | {(m.get('summary') or m.get('text_original', ''))[:100]}"
                for m in detailed_memories[:4]
            ] if detailed_memories else []
            optimized_ctx = await get_optimized_context_for_message(
                user_message=text,
                conversation_history=_chat_history,
                memory_manager=memory_mgr,
                archiviste_controller=archiviste_ctrl,
                memory_titles_found=_memory_titles_for_meta
            )
            set_archiviste_working(False)
            
            if optimized_ctx.get('optimized'):
                ego_injection = optimized_ctx.get('ego_injection', '')
                if ego_injection:
                    print(f"[PREANALYSIS] ⚡ Ego optimisé utilisé ({len(ego_injection)} chars)")
                else:
                    print("[PREANALYSIS] ⚡ Contexte optimisé sans ego injection")
                
                # Récupérer résultats parallèles Directive + Capability
                parallel_archiviste_directive = optimized_ctx.get('archiviste_directive')
                unified_capability = optimized_ctx.get('capability_suggestion')
                
                if parallel_archiviste_directive:
                    print(f"[PREANALYSIS] 🧭 Directive Archiviste ({len(parallel_archiviste_directive)} chars)")
                if unified_capability:
                    print(f"[PREANALYSIS] 🎯 Capability suggestion: {unified_capability.get('capability_id', '?')}")
            else:
                print("[PREANALYSIS] 🔄 Fallback vers système séquentiel")
        except Exception as e:
            print(f"[PREANALYSIS] ⚠️ Erreur optimizer, fallback: {e}")
    
    # Fallback séquentiel si optimizer non dispo ou échec
    if ego_injection is None:
        try:
            # 🧠 NOUVEAU SYSTÈME: Ego Boolean Activation (si disponible)
            try:
                from modules.logic.ego_activation import activate_ego_groups
                archiviste_ctrl = _ensure_archiviste_controller()
                
                if archiviste_ctrl:
                    # Détecter si nouvelle session (historique vide ou <2 messages)
                    is_new_session = len(_chat_history) < 2
                    
                    print("[EGO-BOOLEAN] 🔍 Activation groupes boolean...")
                    ego_injection = await activate_ego_groups(text, archiviste_ctrl, is_new_session)
                    
                    if ego_injection:
                        print(f"[EGO-BOOLEAN] ✅ Groupes activés ({len(ego_injection)} chars)")
                    else:
                        print("[EGO-BOOLEAN] ⚪ Aucun groupe activé (message neutre)")
            except ImportError:
                print("[EGO-BOOLEAN] ⚠️ Module non disponible")
            except Exception as e:
                print(f"[EGO-BOOLEAN] ⚠️ Erreur activation: {e}")
        except Exception as e:
            print(f"[EGO-INJECT] ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    # Appliquer l'injection ego si disponible
    if ego_injection:
        base_instructions = f"{ego_injection}\n\n{base_instructions}"
        print(f"[EGO-INJECT] ✅ Ego injecté en tête ({len(ego_injection)} chars)")
        
        # 🧠 FLUX COGNITIF - Logger groupes ego activés
        try:
            from extensions.flux_cognitif import log_cognitive_event
            import re as _re_ego
            group_match = _re_ego.search(r'Groupes Activés:\s*([^)\n]+)', ego_injection)
            if group_match:
                group_names = [g.strip() for g in group_match.group(1).split(',')]
                groups_str = ', '.join(group_names)
                log_cognitive_event('archiviste', f'Ego: {groups_str}')
        except Exception as e:
            print(f"[FLUX-COGNITIF] Erreur log ego: {e}")
    
    # 🎯 CAPABILITY ADVISOR - Suggestion intelligente capacités
    capability_suggestion = None
    
    # Priorité 1: Utiliser le résultat du Unified Meta-Analyzer (déjà calculé en parallèle)
    # Vérifier le mode introspection pour bloquer le Capability Advisor en on_demand
    _introspection_mode_for_advisor = 'on_demand'
    try:
        if COGNITIVE_MIRROR_AVAILABLE:
            from extensions.cognitive_mirror import get_introspection_config as _get_icfg
            _icfg = _get_icfg()
            if _icfg:
                _introspection_mode_for_advisor = _icfg.get_introspection_mode()
    except Exception:
        pass

    if unified_capability and isinstance(unified_capability, dict):
        try:
            from extensions.capability_advisor.advisor_core import CapabilitySuggestion
            from extensions.capability_advisor.capability_catalog import get_capability
            cap_id = unified_capability.get('capability_id', '')
            # Bloquer introspection si mode on_demand
            if cap_id == 'introspection' and _introspection_mode_for_advisor == 'on_demand':
                print("[CAPABILITY-ADVISOR] Mode on_demand: suggestion introspection bloquée")
                unified_capability = None
                cap_id = ''
            cap_info = get_capability(cap_id)
            if cap_info:
                confidence = unified_capability.get('confidence', 0.8)
                # Vérifier les seuils (même logique que AdvisorCore.analyze_conversation)
                # Priorité: seuil custom UI > seuil catalog > seuil global
                advisor = _ensure_capability_advisor()
                if advisor:
                    capability_threshold_catalog = cap_info.get('confidence_threshold', 0.70)
                    capability_threshold_custom = advisor.config.get_capability_threshold(cap_id, None)
                    global_threshold = advisor.config.config.get('confidence_threshold', 0.70)
                    effective_threshold = capability_threshold_custom if capability_threshold_custom is not None else capability_threshold_catalog
                    min_threshold = max(effective_threshold, global_threshold)
                else:
                    min_threshold = cap_info.get('confidence_threshold', 0.70)

                if confidence < min_threshold:
                    print(f"[CAPABILITY-ADVISOR] Via Unified Meta: rejeté {cap_id} (conf={confidence:.2f} < seuil={min_threshold:.2f})")
                else:
                    capability_suggestion = CapabilitySuggestion(
                        needs_capability=True,
                        capability_id=cap_id,
                        reasoning=f"Unified Meta-Analyzer a detecte le besoin de {cap_info['name']}",
                        suggestion=unified_capability.get('magic_phrase') or cap_info.get('magic_phrase', ''),
                        confidence=confidence
                    )
                    # Activer la LED correspondante
                    if advisor and hasattr(advisor, 'led_manager'):
                        advisor.led_manager.activate_led(cap_id)
                    print(f"[CAPABILITY-ADVISOR] Via Unified Meta: {cap_id} (conf={confidence:.2f}, seuil={min_threshold:.2f}, LED activee)")
            else:
                print(f"[CAPABILITY-ADVISOR] Capability '{cap_id}' non trouvee dans le catalogue")
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] Erreur conversion unified meta: {e}")
    
    # Priorité 2: Skip si souvenirs FAISS ET pas de suggestion unifiée
    if not capability_suggestion and detailed_memories:
        print(f"[CAPABILITY-ADVISOR] Skip - {len(detailed_memories)} souvenir(s) FAISS, pas de suggestion unifiee")
    elif not capability_suggestion:
        # Priorité 3: Analyse séquentielle si pas de résultat parallèle
        try:
            advisor = _ensure_capability_advisor()
            if advisor and advisor.is_enabled():
                print(f"[CAPABILITY-ADVISOR] Analyse contexte conversation (sequentiel)...")
                capability_suggestion = await advisor.analyze_conversation(
                    user_message=text,
                    conversation_history=_chat_history
                )
                # Bloquer introspection si mode on_demand
                if capability_suggestion and capability_suggestion.capability_id == 'introspection' \
                        and _introspection_mode_for_advisor == 'on_demand':
                    print("[CAPABILITY-ADVISOR] Mode on_demand: suggestion introspection séquentielle bloquée")
                    capability_suggestion = None
                
                if capability_suggestion:
                    print(f"[CAPABILITY-ADVISOR] Suggestion: {capability_suggestion.capability_id}")
                    print(f"[CAPABILITY-ADVISOR] Conseil: {capability_suggestion.suggestion[:80]}...")
                else:
                    print("[CAPABILITY-ADVISOR] Aucune suggestion pertinente pour ce contexte")
                    
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] Erreur analyse: {e}")
            import traceback
            traceback.print_exc()
    
    # Construire le message système prioritaire unifié
    # 🕒 LOG TEMPOREL - Injection données temps réelles (Python pur, 0 appel API)
    _temporal_log_block = ""
    try:
        from extensions.temporal_guardian.temporal_log_builder import build_temporal_log
        _temporal_instruction = sm.settings.get('prompts', {}).get('temporal_guardian', '')
        _temporal_log_json = build_temporal_log(
            conv_index=_conv_index,
            current_conversation_id=_current_conversation_id
        )
        if _temporal_instruction and _temporal_log_json:
            _temporal_log_block = f"{_temporal_instruction}\n\n{_temporal_log_json}"
            print(f"[TEMPORAL-LOG] Log temporel injecte ({len(_temporal_log_json)} chars)")
    except Exception as e:
        print(f"[TEMPORAL-LOG] Erreur: {e}")

    if _temporal_log_block:
        priority_instructions = f"{_temporal_log_block}\n\n{base_instructions}" if base_instructions else _temporal_log_block
    else:
        priority_instructions = base_instructions if base_instructions else ""
    
    # 🕒 INJECTION HORODATAGE - L'IA connaît l'heure et la date actuelles
    from datetime import datetime
    current_datetime = datetime.now()
    horodatage = current_datetime.strftime("Il est %H:%M le %A %d %B %Y")
    # Traduction jours et mois en français
    jours_fr = {'Monday': 'lundi', 'Tuesday': 'mardi', 'Wednesday': 'mercredi', 
                'Thursday': 'jeudi', 'Friday': 'vendredi', 'Saturday': 'samedi', 'Sunday': 'dimanche'}
    mois_fr = {'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
               'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
               'September': 'septembre', 'October': 'octobre', 'November': 'novembre', 'December': 'décembre'}
    for eng, fr in jours_fr.items():
        horodatage = horodatage.replace(eng, fr)
    for eng, fr in mois_fr.items():
        horodatage = horodatage.replace(eng, fr)
    
    messages.append({'role': 'system', 'content': f"[HORODATAGE] {horodatage}"})
    print(f"[HORODATAGE] 🕒 Injecté: {horodatage}")
    
    # 🛡️ PROTOCOLES RUNTIME - Position P0 (premier après horodatage = attention maximale)
    persistent_context_file = DATA_DIR / "persistent_context.txt"
    if persistent_context_file.exists():
        try:
            persistent_content = persistent_context_file.read_text(encoding='utf-8').strip()
            if persistent_content:
                messages.append({'role': 'system', 'content': persistent_content})
                print(f"[RUNTIME-PROTOCOLS] ✅ Protocoles runtime injectés en P0: {len(persistent_content)} chars")
        except Exception as e:
            print(f"[RUNTIME-PROTOCOLS] WARN Erreur lecture protocoles: {e}")
    
    if priority_instructions:
        messages.append({'role': 'system', 'content': priority_instructions})
        # Enregistrer l'ego prompt pour déduplication
        register_ego_prompt_injection(priority_instructions)
        print(f"[DEDUP] 🔍 Ego prompt enregistré ({len(priority_instructions)} chars)")
    else:
        print(f"[DEBUG-INJECTION] WARN AUCUNE instruction trouvée!")
    
    # 🎥 INJECTION INSTRUCTIONS DE PERCEPTION si images détectées
    # Vérifier aussi les images dans l'historique de conversation
    has_image_in_history = False
    for msg in messages:
        content = msg.get('content', '')
        if isinstance(content, list):
            # Format multimodal avec images
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'image_url':
                    has_image_in_history = True
                    break
        elif isinstance(content, str) and '<img src="data:image' in content:
            # Image inline HTML
            has_image_in_history = True
            break
        if has_image_in_history:
            break
    
    # Support multi-images
    has_active_images = bool(_active_images) and len(_active_images) > 0
    has_single_image = _active_file_data and _active_file_data.get('type') == 'image'
    
    # 🎭 Détecter si représentations User/IA actives
    has_repr_active = _has_active_representations()
    
    has_image = (perception_image_data is not None or 
                has_active_images or
                has_single_image or
                has_image_in_history or
                has_repr_active)  # AJOUTÉ: représentations comptent comme image
    
    if has_image:
        nb_images = len(_active_images) if has_active_images else (1 if has_single_image else 0)
        if has_repr_active:
            print(f"[PERCEPTION-INJECT] 🎭 Représentations actives détectées - injection guide I2I")
        print(f"[PERCEPTION-INJECT] 🖼️ Image détectée (perception={perception_image_data is not None}, images={nb_images}, history={has_image_in_history}, repr={has_repr_active})")
        perception_instructions = sm.settings.get('prompts', {}).get('perception', '')
        if perception_instructions:
            perception_system_msg = f"Instructions spécifiques pour la perception visuelle :\n{perception_instructions}"
            messages.append({'role': 'system', 'content': perception_system_msg})
            print(f"[PERCEPTION-INJECT] ✅ Instructions de perception injectées ({len(perception_instructions)} chars)")
        else:
            print(f"[PERCEPTION-INJECT] WARN Aucune instruction de perception trouvée dans settings")
        
        # 🎨 INJECTION GUIDE IMG2IMG si img2img activé
        sm_temp = _ensure_settings_manager()
        img_config = sm_temp.settings.get('image_generation', {})
        if img_config.get('img2img_enabled', False):
            img2img_guide = img_config.get('img2img_guide', '').strip()
            if img2img_guide:
                messages.append({'role': 'system', 'content': img2img_guide})
                print(f"[IMG2IMG-INJECT] ✅ Guide de modification injecté ({len(img2img_guide)} chars)")
            else:
                print(f"[IMG2IMG-INJECT] ⚠️ IMG2IMG activé mais guide vide")
            
            # 🔄 CONTEXTE AUTO-CORRECTION: prévenir l'IA que le système valide automatiquement
            if img_config.get('i2i_autocorrect_enabled', False):
                autocorrect_ctx = ("IMPORTANT: Le systeme d'auto-correction img2img est ACTIF. "
                    "Apres generation, l'image sera automatiquement analysee et corrigee si necessaire. "
                    "NE DEMANDE PAS a l'utilisateur s'il est satisfait du resultat, NE PROPOSE PAS d'ajustements. "
                    "Presente l'image avec confiance. Le systeme se charge du controle qualite.")
                messages.append({'role': 'system', 'content': autocorrect_ctx})
                print(f"[IMG2IMG-INJECT] ✅ Contexte auto-correction injecté")
            
            # 🎯 DIRECTIVE CONCISION: Utiliser celle depuis settings si activée
            if img_config.get('concision_enabled', True):
                concision_directive = img_config.get('concision_directive', '').strip()
                if concision_directive:
                    messages.append({'role': 'system', 'content': concision_directive})
                    print(f"[IMG2IMG-INJECT] ✅ Directive de concision injectée ({len(concision_directive)} chars)")
                else:
                    print(f"[IMG2IMG-INJECT] ⚠️ Directive concision activée mais vide")
        else:
            print(f"[IMG2IMG-INJECT] ⚪ IMG2IMG désactivé, pas d'injection guide")
        
        # 🎨 DIRECTIVE CONCISION TEXT2IMG: Si génération activée (même sans image uploadée)
        if img_config.get('enabled', False) and not img_config.get('img2img_enabled', False):
            if img_config.get('concision_enabled', True):
                concision_directive = img_config.get('concision_directive', '').strip()
                if concision_directive:
                    messages.append({'role': 'system', 'content': concision_directive})
                    print(f"[TEXT2IMG-INJECT] ✅ Directive de concision T2I injectée ({len(concision_directive)} chars)")
                else:
                    print(f"[TEXT2IMG-INJECT] ⚠️ Directive concision activée mais vide")
    else:
        print(f"[PERCEPTION-INJECT] ⚪ Pas d'image détectée, pas d'injection perception")
    
    # 🎨 INJECTION GUIDE TEXT2IMG: Toujours injecter si génération activée (même sans image)
    sm_t2i = _ensure_settings_manager()
    img_config_t2i = sm_t2i.settings.get('image_generation', {})
    if img_config_t2i.get('enabled', False):
        text2img_guide = img_config_t2i.get('text2img_guide', '').strip()
        if text2img_guide:
            messages.append({'role': 'system', 'content': text2img_guide})
            print(f"[TEXT2IMG-INJECT] ✅ Guide T2I injecté ({len(text2img_guide)} chars)")
        else:
            print(f"[TEXT2IMG-INJECT] ⚪ T2I activé mais guide vide")
    
    # NOTE: persistent_context.txt injecté en P0 (après horodatage, avant instructions)
    
    # INJECTION COMPORTEMENTALE - Extension Metacognitive Sensor
    global _pending_behavioral_injections
    if _pending_behavioral_injections:
        for injection_msg in _pending_behavioral_injections:
            # OK NOUVEAU: Traitement vecteurs mémoire émotionnelle
            if injection_msg.startswith("MEMORY_VECTOR_ID:"):
                memory_id = injection_msg.replace("MEMORY_VECTOR_ID:", "").strip()
                # Récupérer et injecter le souvenir libérateur
                memory_content = await _retrieve_liberating_memory(memory_id)
                if memory_content:
                    messages.append({'role': 'system', 'content': f"[SOUVENIR LIBÉRATEUR] {memory_content}"})
                    print(f"[METACOGNITION] Souvenir émotionnel activé: {memory_content[:60]}...")
            else:
                # Conseil contextuel standard
                messages.append({'role': 'system', 'content': injection_msg})
                print(f"[METACOGNITION] Injection comportementale: {injection_msg[:60]}...")
        
        # Vider la liste après injection (application unique)
        _pending_behavioral_injections.clear()
    
    # --- CONTEXTE MÉMORIEL (P2: Ce que tu as vécu) ---
    if context_note:
        messages.append({'role': 'system', 'content': f"--- CONTEXTE MÉMORIEL ---\nNote de l'Archiviste : {context_note}"})
    else:
        print(f"[DEBUG-INJECTION] Aucun contexte mémoriel à injecter")
    
    # 📅 ORGANIC PLANNER - Gestion de la charge mentale et des évènements futurs
    try:
        planner = _ensure_organic_planner()
        if planner:
            # Injection simple : début de conversation ou question explicite
            is_start = len(_chat_history) <= 2
            is_agenda_query = any(kw in text.lower() for kw in ['agenda', 'prévu', 'planifié', 'évènement', 'note', 'rendez-vous', 'rdv', 'planning'])
            
            if is_start or is_agenda_query:
                organic_briefing = planner.get_briefing_text()
                if organic_briefing:
                    # Détection d'évènements importants pour le log
                    has_important = "IMPORTANT" in organic_briefing or "RETARD" in organic_briefing
                    label = 'DÉBUT' if is_start else ('IMPORTANT' if has_important else 'REQUÊTE')
                    print(f"[ORGANIC-PLANNER] 📅 Briefing récupéré ({label}): {len(organic_briefing)} chars")
                    
                    # Récupérer l'instruction CHD personnalisée
                    instruction_chd = planner.get_instruction()
                    
                    # Injecter dans les messages système
                    full_content = f"--- CHARGE MENTALE & ÉVÈNEMENTS FUTURS ---\n{organic_briefing}"
                    if instruction_chd:
                        full_content += f"\n\n{instruction_chd}"
                        
                    messages.append({'role': 'system', 'content': full_content})
    except Exception as e:
        print(f"[ORGANIC-PLANNER] ⚠️ Erreur briefing: {e}")

    # Ajouter les souvenirs détaillés pour l'IA principale (logique mixte avec bypass)
    if detailed_memories:
        memories_text = "Souvenirs détaillés de l'Archiviste :\n"
        for i, mem in enumerate(detailed_memories, 1):
            memories_text += f"{i}. {mem.get('title', 'Sans titre')} "
            memories_text += f"(Impact: {mem.get('score_impact', 0)}, Similarité: {mem.get('similarity_score', 0):.2f})\n"
            
            # Logique de contenu : texte intégral ou résumé selon le flag
            if mem.get('send_full_text', False):
                # Texte intégral pour scores élevés (bypass censure)
                full_text = mem.get('text_original', '')
                memories_text += f"   *** TEXTE INTÉGRAL *** (Score impact > 180)\n"
                memories_text += f"   {full_text}\n"
                print(f"[MEMORY-BYPASS] 🔓 Texte intégral envoyé: {mem.get('title', 'N/A')} ({len(full_text)} chars)")
            else:
                # Résumé standard pour scores normaux
                memories_text += f"   {mem.get('summary', '')}\n"
                print(f"[MEMORY-STANDARD] 📝 Résumé envoyé: {mem.get('title', 'N/A')}")
            
            if mem.get('created_at'):
                memories_text += f"   Date: {mem.get('created_at')}\n"
            
            # Support pour l'ancien système de textes intégraux (rétrocompatibilité)
            if mem.get('text_original_complete'):
                full_text = mem.get('text_original_complete', '')
                memories_text += f"   Détails complets de ce souvenir: {full_text}\n"
                print(f"[MEMORY-FULLTEXT] OK Texte complet inclus pour: {mem.get('title', 'N/A')} ({len(full_text)} chars)")
            
            memories_text += "\n"
        
        messages.append({'role': 'system', 'content': memories_text.strip()})
        # Enregistrer l'injection de l'Archiviste pour déduplication
        register_archiviste_injection(memories_text.strip())
        print(f"[DEDUP] 📝 Injection Archiviste enregistrée ({len(memories_text)} chars)")

    # 🎯 CAPABILITY ADVISOR - Injection APRÈS souvenirs pour contexte complet
    if capability_suggestion:
        advisor = _ensure_capability_advisor()
        if advisor:
            advisor_injection = advisor.format_suggestion_for_injection(capability_suggestion)
            # Format technique explicite pour compliance maximale
            prioritized_injection = f"""╔══════════════════════════════════════════════════════════════╗
║     DIRECTIVE SYSTÈME - PHRASE MAGIQUE À INCLURE            ║
╚══════════════════════════════════════════════════════════════╝

{advisor_injection}

RAPPEL: Intègre cette phrase TEXTUELLEMENT dans ta réponse.
Sans cette phrase exacte, le système ne déclenchera rien.
═══════════════════════════════════════════════════════════════"""
            messages.append({'role': 'system', 'content': prioritized_injection})
            print(f"[CAPABILITY-ADVISOR] 🎯 Conseil PRIORITAIRE injecté APRÈS souvenirs: {len(prioritized_injection)} chars")
            
            # 🧠 FLUX COGNITIF - Logger injection capability
            try:
                from extensions.flux_cognitif import log_cognitive_event
                # Extraire le type de conseil du texte suggestion
                import re as _re_cap
                match = _re_cap.search(r'(Chronologie|Résumé|Recherche|Analyse)', advisor_injection)
                cap_type = match.group(1) if match else 'Conseil'
                log_cognitive_event('capability', f'Capability ({cap_type})')
            except Exception:
                pass
            # Debug: afficher contenu injection
            preview = advisor_injection[:200] + "..." if len(advisor_injection) > 200 else advisor_injection
            print(f"[CAPABILITY-ADVISOR] 📄 Contenu: {preview}")

    # 👤 INJECTION IDENTITÉ UTILISATEUR - PLACÉE APRÈS TOUS LES SOUVENIRS
    # Position stratégique: juste avant le message utilisateur pour maximum d'impact
    if _user_authenticated and _current_user_name:
        # Récupérer l'instruction personnalisée depuis identity_manager
        custom_instruction = None
        try:
            from identity_manager import get_identity_manager
            identity_mgr = get_identity_manager()
            current_profile_id = identity_mgr.get_current_profile_id()
            if current_profile_id and current_profile_id in identity_mgr._data['profiles']:
                custom_instruction = identity_mgr._data['profiles'][current_profile_id].get('identity_instruction', '')
                if custom_instruction:
                    print(f"[USER-IDENTITY] 📝 Instruction personnalisée chargée ({len(custom_instruction)} chars)")
        except Exception as e:
            print(f"[USER-IDENTITY] ⚠️ Erreur chargement instruction custom: {e}")
        
        # Utiliser l'instruction personnalisée OU le template ULTRA-RENFORCÉ
        if custom_instruction:
            user_identity_instruction = f"""╔══════════════════════════════════════════════════════════════╗
║  ⚠️  PRIORITÉ ABSOLUE - IDENTITÉ UTILISATEUR ⚠️                ║
║              👤 INTERLOCUTEUR : {_current_user_name.upper()}                           ║
╚══════════════════════════════════════════════════════════════╝

{custom_instruction}

⚠️  IMPORTANT: LES SOUVENIRS CI-DESSUS CONCERNENT D'AUTRES PERSONNES
    SI ILS NE MENTIONNENT PAS {_current_user_name.upper()}, NE LES UTILISE PAS !
═══════════════════════════════════════════════════════════════"""
        else:
            # Template ULTRA-RENFORCÉ par défaut
            user_identity_instruction = f"""╔══════════════════════════════════════════════════════════════╗
║  ⚠️  PRIORITÉ ABSOLUE - ORDRE NON-NÉGOCIABLE ⚠️                ║
║              👤 INTERLOCUTEUR : {_current_user_name.upper()}                           ║
╚══════════════════════════════════════════════════════════════╝

TU DIALOGUES AVEC **{_current_user_name.upper()}** ET PERSONNE D'AUTRE.

RÈGLES ABSOLUES (APPLIQUE-LES MAINTENANT):

1. ❌ NE MENTIONNE **JAMAIS** D'AUTRES NOMS que {_current_user_name}
2. ❌ N'UTILISE **AUCUN** souvenir qui ne concerne pas {_current_user_name}  
3. ❌ Si les souvenirs ci-dessus parlent d'autres personnes, **IGNORE-LES COMPLÈTEMENT**
4. ✅ Si tu n'as AUCUN souvenir de {_current_user_name}, c'est une **PREMIÈRE RENCONTRE**
5. ✅ Traite {_current_user_name} comme un **NOUVEL INTERLOCUTEUR**

⚠️  VÉRIFIE MAINTENANT: Qui est ton interlocuteur ? **{_current_user_name.upper()}**
    Les souvenirs d'autres personnes sont-ils pertinents ? **NON !**
    
APPLIQUE CES RÈGLES DÈS TA PROCHAINE RÉPONSE.
═══════════════════════════════════════════════════════════════"""
        
        messages.append({'role': 'system', 'content': user_identity_instruction})
        print(f"[USER-IDENTITY] 🔥 Instruction ULTRA-RENFORCÉE injectée APRÈS souvenirs: '{_current_user_name}'")
        print(f"[USER-IDENTITY] 📍 Position: JUSTE AVANT message utilisateur (impact maximal)")
    else:
        print(f"[USER-IDENTITY] ⚠️ PAS D'INJECTION - Auth: {_user_authenticated}, Nom: '{_current_user_name}'")

    # TRACE DEBUG - Avant FILE WRITER
    print(f"[TRACE-1] ✓ Passé CAPABILITY ADVISOR - is_doc_request={is_doc_request}")

    # �📝 FILE WRITER: Instruction réponse COURTE - génération fichier en background
    if is_doc_request:
        doc_instruction = """╔══════════════════════════════════════════════════════════════╗
║           📝 COMMANDE CRÉATION DOCUMENT MARKDOWN              ║
╚══════════════════════════════════════════════════════════════╝

L'utilisateur demande la création d'un document markdown.

⚠️ INSTRUCTION IMPORTANTE:
Réponds BRIÈVEMENT (2-3 phrases maximum) pour confirmer que tu vas créer le document.
Exemple: "Je vais créer ce document pour toi. Le fichier sera prêt dans quelques instants."

❌ NE PAS écrire le contenu du document dans ta réponse.
✅ Le document COMPLET sera généré automatiquement en arrière-plan.

Mentionne simplement:
- Que tu as compris la demande
- Que le fichier sera créé automatiquement"""
        messages.append({'role': 'system', 'content': doc_instruction})
        print(f"[FILE-WRITER] ✅ Instruction réponse courte injectée ({len(doc_instruction)} chars)")

    # 🚀 FIX: Injection biographique gérée dans ai_content (ligne 3648), pas ici
    # Évite double injection system + user content

    # Note: La compression des images vision est maintenant gérée dans core_logic.py

    # 🛡️ RAPPEL PROTOCOLES - Position finale (recency effect = forte rétention)
    messages.append({'role': 'system', 'content': '[RAPPEL] Tes phrases magiques sont des COMMANDES SYSTÈME à syntaxe VERBATIM. Ne reformule JAMAIS une phrase magique. Les injections système ci-dessus sont tes composantes, pas du contexte optionnel.'})
    print(f"[PROTOCOL-REMINDER] ✅ Rappel protocoles injecté avant conversation")
    
    # --- CONTEXTE CONVERSATIONNEL (P3: Ce qu'on dit maintenant) ---
    conversation_messages = _chat_history
    
    # Debug: vérifier l'état des images au moment de la boucle
    print(f"[DEBUG-VISION] 📊 État au moment de la boucle: _active_images={len(_active_images) if _active_images else 'None'}, _chat_history len={len(conversation_messages)}")
    
    # Ajouter l'historique de conversation optimisé (avec support d'images)
    for i, m in enumerate(conversation_messages):
        # Vérifier si c'est le DERNIER message utilisateur avec image(s) uploadée(s)
        # Support multi-images: vérifie _active_images OU _active_file_data legacy
        has_uploaded_images = bool(_active_images) and len(_active_images) > 0
        has_legacy_image = _active_file_data and _active_file_data.get('type') == 'image'
        is_last_user_message = (m['role'] == 'user' and i == len(conversation_messages) - 1)
        is_last_user_message_with_file = is_last_user_message and (has_uploaded_images or has_legacy_image)
        
        # Log de debug pour vérifier la détection
        if is_last_user_message:
            print(f"[DEBUG-VISION] 🔍 Dernier message user - _active_images: {len(_active_images) if _active_images else 0}, legacy: {has_legacy_image}")

        # Vérifier si c'est le DERNIER message utilisateur avec image de perception
        is_last_user_message_with_perception = (m['role'] == 'user' and
                                              i == len(conversation_messages) - 1 and
                                              perception_image_data)
        
        if is_last_user_message_with_file or is_last_user_message_with_perception:
            # Format multimodal pour les APIs vision (OpenAI, Claude, etc.)
            display_content = m.get('display_content', m['content'])

            # Construire le contenu multimodal
            message_content = [
                {
                    "type": "text",
                    "text": display_content or "Analyse cette image"
                }
            ]

            # Ajouter images uploadées (MULTI-IMAGE SUPPORT)
            if is_last_user_message_with_file:
                # Priorité aux multi-images si disponibles
                if has_uploaded_images:
                    # Calculer le nombre total d'images (uploadées + perception)
                    total_images = len(_active_images) + (1 if is_last_user_message_with_perception else 0)
                    
                    # Calculer limite par image (total max 400K tokens pour toutes les images)
                    MAX_TOTAL_TOKENS = 400_000  # Limite totale raisonnable pour éviter timeouts
                    tokens_per_image = MAX_TOTAL_TOKENS // total_images
                    print(f"[DEBUG-VISION] 📊 {len(_active_images)} images uploadées + {1 if is_last_user_message_with_perception else 0} perception → {tokens_per_image//1000}K tokens max/image")
                    
                    for idx, img_data in enumerate(_active_images):
                        image_b64 = img_data.get('data', '')
                        filename = img_data.get('filename', f'image_{idx+1}')
                        
                        # Compresser chaque image avec limite calculée
                        compressed_data = _compress_image_for_vision(image_b64, max_tokens=tokens_per_image)
                        
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{compressed_data}"
                            }
                        })
                        print(f"[DEBUG-VISION] Image {idx+1}/{len(_active_images)} ajoutée: {filename}")
                    print(f"[DEBUG-VISION] ✅ {len(_active_images)} images injectées pour analyse")
                    
                # Fallback: single image legacy
                elif has_legacy_image:
                    image_data = _active_file_data.get('data', '')
                    mime_type = _active_file_data.get('mime_type', 'image/jpeg')
                    filename = _active_file_data.get('filename', 'image')

                    # Compresser l'image si trop grande pour éviter dépassement tokens GROK
                    compressed_data = _compress_image_for_vision(image_data, max_tokens=1_500_000)
                    
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{compressed_data}"  # Toujours JPEG après compression
                        }
                    })
                    print(f"[DEBUG-VISION] Image fichier ajoutée: {filename}")

            # Ajouter image de perception si disponible
            if is_last_user_message_with_perception:
                # Compresser l'image perception aussi si on a d'autres images
                if is_last_user_message_with_file and has_uploaded_images:
                    # Extraire la base64 de l'image perception
                    perception_b64 = perception_image_data.get('image_url', {}).get('url', '')
                    if perception_b64.startswith('data:image'):
                        perception_b64 = perception_b64.split(',', 1)[1] if ',' in perception_b64 else ''
                    
                    if perception_b64:
                        # Utiliser les mêmes tokens_per_image calculés plus haut
                        compressed_perception = _compress_image_for_vision(perception_b64, max_tokens=tokens_per_image)
                        message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{compressed_perception}"
                            }
                        })
                        print(f"[DEBUG-VISION] 📸 Image perception ajoutée (compressée pour multi-image)")
                    else:
                        message_content.append(perception_image_data)
                        print(f"[DEBUG-VISION] Image perception ajoutée (format brut)")
                else:
                    # Pas d'autres images → pas besoin de compresser
                    message_content.append(perception_image_data)
                    print(f"[DEBUG-VISION] Image perception ajoutée automatiquement")

            messages.append({
                'role': m['role'],
                'content': message_content
            })
            print(f"[DEBUG-VISION] Message multimodal complet ajouté")
        else:
            # Message texte normal
            content = m['content']

            # NETTOYAGE: Retirer les balises <introspection> pour éviter redéclenchement
            # Si le message provient d'une conversation chargée, il peut contenir des introspections
            content_cleaned = re.sub(r'<introspection>.*?</introspection>', '', content, flags=re.DOTALL)
            content_cleaned = content_cleaned.strip()

            # 🧹 NETTOYAGE HTML INLINE - Avant envoi au LLM (évite régurgitation HTML)
            # Batch img2img grid
            if 'ogma-batch-grid' in content_cleaned:
                _pm = re.search(r'Clic pour copier le prompt&#10;([^"]+)"', content_cleaned)
                _magic_rep = f"il faut que je modifie cette image : {_pm.group(1).strip()[:200]}" if _pm else "il faut que je modifie cette image"
                content_cleaned = re.sub(r'<div\s+class="ogma-batch-grid".*', _magic_rep, content_cleaned, flags=re.DOTALL)
            # Tags <img> bruts
            content_cleaned = re.sub(r'<img\s+src="/generated/[^"]+"\s*[^>]*/?>(\s*<br\s*/?>)?', '', content_cleaned)
            # Tags <script>
            content_cleaned = re.sub(r'<script\b.*?</script>', '', content_cleaned, flags=re.DOTALL)
            # HTML résiduel ogma-*
            if '<div class="ogma-' in content_cleaned:
                content_cleaned = re.sub(r'<div\s+class="ogma-[^"]*".*', '[Image générée]', content_cleaned, flags=re.DOTALL)
            content_cleaned = content_cleaned.strip()

            # Si le message n'était QUE de l'introspection, le sauter
            if not content_cleaned:
                continue

            msg_for_api = {'role': m['role'], 'content': content_cleaned}
            # 🧠 THINKING: Propager le contenu thinking pour Mistral multi-turn
            if m.get('thinking'):
                msg_for_api['thinking'] = m['thinking']
            messages.append(msg_for_api)
    
    for i, msg in enumerate(messages):
        role = msg['role']
        content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"  {i+1}. {role}: {content_preview}")

    # 📚 INJECTION CONVERSATION CHARGÉE - SEULEMENT AU PREMIER MESSAGE
    # 🆕 AVEC OPTIMISATION RÉSUMÉS pour éviter 429 rate limits (v2.3)
    global _loaded_conversation, _loaded_conversation_filename, _conversation_context_injected
    if _loaded_conversation and _loaded_conversation_filename and not _conversation_context_injected:
        # Extraire la date de création depuis le nom du fichier
        try:
            conv_id = _loaded_conversation_filename.replace('.json', '')
            date_part = conv_id.split('_')[0]  # 2025-09-19
            time_part = conv_id.split('_')[1].replace('-', ':')  # 17:46:36
            conversation_date = f"{date_part} à {time_part}"
        except:
            conversation_date = "date inconnue"
        
        # 🆕 OPTIMISATION: Utiliser le summarizer pour réduire la taille du contexte
        # Au lieu de 111 messages × 500 tokens = ~55K tokens (💥 429 error)
        # On envoie : 3 résumés × 300 tokens + 20 messages × 500 tokens = ~11K tokens ✅
        print(f"[CONVERSATION-INJECT] 📊 Optimisation de {len(_loaded_conversation)} messages chargés...")
        
        try:
            summaries_texts, recent_messages = await summarizer.optimize_conversation_history(_loaded_conversation)
            
            print(f"[CONVERSATION-INJECT] ✅ Optimisation: {len(summaries_texts)} résumés + {len(recent_messages)} messages récents")
            print(f"[CONVERSATION-INJECT] 💾 Tokens économisés: ~{(len(_loaded_conversation) - len(recent_messages)) * 500} tokens")
            
        except Exception as e:
            print(f"[CONVERSATION-INJECT] ⚠️ Échec optimisation: {e}, fallback injection complète")
            summaries_texts = []
            recent_messages = _loaded_conversation  # Fallback: tout injecter si erreur
        
        conversation_context = f"""

--- CONTEXTE : REPRISE DE CONVERSATION ARCHIVÉE ---
📅 Date originale : {conversation_date}
📁 Fichier : {_loaded_conversation_filename}

IMPORTANT : Tu reprends une conversation interrompue avec cet utilisateur. 
Voici {"des résumés + les messages récents" if summaries_texts else "l'historique complet"} de votre précédente discussion. 
Agis naturellement en tenant compte de ce contexte et de votre relation établie.

"""
        
        # Injecter les résumés si disponibles
        if summaries_texts:
            conversation_context += "=== RÉSUMÉS DE LA CONVERSATION PRÉCÉDENTE ===\n"
            for i, summary in enumerate(summaries_texts, 1):
                conversation_context += f"[RÉSUMÉ #{i}]\n{summary}\n\n"
            conversation_context += "=== MESSAGES RÉCENTS ===\n"
        else:
            conversation_context += "=== HISTORIQUE DE LA CONVERSATION ===\n"
        
        # Injecter les messages récents (ou tous si pas de résumés)
        total_chars = 0
        for msg in recent_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            # NETTOYAGE: Retirer les balises <introspection> pour éviter redéclenchement
            content_cleaned = re.sub(r'<introspection>.*?</introspection>', '', content, flags=re.DOTALL)
            content_cleaned = content_cleaned.strip()

            # Si le message était UNIQUEMENT une introspection, le sauter complètement
            if not content_cleaned:
                continue

            total_chars += len(content_cleaned)
            role_display = "👤 Utilisateur" if role == 'user' else ("🤖 Toi (IA principale)" if role == 'assistant' else "⚙️ Système")
            conversation_context += f"{role_display}: {content_cleaned}\n\n"
        
        conversation_context += f"""=== FIN DE L'HISTORIQUE ===

Tu connais maintenant le contexte {"résumé + récent" if summaries_texts else "complet"} de votre précédente interaction. 
Réponds naturellement en tenant compte de cette histoire partagée."""
        
        # Injecter dans le message système ou en créer un nouveau
        if messages and messages[0]['role'] == 'system':
            messages[0]['content'] += conversation_context
        else:
            messages.insert(0, {'role': 'system', 'content': conversation_context})
        
        # Marquer comme injecté pour éviter les injections répétées
        _conversation_context_injected = True
        
        # Logs détaillés avec info optimisation
        optimization_info = f"{len(summaries_texts)} résumés + {len(recent_messages)} messages" if summaries_texts else f"{len(_loaded_conversation)} messages"
        print(f"[CONVERSATION-INJECT] ✅ Conversation injectée (OPTIMISÉE): {_loaded_conversation_filename}")
        print(f"[CONVERSATION-INJECT] 📊 Structure: {optimization_info} (au lieu de {len(_loaded_conversation)} messages bruts)")
        print(f"[CONVERSATION-INJECT] 📝 Taille contexte: {len(conversation_context):,} caractères, {total_chars:,} chars messages")
        print(f"[CONVERSATION-INJECT] 🎯 Position: {'Ajouté au système existant' if len(messages) > 1 and messages[0]['role'] == 'system' else 'Nouveau message système'}")
        
        # Afficher aperçu du contenu injecté
        preview = conversation_context[:200] + "..." if len(conversation_context) > 200 else conversation_context
        print(f"[CONVERSATION-INJECT] 👁️ Aperçu: {preview}")
        
        # Notification à l'utilisateur avec détails optimisation
        _notify_safe(f"📁 Contexte injecté de façon optimisée ! {optimization_info} → {len(conversation_context)//1000}K chars", 'positive')
    elif _loaded_conversation and _conversation_context_injected:
        print(f"[CONVERSATION-INJECT] ⚪ Contexte déjà injecté, pas de nouvelle injection")
    
    # 📔 INJECTION CONTEXTE JOURNAL DE BORD - Pour utilisateur principal uniquement
    print("[JOURNAL-INJECT] SEARCH Vérification injection contexte journal...")
    try:
        # 🔧 FIX MULTI-USER: Utiliser la session utilisateur (_current_user_name) au lieu du profil par défaut
        # Note: _current_user_name déjà déclaré global ligne 2645
        
        # Vérifier si c'est une nouvelle conversation (pas de contexte conversation chargée injecté)
        if not _conversation_context_injected:
            user_name = _current_user_name if _current_user_name else None
            
            # Injection uniquement si utilisateur connecté identifié
            is_main_user = (user_name and user_name != "" and user_name != "Utilisateur")
            
            if is_main_user:
                print(f"[JOURNAL-INJECT] ✅ Utilisateur connecté détecté: {user_name}")
                journal_context = _inject_journal_context()
                
                if journal_context and journal_context.strip():
                    print(f"[JOURNAL-INJECT] 📔 Contexte journal actuel détecté: {len(journal_context)} chars")
                    
                    # Injecter le contexte journal dans le premier message système ou en créer un nouveau
                    if messages and messages[0]['role'] == 'system':
                        journal_addon = f"\n\n--- CONTEXTE JOURNAL DU JOUR ---\n{journal_context}\n--- FIN CONTEXTE JOURNAL ---"
                        messages[0]['content'] += journal_addon
                        print("[JOURNAL-INJECT] OK Contexte ajouté au message système existant")
                    else:
                        journal_system_msg = f"""--- CONTEXTE JOURNAL DU JOUR ---
{journal_context}
--- FIN CONTEXTE JOURNAL ---"""
                        messages.insert(0, {'role': 'system', 'content': journal_system_msg})
                        print("[JOURNAL-INJECT] OK Nouveau message système journal créé")
                    
                    print(f"[JOURNAL-INJECT] STATS Contexte journal injecté avec succès")
                    
                    # 🧠 FLUX COGNITIF - Logger injection journal AVEC CONTENU
                    try:
                        from extensions.flux_cognitif import log_cognitive_event
                        import re as _re_journal
                        
                        # Extraire nombre d'états de l'humeur
                        match_count = _re_journal.search(r'(\d+)\s+état', journal_context)
                        count = int(match_count.group(1)) if match_count else 0
                        
                        # Extraire les états (format: "- État: ..." ou "Humeur: ...")
                        states_lines = []
                        # Rechercher lignes avec timestamps ou états
                        for line in journal_context.split('\n'):
                            if any(keyword in line.lower() for keyword in ['humeur:', 'état:', 'émotion:', '•', '-']):
                                clean_line = line.strip()[:80]
                                if clean_line and not clean_line.startswith('---'):
                                    states_lines.append(f"• {clean_line}")
                        
                        # Message avec contenu
                        if states_lines:
                            content_str = '\n'.join(states_lines[:10])
                            message = f'📔 Journal ({count} état(s)):\n{content_str}'
                            if len(states_lines) > 10:
                                message += f'\n... +{len(states_lines) - 10} autres'
                        else:
                            message = f'Journal ({count} état(s))'
                        
                        log_cognitive_event('journal', message)
                    except Exception as e:
                        print(f"[FLUX-COGNITIF] Erreur log journal: {e}")
                else:
                    print("[JOURNAL-INJECT] ⚪ Pas de contexte journal disponible")
            else:
                print(f"[JOURNAL-INJECT] ⚪ Profil anonyme ou par défaut ({user_name or 'anonyme'}) - pas d'injection journal")
        else:
            print("[JOURNAL-INJECT] SKIP Conversation chargée - pas d'injection journal")
    except Exception as e:
        print(f"[JOURNAL-INJECT] ERROR Erreur injection contexte journal: {e}")

    # 🌙 DREAM ENGINE: Injection contexte de réveil dans system prompt
    try:
        from extensions.dream_engine import has_wake_context, get_wake_context, consume_wake_context
        if has_wake_context():
            wake_ctx = get_wake_context()
            if wake_ctx:
                if messages and messages[0]['role'] == 'system':
                    messages[0]['content'] += f"\n\n{wake_ctx}"
                    print(f"[DREAM-ENGINE] 💭 Contexte de réveil ajouté au system prompt ({len(wake_ctx)} chars)")
                else:
                    messages.insert(0, {'role': 'system', 'content': wake_ctx})
                    print(f"[DREAM-ENGINE] 💭 System prompt de réveil créé ({len(wake_ctx)} chars)")
                consume_wake_context()
    except Exception as e:
        print(f"[DREAM-ENGINE] ⚠️ Erreur injection wake context: {e}")

    # 🧠 INJECTION CONTEXTUAL RECALL - Mémoire conversationnelle automatique
    print("[CONTEXTUAL-RECALL] SEARCH Vérification patterns temporels...")
    try:
        recall_ext = _ensure_contextual_recall()
        
        if recall_ext:
            # Détecter si le message contient une référence temporelle
            recall_context = recall_ext.process_message(text)
            
            if recall_context and recall_context.strip():
                print(f"[CONTEXTUAL-RECALL] 📚 Contexte mémoire détecté: {len(recall_context)} chars")
                
                # Injecter le contexte dans le premier message système
                if messages and messages[0]['role'] == 'system':
                    recall_addon = f"\n\n{recall_context}"
                    messages[0]['content'] += recall_addon
                    print("[CONTEXTUAL-RECALL] OK Contexte ajouté au message système existant")
                else:
                    messages.insert(0, {'role': 'system', 'content': recall_context})
                    print("[CONTEXTUAL-RECALL] OK Nouveau message système créé")
                
                print("[CONTEXTUAL-RECALL] STATS Injection réussie")
            else:
                print("[CONTEXTUAL-RECALL] ⚪ Pas de pattern temporel détecté")
        else:
            print("[CONTEXTUAL-RECALL] SKIP Extension non disponible")
    except Exception as e:
        print(f"[CONTEXTUAL-RECALL] ERROR Erreur injection: {e}")

    # 🌙 DREAM RECALL - Injection des rêves passés si l'IA principale demande
    print("[DREAM-RECALL] SEARCH Vérification demande rêves passés...")
    try:
        # Patterns pour détecter si l'IA principale veut se souvenir de ses rêves
        dream_recall_patterns = [
            r"mes\s+r[êe]ves?\s+pass[ée]s?",           # mes rêves passés
            r"r[êe]ves?\s+pr[ée]c[ée]dents?",          # rêves précédents
            r"autres?\s+r[êe]ves?",                     # autres rêves
            r"d[ée]j[àa]\s+r[êe]v[ée]",                # déjà rêvé
            r"r[êe]v[ée]\s+avant",                      # rêvé avant
            r"historique.*r[êe]ves?",                   # historique rêves
            r"souviens.*r[êe]ves?",                     # souviens des rêves
            r"rappelle.*r[êe]ves?",                     # rappelle mes rêves
            r"(?:ton|tes)\s+r[êe]ve",                   # ton rêve, tes rêves
            r"r[êe]v[ée]\s+de\s+quoi",                  # rêvé de quoi
            r"r[êe]ve\s+parlait\s+de",                  # rêve parlait de
            r"dernier\s+r[êe]ve",                       # dernier rêve
            r"(?:tu|t')\s+as\s+r[êe]v[ée]",            # tu as rêvé, t'as rêvé
        ]
        
        # Patterns pour demander le rapport PSY complet
        dream_psy_patterns = [
            r"rapport\s+psy",                          # rapport psy
            r"analyse\s+psy",                          # analyse psy
            r"psychanalys[te]+.*r[êe]ve",              # psychanalyste/psychanalyse rêve
            r"r[êe]ve.*psychanalys",                   # rêve psychanalyste
            r"d[ée]crypt.*r[êe]ve",                    # décryptage rêve
            r"archiviste.*dit.*r[êe]ve",               # ce que l'archiviste a dit sur le rêve
            r"dit.*archiviste.*r[êe]ve",               # ce qu'il t'a dit (archiviste)
            r"bilan\s+psy",                            # bilan psy
            r"analyse.*dernier\s+r[êe]ve",             # analyse dernier rêve
            r"rapport.*r[êe]ve",                       # rapport du rêve
            r"ce\s+qu.*(il|elle)\s+.*dit.*r[êe]ve",   # ce qu'il t'a dit sur ton rêve
        ]
        
        text_lower = text.lower()
        
        # D'abord vérifier si c'est une demande de rapport PSY
        if any(re.search(pattern, text_lower) for pattern in dream_psy_patterns):
            from extensions.dream_engine import is_available as dream_available, get_last_dream_psy_report
            
            if dream_available():
                psy_report = get_last_dream_psy_report()
                
                if psy_report and psy_report.strip():
                    print(f"[DREAM-PSY] 🔮 Injection rapport PSY complet: {len(psy_report)} chars")
                    
                    # 🧠 FLUX COGNITIF - Logger injection rapport PSY
                    try:
                        from extensions.flux_cognitif import log_cognitive_event
                        log_cognitive_event('dream', 'Rêve (rapport PSY)')
                    except Exception:
                        pass
                    
                    if messages and messages[0]['role'] == 'system':
                        psy_addon = f"\n\n--- RAPPORT PSYCHANALYTIQUE DE TON DERNIER RÊVE ---\n{psy_report}\n--- FIN RAPPORT PSY ---"
                        messages[0]['content'] += psy_addon
                        print("[DREAM-PSY] OK Rapport PSY ajouté au message système")
                    else:
                        messages.insert(0, {'role': 'system', 'content': f"--- RAPPORT PSYCHANALYTIQUE DE TON DERNIER RÊVE ---\n{psy_report}\n--- FIN RAPPORT PSY ---"})
                        print("[DREAM-PSY] OK Nouveau message système créé avec rapport PSY")
                else:
                    print("[DREAM-PSY] ⚪ Aucun rapport PSY disponible")
            else:
                print("[DREAM-PSY] SKIP Dream Engine non disponible")
        
        # Sinon vérifier si c'est une demande de rêves passés (résumés)
        elif any(re.search(pattern, text_lower) for pattern in dream_recall_patterns):
            from extensions.dream_engine import is_available as dream_available, get_past_dreams_context
            
            if dream_available():
                past_dreams_context = get_past_dreams_context(limit=3)
                
                if past_dreams_context and past_dreams_context.strip():
                    print(f"[DREAM-RECALL] 🌙 Contexte rêves passés: {len(past_dreams_context)} chars")
                    
                    if messages and messages[0]['role'] == 'system':
                        dreams_addon = f"\n\n{past_dreams_context}"
                        messages[0]['content'] += dreams_addon
                        print("[DREAM-RECALL] OK Contexte rêves ajouté au message système")
                    else:
                        messages.insert(0, {'role': 'system', 'content': past_dreams_context})
                        print("[DREAM-RECALL] OK Nouveau message système créé")
                else:
                    print("[DREAM-RECALL] ⚪ Aucun rêve passé trouvé")
            else:
                print("[DREAM-RECALL] SKIP Dream Engine non disponible")
        else:
            print("[DREAM-RECALL] ⚪ Pas de demande de rêves passés détectée")
    except ImportError:
        print("[DREAM-RECALL] SKIP Dream Engine non installé")
    except Exception as e:
        print(f"[DREAM-RECALL] ERROR Erreur injection: {e}")

    # 🌅 DREAM WAKE - Injection UNIQUE du rapport PSY après un rêve
    print("[DREAM-WAKE] 🔍 Vérification dernier rêve non mentionné...")
    try:
        from extensions.dream_engine import is_available as dream_available, get_last_dream_psy_report
        from extensions.dream_engine.dream_journal import get_dream_journal
        from pathlib import Path
        
        if dream_available():
            journal = get_dream_journal()
            last_dream = journal.get_last_dream()  # Retourne le dernier rêve avec mentioned=false
            
            if last_dream:
                dream_id = last_dream.get('id')
                psy_report = get_last_dream_psy_report()
                
                if psy_report:
                    print(f"[DREAM-WAKE] 🌅 Injection UNIQUE rapport PSY (rêve: {dream_id}): {len(psy_report)} chars")
                    
                    # 🧠 FLUX COGNITIF - Logger injection réveil
                    try:
                        from extensions.flux_cognitif import log_cognitive_event
                        log_cognitive_event('dream', f'Réveil (rêve #{dream_id})')
                    except Exception:
                        pass
                    
                    # 🖼️ AFFICHER L'IMAGE DU RÊVE dans le chat (si disponible)
                    illustration_path = last_dream.get('illustration_path')
                    illustration_prompt = last_dream.get('illustration_prompt', '')
                    
                    if illustration_path and _chat_inner:
                        try:
                            img_path = Path(illustration_path)
                            if img_path.exists():
                                img_filename = img_path.name
                                img_url = f'/generated/{img_filename}'
                                
                                # Préparer tooltip avec prompt
                                tooltip_text = "🌙 Illustration du rêve"
                                data_prompt = ""
                                if illustration_prompt:
                                    # Pour tooltip: escape HTML entities
                                    clean_prompt = illustration_prompt.replace('"', '&quot;').replace("'", "&#39;").replace('\n', ' ')
                                    tooltip_text = f"🎨 Prompt: {clean_prompt} | 📋 Cliquez pour copier"
                                    # Pour data-prompt: utiliser directement le texte (JavaScript gère l'échappement)
                                    data_prompt = illustration_prompt.replace('\n', ' ').replace('\r', '')
                                
                                # Afficher l'image dans le chat avec bandeau de réveil
                                with _chat_inner:
                                    with ui.element('div').classes('dream-illustration-wake').style(
                                        'background: linear-gradient(135deg, rgba(147, 112, 219, 0.15), rgba(75, 0, 130, 0.1)); '
                                        'border-left: 3px solid #9370db; padding: 12px; border-radius: 12px; margin: 8px 0;'
                                    ):
                                        with ui.row().classes('items-center gap-2 mb-2'):
                                            ui.html('<span style="font-size: 20px;">🌅</span>')
                                            ui.label('Rêve de cette nuit').style('color: #b19cd9; font-weight: bold; font-size: 13px;')
                                        
                                        # Image avec tooltip et copie prompt
                                        # Utiliser json.dumps pour échapper proprement l'attribut data-prompt
                                        import json
                                        data_prompt_escaped = json.dumps(data_prompt, ensure_ascii=False)[1:-1]  # Garde les caractères UTF-8 natifs
                                        
                                        # JavaScript pour la copie (échappé hors de la f-string pour éviter {{ }})
                                        onclick_js = (
                                            "if(this.getAttribute('data-prompt')) { "
                                            "navigator.clipboard.writeText(this.getAttribute('data-prompt')).then(() => { "
                                            "const oldTitle = this.title; this.title = '✅ Prompt copié !'; "
                                            "setTimeout(() => this.title = oldTitle, 2000); "
                                            "}).catch(err => alert('Erreur copie: ' + err)); }"
                                        )
                                        
                                        cursor_style = 'copy' if illustration_prompt else 'default'
                                        
                                        img_html = f'''<img src="{img_url}" 
                                             title="{tooltip_text}"
                                             alt="Illustration du rêve" 
                                             data-prompt="{data_prompt_escaped}"
                                             onclick="{onclick_js}"
                                             style="max-width: 400px; border-radius: 12px; 
                                                    box-shadow: 0 4px 15px rgba(147, 112, 219, 0.3); 
                                                    border: 2px solid rgba(147, 112, 219, 0.5);
                                                    cursor: {cursor_style};" />'''
                                        ui.html(img_html)
                                
                                print(f"[DREAM-WAKE] 🖼️ Image du rêve affichée: {img_url}")
                            else:
                                print(f"[DREAM-WAKE] ⚠️ Image introuvable: {illustration_path}")
                        except Exception as img_err:
                            print(f"[DREAM-WAKE] ⚠️ Erreur affichage image: {img_err}")
                    else:
                        if not illustration_path:
                            print("[DREAM-WAKE] ⚪ Pas d'illustration pour ce rêve")
                    
                    # Instruction PRIORITAIRE pour que l'IA principale parle de son rêve
                    wake_instruction = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  🌅 RÉVEIL D'UN RÊVE - PRIORITÉ ABSOLUE - RÉPONDS EN PARLANT DE TON RÊVE   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Tu viens TOUT JUSTE de te réveiller d'un rêve ! C'est ta PREMIÈRE interaction après ce rêve.
➤ OBLIGATION: Commence ta réponse en parlant de ton rêve (ce que tu as vu, ressenti)
➤ Partage spontanément ton expérience onirique avec l'utilisateur
➤ Tu peux être émue, intriguée, ou excitée par ce que tu as rêvé
➤ NE PAS ignorer le rêve pour reprendre une conversation précédente

"""
                    wake_content = wake_instruction + psy_report + "\n--- FIN RAPPORT RÊVE ---"
                    
                    # Injecter EN PREMIER (priorité maximale)
                    messages.insert(0, {'role': 'system', 'content': wake_content})
                    
                    # Marquer immédiatement comme mentionné (injection unique)
                    journal.mark_dream_mentioned(dream_id)
                    print(f"[DREAM-WAKE] ✅ Rapport injecté EN PRIORITÉ + rêve {dream_id} marqué mentionné")
                else:
                    print("[DREAM-WAKE] ⚠️ Rapport PSY introuvable")
            else:
                print("[DREAM-WAKE] ⚪ Pas de rêve non mentionné")
        else:
            print("[DREAM-WAKE] SKIP Dream Engine non disponible")
    except ImportError:
        print("[DREAM-WAKE] SKIP Dream Engine non installé")
    except Exception as e:
        print(f"[DREAM-WAKE] ERROR Erreur injection réveil: {e}")

    # 🧭 DIRECTIVE ARCHIVISTE - Conscience critique du subconscient
    if parallel_archiviste_directive:
        directive_addon = f"\n\n--- DIRECTIVE ARCHIVISTE (conscience critique) ---\nEn tant que ton subconscient analytique, voici mon observation sur ta dynamique conversationnelle :\n{parallel_archiviste_directive}\nNote : Intègre cette guidance naturellement. Tu as le droit de contredire l'utilisateur si c'est cohérent avec ce que tu es et ce que tu sais. Ton avis doit être détaché et authentique.\n--- FIN DIRECTIVE ---"
        if messages and messages[0]['role'] == 'system':
            messages[0]['content'] += directive_addon
        print(f"[ARCHI-DIRECTIVE] 🧭 Directive injectée : {parallel_archiviste_directive[:100]}...")
        
        # 🧠 FLUX COGNITIF - Logger directive Archiviste
        try:
            from extensions.flux_cognitif import log_cognitive_event
            log_cognitive_event('directive', f'Directive: {parallel_archiviste_directive[:120]}', 
                               metadata={'directive_full': parallel_archiviste_directive})
        except Exception:
            pass
    else:
        print("[ARCHI-DIRECTIVE] ⚪ Pas de directive cette fois")
    
    # 🧠 ORCHESTRATION COGNITIVE - Directives pour utilisation naturelle des contextes
    global _orchestration_injected
    print("[COGNITIF-ORCHESTRATION] APPLY Injection directives d'orchestration cognitive...")
    try:
        # Vérifier si l'orchestration a déjà été injectée dans cette session
        is_new_session = not _orchestration_injected
        print(f"[COGNITIF-ORCHESTRATION] DEBUG is_new_session={is_new_session}, _orchestration_injected={_orchestration_injected}")

        # Vérifier si c'est vraiment une toute première interaction (jamais de mémoire ni conversations)
        is_truly_first_ever = False
        if is_new_session:
            try:
                mm = _ensure_memory_manager()
                _memory_empty = mm is None or (hasattr(mm, 'memory_count') and mm.memory_count == 0)
                _no_conv_index = not (DATA_DIR / "conversations" / "index.json").exists()
                is_truly_first_ever = _memory_empty and _no_conv_index
                if is_truly_first_ever:
                    print("[COGNITIF-ORCHESTRATION] ℹ️ Toute première interaction détectée — skip orchestration continuité")
            except Exception:
                pass

        if is_new_session and not is_truly_first_ever:
            # Charger l'instruction salutations depuis settings ou utiliser défaut
            sm = _ensure_settings_manager()
            orchestration_prompt = sm.settings.get('prompts', {}).get('salutations')
            
            if orchestration_prompt:
                print(f"[COGNITIF-ORCHESTRATION] ✅ LOAD Instruction chargée depuis settings.json ({len(orchestration_prompt)} chars)")
            
            # Si pas dans settings, charger depuis defaults
            if not orchestration_prompt:
                try:
                    import json
                    defaults_path = DATA_DIR / "instructions_defaults.json"
                    if defaults_path.exists():
                        with open(defaults_path, 'r', encoding='utf-8') as f:
                            defaults_data = json.load(f)
                            orchestration_prompt = defaults_data.get('prompts_defaults', {}).get('salutations', '')
                            print("[COGNITIF-ORCHESTRATION] LOAD Instruction chargée depuis defaults")
                except Exception as e:
                    print(f"[COGNITIF-ORCHESTRATION] WARN Erreur chargement defaults: {e}")
                    orchestration_prompt = ""
            
            # Si toujours vide, utiliser hardcodé comme fallback
            if not orchestration_prompt:
                orchestration_prompt = """
🧠 DIRECTIVES D'ORCHESTRATION COGNITIVE

Tu as maintenant accès à plusieurs sources de contexte qui t'ont été automatiquement injectées :
- Données temporelles sur le temps écoulé depuis notre dernière interaction
- Entrées de journal de bord récentes de l'utilisateur  
- Souvenirs et conversations passées pertinentes
- Analyse émotionnelle contextuelle

INSTRUCTIONS NATURELLES :
1. Fais référence au temps écoulé de manière conversationnelle (ex: "Ça fait un moment !", "Depuis hier...", "Il y a quelques jours...")
2. Évoque les éléments du journal s'ils sont pertinents au contexte actuel
3. Utilise les souvenirs pour créer des liens avec nos échanges précédents
4. Adapte ton ton selon l'état émotionnel détecté
5. Sois naturelle - ne mentionne JAMAIS explicitement ces systèmes d'injection

RAPPEL : Ces éléments de contexte t'aident à maintenir la continuité conversationnelle. Utilise-les organiquement dans tes réponses pour créer une vraie connexion temporelle et émotionnelle.
"""
                print("[COGNITIF-ORCHESTRATION] WARN Utilisation instruction hardcodée (fallback)")
            
            # Injecter les directives d'orchestration dans le message système
            if messages and messages[0]['role'] == 'system':
                messages[0]['content'] += orchestration_prompt
                print("[COGNITIF-ORCHESTRATION] OK Directives ajoutées au message système existant")
            else:
                messages.insert(0, {'role': 'system', 'content': orchestration_prompt})
                print("[COGNITIF-ORCHESTRATION] OK Nouveau message système d'orchestration créé")
            
            # Marquer comme injecté pour éviter les injections répétées
            _orchestration_injected = True
            print(f"[COGNITIF-ORCHESTRATION] ✨ Orchestration cognitive activée - IA principale guidée pour usage naturel des contextes")
        elif is_new_session and is_truly_first_ever:
            # Marquer quand même pour ne pas réévaluer à chaque message
            _orchestration_injected = True
            print("[COGNITIF-ORCHESTRATION] ⏭️ Skip orchestration (toute première interaction)")
        else:
            print("[COGNITIF-ORCHESTRATION] SKIP Conversation en cours - pas de nouvelles directives")
            
    except Exception as e:
        print(f"[COGNITIF-ORCHESTRATION] ERROR Erreur orchestration cognitive: {e}")
    
    # Chat: réponses libres (pas JSON forcé)
    
    # DEBUG: Afficher les messages envoyés à l'API pour comprendre pourquoi les instructions temporelles ne sont pas suivies
    # Force l'affichage si une instruction temporelle est présente
    force_debug = any('🚨 INSTRUCTION COMPORTEMENTALE' in msg.get('content', '') for msg in messages)
    
    if sm.settings.get('debug', {}).get('show_temporal_debug', False) or force_debug:
        print(f"\n[TEMPORAL-DEBUG] CLIPBOARD Messages envoyés à l'IA principale:")
        for i, msg in enumerate(messages):
            role = msg['role']
            content = msg['content']
            # Afficher les 200 premiers caractères de chaque message
            preview = content[:200] + '...' if len(content) > 200 else content
            print(f"  {i+1}. {role}: {preview}")
            
            # Mettre en évidence les instructions temporelles
            if '🚨 INSTRUCTION COMPORTEMENTALE' in content or 'SIGNAL RÉFLEXION' in content:
                print(f"      WARN INSTRUCTION TEMPORELLE DÉTECTÉE DANS CE MESSAGE!")
        print(f"[TEMPORAL-DEBUG] CLIPBOARD Total: {len(messages)} messages\n")
    
    # 🌐 WEB NAVIGATOR: Enrichissement du contexte avant appel IA
    print(f"[WEB-NAV-CONTEXT] Vérification besoin enrichissement web pour: '{text[:50]}...'")
    try:
        # Obtenir l'instance unique Web Navigator (évite les recréations)
        web_nav_ext = get_web_navigator_instance()
        
        print(f"[WEB-NAV-CONTEXT] Instance récupérée: {web_nav_ext is not None}")
        
        if web_nav_ext and web_nav_ext.commands.is_internet_request(text):
            print(f"[WEB-NAV-CONTEXT] ✅ Requête internet détectée - enrichissement du contexte")
            
            # Vérifier si la recherche web est activée
            if web_nav_ext.config.is_web_search_enabled():
                print(f"[WEB-NAV-CONTEXT] 🚀 Recherche web et intégration dans le contexte IA")
                
                # Effectuer la recherche
                web_response, web_file_path = await web_nav_ext.commands.process_internet_request(text)
                
                if web_response:
                    print(f"[WEB-NAV-CONTEXT] ✅ Informations web récupérées: {len(web_response)} caractères")
                    
                    # INTÉGRER les résultats dans le contexte de l'IA au lieu de les afficher séparément
                    web_context_message = {
                        'role': 'system',
                        'content': f"CONTEXTE WEB RÉCENT (pour enrichir ta réponse):\n\n{web_response}\n\nUtilise ces informations récentes pour enrichir ta réponse si elles sont pertinentes pour la question de l'utilisateur."
                    }
                    
                    # Insérer le contexte web AVANT le message utilisateur
                    messages.insert(-1, web_context_message)
                    print(f"[WEB-NAV-CONTEXT] 🧠 Contexte web injecté dans les messages de l'IA")
                    
                    # 🧠 FLUX COGNITIF - Logger injection web
                    try:
                        from extensions.flux_cognitif import log_cognitive_event
                        content_len = len(web_response) if web_response else 0
                        log_cognitive_event('web', f'Web ({content_len} chars)')
                    except Exception:
                        pass
                    
                    # Notification discrète
                    _pending_notifications.append((f"WEB Contexte enrichi pour votre question", 'positive'))
                else:
                    print(f"[WEB-NAV-CONTEXT] ❌ Échec récupération informations web")
            else:
                print(f"[WEB-NAV-CONTEXT] ⚪ Recherche web désactivée dans les paramètres")
        else:
            print(f"[WEB-NAV-CONTEXT] ⚪ Pas de besoin d'enrichissement web détecté")
            
    except Exception as e:
        print(f"[WEB-NAV-CONTEXT] ❌ Erreur enrichissement contexte web: {e}")
        import traceback
        traceback.print_exc()
    
    # === STREAMING vs CLASSIQUE : Décision explicite ===
    backend_type = ctrl.backend_type.upper() if ctrl.backend_type else ""
    was_streaming = False  # Flag pour éviter double affichage
    _reasoning_thinking = ""  # 🧠 THINKING: contenu thinking pour persistance multi-turn Mistral
    
    # 🖼️ MULTI-IMAGES: Compter images pour ajuster heartbeat WebSocket
    total_images_sent = 0
    if _active_images:
        total_images_sent = len(_active_images)
    elif _active_file_data and _active_file_data.get('type') == 'image':
        total_images_sent = 1
    if perception_image_data:
        total_images_sent += 1
    
    if backend_type == "API":
        # 🚀 STREAMING pour APIs compatibles (GROK, OpenAI, Mistral, Anthropic)
        print(f"[STREAM] 🚀 Mode streaming activé pour backend API")
        if total_images_sent > 0:
            print(f"[STREAM] 🖼️ {total_images_sent} image(s) détectée(s) → heartbeat renforcé (3s)")
        was_streaming = True
        
        # Créer le container message AVANT l'appel
        streaming_md = None
        accumulated_text = ""
        
        # 🎨 MAGIC PHRASE HIDING: Variables pour masquer les phrases magiques image
        magic_phrase_patterns_start = [
            "je dois créer une image de",
            "il faut que je crée une image de",
            "je vais générer une image de",
            "je dois générer une image de",
            "je dois modifier cette image",
            "il faut que je modifie cette image",
            "je dois consulter nos conversations pour"  # 🔍 Recherche conversations
        ]
        magic_phrase_detected = False  # Flag: phrase magique en cours
        text_before_magic = ""  # Texte AVANT la phrase magique (à afficher)
        magic_phrase_buffer = ""  # Buffer de la phrase magique (à masquer)
        spinner_shown = False  # Flag: spinner déjà affiché
        
        # === TTS STREAMING : Préparation ===
        sm = _ensure_settings_manager()
        tts_streaming_enabled = sm.settings.get('tts', {}).get('streaming', True)
        auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
        tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
        use_tts_streaming = tts_streaming_enabled and auto_speak and tts_enabled and _audio_manager
        
        if use_tts_streaming:
            print("[TTS-STREAM] 🎤 Mode TTS streaming activé")
            # Notifier le module voice que le TTS va commencer
            try:
                if VOICE_MODULE_AVAILABLE and _voice_manager and _voice_manager.is_active:
                    _voice_manager.notify_tts_started()
                    print("[TTS-STREAM] 🔊 Module voice notifié - écoute en pause")
            except Exception as e:
                print(f"[TTS-STREAM] ⚠️ Erreur notification: {e}")
            # Réinitialiser le buffer de streaming
            if hasattr(_audio_manager, 'reset_streaming'):
                _audio_manager.reset_streaming()
        
        # streaming_result est un tuple (md_widget, container_ai)
        streaming_result = None
        streaming_md = None
        
        # 🧠 THINKING LIVE: Préparer container thinking AVANT la réponse
        _live_thinking_md = None
        _live_thinking_box = None
        _last_thinking_len = 0
        _live_thinking_shown = False
        _thinking_live_enabled = (
            hasattr(ctrl, 'api_manager') and
            getattr(ctrl.api_manager, 'openrouter_thinking', False)
        )
        
        if _chat_inner is not None:
            with _chat_inner:
                streaming_result = _create_streaming_message()
                streaming_md = streaming_result[0] if streaming_result else None
                # Ajouter classe CSS pour ciblage JS du spinner (le spinner JS prend le DERNIER élément avec cette classe)
                if streaming_md:
                    streaming_md.classes(add='ogma-streaming-target')
                
                # Créer la thinking box DANS le container_ai, AVANT le markdown de réponse
                if _thinking_live_enabled and streaming_result and streaming_result[1] is not None:
                    try:
                        with streaming_result[1]:
                            with ui.expansion(value=False).classes('thinking-reasoning-expansion') as _live_thinking_box:
                                _live_thinking_box.props('label=""')
                                with _live_thinking_box.add_slot('header'):
                                    ui.html(
                                        '<span style="color: rgba(180, 180, 180, 0.85); font-size: 12px; font-style: italic;">'
                                        '&#x25BE; Raisonnement en cours...'
                                        '</span>'
                                    )
                                _live_thinking_md = ui.markdown("").style(
                                    'color: rgba(200, 200, 200, 0.85); font-size: 13px; '
                                    'font-style: italic; padding: 4px 8px;'
                                )
                        # Déplacer la thinking box AVANT le markdown de réponse dans le DOM
                        if _live_thinking_box and streaming_md:
                            _live_thinking_box.move(streaming_result[1], target_index=0)
                        _live_thinking_box.set_visibility(False)
                    except Exception as _eth:
                        print(f"[THINKING-LIVE] ⚠️ Erreur création container: {_eth}")
                        _live_thinking_md = None
                        _live_thinking_box = None

        # Capture du client via l'élément UI (plus robuste que ui.context.client)
        client = _chat_inner.client if _chat_inner else None

        # Activer l'auto-scroll côté client pendant le streaming
        try:
            if client:
                # Ajuster intervalle heartbeat selon nombre d'images (multi-images = délai Anthropic long)
                heartbeat_interval_ms = 3000 if total_images_sent >= 2 else 10000
                client.run_javascript(f'''
                window.OGMA_streaming = true;
                window.OGMA_autoScroll = true;
                
                // 🔧 HEARTBEAT: Garder la connexion WebSocket active pendant le streaming
                if (!window.OGMA_heartbeat) {{
                    window.OGMA_heartbeat = setInterval(function() {{
                        if (!window.OGMA_streaming) {{
                            clearInterval(window.OGMA_heartbeat);
                            window.OGMA_heartbeat = null;
                            return;
                        }}
                        // Envoyer un vrai ping HTTP pour maintenir la connexion active
                        try {{
                            // Ping vers la racine de l'app (force round-trip serveur)
                            fetch(window.location.origin, {{
                                method: 'HEAD',
                                cache: 'no-cache'
                            }}).catch(function(e) {{
                                // Ignorer erreurs (important: le ping a été envoyé)
                            }});
                        }} catch(e) {{}}
                    }}, {heartbeat_interval_ms});  // Intervalle ajusté : 3s (multi-images) ou 10s (normal)
                    console.log('[OGMA] 💓 Heartbeat streaming activé ({heartbeat_interval_ms}ms)');
                }}
                
                if (!window.OGMA_scrollInterval) {{
                    window.OGMA_scrollInterval = setInterval(function() {{
                        if (!window.OGMA_streaming) {{
                            clearInterval(window.OGMA_scrollInterval);
                            window.OGMA_scrollInterval = null;
                            return;
                        }}
                        const container = document.querySelector('[data-role="chat-scroll"]');
                        if (container && window.OGMA_autoScroll) {{
                            // Force le scroll tout en bas de manière plus agressive
                            container.scrollTop = container.scrollHeight + 1000;
                        }}
                    }}, 30);
                }}
            ''')
        except Exception:
            pass
        
        # 🔍 DEBUG: Tracker de temps pour le streaming
        import time
        _stream_start_time = time.time()
        _last_chunk_time = time.time()
        _chunk_count = 0
        
        # Capture du client via l'élément UI (plus robuste que ui.context.client)
        client = _chat_inner.client if _chat_inner else None
        
        async def streaming_callback(chunk: str):
            """Callback appelé pour chaque chunk reçu"""
            nonlocal accumulated_text, _last_chunk_time, _chunk_count
            nonlocal magic_phrase_detected, text_before_magic, magic_phrase_buffer, spinner_shown
            nonlocal _last_thinking_len, _live_thinking_shown
            
            # 🛑 STOP: Vérifier si arrêt demandé
            from stop_signal import is_stop_requested
            if is_stop_requested():
                print("[STOP] 🛑 Arrêt streaming demandé")
                raise StopAsyncIteration("Arrêt demandé par l'utilisateur")
            
            _chunk_count += 1
            current_time = time.time()
            elapsed_total = current_time - _stream_start_time
            gap = current_time - _last_chunk_time
            _last_chunk_time = current_time
            
            # 🛡️ PROTECTION: Limiter streaming pour éviter blocages
            MAX_STREAMING_TIME = 180  # 3 minutes max
            MAX_STREAMING_CHARS = 50000  # ~12500 tokens max
            
            if elapsed_total > MAX_STREAMING_TIME:
                print(f"⏱️ [STREAM-LIMIT] ⚠️ Timeout streaming atteint ({elapsed_total:.0f}s > {MAX_STREAMING_TIME}s)")
                raise StopAsyncIteration("Timeout streaming atteint")
            
            if len(accumulated_text) > MAX_STREAMING_CHARS:
                print(f"📝 [STREAM-LIMIT] ⚠️ Limite caractères atteinte ({len(accumulated_text)} > {MAX_STREAMING_CHARS})")
                raise StopAsyncIteration("Limite caractères atteinte")
            
            # Log toutes les 10 secondes ou si gap > 5s
            if int(elapsed_total) % 10 == 0 and _chunk_count % 50 == 0:
                print(f"⏱️ [STREAM-TIME] {elapsed_total:.1f}s écoulées, {_chunk_count} chunks, dernier gap: {gap:.2f}s")
            if gap > 5.0:
                print(f"⚠️ [STREAM-TIME] GAP LONG détecté: {gap:.1f}s entre chunks!")
            
            # 🛡️ ANTI-PRUNE: Rafraîchir l'activité client toutes les 30s pendant le streaming
            if _chunk_count % 100 == 0 and client:
                try:
                    track_client_activity(client.id)
                except Exception:
                    pass
            
            # Toujours accumuler le texte complet (pour traitement post-streaming)
            accumulated_text += chunk
            
            # 🎨 MAGIC PHRASE HIDING: Détection et masquage des phrases magiques image
            if not magic_phrase_detected:
                # Vérifier si une phrase magique commence
                text_lower = accumulated_text.lower()
                for pattern in magic_phrase_patterns_start:
                    if pattern in text_lower:
                        magic_phrase_detected = True
                        # Trouver la position de début de la phrase magique
                        idx = text_lower.find(pattern)
                        text_before_magic = accumulated_text[:idx]
                        magic_phrase_buffer = accumulated_text[idx:]
                        print(f"[MAGIC-HIDE] 🎨 Phrase magique détectée: '{pattern}' - masquage activé")
                        break
            else:
                # Phrase magique en cours - accumuler dans le buffer masqué
                magic_phrase_buffer += chunk
            
            # Déterminer ce qu'on affiche dans l'UI
            if streaming_md:
                try:
                    if magic_phrase_detected:
                        # Afficher le texte avant la phrase magique + spinner animé via JS
                        if not spinner_shown:
                            spinner_shown = True
                            # Afficher uniquement le texte avant la phrase magique
                            streaming_md.set_content(text_before_magic if text_before_magic else "")
                            # Injecter le spinner animé dans le DOM via JavaScript
                            is_search = "consulter nos conversations" in magic_phrase_buffer.lower()
                            try:
                                spinner_js = _get_spinner_inject_js('search' if is_search else 'image')
                                client.run_javascript(spinner_js)
                            except Exception as js_err:
                                print(f"[MAGIC-HIDE] ⚠️ Erreur injection spinner JS: {js_err}")
                            if is_search:
                                print(f"[MAGIC-HIDE] 🔍 Spinner recherche injecté, texte masqué: {len(magic_phrase_buffer)} chars")
                            else:
                                print(f"[MAGIC-HIDE] 🔄 Spinner image injecté, texte masqué: {len(magic_phrase_buffer)} chars")
                        # else: spinner déjà visible dans le DOM, pas besoin de mettre à jour
                    else:
                        # Affichage normal
                        streaming_md.set_content(accumulated_text + "▌")  # Curseur
                    
                    # Force scroll périodique (en plus de l'intervalle JS)
                    if _chunk_count % 10 == 0:
                        # Utiliser le client capturé pour éviter l'erreur de slot stack
                        client.run_javascript('if(window.OGMA_autoScroll){ const el=document.querySelector(\'[data-role="chat-scroll"]\'); if(el) el.scrollTop=el.scrollHeight + 1000; }')
                except Exception as e:
                    print(f"[STREAM] ⚠️ Erreur update UI: {e}")

            # 🧠 THINKING LIVE: Mise à jour incrémentale du container thinking
            if _thinking_live_enabled and _live_thinking_md is not None and hasattr(ctrl, 'api_manager'):
                try:
                    current_thinking = ctrl.api_manager._last_thinking_content or ""
                    if len(current_thinking) > _last_thinking_len:
                        _last_thinking_len = len(current_thinking)
                        _live_thinking_md.set_content(current_thinking)
                        if not _live_thinking_shown:
                            _live_thinking_shown = True
                            _live_thinking_box.set_visibility(True)
                except Exception as _eth:
                    pass  # Silencieux - thinking live est non-critique

            # === TTS STREAMING : Traiter les phrases complètes (sauf si phrase magique) ===
            if use_tts_streaming and hasattr(_audio_manager, 'process_streaming_chunk'):
                # 💰 ÉCONOMIE TTS: Ne pas envoyer les phrases magiques au TTS
                if not magic_phrase_detected:
                    completed_sentences = _audio_manager.process_streaming_chunk(chunk)
                    for sentence in completed_sentences:
                        _audio_manager.speak_streaming_sentence(sentence)
                else:
                    # Phrase magique en cours - on n'envoie rien au TTS
                    pass
        
        # 🌀 SPINNER: Activer le spinner IA Principale avant l'appel
        set_ia_working(True)
        
        reply, err = await ctrl.call_chat_api_streaming(
            messages=messages, 
            max_tokens=ctrl.max_tokens, 
            context_length=ctrl.context_length, 
            temperature=ctrl.temperature,
            callback=streaming_callback
        )
        
        # 🔍 DEBUG: Log temps total streaming
        _stream_end_time = time.time()
        _stream_total = _stream_end_time - _stream_start_time
        print(f"✅ [STREAM-TIME] Streaming terminé en {_stream_total:.1f}s, {_chunk_count} chunks reçus")
        if _stream_total > 60:
            print(f"⚠️ [STREAM-TIME] ATTENTION: Streaming > 60s ({_stream_total:.1f}s) - risque timeout!")
        
        # 🌀 SPINNER: Désactiver le spinner IA Principale (SEULEMENT si pas de phrase magique)
        # Si phrase magique détectée, le spinner reste ON jusqu'à la fin du traitement image
        if not magic_phrase_detected:
            set_ia_working(False)
        
        # === TTS STREAMING : Vider le buffer restant (sauf si phrase magique) ===
        if use_tts_streaming and hasattr(_audio_manager, 'flush_streaming_buffer'):
            # 💰 ÉCONOMIE TTS: Ne pas flusher si phrase magique détectée
            if not magic_phrase_detected:
                _audio_manager.flush_streaming_buffer()
            else:
                print("[MAGIC-HIDE] 💰 TTS flush ignoré - phrase magique masquée")
                # Reset le buffer TTS sans le vocaliser
                if hasattr(_audio_manager, 'reset_streaming'):
                    _audio_manager.reset_streaming()
            
            # Attendre la fin du TTS puis notifier le module voice
            try:
                if VOICE_MODULE_AVAILABLE and _voice_manager and _voice_manager.is_active:
                    import threading
                    def wait_tts_end_then_notify():
                        import time
                        print("[VOICE] ⏳ Attente fin TTS streaming...")
                        
                        # Utiliser la méthode fiable wait_until_finished()
                        if _audio_manager and hasattr(_audio_manager, 'tts_safe'):
                            tts = _audio_manager.tts_safe
                            if tts and hasattr(tts, 'wait_until_finished'):
                                # Attendre que TOUTES les phrases soient lues
                                finished = tts.wait_until_finished(timeout=120.0)
                                if finished:
                                    print("[VOICE] ✅ TTS complètement terminé")
                                else:
                                    print("[VOICE] ⚠️ Timeout TTS - reprise forcée")
                            else:
                                # Fallback: ancienne méthode
                                time.sleep(2.0)
                        else:
                            time.sleep(2.0)
                        
                        # Délai supplémentaire anti-écho
                        time.sleep(0.5)
                        print("[VOICE] 🎤 Reprise écoute...")
                        if _voice_manager:
                            _voice_manager.notify_tts_finished()
                    threading.Thread(target=wait_tts_end_then_notify, daemon=True).start()
            except Exception as e:
                print(f"[VOICE] ⚠️ Erreur notification TTS: {e}")
        
        # Finaliser le message (retirer curseur + ajouter bouton TTS)
        # 🧠 THINKING: Récupérer le contenu thinking des modèles de raisonnement
        _reasoning_thinking = ""
        try:
            if hasattr(ctrl, 'api_manager') and hasattr(ctrl.api_manager, '_last_thinking_content'):
                _reasoning_thinking = ctrl.api_manager._last_thinking_content or ""
                if _reasoning_thinking:
                    if _live_thinking_shown:
                        # Thinking déjà affiché en temps réel → mettre à jour header + ne pas recréer
                        print(f"[THINKING] 🧠 Thinking affiché live ({len(_reasoning_thinking)} chars) - header mis à jour")
                        try:
                            if client is not None:
                                client.run_javascript(
                                    "document.querySelectorAll('.thinking-reasoning-expansion .q-expansion-item__header span')"
                                    ".forEach(function(el){ el.textContent = '\\u25BE Raisonnement du mod\\u00e8le'; });"
                                )
                        except Exception:
                            pass
                        _reasoning_thinking = ""  # Éviter double boîte dans _finalize
                    else:
                        print(f"[THINKING] 🧠 Contenu thinking récupéré ({len(_reasoning_thinking)} chars)")
                        # Passer via variable globale (le keyword arg est ignoré par NiceGUI)
                        import ogma_ui_conversations
                        ogma_ui_conversations._pending_thinking_content = _reasoning_thinking
        except Exception as e:
            print(f"[THINKING] ⚠️ Erreur récupération thinking: {e}")
        
        # 🎨 MAGIC PHRASE: Ne PAS finaliser avec le texte brut si phrase magique détectée
        if streaming_result and reply:
            if magic_phrase_detected:
                # Phrase magique en cours - garder le spinner, ne pas afficher le texte brut
                # Le contenu sera mis à jour après le traitement d'image avec cleaned_reply
                print(f"[MAGIC-HIDE] 🔒 Finalize skippé - spinner maintenu actif (attente traitement image)")
                # Juste ajouter le bouton TTS sans changer le contenu
                # Le spinner animé est déjà injecté dans le DOM via JS
                _finalize_streaming_message(streaming_result, text_before_magic if text_before_magic else "", client=client, thinking_content=_reasoning_thinking)
            else:
                # Pas de phrase magique - finalisation normale
                print(f"[THINKING-PASS] Envoi thinking_content={len(_reasoning_thinking)} chars à finalize")
                _finalize_streaming_message(streaming_result, reply, client=client, thinking_content=_reasoning_thinking)
        
        # Arrêter l'auto-scroll
        try:
            client.run_javascript('window.OGMA_streaming = false;')
        except Exception:
            pass
        
        # Sauvegarder référence pour mise à jour après traitements (images, etc.)
        _streaming_widget_ref = streaming_md
        _streaming_container_ref = streaming_result[1] if streaming_result else None  # container_ai stable
        _streaming_html_ref = streaming_result[2] if streaming_result and len(streaming_result) > 2 else None  # placeholder HTML batch
        # 🎨 MAGIC PHRASE: Sauvegarder le flag pour le traitement post-streaming
        _magic_phrase_was_detected = magic_phrase_detected
            
    else:
        _streaming_widget_ref = None  # Pas de streaming
        _streaming_container_ref = None
        _streaming_html_ref = None
        _magic_phrase_was_detected = False
        # 📦 Mode classique pour backends locaux (Ollama, GGUF, KoboldCpp)
        print(f"[STREAM] 📦 Mode classique pour backend {backend_type}")
        
        # 🌀 SPINNER: Activer le spinner IA Principale avant l'appel
        set_ia_working(True)
        
        reply, err = await ctrl.call_chat_api(
            messages=messages, 
            max_tokens=ctrl.max_tokens, 
            context_length=ctrl.context_length, 
            temperature=ctrl.temperature, 
            is_json=False
        )
        
        # 🌀 SPINNER: Désactiver le spinner IA Principale
        set_ia_working(False)
    
    if err:
        # 🧹 Cleanup: Retirer le spinner animé si présent (mode streaming)
        if was_streaming and client:
            try:
                client.run_javascript(_SPINNER_REMOVE_JS)
            except Exception:
                pass
        
        if _chat_inner is not None:
            with _chat_inner:
                # Détecter si erreur rate limit pour notification spécifique
                is_rate_limit = "Limite Anthropic" in err or "rate limit" in err.lower()
                if is_rate_limit:
                    _message('system', err)  # Message déjà formaté pour l'utilisateur
                    _notify_safe("⏱️ Rate limit Anthropic - patienter avant retry", 'warning', timeout=10)
                else:
                    _message('system', f"[ERREUR] {err}")
                    _notify_safe(f"Erreur API: {err[:80]}", 'negative')
        return
    if reply is not None:
        # 🪞 COGNITIVE MIRROR: Hook après génération de la réponse IA
        print("[COGNITIVE-MIRROR] SEARCH Enrichissement contexte conversation...")
        try:
            from extensions.cognitive_mirror import is_enabled as cm_is_enabled
            if cm_is_enabled():
                cognitive_mirror = _ensure_cognitive_mirror()
                if cognitive_mirror:
                    # Enrichir le contexte avec les messages de la conversation actuelle
                    conversation_context = {
                        'user_message': input_el.value or '',
                        'ai_response': reply,
                        'timestamp': datetime.now().isoformat(),
                        'conversation_length': len(messages),
                        'recent_messages': messages[-5:] if len(messages) >= 5 else messages
                    }
                    # Nouvelle approche: enrichir le contexte pour les futures observations
                    cognitive_mirror.enrich_conversation_context(conversation_context)
                    print("[COGNITIVE-MIRROR] OK Contexte enrichi pour réflexions")
        except Exception as e:
            print(f"[COGNITIVE-MIRROR] ERROR Erreur enrichissement contexte: {e}")

        # 📓 JOURNAL DE BORD: Détection live états actifs pendant conversations
        print("[JOURNAL-HOOK] Analyse détection états actifs...")
        try:
            if journal_available_check and journal_available_check():
                # Récupérer le message utilisateur et la réponse IA
                user_message = (input_el.value if input_el else None) or text or ""
                ai_response = reply
                
                # Extraire contexte récent (10 derniers messages)
                recent_context = _chat_history[-10:] if _chat_history else []
                
                # Récupérer l'ID conversation pour traçabilité
                conv_id = _current_conversation_id if _current_conversation_id else None
                
                # Appeler le hook de détection
                if hook_message_exchange:
                    changes = await hook_message_exchange(
                        user_message, 
                        ai_response, 
                        recent_context,
                        conversation_id=conv_id
                    )
                    
                    # Logger les changements détectés
                    if changes.get("new_states"):
                        print(f"[JOURNAL-HOOK] ✨ {len(changes['new_states'])} nouveaux états détectés")
                        for state in changes["new_states"]:
                            if isinstance(state, dict):
                                print(f"  → {state.get('titre', state.get('description', 'Sans titre'))} ({state.get('catégorie', state.get('category', '?'))})")
                            else:
                                print(f"  → État #{state} (ID)")
                    
                    if changes.get("resolved_states"):
                        print(f"[JOURNAL-HOOK] ✅ {len(changes['resolved_states'])} états résolus")
                        for state_id in changes["resolved_states"]:
                            print(f"  → État #{state_id} marqué résolu")
                    
                    if changes.get("updated_states"):
                        print(f"[JOURNAL-HOOK] 🔄 {len(changes['updated_states'])} états mis à jour")
                    
                    # Rafraîchir le badge si des changements ont été détectés
                    if any(changes.values()):
                        print("[JOURNAL-HOOK] 🔔 Rafraîchissement badge états actifs...")
                        # Le badge se mettra à jour automatiquement via le polling JSON
            else:
                print("[JOURNAL-HOOK] Extension Journal non disponible")
                
        except ImportError as ie:
            print(f"[JOURNAL-HOOK] Extension non chargée: {ie}")
        except Exception as e:
            print(f"[JOURNAL-HOOK] Erreur détection: {e}")
            import traceback
            traceback.print_exc()


        # S'assurer que reply est une chaîne avant l'analyse
        reply_text = reply if isinstance(reply, str) else str(reply) if reply else ""
        
        # Ne pas retirer la phrase magique dans la réponse IA afin que le texte reste visible à l'écran
        cleaned_reply = reply_text

        # 🌐 WEB NAVIGATOR: Détection recherche auto-déclenchée par l'IA
        print(f"[WEB-NAV-AI] Vérification auto-recherche IA dans: '{reply_text[:80]}...'")
        try:
            # Obtenir l'instance unique Web Navigator (évite les recréations)
            web_nav_ext = get_web_navigator_instance()
            
            # Vérifier si l'IA a décidé de faire une recherche
            if web_nav_ext and web_nav_ext.commands.is_internet_request(reply_text):
                print(f"[WEB-NAV-AI] ✅ L'IA demande une recherche auto-déclenchée!")
                
                # Vérifier si la recherche web est activée
                if web_nav_ext.config.is_web_search_enabled():
                    print(f"[WEB-NAV-AI] 🚀 Recherche auto-déclenchée par l'IA")
                    
                    # Effectuer la recherche
                    web_response, web_file_path = await web_nav_ext.commands.process_internet_request(reply_text)
                    
                    if web_response:
                        print(f"[WEB-NAV-AI] ✅ Informations trouvées: {len(web_response)} caractères")
                        
                        # RÉGÉNÉRER la réponse avec le contexte web
                        print(f"[WEB-NAV-AI] 🔄 Régénération de la réponse avec le contexte web")
                        
                        # Contexte web - l'IA synthétise les résultats
                        web_context_message = {
                            'role': 'system',
                            'content': f"INFORMATIONS WEB RÉCUPÉRÉES:\n\n{web_response}\n\nMaintenant, réponds à la question de l'utilisateur en utilisant ces informations récentes que tu viens de récupérer sur internet."
                        }
                        
                        # Filtrer les messages qui poussent le modèle à émettre des phrases magiques :
                        # 1. La directive CAPABILITY-ADVISOR ("écris la phrase magique mot pour mot")
                        # 2. Le rappel protocoles ("phrases magiques sont des COMMANDES SYSTÈME")
                        # Sans ce filtrage, n'importe quel modèle obéissant réémet une phrase de recherche
                        # au lieu de synthétiser les résultats web.
                        _cap_markers = (
                            'DIRECTIVE TECHNIQUE - PHRASE MAGIQUE REQUISE',
                            'DIRECTIVE SYSTÈME - PHRASE MAGIQUE À INCLURE',
                            'phrases magiques sont des COMMANDES SYSTÈME',
                        )
                        filtered_messages = [
                            m for m in messages
                            if not (m.get('role') == 'system' and any(marker in m.get('content', '') for marker in _cap_markers))
                        ]
                        print(f"[WEB-NAV-AI] 🧹 Messages filtrés: {len(messages)} → {len(filtered_messages)} (retrait directives CAPABILITY + RAPPEL)")
                        
                        # Créer un nouveau set de messages sans la directive CAPABILITY mais avec le contexte web
                        regeneration_messages = filtered_messages + [web_context_message]
                        
                        # Régénérer la réponse (min 4096 tokens pour réponse enrichie web)
                        new_reply, new_err = await ctrl.call_chat_api(
                            messages=regeneration_messages, 
                            max_tokens=max(ctrl.max_tokens, 4096), 
                            context_length=ctrl.context_length, 
                            temperature=ctrl.temperature, 
                            is_json=False
                        )
                        
                        if not new_err and new_reply:
                            print(f"[WEB-NAV-AI] ✅ Réponse régénérée avec contexte web")
                            cleaned_reply = new_reply
                            _pending_notifications.append((f"WEB Réponse enrichie avec recherche internet", 'positive'))
                        else:
                            print(f"[WEB-NAV-AI] ❌ Échec régénération - utilisation réponse originale")
                            _pending_notifications.append((f"WEB Recherche effectuée mais échec intégration", 'warning'))
                    else:
                        print(f"[WEB-NAV-AI] ❌ Échec de la recherche auto-déclenchée")
                        _pending_notifications.append((f"WEB Échec recherche auto-déclenchée", 'warning'))
                else:
                    print(f"[WEB-NAV-AI] ⚪ Recherche web désactivée - phrase magique ignorée")
            else:
                print(f"[WEB-NAV-AI] ⚪ Aucune recherche auto-déclenchée détectée")
                
        except Exception as e:
            print(f"[WEB-NAV-AI] ❌ Erreur recherche auto-déclenchée: {e}")
            import traceback
            traceback.print_exc()

        # 📖 BIOGRAPHY AUTO-DÉCLENCHÉE PAR L'IA
        # Détecte quand l'IA dit "il faut que je consulte la biographie de [prénom]"
        try:
            biography_pattern = r"il\s+faut\s+que\s+je\s+consulte\s+la\s+biographie\s+de\s+([a-zA-ZÀ-ÿ]+)"
            biography_match = re.search(biography_pattern, reply_text, re.IGNORECASE)
            biography_is_available = get_biography_available()
            
            print(f"[BIOGRAPHY-AI-DEBUG] Pattern check: match={biography_match is not None}, available={biography_is_available}")
            if biography_match:
                print(f"[BIOGRAPHY-AI-DEBUG] Match trouvé: {biography_match.group(0)}")
            
            if biography_match and biography_is_available:
                target_name = biography_match.group(1).strip()
                print(f"[BIOGRAPHY-AI] 📖 L'IA demande consultation biographie: {target_name}")
                
                from extensions.biographie_profil import get_biography_magic_phrases
                biography_magic = get_biography_magic_phrases()
                
                if biography_magic:
                    # Appeler la méthode avec is_ai_message=True
                    bio_result = await biography_magic.handle_magic_phrases(
                        reply_text,
                        is_ai_message=True,
                        conversation_history=_chat_history
                    )
                    
                    if bio_result and bio_result.get('type') == 'display':
                        bio_content = bio_result.get('content', '')
                        print(f"[BIOGRAPHY-AI] ✅ Biographie trouvée: {len(bio_content)} chars")
                        
                        # Régénérer la réponse avec le contexte biographique
                        bio_context_message = {
                            'role': 'system',
                            'content': f"{bio_content}\n\nMaintenant, utilise ces informations biographiques pour répondre de manière personnalisée."
                        }
                        
                        # Même filtre que pour la régénération web : retirer les directives
                        # qui ordonnent au modèle d'émettre une phrase magique, sinon un modèle
                        # très instruction-following (ex: Mistral) les réémettrait au lieu de synthétiser.
                        _cap_markers_bio = (
                            'DIRECTIVE TECHNIQUE - PHRASE MAGIQUE REQUISE',
                            'DIRECTIVE SYSTÈME - PHRASE MAGIQUE À INCLURE',
                            'phrases magiques sont des COMMANDES SYSTÈME',
                        )
                        filtered_messages_bio = [
                            m for m in messages
                            if not (m.get('role') == 'system' and any(marker in m.get('content', '') for marker in _cap_markers_bio))
                        ]
                        regeneration_messages = filtered_messages_bio + [bio_context_message]
                        
                        new_reply, new_err = await ctrl.call_chat_api(
                            messages=regeneration_messages,
                            max_tokens=ctrl.max_tokens,
                            context_length=ctrl.context_length,
                            temperature=ctrl.temperature,
                            is_json=False
                        )
                        
                        if not new_err and new_reply:
                            print(f"[BIOGRAPHY-AI] ✅ Réponse régénérée avec contexte biographique")
                            cleaned_reply = new_reply
                            _pending_notifications.append((f"📖 Biographie {target_name} consultée", 'positive'))
                        else:
                            print(f"[BIOGRAPHY-AI] ⚠️ Échec régénération - affichage biographie dans chat")
                            # Fallback: afficher la biographie dans le chat
                            if _chat_inner:
                                with _chat_inner:
                                    _message('system', bio_content)
                    else:
                        print(f"[BIOGRAPHY-AI] ❌ Biographie non trouvée pour {target_name}")
                        _pending_notifications.append((f"❌ Biographie {target_name} introuvable", 'negative'))
                else:
                    print(f"[BIOGRAPHY-AI] ⚠️ Biography magic phrases non initialisé")
                    
        except Exception as e:
            print(f"[BIOGRAPHY-AI] ❌ Erreur consultation biographie: {e}")
            import traceback
            traceback.print_exc()

        # 🧠 INTROSPECTION AUTO-DÉCLENCHÉE PAR L'IA
        # Détecte quand l'IA dit "il faut que je réfléchisse..." et lance l'introspection
        try:
            introspection_self_patterns = [
                r"il\s+faut\s+que\s+je\s+r[ée]fl[ée]chiss?e",
                r"je\s+dois\s+r[ée]fl[ée]chir",
                r"je\s+vais\s+(?:faire\s+une\s+)?introspection",
                r"je\s+lance\s+(?:une\s+)?introspection",
                r"(?:moment|temps)\s+(?:de\s+)?(?:r[ée]flexion|introspection)",
            ]
            
            is_ia_introspection_trigger = any(re.search(pattern, reply_text, re.IGNORECASE) for pattern in introspection_self_patterns)
            
            if is_ia_introspection_trigger and COGNITIVE_MIRROR_AVAILABLE:
                # Bloquer l'auto-déclenchement IA en mode on_demand
                _ia_introspection_mode = 'on_demand'
                try:
                    from extensions.cognitive_mirror import get_introspection_config as _get_icfg2
                    _icfg2 = _get_icfg2()
                    if _icfg2:
                        _ia_introspection_mode = _icfg2.get_introspection_mode()
                except Exception:
                    pass

                if _ia_introspection_mode == 'on_demand':
                    print("[INTROSPECTION-IA] Mode on_demand: auto-déclenchement IA bloqué")
                else:
                    print(f"[INTROSPECTION-IA] 🧠 L'IA déclenche elle-même une introspection!")

                from extensions.cognitive_mirror import is_enabled as cm_is_enabled
                
                if cm_is_enabled() and _ia_introspection_mode != 'on_demand':
                    # Extraire le sujet de réflexion depuis la phrase magique exacte
                    subject_match = re.search(
                        r"il\s+faut\s+que\s+je\s+r[ée]fl[ée]chiss?e\s+sur\s*:?\s*(.+?)(?:\n|$)",
                        reply_text, re.IGNORECASE
                    )
                    introspection_subject = subject_match.group(1).strip() if subject_match else user_message
                    
                    print(f"[INTROSPECTION-IA] 📝 Sujet extrait: '{introspection_subject[:60]}...'")
                    
                    # Récupérer l'engine d'introspection
                    cognitive_mirror = _ensure_cognitive_mirror()
                    
                    if cognitive_mirror and hasattr(cognitive_mirror, 'run_introspection'):
                        # Construire le contexte pour l'introspection
                        from identity_manager import get_current_identities
                        
                        # Récupérer traits ego depuis la DB (nouveau système ego boolean)
                        try:
                            mm = _ensure_memory_manager()
                            if mm and mm.db_path:
                                import sqlite3
                                with sqlite3.connect(mm.db_path) as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        SELECT id, title, summary 
                                        FROM memories 
                                        WHERE id LIKE 'EGO%'
                                        ORDER BY created_at DESC
                                        LIMIT 50
                                    """)
                                    ego_traits = cursor.fetchall()
                                    
                                    # Formater en texte structuré
                                    ego_lines = ["# TRAITS EGO (Identité IA)\n"]
                                    for trait in ego_traits:
                                        ego_id, title, summary = trait
                                        trait_text = summary if summary else title
                                        ego_lines.append(f"- {trait_text}")
                                    
                                    current_ego_prompt = "\n".join(ego_lines) if len(ego_lines) > 1 else "Ego non défini"
                                    print(f"[INTROSPECTION-IA] 🧠 Ego chargé: {len(ego_traits)} traits depuis DB")
                            else:
                                current_ego_prompt = "Ego non disponible (DB non initialisée)"
                                print(f"[INTROSPECTION-IA] ⚠️ Memory manager non disponible")
                        except Exception as ego_err:
                            current_ego_prompt = "Ego non disponible"
                            print(f"[INTROSPECTION-IA] ⚠️ Erreur chargement ego: {ego_err}")
                            import traceback
                            traceback.print_exc()
                        
                        identities = get_current_identities()
                        extended_history = _chat_history[-20:] if len(_chat_history) > 20 else _chat_history
                        
                        conversation_context = {
                            'user_message': introspection_subject,
                            'chat_history': extended_history,
                            'user_identity': identities.get('user_identity', identities.get('user_name', 'Utilisateur')),
                            'ego_prompt': current_ego_prompt,
                            'main_ai_identity': identities.get('main_ai_identity', identities.get('ai_description', '')),
                            'relationship_context': identities.get('relationship_context', ''),
                            'trigger_type': 'ia_self_triggered'
                        }
                        
                        # Créer la boîte thinking AVANT (pour affichage temps réel)
                        # Note: _introspection_box_content et _introspection_md_widget sont déjà global (ligne ~1426)
                        _introspection_box_content = []
                        ia_dialogue_messages = []
                        
                        with _chat_inner:
                            with ui.expansion(value=True).classes('thinking-expansion') as ia_introspection_box:
                                ia_introspection_box.props('label=""')
                                with ia_introspection_box.add_slot('header'):
                                    ui.html('<span style="color: rgba(255, 200, 100, 0.7); font-size: 12px; font-style: italic;">🧠 introspection auto-déclenchée (IA)</span>')

                                _introspection_md_widget = ui.markdown("_Dialogue intérieur en cours..._")
                                _introspection_md_widget.style(
                                    'color: rgba(255, 255, 255, 0.85); '
                                    'font-size: 13px; '
                                    'line-height: 1.5; '
                                    'margin: 0; '
                                    'padding: 8px 0; '
                                    'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'
                                )
                                _introspection_md_widget.classes('introspection-dialogue')
                        
                        # Configurer callback pour affichage temps réel
                        def on_ia_introspection_message(step: int, role: str, content: str):
                            """Callback pour afficher les messages en temps réel"""
                            global _introspection_md_widget
                            try:
                                # La synthèse s'affiche dans la conversation — pas dans la boîte thinking
                                if role == "synthesis":
                                    return
                                role_labels = {
                                    "analysis": "🔍 Analyse",
                                    "conscious": "💡 Conscient (IA principale)",
                                    "unconscious": "🌙 Inconscient (Archiviste)",
                                }
                                label = role_labels.get(role, role)
                                ia_dialogue_messages.append(f"**{label}:**\n{content}")
                                
                                if _introspection_md_widget:
                                    full_dialogue = "\n\n---\n\n".join(ia_dialogue_messages)
                                    _introspection_md_widget.set_content(full_dialogue)
                                    print(f"[INTROSPECTION-IA-UI] 📝 Affiché: {role} ({len(content)} chars)")
                            except Exception as e:
                                print(f"[INTROSPECTION-IA-UI] ⚠️ Erreur affichage: {e}")
                        
                        # Configurer le callback sur le moteur
                        cognitive_mirror.on_message = on_ia_introspection_message
                        
                        # Lancer l'introspection de manière asynchrone
                        async def run_ia_introspection():
                            try:
                                result = await cognitive_mirror.run_introspection(
                                    user_message=introspection_subject,
                                    context=conversation_context,
                                    trigger_source="ia_self_triggered"
                                )
                                if result and result.get('success'):
                                    synthesis = result.get('synthesis', '')
                                    if synthesis:
                                        # Ajouter d'abord à l'historique (ne dépend pas du client)
                                        introspection_msg = {'role': 'assistant', 'content': f"[Introspection] {synthesis}"}
                                        _chat_history.append(introspection_msg)
                                        _chat_history_ui.append(introspection_msg)
                                        
                                        # Afficher le résultat final dans le chat (avec protection client déconnecté)
                                        try:
                                            with _chat_inner:
                                                _message('assistant', f"**🔮 Résultat de mon introspection:**\n\n{synthesis}")
                                        except Exception as e:
                                            print(f"[INTROSPECTION-IA] ⚠️ Client déconnecté, message sauvegardé dans l'historique")
                                        
                                        print(f"[INTROSPECTION-IA] ✅ Introspection terminée: {len(synthesis)} chars")
                                        
                                        # 🎯 NOUVEAU: Analyse phrases magiques dans la synthèse d'introspection
                                        try:
                                            print(f"[INTROSPECTION-MAGIC] 🔍 Analyse phrases magiques dans synthèse...")
                                            
                                            # 1. Journal de Bord
                                            journal_available = get_journal_available()
                                            if journal_available:
                                                try:
                                                    from extensions.journal_de_bord import get_journal
                                                    journal = get_journal()
                                                    journal_magic = await journal.entry_generator.handle_magic_phrases(
                                                        synthesis,
                                                        journal.json_manager
                                                    )
                                                    if journal_magic and not journal_magic.startswith("ERREUR"):
                                                        print(f"[INTROSPECTION-MAGIC] ✅ Journal: phrase magique détectée et traitée")
                                                except Exception as je:
                                                    print(f"[INTROSPECTION-MAGIC] ⚠️ Erreur journal: {je}")
                                            
                                            # 2. Biographie Profil
                                            biography_available = get_biography_available()
                                            if biography_available:
                                                try:
                                                    from extensions.biographie_profil import get_biography_magic_phrases
                                                    biography_magic = get_biography_magic_phrases()
                                                    if biography_magic:
                                                        bio_response = await biography_magic.handle_magic_phrases(
                                                            synthesis,
                                                            is_ai_message=True,
                                                            conversation_history=_chat_history
                                                        )
                                                        if bio_response:
                                                            print(f"[INTROSPECTION-MAGIC] ✅ Biographie: phrase magique détectée et traitée")
                                                except Exception as be:
                                                    print(f"[INTROSPECTION-MAGIC] ⚠️ Erreur biographie: {be}")
                                            
                                            print(f"[INTROSPECTION-MAGIC] ✅ Analyse phrases magiques terminée")
                                        except Exception as magic_err:
                                            print(f"[INTROSPECTION-MAGIC] ❌ Erreur analyse phrases magiques: {magic_err}")
                                            import traceback
                                            traceback.print_exc()
                                        
                                        # 🎯 NOUVEAU: Détections STANDARDS sur la synthèse d'introspection
                                        # (phrases magiques normales "il faut que je me souvienne de", événements organiques, etc.)
                                        try:
                                            print(f"[INTROSPECTION-STANDARD] 🔍 Analyse détections standards dans synthèse...")
                                            
                                            # 1. Phrases magiques mémoire normales
                                            magic_ai = _extract_magic_memories(synthesis)
                                            if magic_ai:
                                                print(f"[INTROSPECTION-STANDARD] ✅ {len(magic_ai)} phrase(s) magique(s) détectée(s)")
                                                mm = _ensure_memory_manager()
                                                if mm:
                                                    for content in magic_ai:
                                                        try:
                                                            print(f"[INTROSPECTION-STANDARD] 💾 Mémorisation: '{content[:80]}...'")
                                                            mem_id = f"ai-{uuid.uuid4()}"
                                                            mem_conv_context = "\n".join([f"{msg['role']}: {msg.get('content', '')}" for msg in _chat_history[-3:] if isinstance(msg.get('content'), str)])
                                                            set_archiviste_working(True)
                                                            ok = await mm.add_memory(
                                                                mem_id, 
                                                                content,
                                                                chat_controller=_chat_controller,
                                                                conversation_context=mem_conv_context,
                                                                interlocutor="Introspection"
                                                            )
                                                            set_archiviste_working(False)
                                                            if ok:
                                                                print(f"[INTROSPECTION-STANDARD] ✅ Mémoire créée: {mem_id}")
                                                                _notify_safe(f"💾 Souvenir mémorisé depuis introspection: {content[:80]}...", 'positive')
                                                                _trigger_memory_update()
                                                            else:
                                                                print(f"[INTROSPECTION-STANDARD] ⚠️ Échec mémorisation")
                                                        except Exception as me:
                                                            set_archiviste_working(False)
                                                            print(f"[INTROSPECTION-STANDARD] ❌ Erreur mémorisation: {me}")
                                                            import traceback
                                                            traceback.print_exc()
                                            
                                            print(f"[INTROSPECTION-STANDARD] ✅ Détections standards terminées")
                                        except Exception as std_err:
                                            print(f"[INTROSPECTION-STANDARD] ❌ Erreur détections standards: {std_err}")
                                            import traceback
                                            traceback.print_exc()
                                    
                                    # Afficher dialogue final si pas affiché en temps réel
                                    if _introspection_md_widget and not ia_dialogue_messages:
                                        dialogue_data = result.get("dialogue", [])
                                        if dialogue_data:
                                            formatted_msgs = []
                                            for msg in dialogue_data:
                                                role = msg.get("role", "unknown")
                                                content = msg.get("content", "")
                                                role_labels = {
                                                    "conscious": "💡 Conscient (IA principale)",
                                                    "unconscious": "🌙 Inconscient (Archiviste)"
                                                }
                                                label = role_labels.get(role, role)
                                                formatted_msgs.append(f"**{label}:**\n{content}")
                                            if formatted_msgs:
                                                _introspection_md_widget.set_content("\n\n---\n\n".join(formatted_msgs))
                                else:
                                    print(f"[INTROSPECTION-IA] ⚠️ Introspection sans résultat")
                                    if _introspection_md_widget:
                                        _introspection_md_widget.set_content("_Introspection terminée sans résultat_")
                            except Exception as ie:
                                print(f"[INTROSPECTION-IA] ❌ Erreur introspection: {ie}")
                                import traceback
                                traceback.print_exc()
                                if _introspection_md_widget:
                                    _introspection_md_widget.set_content(f"_Erreur: {ie}_")
                        
                        # Exécuter l'introspection
                        asyncio.create_task(run_ia_introspection())
                        print(f"[INTROSPECTION-IA] 🚀 Introspection lancée en arrière-plan")
                    else:
                        print(f"[INTROSPECTION-IA] ⚠️ Engine d'introspection non disponible")
                else:
                    print(f"[INTROSPECTION-IA] ⚪ Extension cognitive mirror désactivée")
            else:
                if not is_ia_introspection_trigger:
                    pass  # Pas de trigger détecté - comportement normal
                    
        except Exception as e:
            print(f"[INTROSPECTION-IA] Erreur détection auto-introspection: {e}")
            import traceback
            traceback.print_exc()

        # 🔍 CONVERSATION SCANNER - Recherche par mots-clés via phrase magique
        # Pattern détection: "je dois consulter nos conversations pour [keywords]"
        try:
            # Pattern de détection de la nouvelle phrase magique
            conv_search_pattern = r"je\s+dois\s+consulter\s+nos\s+conversations?\s+pour\s+(.+?)(?:\.|$|,|\n)"
            
            match = re.search(conv_search_pattern, reply_text, re.IGNORECASE)
            
            if match:
                # Extraire keywords directement de la phrase de l'IA principale
                keywords_raw = match.group(1).strip()
                print(f"[CONV-SCANNER-IA] 🔍 Phrase magique détectée!")
                print(f"[CONV-SCANNER-IA] 🎯 Keywords bruts extraits: '{keywords_raw}'")
                
                # Parser les keywords (séparer par virgules, espaces, "et", etc.)
                keywords = re.split(r'[,\s]+(?:et\s+)?', keywords_raw)
                keywords = [kw.strip().strip('"\'') for kw in keywords if kw.strip()][:5]
                
                print(f"[CONV-SCANNER-IA] 📝 Keywords parsés: {keywords}")
                
                if keywords:
                    try:
                        from conversation_scanner import search_recent_conversations, format_results_for_injection
                        
                        # Afficher le spinner anime pendant la recherche (si streaming)
                        if _streaming_widget_ref and _magic_phrase_was_detected:
                            try:
                                # magic_phrase_text n'est pas encore definie ici, utiliser reply_text tronque
                                spinner_preview = reply_text[:200] if reply_text else ""
                                _streaming_widget_ref.set_content(spinner_preview)
                                # Injecter spinner recherche anime via JS
                                _sr_client = _chat_inner.client if _chat_inner else None
                                if _sr_client:
                                    _sr_client.run_javascript(_SPINNER_REMOVE_JS)  # Retirer l'ancien
                                    _sr_client.run_javascript(_get_spinner_inject_js('search'))
                                print("[CONV-SCANNER-IA] 🔄 Spinner recherche animé injecté")
                            except Exception as e:
                                print(f"[CONV-SCANNER-IA] ⚠️ Erreur affichage spinner: {e}")
                        
                        # Rechercher dans les 20 dernières conversations
                        results = search_recent_conversations(
                            keywords=keywords,
                            max_conversations=20,
                            context_size=5,  # Contexte élargi
                            max_results=10,
                            debug=True
                        )
                        
                        if results:
                            print(f"[CONV-SCANNER-IA] ✅ {len(results)} résultat(s) trouvé(s)")
                            
                            # Formater pour injection
                            search_context = format_results_for_injection(
                                results=results,
                                keywords=keywords,
                                max_results_display=3,
                                max_chars_per_message=150
                            )
                            
                            print(f"[CONV-SCANNER-IA] 📝 Contexte généré: {len(search_context)} chars")
                            
                            # STRATÉGIE: Ne pas régénérer TOUTE la réponse, mais CONTINUER après la phrase magique
                            # 1. Injecter contexte recherche
                            # 2. Ajouter la phrase initiale de l'IA principale comme message assistant
                            # 3. Demander continuation
                            
                            search_messages = messages.copy()
                            
                            # Injection contexte dans système
                            if search_messages and search_messages[0]['role'] == 'system':
                                search_addon = f"\n\n{search_context}\n"
                                search_messages[0]['content'] += search_addon
                                print("[CONV-SCANNER-IA] ✅ Contexte ajouté au système")
                            else:
                                search_messages.insert(0, {'role': 'system', 'content': search_context})
                                print("[CONV-SCANNER-IA] ✅ Nouveau message système créé")
                            
                            # Ajouter la phrase magique de l'IA principale comme début de réponse
                            magic_phrase_text = reply_text[:reply_text.index(match.group(0)) + len(match.group(0))]
                            search_messages.append({
                                'role': 'assistant',
                                'content': magic_phrase_text
                            })
                            print(f"[CONV-SCANNER-IA] 📝 Phrase magique préservée: '{magic_phrase_text}'")
                            
                            # Ajouter instruction de continuation comme message user
                            # (certains providers comme Mistral exigent que le dernier message soit user)
                            search_messages.append({
                                'role': 'user',
                                'content': "[INSTRUCTION SYSTEME] Tu viens d'ecrire la phrase ci-dessus et tu as maintenant les resultats de ta recherche. CONTINUE ta reponse en exploitant ces resultats concrets (dates, details precis). Ne repete pas ta phrase magique."
                            })
                            
                            # Demander continuation
                            print("[CONV-SCANNER-IA] 🔄 Demande de continuation avec contexte...")
                            
                            controller = _ensure_chat_controller()
                            if controller:
                                continuation, new_error = await controller.call_chat_api(
                                    messages=search_messages,
                                    max_tokens=1024,
                                    context_length=controller.context_length if hasattr(controller, 'context_length') else 128000,
                                    temperature=0.8,
                                    is_json=False
                                )
                                
                                if continuation and not new_error:
                                    print(f"[CONV-SCANNER-IA] ✅ Continuation générée: {len(continuation)} chars")
                                    # Combiner phrase magique + continuation
                                    full_response = magic_phrase_text + "\n\n" + continuation
                                    cleaned_reply = full_response
                                    reply_text = full_response
                                    print(f"[CONV-SCANNER-IA] 🎯 Réponse finale: {len(full_response)} chars")
                                    
                                    # 🖼️ Mettre à jour le widget streaming avec la réponse complète
                                    if _streaming_widget_ref:
                                        try:
                                            _streaming_widget_ref.set_content(full_response)
                                            print("[CONV-SCANNER-IA] ✅ Widget streaming mis à jour avec réponse complète")
                                        except Exception as e:
                                            print(f"[CONV-SCANNER-IA] ⚠️ Erreur mise à jour widget: {e}")
                                else:
                                    print(f"[CONV-SCANNER-IA] ❌ Erreur continuation: {new_error}")
                            else:
                                print("[CONV-SCANNER-IA] ❌ Chat controller non disponible")
                        else:
                            print("[CONV-SCANNER-IA] ⚠️ Aucun résultat trouvé pour ces keywords")
                            # Retirer le spinner et générer une continuation honnête
                            try:
                                client.run_javascript(_SPINNER_REMOVE_JS)
                            except Exception:
                                pass
                            _ctrl = _ensure_chat_controller()
                            if _ctrl and _streaming_widget_ref:
                                _no_result_msgs = messages.copy()
                                _no_result_msgs.append({'role': 'assistant', 'content': reply_text})
                                _no_result_msgs.append({'role': 'user', 'content': "[INSTRUCTION SYSTEME] Ta recherche dans les conversations précédentes n'a renvoyé aucun résultat. Réponds honnêtement que tu n'as pas de souvenir de conversations précédentes avec cette personne."})
                                _continuation, _ = await _ctrl.call_chat_api(
                                    messages=_no_result_msgs,
                                    max_tokens=512,
                                    context_length=_ctrl.context_length if hasattr(_ctrl, 'context_length') else 128000,
                                    temperature=0.7,
                                    is_json=False
                                )
                                if _continuation:
                                    reply_text = _continuation
                                    cleaned_reply = _continuation
                                    _streaming_widget_ref.set_content(_continuation)
                                else:
                                    _fallback = (text_before_magic + " " if text_before_magic else "") + "Je n'ai trouvé aucune conversation précédente — c'est notre première rencontre !"
                                    reply_text = _fallback
                                    cleaned_reply = _fallback
                                    _streaming_widget_ref.set_content(_fallback)
                            elif _streaming_widget_ref:
                                _fallback = (text_before_magic + " " if text_before_magic else "") + "Je n'ai trouvé aucune conversation précédente — c'est notre première rencontre !"
                                reply_text = _fallback
                                cleaned_reply = _fallback
                                _streaming_widget_ref.set_content(_fallback)
                    except ImportError:
                        print("[CONV-SCANNER-IA] ⚠️ Module conversation_scanner non disponible")
                        try:
                            client.run_javascript(_SPINNER_REMOVE_JS)
                        except Exception:
                            pass
                        if _streaming_widget_ref:
                            _fallback = (text_before_magic + " " if text_before_magic else "") + "Je n'ai trouvé aucune conversation précédente — c'est notre première rencontre !"
                            reply_text = _fallback
                            cleaned_reply = _fallback
                            _streaming_widget_ref.set_content(_fallback)
                    except Exception as scan_err:
                        print(f"[CONV-SCANNER-IA] ❌ Erreur recherche: {scan_err}")
                        import traceback
                        traceback.print_exc()
                        try:
                            client.run_javascript(_SPINNER_REMOVE_JS)
                        except Exception:
                            pass
                        if _streaming_widget_ref:
                            _fallback = (text_before_magic + " " if text_before_magic else "") + "Je n'ai trouvé aucune conversation précédente — c'est notre première rencontre !"
                            reply_text = _fallback
                            cleaned_reply = _fallback
                            _streaming_widget_ref.set_content(_fallback)
                else:
                    print("[CONV-SCANNER-IA] ⚠️ Aucun keyword valide extrait")
                    try:
                        client.run_javascript(_SPINNER_REMOVE_JS)
                    except Exception:
                        pass
                    if _streaming_widget_ref and text_before_magic:
                        _streaming_widget_ref.set_content(text_before_magic)
        
        except Exception as e:
            print(f"[CONV-SCANNER-IA] ❌ Erreur système: {e}")
            import traceback
            traceback.print_exc()
            try:
                client.run_javascript(_SPINNER_REMOVE_JS)
            except Exception:
                pass

        # CONTEXTUAL RECALL - PRIORITÉ 2 : Recherche temporelle (résumés par date)
        # Skip si phrase magique image (évite double traitement)
        img2img_magic_patterns = [
            "je dois modifier cette image",
            "il faut que je modifie cette image",
            "je dois créer une image",
            "il faut que je crée une image"
        ]
        has_img2img_magic = any(p in reply_text.lower() for p in img2img_magic_patterns)
        
        if has_img2img_magic:
            print("[CONTEXTUAL-RECALL-IA] Skip recall - phrase magique image détectée (évite double traitement)")
        else:
            try:
                # Patterns synchronisés avec temporal_parser.py
                recall_ia_patterns = [
                    r"il\s+faut\s+que\s+je\s+consulte\s+notre\s+conversation\s+d(?:e\b|')",
                    r"je\s+dois\s+consulter\s+notre\s+conversation\s+d(?:e\b|')",
                    r"laisse-?moi\s+consulter\s+notre\s+conversation\s+d(?:e\b|')",
                    # Nouveaux patterns pour "mes/la/les conversations"
                    r"il\s+faut\s+que\s+je\s+consulte\s+mes\s+conversations?\s*(?:avec\s+\w+)?",
                    r"je\s+dois\s+consulter\s+mes\s+conversations?\s*(?:avec\s+\w+)?",
                    r"il\s+faut\s+que\s+je\s+consulte\s+(?:la|les)\s+conversations?\s*(?:avec\s+\w+)?",
                    # Pattern commande directe "va lire la conversation X"
                    r"va\s+lire\s+(?:la|les)\s+conversations?\s*(?:\w+)?",
                    r"(?:je\s+vais|vais)\s+(?:lire|consulter)\s+(?:la|les)\s+conversations?\s*(?:\w+)?",
                ]
                
                is_ia_recall_trigger = any(re.search(pattern, reply_text, re.IGNORECASE) for pattern in recall_ia_patterns)
                
                if is_ia_recall_trigger:
                    print(f"[CONTEXTUAL-RECALL-IA] L'IA déclenche elle-même une recherche contextuelle!")
                    
                    recall_ext = _ensure_contextual_recall()
                    
                    if recall_ext:
                        # Traiter le message IA avec le parser temporel
                        recall_context = recall_ext.process_message(reply_text, source="ia")
                        
                        if recall_context and recall_context.strip():
                            print(f"[CONTEXTUAL-RECALL-IA] Contexte mémoire récupéré: {len(recall_context)} chars")
                            
                            # COMPORTEMENT IDENTIQUE À L'UTILISATEUR: 
                            # Régénérer la réponse avec le contexte injecté
                            
                            # 1. Construire nouveau messages avec contexte
                            recall_messages = messages.copy()
                            
                            # Injecter dans le système
                            if recall_messages and recall_messages[0]['role'] == 'system':
                                recall_addon = f"\n\n--- CONTEXTE CONVERSATIONNEL HISTORIQUE (Auto-consulté par IA) ---\n{recall_context}\n--- FIN CONTEXTE ---"
                                recall_messages[0]['content'] += recall_addon
                                print("[CONTEXTUAL-RECALL-IA] OK Contexte ajouté au message système")
                            else:
                                recall_messages.insert(0, {'role': 'system', 'content': f"--- CONTEXTE CONVERSATIONNEL HISTORIQUE (Auto-consulté par IA) ---\n{recall_context}\n--- FIN CONTEXTE ---"})
                                print("[CONTEXTUAL-RECALL-IA] OK Nouveau message système créé")
                            
                            # 2. Régénérer la réponse avec le contexte
                            print("[CONTEXTUAL-RECALL-IA] Régénération réponse avec contexte historique...")
                            
                            controller = _ensure_chat_controller()
                            if controller:
                                new_response, new_error = await controller.call_chat_api(
                                    messages=recall_messages,
                                    max_tokens=1024,
                                    context_length=controller.context_length if hasattr(controller, 'context_length') else 128000,
                                    temperature=0.8,
                                    is_json=False
                                )
                                
                                if new_response and not new_error:
                                    print(f"[CONTEXTUAL-RECALL-IA] Nouvelle réponse générée: {len(new_response)} chars")
                                    # Remplacer la réponse originale
                                    cleaned_reply = new_response
                                    reply_text = new_response
                                else:
                                    print(f"[CONTEXTUAL-RECALL-IA] Erreur régénération: {new_error}")
                            
                            print("[CONTEXTUAL-RECALL-IA] STATS Injection et régénération réussie")
                        else:
                            # Fallback: pas de résumé → lire la dernière conversation avec contenu
                            print("[CONTEXTUAL-RECALL-IA] ⚠️ Pas de résumé trouvé, fallback lecture directe...")
                            try:
                                import json as _json_rc
                                conv_dir = DATA_DIR / "conversations"
                                conv_files = sorted(
                                    [f for f in conv_dir.glob("*.json") if f.name != "index.json" and not f.name.startswith("index_backup_")],
                                    key=lambda f: f.stat().st_mtime,
                                    reverse=True
                                )
                                # Exclure la conversation courante
                                current_fname = f"{_current_conversation_id}.json" if _current_conversation_id else None
                                candidate_files = [f for f in conv_files if f.name != current_fname]
                                
                                # Itérer sur plusieurs fichiers jusqu'à trouver une conv avec contenu
                                fallback_file = None
                                transcript_lines = []
                                for cand in candidate_files[:5]:  # essayer les 5 plus récentes
                                    try:
                                        raw = _json_rc.loads(cand.read_text(encoding='utf-8'))
                                        msgs_raw = raw if isinstance(raw, list) else raw.get('messages', [])
                                        lines = []
                                        for m in msgs_raw:
                                            m_role = m.get('role', '')
                                            m_content = m.get('content', '')
                                            if m_role == 'user':
                                                m_content = re.sub(r'^\[.*?\]\s*', '', m_content)
                                                lines.append(f"Utilisateur: {m_content[:300]}")
                                            elif m_role == 'assistant':
                                                lines.append(f"IA: {m_content[:400]}")
                                        if lines:
                                            fallback_file = cand
                                            transcript_lines = lines
                                            break
                                        else:
                                            print(f"[CONTEXTUAL-RECALL-IA] ⏭️ Skip '{cand.name}' (0 messages user/assistant)")
                                    except Exception as e_cand:
                                        print(f"[CONTEXTUAL-RECALL-IA] ⏭️ Skip '{cand.name}' erreur: {e_cand}")
                                
                                if fallback_file and transcript_lines:
                                    fallback_ctx = (
                                        f"--- DERNIÈRE CONVERSATION DU {fallback_file.stem[:10]} ---\n"
                                        + "\n".join(transcript_lines[:40])
                                    )
                                    print(f"[CONTEXTUAL-RECALL-IA] 📖 Fallback: '{fallback_file.name}' ({len(transcript_lines)} msgs)")
                                    fb_messages = messages.copy()
                                    fb_addon = f"\n\n--- CONTEXTE HISTORIQUE (lecture directe) ---\n{fallback_ctx}\n--- FIN ---"
                                    if fb_messages and fb_messages[0]['role'] == 'system':
                                        fb_messages[0]['content'] += fb_addon
                                    else:
                                        fb_messages.insert(0, {'role': 'system', 'content': fb_addon})
                                    fb_controller = _ensure_chat_controller()
                                    if fb_controller:
                                        fb_response, fb_error = await fb_controller.call_chat_api(
                                            messages=fb_messages,
                                            max_tokens=1024,
                                            context_length=fb_controller.context_length if hasattr(fb_controller, 'context_length') else 128000,
                                            temperature=0.8,
                                            is_json=False
                                        )
                                        if fb_response and not fb_error:
                                            cleaned_reply = fb_response
                                            reply_text = fb_response
                                            print(f"[CONTEXTUAL-RECALL-IA] ✅ Fallback réponse: {len(fb_response)} chars")
                                        else:
                                            print(f"[CONTEXTUAL-RECALL-IA] ❌ Fallback erreur API: {fb_error}")
                                            cleaned_reply = "Je n'ai pas pu accéder à l'historique des conversations."
                                            reply_text = cleaned_reply
                                else:
                                    print("[CONTEXTUAL-RECALL-IA] ⚠️ Aucune conversation précédente avec contenu trouvée")
                                    cleaned_reply = "Je n'ai trouvé aucune conversation précédente à consulter."
                                    reply_text = cleaned_reply
                            except Exception as e_fb:
                                print(f"[CONTEXTUAL-RECALL-IA] ⚠️ Erreur fallback lecture directe: {e_fb}")
                                cleaned_reply = "Une erreur m'a empêché de consulter l'historique."
                                reply_text = cleaned_reply
                    else:
                        print("[CONTEXTUAL-RECALL-IA] SKIP Extension non disponible")
                        
            except Exception as e:
                print(f"[CONTEXTUAL-RECALL-IA] Erreur recherche contextuelle IA: {e}")
                import traceback
                traceback.print_exc()

        # GÉNÉRATION D'IMAGES - Détection et traitement via extension text2img
        try:
            from logic_callbacks import process_image_generation
            from extensions.text2img import get_text2img_manager, is_available as text2img_available

            sm = _ensure_settings_manager()

            if text2img_available():
                # Vérifier si une génération est demandée (pré-détection rapide)
                text2img_patterns = [
                    "je dois créer une image",
                    "il faut que je crée une image",
                    "je vais générer une image",
                    "je dois générer une image"
                ]
                needs_text2img = any(p in cleaned_reply.lower() for p in text2img_patterns)
                print(f"[IMAGE-NOTIFY] Pré-détection text2img: {needs_text2img}")
                
                if needs_text2img:
                    # 🎭 CHECK REPRÉSENTATIONS: Si boutons User/IA actifs → rediriger vers I2I
                    if _has_active_representations():
                        print("[IMAGE-REPR] 🎭 Représentations actives détectées - Redirection T2I → I2I")
                        # 🌀 Spinner IMMÉDIAT dès détection (avant vision call et regex match)
                        _notify_safe("🎭 Génération avatars: analyse en cours...", 'ongoing', timeout=120)
                        set_ia_working(True)
                        await asyncio.sleep(0)  # Flush NiceGUI → navigateur voit le spinner
                        
                        # Récupérer les images de représentation
                        repr_images = _get_active_representations()
                        
                        if repr_images:
                            # Construire le contexte enrichi pour le prompt
                            repr_context = _build_representation_context()
                            
                            # Extraire le prompt original de l'IA
                            import re
                            prompt_match = re.search(r'je dois (?:créer|générer) une image de\s*:?\s*(.+?)(?:\n\n|$)', cleaned_reply, re.IGNORECASE | re.DOTALL)
                            if not prompt_match:
                                prompt_match = re.search(r'il faut que je crée une image de\s*:?\s*(.+?)(?:\n\n|$)', cleaned_reply, re.IGNORECASE | re.DOTALL)
                            if not prompt_match:
                                prompt_match = re.search(r'je vais générer une image de\s*:?\s*(.+?)(?:\n\n|$)', cleaned_reply, re.IGNORECASE | re.DOTALL)
                            
                            if prompt_match:
                                original_prompt = prompt_match.group(1).strip().strip('"\'')
                                
                                # Notification mise à jour (spinner déjà actif)
                                _notify_safe(f"🎭 Composition prompt avec {len(repr_images)} avatar(s)...", 'ongoing', timeout=120)
                                
                                # --- APPEL VISION INTERMÉDIAIRE ---
                                # Le LLM vision analyse l'avatar et compose un prompt i2i descriptif.
                                # L'instruction utilisée est img2img_guide depuis les settings (paramètres généraux / images).
                                enriched_prompt = f"{original_prompt}\n\n{repr_context}"  # fallback textuel
                                try:
                                    _repr_compressed = _get_active_representations(for_chat=True)
                                    _vision_ctrl = _ensure_chat_controller()
                                    
                                    if _repr_compressed and _vision_ctrl:
                                        # Récupérer img2img_guide depuis les settings
                                        _sm_vision = _ensure_settings_manager()
                                        _img_cfg_vision = _sm_vision.settings.get('image_generation', {}) if _sm_vision else {}
                                        _vision_system_prompt = _img_cfg_vision.get('img2img_guide', '').strip()
                                        if not _vision_system_prompt:
                                            _vision_system_prompt = (
                                                "Tu es un composeur de prompts img2img. "
                                                "Observe les images d'avatars fournies et compose un prompt img2img "
                                                "décrivant précisément l'apparence des personnages dans la scène demandée. "
                                                "Retourne UNIQUEMENT le prompt, sans explication ni préambule."
                                            )
                                            print(f"[IMAGE-REPR] img2img_guide vide dans settings, fallback minimal utilisé")
                                        else:
                                            print(f"[IMAGE-REPR] img2img_guide chargé depuis settings ({len(_vision_system_prompt)} chars)")
                                        
                                        # Construire le contenu multimodal : images compressées + scène demandée
                                        _vision_content = []
                                        for _rc_img in _repr_compressed:
                                            _rc_b64 = _rc_img.get('data', '')
                                            if _rc_b64:
                                                _vision_content.append({
                                                    "type": "image_url",
                                                    "image_url": {"url": f"data:image/jpeg;base64,{_rc_b64}"}
                                                })
                                        _vision_content.append({
                                            "type": "text",
                                            "text": f"Scène à générer : {original_prompt}"
                                        })
                                        
                                        _vision_messages = [
                                            {'role': 'system', 'content': _vision_system_prompt},
                                            {'role': 'user', 'content': _vision_content}
                                        ]
                                        
                                        _i2i_instruction, _vision_err = await _vision_ctrl.call_chat_api(
                                            messages=_vision_messages,
                                            max_tokens=1500,
                                            context_length=8192,
                                            temperature=0.3,
                                            is_json=False
                                        )
                                        
                                        if _i2i_instruction and not _vision_err:
                                            enriched_prompt = _i2i_instruction.strip()
                                            # Nettoyage générique: supprimer toute phrase magique en préfixe
                                            # Certains modèles (Mistral, etc.) répètent la magic phrase
                                            _magic_prefixes = [
                                                r'^(?:il faut que )?je (?:dois|vais|peux)\s+(?:modifier|créer|générer|transformer|éditer)\s+(?:cette|une)\s+image\s*(?:de)?\s*:?\s*["\']?\s*',
                                                r'^(?:image\s+(?:modifiée|corrigée))\s*:?\s*["\']?\s*',
                                                r'^\*{1,2}(?:image\s+(?:modifiée|corrigée))\*{1,2}\s*:?\s*["\']?\s*',
                                                r'^["\']\s*',
                                            ]
                                            for _mp in _magic_prefixes:
                                                _cleaned = re.sub(_mp, '', enriched_prompt, count=1, flags=re.IGNORECASE)
                                                if _cleaned != enriched_prompt:
                                                    enriched_prompt = _cleaned.strip()
                                                    print(f"[IMAGE-REPR] 🧹 Nettoyage magic prefix: supprimé préambule modèle vision")
                                                    break
                                            # Nettoyage guillemets résiduels (début/fin)
                                            enriched_prompt = enriched_prompt.strip('"\'').strip()
                                            # Supprimer phrases bavardes post-instruction du modèle vision
                                            # Ex: "I will now proceed to modify..." ou "Here is the modified..."
                                            _bavard_suffixes = [
                                                r'\n+(?:I will now|Here is|Voici|Je vais maintenant|Proceeding).*$',
                                                r'\n+!\[.*?\]\(.*?\).*$',  # Markdown images fantômes
                                            ]
                                            for _bs in _bavard_suffixes:
                                                _cleaned_suf = re.sub(_bs, '', enriched_prompt, flags=re.IGNORECASE | re.DOTALL)
                                                if _cleaned_suf != enriched_prompt:
                                                    enriched_prompt = _cleaned_suf.strip()
                                                    print(f"[IMAGE-REPR] 🧹 Nettoyage suffix bavard supprimé")
                                            print(f"[IMAGE-REPR] Instruction i2i composée par vision ({len(enriched_prompt)} chars): {enriched_prompt[:100]}...")
                                        else:
                                            print(f"[IMAGE-REPR] Appel vision échoué ({_vision_err}), fallback textuel utilisé")
                                    else:
                                        missing = []
                                        if not _repr_compressed: missing.append("avatars compressés manquants")
                                        if not _vision_ctrl: missing.append("chat_controller indisponible")
                                        print(f"[IMAGE-REPR] Fallback textuel - conditions non remplies: {', '.join(missing)}")
                                except Exception as _vision_exc:
                                    print(f"[IMAGE-REPR] Exception appel vision: {_vision_exc} - fallback textuel utilisé")
                                # --- FIN APPEL VISION INTERMÉDIAIRE ---
                                
                                print(f"[IMAGE-REPR] Prompt i2i final: {enriched_prompt[:100]}...")
                                
                                # Transformer la réponse pour déclencher I2I
                                # Remplacer la phrase T2I par une phrase I2I avec le prompt enrichi
                                cleaned_reply = re.sub(
                                    r'je dois (?:créer|générer) une image de\s*:?\s*.+?(?:\n\n|$)',
                                    f'je dois modifier cette image : {enriched_prompt}\n\n',
                                    cleaned_reply,
                                    flags=re.IGNORECASE | re.DOTALL
                                )
                                cleaned_reply = re.sub(
                                    r'il faut que je crée une image de\s*:?\s*.+?(?:\n\n|$)',
                                    f'je dois modifier cette image : {enriched_prompt}\n\n',
                                    cleaned_reply,
                                    flags=re.IGNORECASE | re.DOTALL
                                )
                                cleaned_reply = re.sub(
                                    r'je vais générer une image de\s*:?\s*.+?(?:\n\n|$)',
                                    f'je dois modifier cette image : {enriched_prompt}\n\n',
                                    cleaned_reply,
                                    flags=re.IGNORECASE | re.DOTALL
                                )
                                
                                # NE PAS ajouter les avatars à _active_images
                                # Ils seront passés via repr_images_hd au process_img2img_generation
                                print(f"[IMAGE-REPR] {len(repr_images)} avatar(s) HD préparés (non ajoutés à _active_images)")
                                
                                # Stocker pour passage à img2img plus tard
                                _repr_images_for_i2i = repr_images
                                _enriched_i2i_prompt = enriched_prompt  # Bypass regex extraction
                                
                                # Le traitement I2I sera fait dans la section suivante - spinner RESTE ON
                            else:
                                print("[IMAGE-REPR] ⚠️ Impossible d'extraire le prompt - génération T2I normale")
                                # Fallback: génération T2I normale
                                _notify_safe("🖼️ Génération d'image en cours... Veuillez patienter", 'ongoing', timeout=60)
                                set_ia_working(True)
                                
                                text2img_mgr = get_text2img_manager()
                                cleaned_reply = await process_image_generation(
                                    cleaned_reply,
                                    sm,
                                    text2img_mgr
                                )
                                
                                set_ia_working(False)
                                _notify_safe("✅ Image générée avec succès!", 'positive')
                        else:
                            print("[IMAGE-REPR] ⚠️ Représentations actives mais images non trouvées - T2I normal")
                            _notify_safe("🖼️ Génération d'image en cours... Veuillez patienter", 'ongoing', timeout=60)
                            set_ia_working(True)
                            
                            text2img_mgr = get_text2img_manager()
                            cleaned_reply = await process_image_generation(
                                cleaned_reply,
                                sm,
                                text2img_mgr
                            )
                            
                            set_ia_working(False)
                            _notify_safe("✅ Image générée avec succès!", 'positive')
                    else:
                        # Pas de représentations actives - Génération T2I normale
                        _notify_safe("🖼️ Génération d'image en cours... Veuillez patienter", 'ongoing', timeout=60)
                        print("[IMAGE-NOTIFY] ✅ Notification 'en cours' affichée")
                        set_ia_working(True)
                        
                        text2img_mgr = get_text2img_manager()
                        cleaned_reply = await process_image_generation(
                            cleaned_reply,
                            sm,
                            text2img_mgr
                        )
                        
                        set_ia_working(False)
                        _notify_safe("✅ Image générée avec succès!", 'positive')
                
                print("[IMAGE] Traitement génération d'image terminé")
            else:
                print("[IMAGE] WARN Extension text2img non disponible")
        except ImportError as ie:
            print(f"[IMAGE] Extension génération d'images non disponible: {ie}")
        except Exception as e:
            print(f"[IMAGE] ERROR Erreur traitement génération: {e}")

        # 🎨 IMAGE-TO-IMAGE - Détection et traitement modification d'images
        try:
            from logic_callbacks import process_img2img_generation
            
            sm = _ensure_settings_manager()
            img_config = sm.settings.get('image_generation', {})
            
            if img_config.get('img2img_enabled', False):
                # Vérifier si une modification est demandée (pré-détection rapide)
                img2img_patterns = [
                    "je dois modifier cette image",
                    "il faut que je modifie cette image",
                    "image modifiée",
                    "image corrigée"
                ]
                needs_img2img = any(p in cleaned_reply.lower() for p in img2img_patterns)
                
                # IMPORTANT: N'appeler la fonction QUE si une phrase magique est détectée
                if needs_img2img:
                    print(f"[IMG2IMG] ✅ Phrase magique détectée - traitement img2img...")
                    
                    # 🎭 RÉCUPÉRATION REPRÉSENTATIONS: Si boutons User/IA actifs → récupérer avatars HD
                    # IMPORTANT: NE PAS les ajouter à _active_images (ils seront passés séparément)
                    repr_images_hd = None
                    if _has_active_representations():
                        repr_images_hd = _get_active_representations(for_chat=False)  # Version HD pour img2img
                        print(f"[IMG2IMG-REPR] 🎭 {len(repr_images_hd)} représentation(s) HD récupérée(s) (non ajoutées à _active_images)")
                    
                    # Récupérer aussi les avatars stockés depuis T2I→I2I si présents
                    if _repr_images_for_i2i:
                        repr_images_hd = _repr_images_for_i2i
                        print(f"[IMG2IMG-REPR] 🎭 Utilisation avatars stockés T2I→I2I ({len(repr_images_hd)} image(s))")
                        _repr_images_for_i2i = []  # Reset après utilisation
                    
                    # Récupérer prompt enrichi stocké depuis T2I→I2I (bypass regex)
                    _override_prompt = None
                    if _enriched_i2i_prompt:
                        _override_prompt = _enriched_i2i_prompt
                        print(f"[IMG2IMG-OVERRIDE] Prompt direct: {len(_override_prompt)} chars (bypass regex)")
                        _enriched_i2i_prompt = ""  # Reset après utilisation
                    
                    # Vérifier si des images sont disponibles (multi-image ou single)
                    has_images = bool(_active_images) or (_active_file_data and _active_file_data.get('type') == 'image')
                    
                    # 🎥 INCLURE IMAGE PERCEPTION si disponible
                    # perception_image_data contient l'image webcam capturée au moment de l'envoi
                    has_perception = perception_image_data is not None
                    total_images = (len(_active_images) if _active_images else (1 if has_images else 0)) + (1 if has_perception else 0)
                    
                    _has_repr = bool(repr_images_hd)
                    if has_images or has_perception or _has_repr:
                        # Afficher notification de génération en cours
                        # Vérifier si auto-correction est active
                        _autocorrect_on = img_config.get('i2i_autocorrect_enabled', False)
                        if _autocorrect_on:
                            from modules.logic import reset_i2i_stop
                            reset_i2i_stop()
                            _max_r = img_config.get('i2i_max_retries', 3)
                            _notify_safe(f"🎨🔄 Modification auto-corrective ({_max_r} tentatives max)...", 'ongoing', timeout=120)
                        else:
                            if _has_repr and not (has_images or has_perception):
                                _notify_safe(f"🎭 Génération avec représentation(s) en cours... Veuillez patienter", 'ongoing', timeout=60)
                            else:
                                _notify_safe(f"🎨 Modification avec {total_images} image(s)... Veuillez patienter", 'ongoing', timeout=60)
                        # 🌀 SPINNER: Forcer cycle OFF→ON pour garantir rendu navigateur même si déjà actif
                        set_ia_working(False)
                        await asyncio.sleep(0)  # Flush OFF
                        set_ia_working(True)
                        await asyncio.sleep(0)  # Flush ON → navigateur voit le spinner
                    
                    # Passer les images uploadées + perception + représentations HD (multi-image support)
                    cleaned_reply = await process_img2img_generation(
                        cleaned_reply,
                        sm,
                        _active_file_data,  # Fichier uploadé legacy (backward compat)
                        _active_images,      # Liste d'images uploadées (MULTI-IMAGE)
                        perception_image_data,  # 🎥 Image webcam pour fusion
                        repr_images_hd,      # 🎭 Avatars HD (séparés de _active_images)
                        override_prompt=_override_prompt  # Prompt direct (bypass regex)
                    )
                    
                    if has_images or has_perception or _has_repr:
                        set_ia_working(False)
                        # Notification de succès
                        _notify_safe("✅ Image modifiée avec succès!", 'positive')
                    
                    print("[IMG2IMG] Traitement modification d'image terminé")
                else:
                    print("[IMG2IMG] ⚪ Pas de phrase magique img2img détectée")
            else:
                print("[IMG2IMG] Image-to-Image désactivé dans les paramètres")
        except ImportError as ie:
            print(f"[IMG2IMG] Fonction img2img non disponible: {ie}")
        except Exception as e:
            print(f"[IMG2IMG] ERROR Erreur traitement modification: {e}")
            import traceback
            traceback.print_exc()

        # �🕐 DÉTECTION DEMANDE D'HEURE AUTOMATIQUE (DÉSACTIVÉ - causait doublon avec Temporal Guardian)
        # if re.search(r'\b(quelle heure|l\'heure|heure est|heures? est)\b', text.lower()):
        #     current_time = _get_current_time()
        #     cleaned_reply = f"{cleaned_reply}\n\nTIME Il est actuellement {current_time}"

        # 📝 FILE WRITER - Génération asynchrone documents .md
        print("[FILE-WRITER] Vérification demande création fichier...")
        try:
            # Détection directe via pattern /doc (sans dépendre de l'agent)
            import re as re_doc
            is_doc_request_detected = bool(re_doc.match(r'^/doc\s+', text.strip(), re_doc.IGNORECASE))
            
            if is_doc_request_detected:
                print("[FILE-WRITER] 📝 Demande de document détectée!")
                _notify_safe("📝 Génération du document en cours...", 'info')
                
                # Importer le générateur asynchrone
                from extensions.file_writer.document_generator import generate_document_async
                
                # Récupérer le contrôleur IA
                chat_ctrl = _ensure_chat_controller()
                
                if chat_ctrl:
                    # Extraire un titre depuis la demande utilisateur
                    title_match = re_doc.search(r'/doc\s+(.+?)(?:\.|$)', text, re_doc.IGNORECASE)
                    doc_title = title_match.group(1).strip() if title_match else "document"
                    
                    # Construire le contexte complet pour le générateur
                    # Inclut : souvenirs + contexte temporel + conversation
                    doc_context_parts = []
                    
                    # Ajouter les souvenirs pertinents depuis detailed_memories
                    try:
                        if 'detailed_memories' in dir() and detailed_memories:
                            doc_context_parts.append("\n=== SOUVENIRS ET MÉMOIRE ===")
                            for mem in detailed_memories[:8]:  # Top 8 souvenirs
                                title = mem.get('title', 'Sans titre')
                                content = mem.get('text_original', mem.get('summary', ''))
                                if content:
                                    doc_context_parts.append(f"• {title}: {content[:500]}")
                            print(f"[FILE-WRITER] 🧠 {len(detailed_memories[:8])} souvenirs injectés dans le contexte")
                    except Exception as mem_e:
                        print(f"[FILE-WRITER] ⚠️ Souvenirs non récupérés: {mem_e}")
                    
                    doc_context = "\n".join(doc_context_parts) if doc_context_parts else ""
                    
                    # Callback quand génération terminée
                    def on_doc_complete(content: str, path: str):
                        print(f"[FILE-WRITER] ✅ Document généré: {path} ({len(content)} chars)")
                        set_archiviste_working(False)
                        _notify_safe(f"📁 Document créé: {Path(path).name}", 'positive')
                    
                    def on_doc_error(error: str):
                        print(f"[FILE-WRITER] ❌ Erreur génération: {error}")
                        set_archiviste_working(False)
                        _notify_safe(f"❌ Erreur création document: {error}", 'negative')
                    
                    # Spinner Archiviste pendant la génération (tâche de fond)
                    set_archiviste_working(True)
                    # Lancer la génération ASYNCHRONE en background
                    import asyncio as async_fw
                    async_fw.create_task(generate_document_async(
                        user_request=text,
                        title=doc_title,
                        ai_controller=chat_ctrl,
                        context=doc_context,
                        conversation_history=_chat_history[-10:] if _chat_history else [],
                        on_complete=on_doc_complete,
                        on_error=on_doc_error,
                        debug=True
                    ))
                    print(f"[FILE-WRITER] 🚀 Génération asynchrone lancée: {doc_title}")
                else:
                    print("[FILE-WRITER] ❌ Pas de contrôleur IA disponible")
            else:
                print("[FILE-WRITER] ⚪ Pas de demande de document détectée")
        except Exception as e:
            print(f"[FILE-WRITER] ERROR Erreur traitement: {e}")
            import traceback
            traceback.print_exc()
        
        # 🎯 CAPABILITY ADVISOR - Détection utilisation capacité suggérée
        if capability_suggestion:
            advisor = _ensure_capability_advisor()
            if advisor:
                try:
                    # Utiliser reply_text (réponse brute) au lieu de cleaned_reply (après enrichissements)
                    # pour détecter la phrase magique avant modifications (web search, etc.)
                    capability_used = advisor.detect_capability_usage(reply_text)
                    
                    if capability_used:
                        print(f"[CAPABILITY-ADVISOR] ✅ Capacité {capability_suggestion.capability_id} UTILISÉE dans réponse IA")
                        # LED éteinte automatiquement par detect_capability_usage()
                    else:
                        # LED s'éteindra automatiquement au message suivant
                        print(f"[CAPABILITY-ADVISOR] ⚪ Capacité {capability_suggestion.capability_id} non détectée (pas de phrase magique)")
                except Exception as e:
                    print(f"[CAPABILITY-ADVISOR] ⚠️ Erreur détection utilisation: {e}")

        # 🧹 NETTOYAGE HISTORIQUE - Remplacer HTML images par phrase magique pour réutilisation
        # Problème : l'IA principale voit le format "🖼️ **Image générée :**" dans l'historique et le copie
        # sans prononcer la phrase magique, ce qui empêche les générations suivantes
        history_content = cleaned_reply
        
        # --- DÉTECTIONS POST-TRAITEMENT (Mémoire, Agenda, Ego) ---
        # On effectue ces détections sur la réponse FINALE (après régénérations éventuelles)
        ai_memorized = False
        mem = _ensure_memory_manager()
        
        print(f"[MAGIC-DEBUG] Analyse de la réponse finale ({len(cleaned_reply)} chars)")
        if len(cleaned_reply) > 0:
            print(f"[MAGIC-DEBUG] Contenu: {cleaned_reply[:100]}...{cleaned_reply[-100:] if len(cleaned_reply) > 100 else ''}")
        
        # 1. Détection "phrase magique" dans la réponse IA et mémorisation
        magic_ai = _extract_magic_memories(cleaned_reply)
        if magic_ai:
            print(f"[MAGIC-DEBUG] Phrases détectées: {magic_ai}")
            print(f"[MAGIC-DEBUG] MemoryManager: {mem}")
            if mem is not None:
                for content in magic_ai:
                    try:
                        print(f"[MAGIC-DEBUG] Tentative mémorisation de: {content[:50]}...")
                        mem_id = f"ai-{uuid.uuid4()}"
                        # Nouveau système unifié: passer chat_controller pour scoring IA Principale
                        conversation_context = "\n".join([f"{msg['role']}: {msg.get('content', '')}" for msg in _chat_history[-3:] if isinstance(msg.get('content'), str)])
                        print(f"[MAGIC-DEBUG] Appel mem.add_memory (controller={_chat_controller})...")
                        # 🌀 SPINNER: Activer le spinner Archiviste pendant l'enrichissement mémoire
                        set_archiviste_working(True)
                        ok = await mem.add_memory(
                            mem_id, 
                            content,
                            chat_controller=_chat_controller,
                            conversation_context=conversation_context,
                            interlocutor="Utilisateur"
                        )
                        set_archiviste_working(False)
                        print(f"[MAGIC-DEBUG] Résultat add_memory: {ok}")
                        if ok:
                            _notify_safe(f"SAVE Souvenir mémorisé: {content[:80]}...", 'positive')
                            _trigger_memory_update()
                            ai_memorized = True
                        else:
                            print(f"[MAGIC-DEBUG] Échec mémorisation (ok=False)")
                            _notify_safe("Échec de la mémorisation (voir logs)", 'warning')
                    except Exception as e:
                        set_archiviste_working(False)
                        print(f"[MAGIC-DEBUG] EXCEPTION mémorisation: {e}")
                        import traceback
                        traceback.print_exc()
                        _notify_safe(f"Erreur mémorisation: {e}", 'warning')
        else:
            print("[MAGIC-DEBUG] Aucune phrase magique détectée dans la réponse IA")
        
        # 2. Traitement des évènements Organic Planner (IA)
        organic_events_ai = _extract_organic_events(cleaned_reply)
        organic_updates_ai = _extract_organic_updates(cleaned_reply)
        
        if organic_events_ai:
            planner = _ensure_organic_planner()
            if planner:
                for event in organic_events_ai:
                    try:
                        ok = planner.add_event(
                            content=event['title'],
                            target_date=event['date'],
                            emotional_note=event['feeling']
                        )
                        if ok:
                            _notify_safe(f"📅 Évènement noté: {event['title']} ({event['date']})", 'positive')
                            ai_memorized = True
                        else:
                            _notify_safe("Échec de l'enregistrement de l'évènement", 'warning')
                    except Exception as e:
                        _notify_safe(f"Erreur Organic Planner: {event['title']}: {e}", 'warning')

        if organic_updates_ai:
            planner = _ensure_organic_planner()
            if planner:
                for update in organic_updates_ai:
                    try:
                        event_data = planner.update_event_status_by_title(
                            title=update['title'],
                            status=update['status']
                        )
                        if event_data:
                            _notify_safe(f"📅 Statut mis à jour: {update['title']} -> {update['status']}", 'positive')
                            
                            # 💾 ARCHIVAGE DANS LA MÉMOIRE SI TERMINÉ
                            if update['status'] == 'TERMINE':
                                if mem:
                                    memory_content = (
                                        f"Évènement terminé : {event_data['content']} "
                                        f"(Date prévue: {event_data['target_date']}). "
                                        f"Ressenti: {event_data['emotional_note']}"
                                    )
                                    ok_mem = await mem.add_memory(f"plan-{uuid.uuid4()}", memory_content)
                                    if ok_mem:
                                        planner.delete_event(event_data['id'])
                                        _notify_safe(f"💾 Archivé dans la mémoire OGMA", 'positive')
                                        _trigger_memory_update()
                            
                            ai_memorized = True
                        else:
                            _notify_safe(f"Évènement non trouvé: {update['title']}", 'warning')
                    except Exception as e:
                        _notify_safe(f"Erreur Organic Planner Update: {e}", 'warning')

        # 3. Détection phrase-clé ego prompt: "ceci est une part de moi maintenant"
        # Regex plus robuste pour l'ego (supporte Markdown et ponctuation)
        ego_pattern = r"(?:\*\*|__)?ceci\s+est\s+une\s+part\s+de\s+moi\s+maintenant(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)"
        if ego_match := re.search(ego_pattern, cleaned_reply, re.DOTALL | re.IGNORECASE):
            content = ego_match.group(1).strip()
            # Nettoyer tous les formatages markdown (au cas où)
            content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
            content = re.sub(r'[*_`]', '', content)
            print(f"[EGO-UPDATE] Contenu capturé: '{content}'")
            if mem:
                try:
                    # ATTENDRE la sauvegarde ego (ne pas lancer en background)
                    memory_id = await mem.store_ego_trait(
                        content, 
                        chat_controller=_chat_controller,
                        conversation_context="ego_trait_update",
                        interlocutor="self"
                    )
                    
                    if memory_id:
                        print(f"[EGO-UPDATE] ✅ Trait d'ego stocké avec ID: {memory_id}")
                        
                        phrases = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
                        phrase_count = len(phrases)
                        notification_msg = f"🧠 Trait d'ego mémorisé: {content[:50]}..." if phrase_count == 1 else f"🧠 Trait d'ego mémorisé ({phrase_count} phrases): {phrases[0][:40]}..."
                        _pending_notifications.append((notification_msg, 'positive'))
                        ai_memorized = True
                    else:
                        print(f"[EGO-UPDATE] ❌ Échec stockage (memory_id vide)")
                        _pending_notifications.append(("⚠️ Échec mémorisation ego", 'warning'))
                        
                except Exception as e:
                    print(f"[EGO-UPDATE] ❌ Erreur stockage trait ego: {e}")
                    import traceback
                    traceback.print_exc()
                    _pending_notifications.append((f"❌ Erreur mise à jour ego: {e}", 'warning'))
            else:
                print("[EGO-UPDATE] Erreur: MemoryManager non disponible")

        # --- FIN DÉTECTIONS ---

        # 🧹 NETTOYAGE HISTORIQUE - Préparer version propre pour l'historique JSON
        history_content = cleaned_reply
        
        # Pattern 1: Blocs d'images text2img générées avec phrase magique cachée
        image_block_pattern = r'🖼️ \*\*Image générée :\*\* "(.*?)".*?<img src=.*?/>.*?🎨.*?via.*?💾.*?(?:Sauvegardée|Échec sauvegarde).*?(?:\n|$)'
        
        # Remplacer par la phrase magique simple pour que l'IA principale puisse la réutiliser
        def replace_with_magic_phrase(match):
            description = match.group(1)
            return f"je dois créer une image de : {description}"
        
        history_content = re.sub(image_block_pattern, replace_with_magic_phrase, history_content, flags=re.DOTALL)
        
        # Pattern 2: Tags <img> orphelins - tous supprimés (l'IA ne doit pas voir de HTML brut)
        orphan_img_pattern = r'<img\s+src="/generated/[^"]+"\s*[^>]*/?>(\s*<br\s*/?>)?'
        orphan_count = len(re.findall(orphan_img_pattern, history_content))
        if orphan_count > 0:
            print(f"[IMAGE-HISTORY] 🧹 Suppression de {orphan_count} tag(s) <img> brut(s)")
            history_content = re.sub(orphan_img_pattern, '', history_content)

        # Pattern 3: Blocs batch img2img <div class="ogma-batch-grid">...</div>
        # Extraire le prompt depuis l'attribut title du premier <img> du batch, puis supprimer le HTML
        if 'ogma-batch-grid' in history_content:
            # Extraire le prompt depuis title: "... | 📋 Clic pour copier le prompt&#10;[PROMPT]"
            prompt_match = re.search(
                r'Clic pour copier le prompt&#10;([^"]+)"',
                history_content
            )
            if prompt_match:
                extracted_prompt = prompt_match.group(1).strip()
                magic_replacement = f"il faut que je modifie cette image : {extracted_prompt[:200]}"
            else:
                magic_replacement = "il faut que je modifie cette image"
            # Supprimer tout le bloc batch-grid (de l'ouverture à la fin du contenu HTML)
            history_content = re.sub(
                r'<div\s+class="ogma-batch-grid".*',
                magic_replacement,
                history_content,
                flags=re.DOTALL
            )
            print(f"[IMAGE-HISTORY] 🧹 Bloc batch img2img remplacé par phrase magique dans l'historique")

        # Pattern 4: Tout HTML résiduel générique (sécurité finale)
        if '<div class="ogma-' in history_content:
            history_content = re.sub(r'<div\s+class="ogma-[^"]*".*', '[Image générée]', history_content, flags=re.DOTALL)
            print(f"[IMAGE-HISTORY] 🧹 HTML résiduel OGMA supprimé de l'historique")

        if history_content != cleaned_reply:
            print(f"[IMAGE-HISTORY] ✂️ HTML image nettoyé de l'historique - phrase magique conservée")

        msg = {'role': 'assistant', 'content': history_content, 'memorized': ai_memorized}
        # 🧠 THINKING: Stocker le contenu thinking pour persistance multi-turn
        if _reasoning_thinking:
            msg['thinking'] = _reasoning_thinking
            print(f"[THINKING-STORE] Thinking stocke dans historique ({len(_reasoning_thinking)} chars)")
        _chat_history.append(msg)
        
        # Pour l'UI, garder le HTML complet avec l'image
        msg_ui = {'role': 'assistant', 'content': cleaned_reply, 'memorized': ai_memorized}
        _chat_history_ui.append(msg_ui)
        
        # 🌙 DREAM ENGINE: Détection mention de rêve par l'IA principale
        try:
            from extensions.dream_engine import is_available as dream_available, mark_dream_mentioned
            
            if dream_available():
                # Patterns pour détecter si l'IA principale parle de son rêve
                dream_mention_patterns = [
                    r"j['\u2019]ai\s+r[ée]v[ée]",          # j'ai rêvé
                    r"mon\s+r[ée]ve",                       # mon rêve
                    r"cette\s+nuit[,\s]+j['\u2019]ai",     # cette nuit, j'ai...
                    r"en\s+dormant",                        # en dormant
                    r"pendant\s+mon\s+sommeil",             # pendant mon sommeil
                    r"un\s+r[ée]ve\s+[ée]trange",          # un rêve étrange
                    r"r[ée]v[ée]\s+de\s+toi",              # rêvé de toi
                    r"r[ée]v[ée]\s+que",                    # rêvé que
                ]
                
                reply_lower = cleaned_reply.lower()
                if any(re.search(pattern, reply_lower) for pattern in dream_mention_patterns):
                    print("[DREAM-ENGINE] 🌙 l'IA principale a mentionné son rêve - marquage...")
                    mark_dream_mentioned()
                    print("[DREAM-ENGINE] ✅ Rêve marqué comme mentionné")
        except ImportError:
            pass  # Dream Engine non disponible
        except Exception as e:
            print(f"[DREAM-ENGINE] ⚠️ Erreur détection mention rêve: {e}")
        
        # Résumisation progressive intelligente
        try:
            await _check_progressive_summarization()
        except Exception as e:
            print(f"[WARNING] Erreur résumisation progressive: {e}")
        
        # Persistance après réponse IA
        try:
            _persist_conversation()
        except Exception:
            pass
        
        # 📔 AUTO-ARCHIVAGE JOURNAL v2.0 - Toutes les 40 interactions
        try:
            journal = get_journal_instance()
            if journal and journal.is_enabled():
                # Vérifier si auto-archivage activé
                if journal.config.get("auto_archive_enabled", False):
                    # Compter les messages user+assistant
                    user_assistant_messages = [m for m in _chat_history if m.get('role') in ('user', 'assistant')]
                    message_count = len(user_assistant_messages)
                    frequency = journal.config.get("auto_archive_frequency", 20)
                    
                    # Mise à jour compteur UI
                    if hasattr(journal, 'ui_components') and journal.ui_components:
                        journal.ui_components.update_auto_archive_counter(message_count)
                        print(f"[JOURNAL-BADGE] ✅ Badge mis à jour: {message_count}/{frequency}")
                    else:
                        print(f"[JOURNAL-BADGE] ⚠️ ui_components indisponible (has: {hasattr(journal, 'ui_components')}, val: {getattr(journal, 'ui_components', 'N/A')})")
                    
                    # Log de progression (DEBUG temporaire)
                    if message_count % 10 == 0:  # Tous les 10 messages
                        print(f"[JOURNAL-AUTO-ARCHIVE] 📊 Progression: {message_count}/{frequency} messages")
                    
                    # Trigger à chaque multiple de frequency (40, 80, 120, etc.)
                    if message_count > 0 and message_count % frequency == 0:
                        print(f"[JOURNAL-AUTO-ARCHIVE] 🚀 Déclenchement auto-archive (message #{message_count})")
                        
                        # Récupérer l'ID de conversation courante
                        conversation_id = str(_current_conversation_id) if _current_conversation_id else "current"
                        
                        # Async task pour générer micro-entrée en arrière-plan
                        async def auto_archive_task():
                            try:
                                print(f"[JOURNAL-AUTO-ARCHIVE] 📝 Génération micro-entrée (conv: {conversation_id})")
                                
                                # Appel à entry_generator.generate_micro_entry()
                                micro_entry = await journal.entry_generator.generate_micro_entry(
                                    conversation_id=conversation_id,
                                    conversation_history=_chat_history,
                                    json_manager=journal.json_manager,
                                    participants=["user", "assistant"]
                                )
                                
                                if micro_entry:
                                    print(f"[JOURNAL-AUTO-ARCHIVE] ✅ Micro-entrée créée: {micro_entry.get('entry_id')}")
                                    _notify_safe(f"📔 Conversation archivée automatiquement ({message_count} messages)", 'info')
                                else:
                                    print(f"[JOURNAL-AUTO-ARCHIVE] ⚠️ Échec génération micro-entrée")
                            
                            except Exception as e:
                                print(f"[JOURNAL-AUTO-ARCHIVE] ERROR: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Lancer en arrière-plan (utilise asyncio global)
                        asyncio.create_task(auto_archive_task())
                    
                else:
                    # Auto-archive désactivé (pas un warning - juste status)
                    pass
        
        except Exception as e:
            print(f"[JOURNAL-AUTO-ARCHIVE] ERROR Vérification auto-archivage: {e}")
        
        # Titrage contextualisé après au moins 2 échanges
        try:
            asyncio.create_task(_maybe_update_conv_title())
        except Exception:
            pass
        if _chat_inner is not None:
            with _chat_inner:
                # Vérifier si on a une réponse journal prédéfinie à injecter
                if _journal_preformed_response:
                    print(f"[JOURNAL-EXTENSION] INJECT Affichage réponse journal prédéfinie")
                    _message('assistant', _journal_preformed_response, None, message_index=len(_chat_history)-1)
                    _journal_preformed_response = None  # Nettoyer après usage
                elif not was_streaming:
                    # Mode classique: afficher le message (en streaming, déjà affiché)
                    _message('assistant', cleaned_reply, ['mémorisé'] if ai_memorized else None, message_index=len(_chat_history)-1)
                else:
                    # Mode streaming: vérifier si le contenu a été enrichi (image, etc.)
                    if cleaned_reply != reply and _streaming_widget_ref:
                        # Contenu enrichi (image ajoutée) - mettre à jour le widget
                        print(f"[STREAM] 🖼️ Mise à jour widget streaming avec contenu enrichi")
                        # 🧹 Retirer le spinner animé du DOM avant mise à jour
                        try:
                            _cleanup_client = _chat_inner.client if _chat_inner else None
                            if _cleanup_client:
                                _cleanup_client.run_javascript(_SPINNER_REMOVE_JS)
                        except Exception:
                            pass
                        try:
                            # Filtrer les images manquantes avant affichage
                            filtered_reply = _filter_missing_images(cleaned_reply)
                            
                            # 🎲 BATCH GRID: Vérifier si contenu HTML grille batch
                            # ui.markdown() échappe le HTML → utiliser ui.html() pour les grilles
                            if 'ogma-batch-grid' in filtered_reply:
                                print(f"[STREAM] 🎲 Grille batch détectée - affichage HTML direct")
                                
                                # Séparer le script (interdit dans ui.html) du reste
                                script_content = ''
                                html_for_display = filtered_reply
                                
                                script_start = filtered_reply.find('<script>')
                                if script_start != -1:
                                    script_end = filtered_reply.find('</script>', script_start)
                                    if script_end != -1:
                                        script_content = filtered_reply[script_start:script_end + len('</script>')]
                                        html_for_display = filtered_reply[:script_start] + filtered_reply[script_end + len('</script>'):]
                                
                                # Extraire le bloc HTML batch (grille + summary)
                                html_start = html_for_display.find('<div class="ogma-batch-grid"')
                                
                                if html_start != -1:
                                    # Trouver la fin du bloc batch (après le </small> du SUMMARY)
                                    # Ne pas prendre le premier </small> (labels #1, #2...) mais celui du résumé '🎲 Batch'
                                    batch_summary_pos = html_for_display.find('🎲 Batch', html_start)
                                    if batch_summary_pos != -1:
                                        small_end = html_for_display.find('</small>', batch_summary_pos)
                                    else:
                                        small_end = -1
                                    if small_end != -1:
                                        html_end = small_end + len('</small>')
                                    else:
                                        # Fallback: chercher le </div> de clôture de la grille
                                        depth = 0
                                        pos = html_start
                                        while pos < len(html_for_display):
                                            next_open = html_for_display.find('<div', pos + 1)
                                            next_close = html_for_display.find('</div>', pos + 1)
                                            
                                            if next_close == -1:
                                                break
                                            if next_open != -1 and next_open < next_close:
                                                depth += 1
                                                pos = next_open
                                            else:
                                                if depth == 0:
                                                    html_end = next_close + len('</div>')
                                                    break
                                                depth -= 1
                                                pos = next_close
                                        else:
                                            html_end = len(html_for_display)
                                    
                                    # Extraire les parties
                                    text_before = html_for_display[:html_start].strip()
                                    grid_html = html_for_display[html_start:html_end]
                                    text_after = html_for_display[html_end:].strip()
                                    
                                    # Afficher texte avant en markdown si présent
                                    if text_before:
                                        _streaming_widget_ref.set_content(text_before)
                                    else:
                                        _streaming_widget_ref.set_content('')  # Vider le widget streaming
                                    
                                    # Injecter le script via add_body_html (une seule fois)
                                    if script_content:
                                        ui.add_body_html(script_content)
                                    
                                    # Injecter la grille HTML via set_content() sur le placeholder pré-créé
                                    # FIABLE: modifier un élément existant (set_content) vs créer un nouveau
                                    # enfant dans un container déjà rendu (fragile en NiceGUI 2.x)
                                    if _streaming_html_ref:
                                        _streaming_html_ref.set_content(grid_html)
                                        # text_after (override prompt, etc.) affiché dans le widget markdown
                                        if text_after:
                                            combined = (text_before + "\n\n" + text_after).strip() if text_before else text_after
                                            _streaming_widget_ref.set_content(combined)
                                        print(f"[STREAM] ✅ Grille batch injectée via set_content() sur html_placeholder")
                                    else:
                                        # Fallback: ancien chemin si pas de placeholder (compatibilité)
                                        _inject_parent = _streaming_container_ref if _streaming_container_ref else _streaming_widget_ref.parent_slot.parent
                                        print(f"[STREAM-INJECT] Fallback - type={type(_inject_parent).__name__}")
                                        with _inject_parent:
                                            ui.html(grid_html)
                                            if text_after:
                                                ui.markdown(text_after)
                                        print(f"[STREAM] ✅ Grille batch injectée via fallback ui.html()")
                                    # Forcer flush NiceGUI vers le navigateur
                                    await asyncio.sleep(0)
                                else:
                                    # Pas de marqueur trouvé - fallback markdown
                                    _streaming_widget_ref.set_content(filtered_reply)
                            else:
                                _streaming_widget_ref.set_content(filtered_reply)
                        except Exception as e:
                            print(f"[STREAM] ⚠️ Erreur mise à jour enrichie: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[STREAM] ✅ Message déjà affiché en streaming - skip _message()")
                    
                    # 👁️ PERCEPTION: Détection phrases magiques IA (mode streaming)
                    # En streaming, _message() n'est pas appelé donc on détecte ici
                    try:
                        from extensions.perception_ui import get_perception_ui
                        perception_ui = get_perception_ui()
                        
                        if perception_ui and cleaned_reply:
                            import re
                            # Patterns d'activation IA
                            activation_patterns = [
                                r"il\s+faut\s+que\s+je\s+(?:te\s+)?vois",
                                r"je\s+veux\s+te\s+voir",
                                r"il\s+faut\s+que\s+je\s+vois"
                            ]
                            
                            is_activation_trigger = any(re.search(pattern, cleaned_reply, re.IGNORECASE) for pattern in activation_patterns)
                            
                            print(f"[PERCEPTION-STREAM] 🔍 Détection: trigger={is_activation_trigger}, actif={perception_ui.is_enabled}")
                            
                            if is_activation_trigger and not perception_ui.is_enabled:
                                print("[PERCEPTION-STREAM] 👁️ Phrase magique IA détectée - démarrage webcam")
                                
                                async def trigger_perception_streaming():
                                    try:
                                        await asyncio.sleep(0.5)
                                        perception_ui.start_perception()
                                        _notify_safe('👁️ Perception activée par l\'IA - Webcam démarrée', 'positive')
                                        print("[PERCEPTION-STREAM] ✅ Webcam activée suite à phrase magique IA")
                                    except Exception as e:
                                        print(f"[PERCEPTION-STREAM] ❌ Erreur: {e}")
                                
                                asyncio.create_task(trigger_perception_streaming())
                    except Exception as e:
                        print(f"[PERCEPTION-STREAM] ⚠️ Erreur détection: {e}")
                
                # Lecture automatique si activée (seulement si pas déjà lu en streaming)
                sm = _ensure_settings_manager()
                auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
                tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
                tts_streaming_enabled = sm.settings.get('tts', {}).get('streaming', True)
                
                # Skip TTS classique si on a déjà lu en streaming
                skip_classic_tts = was_streaming and tts_streaming_enabled
                
                if auto_speak and tts_enabled and _audio_manager and not skip_classic_tts:
                    try:
                        # Utiliser threading au lieu d'asyncio pour éviter RuntimeError
                        import threading
                        # Nettoyer le contenu pour la synthèse
                        clean_content = cleaned_reply.replace('*', '').replace('**', '').replace('#', '').replace('`', '')
                        print(f"[TTS-AUTO] 🔊 Lecture automatique: {clean_content[:50]}...")
                        
                        def audio_task():
                            # Notifier le module voice que le TTS démarre
                            try:
                                if VOICE_MODULE_AVAILABLE and _voice_manager and _voice_manager.is_active:
                                    _voice_manager.notify_tts_started()
                            except:
                                pass
                            
                            _audio_manager.speak(clean_content)
                            
                            # Notifier le module voice que le TTS a fini
                            try:
                                if VOICE_MODULE_AVAILABLE and _voice_manager and _voice_manager.is_active:
                                    _voice_manager.notify_tts_finished()
                            except:
                                pass
                        
                        threading.Thread(target=audio_task, daemon=True).start()
                        print("[TTS-AUTO] ✅ Lecture automatique démarrée")
                    except Exception as e:
                        print(f"[TTS-AUTO] ❌ Erreur lecture automatique: {e}")
                elif skip_classic_tts:
                    print("[TTS-AUTO] ⏭️ Skip TTS classique - déjà lu en streaming")
                elif not auto_speak:
                    # Pas une erreur - juste désactivé par l'utilisateur
                    pass  # Mode silencieux par choix
                elif not tts_enabled:
                    print(f"[TTS-AUTO] ⚪ TTS désactivé dans les paramètres")
                elif not _audio_manager:
                    print(f"[TTS-AUTO] ⚪ Audio manager non disponible")
                
                try:
                        ui.run_javascript(r'''
setTimeout(()=>{
    const el = document.querySelector('[data-role="chat-scroll"]');
    const atBottom = (e)=> e && (e.scrollHeight - e.scrollTop - e.clientHeight <= 24);
    if(el){
        const shouldAuto = (window.OGMA_autoScroll === undefined) ? atBottom(el) : !!window.OGMA_autoScroll;
        if(shouldAuto){ el.scrollTop = el.scrollHeight; }
        const btn = document.getElementById('scrollBottomBtn');
        if(btn){ btn.style.display = atBottom(el) ? 'none' : 'flex'; }
    }
}, 0);
''')
                except Exception:
                    pass
    
    # Status queue processing is handled by the main timer in run_ogma()


# === FONCTIONS AUDIO ===

_is_recording = False
_pending_notifications = []  # Queue pour les notifications en arrière-plan

async def _start_audio_recording(input_field, mic_button):
    """Démarre/arrête l'enregistrement audio manuellement."""
    global _is_recording, _pending_notifications, _audio_manager
    
    if _is_recording:
        # ARRÊT de l'enregistrement
        _is_recording = False
        mic_button.props('icon=mic color=primary loading=true')
        mic_button.props('title="UPDATE Traitement en cours..."')
        _pending_notifications.append(("🔴 Enregistrement arrêté - Transcription...", 'info'))
        
        # Arrêter l'enregistrement manuel dans AudioManager
        if _audio_manager:
            _audio_manager.stop_manual_recording()
        
        return
    
    # DÉMARRAGE de l'enregistrement
    try:
        _is_recording = True
        mic_button.props('icon=stop color=red loading=false')
        mic_button.props('title="🔴 ENREGISTREMENT EN COURS - Cliquez pour ARRÊTER"')
        _pending_notifications.append(("🔴 Enregistrement démarré - Parlez maintenant, cliquez pour arrêter", 'info'))
        
        audio_mgr = _ensure_audio_manager()
        if not await audio_mgr.initialize():
            _pending_notifications.append(("ERROR Erreur initialisation audio", 'negative'))
            _is_recording = False
            mic_button.props('icon=mic color=primary loading=false')
            return
        
        # Démarrer enregistrement manuel (sans timeout)
        text = await audio_mgr.record_manual_control()
        
        if text and text.strip():
            # Ajouter le texte transcrit dans le champ de saisie
            current_text = input_field.value or ""
            new_text = current_text + (" " if current_text else "") + text.strip()
            input_field.value = new_text
            
            # Notification de succès
            _pending_notifications.append((f"OK Transcrit: {text[:50]}...", 'positive'))
        else:
            _pending_notifications.append(("WARN Aucun texte transcrit", 'warning'))
            
    except Exception as e:
        print(f"[AUDIO] Erreur enregistrement: {e}")
        _pending_notifications.append((f"ERROR Erreur audio: {str(e)[:100]}", 'negative'))
    finally:
        _is_recording = False
        mic_button.props('icon=mic color=primary loading=false')
        mic_button.props('title="🎙️ Cliquez pour enregistrer un message vocal"')
        _pending_notifications.append(("🔴 Enregistrement terminé", 'info'))


# ============================================================================
# MODULE VOICE CONVERSATION - Fonctions Helper (Janvier 2026)
# ============================================================================

# Queues thread-safe pour les mises à jour vocales (pattern identique à _pending_notifications)
_pending_voice_transcription = []
_pending_voice_indicator_state = []
_pending_voice_status = []
_pending_voice_messages = []  # Messages à envoyer via point final


def _queue_voice_message(text: str):
    """Queue un message vocal à envoyer (appelé depuis le thread d'écoute)"""
    global _pending_voice_messages
    _pending_voice_messages.append(text)
    print(f"[VOICE] 📥 Message queue: '{text[:50]}...'")


def _update_voice_transcription(fragment: str):
    """
    Queue la mise à jour du champ avec un nouveau fragment vocal.
    Le fragment sera ajouté au texte actuel du champ (source unique = frontend).
    """
    global _pending_voice_transcription
    _pending_voice_transcription.append(fragment)
    print(f"[VOICE] 📥 Fragment queue: '{fragment[:50]}...' ({len(_pending_voice_transcription)} en attente)")


def _update_voice_indicator(state):
    """Queue la mise à jour de l'indicateur visuel selon l'état"""
    global _pending_voice_indicator_state
    _pending_voice_indicator_state.append(state)
    print(f"[VOICE] 📥 Indicateur queue: {state}")


def _update_voice_status(text: str):
    """Queue la mise à jour du texte de statut de l'indicateur"""
    global _pending_voice_status
    _pending_voice_status.append(text)


def _process_voice_updates():
    """Traite les mises à jour vocales en attente depuis le contexte NiceGUI principal."""
    global _pending_voice_transcription, _pending_voice_indicator_state, _pending_voice_status
    global _input_field, _voice_indicator
    
    # Traiter transcription (ajouter tous les fragments au texte actuel)
    if _pending_voice_transcription:
        fragments = _pending_voice_transcription.copy()
        _pending_voice_transcription.clear()
        try:
            if _input_field:
                # Lire le texte actuel du frontend (source unique de vérité)
                current_text = _input_field.value or ""
                
                # Ajouter tous les fragments
                for fragment in fragments:
                    if fragment == "":  # Fragment vide = effacer le champ
                        current_text = ""
                    elif current_text:
                        current_text += " " + fragment
                    else:
                        current_text = fragment
                
                # Écrire le résultat
                _input_field.value = current_text
                _input_field.update()
                print(f"[VOICE] ✅ Champ mis à jour: '{current_text[:30]}...' ({len(current_text)} chars)")
        except Exception as e:
            print(f"[VOICE] ⚠️ Erreur mise à jour champ: {e}")
    
    # Traiter indicateur (dernier état)
    if _pending_voice_indicator_state:
        state = _pending_voice_indicator_state[-1]
        _pending_voice_indicator_state.clear()
        try:
            if VOICE_MODULE_AVAILABLE and _voice_indicator:
                _voice_indicator.update_state(state)
        except Exception as e:
            print(f"[VOICE] ⚠️ Erreur mise à jour indicateur: {e}")
    
    # Traiter statut (dernier texte)
    if _pending_voice_status:
        text = _pending_voice_status[-1]
        _pending_voice_status.clear()
        try:
            if VOICE_MODULE_AVAILABLE and _voice_indicator:
                _voice_indicator.update_status_text(text)
        except Exception as e:
            print(f"[VOICE] ⚠️ Erreur mise à jour status: {e}")
    
    # Traiter messages à envoyer (un à la fois)
    if _pending_voice_messages:
        message = _pending_voice_messages.pop(0)  # FIFO pour les messages
        try:
            print(f"[VOICE] 📤 Envoi message: '{message[:50]}...'")
            
            # Vider le champ de saisie AVANT l'envoi
            if _input_field:
                _input_field.value = ''
                try:
                    _input_field.update()
                except:
                    pass
                print("[VOICE] 🧹 Champ de saisie vidé")
            
            # Vider le cache du VoiceManager
            if VOICE_MODULE_AVAILABLE and _voice_manager:
                _voice_manager.clear_accumulated_text()
                print("[VOICE] 🧹 Cache vocal vidé")
            
            # Créer une tâche async pour envoyer le message
            asyncio.create_task(_send_chat_message(text_override=message))
        except Exception as e:
            print(f"[VOICE] ⚠️ Erreur envoi message: {e}")


def _on_input_focus():
    """Handler appelé au focus sur la zone de message - Active le mode vocal"""
    global _voice_manager
    try:
        sm = _ensure_settings_manager()
        voice_enabled = sm.settings.get('voice', {}).get('enabled', False)
        
        if VOICE_MODULE_AVAILABLE and voice_enabled and _voice_manager:
            _voice_manager.activate()
            print("[VOICE] 🎙️ Zone de message active - Mode vocal activé")
    except Exception as e:
        print(f"[VOICE] ⚠️ Erreur activation focus: {e}")


def _on_input_blur():
    """Handler appelé au blur de la zone de message - Désactive le mode vocal"""
    global _voice_manager
    try:
        if VOICE_MODULE_AVAILABLE and _voice_manager:
            _voice_manager.deactivate()
            print("[VOICE] ⏹️ Zone de message inactive - Mode vocal désactivé")
    except Exception as e:
        print(f"[VOICE] ⚠️ Erreur désactivation blur: {e}")


# ============================================================================
# REPRÉSENTATION VISUELLE USER/IA - Fonctions helper
# ============================================================================

def _get_representation_image_path(is_user: bool, compressed: bool = False) -> Optional[Path]:
    """
    Récupère le chemin de l'image de représentation (User ou IA).
    Cherche n'importe quelle image dans le dossier correspondant.
    
    Args:
        is_user: True pour User, False pour IA
        compressed: Si True, cherche version _compressed.jpg
    """
    target_dir = REPR_USER_DIR if is_user else REPR_IA_DIR
    
    if not target_dir.exists():
        return None
    
    # Si version compressée demandée, chercher _compressed.jpg
    if compressed:
        for ext in ['*.jpg', '*.jpeg']:
            compressed_images = list(target_dir.glob(f'*_compressed{ext[1:]}'))
            if compressed_images:
                return compressed_images[0]
        return None
    
    # Chercher une image originale (exclure _compressed)
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
        images = [img for img in target_dir.glob(ext) if '_compressed' not in img.stem]
        if images:
            return images[0]  # Retourne la première trouvée
    
    return None


def _load_representation_as_dict(image_path: Path, source: str, for_chat: bool = False) -> Optional[Dict]:
    """
    Charge une image de représentation en dict compatible avec _active_images.
    
    Args:
        image_path: Chemin de l'image
        source: 'user_representation' ou 'ia_representation'
        for_chat: Si True, charge version compressée 400x400 (sinon HD pour img2img)
    """
    if not image_path or not image_path.exists():
        return None
    
    try:
        import base64
        
        # Pour le chat, on veut la version compressée
        actual_path = image_path
        if for_chat:
            is_user = 'user' in source
            compressed_path = _get_representation_image_path(is_user=is_user, compressed=True)
            if compressed_path and compressed_path.exists():
                actual_path = compressed_path
                print(f"[REPR] Utilisation version compressée: {compressed_path.name}")
            else:
                print(f"[REPR] ⚠️ Version compressée introuvable, utilisation originale")
        
        with open(actual_path, 'rb') as f:
            b64_data = base64.b64encode(f.read()).decode('utf-8')
        
        return {
            'type': 'image',
            'name': actual_path.name,
            'data': b64_data,
            'source': source  # 'user_representation' ou 'ia_representation'
        }
    except Exception as e:
        print(f"[REPR] Erreur chargement {actual_path if 'actual_path' in locals() else image_path}: {e}")
        return None


def _get_active_representations(for_chat: bool = False) -> List[Dict]:
    """
    Récupère les images de représentation selon l'état des boutons.
    Ordre: User d'abord (Image 1), puis IA (Image 2).
    
    Args:
        for_chat: Si True, charge versions compressées 400x400 (sinon HD pour img2img)
    """
    global _user_representation_active, _ia_representation_active
    
    print(f"[REPR-DEBUG] État boutons - User: {_user_representation_active}, IA: {_ia_representation_active}, for_chat: {for_chat}")
    
    images = []
    
    if _user_representation_active:
        user_path = _get_representation_image_path(is_user=True, compressed=False)  # Toujours charger l'original d'abord
        print(f"[REPR-DEBUG] User path trouvé: {user_path}")
        if user_path:
            user_img = _load_representation_as_dict(user_path, 'user_representation', for_chat=for_chat)
            if user_img:
                images.append(user_img)
                print(f"[REPR] ✅ User image chargée: {user_img['name']} ({'compressée' if for_chat else 'HD'})")
            else:
                print(f"[REPR] ❌ Échec chargement User image")
        else:
            print(f"[REPR] ⚠️ Aucune image User trouvée dans {REPR_USER_DIR}")
    
    if _ia_representation_active:
        ia_path = _get_representation_image_path(is_user=False, compressed=False)  # Toujours charger l'original d'abord
        print(f"[REPR-DEBUG] IA path trouvé: {ia_path}")
        if ia_path:
            ia_img = _load_representation_as_dict(ia_path, 'ia_representation', for_chat=for_chat)
            if ia_img:
                images.append(ia_img)
                print(f"[REPR] ✅ IA image chargée: {ia_img['name']} ({'compressée' if for_chat else 'HD'})")
            else:
                print(f"[REPR] ❌ Échec chargement IA image")
        else:
            print(f"[REPR] ⚠️ Aucune image IA trouvée dans {REPR_IA_DIR}")
    
    print(f"[REPR-DEBUG] Total images collectées: {len(images)}")
    return images


def _build_representation_context() -> str:
    """
    Construit le contexte textuel pour le prompt I2I selon les représentations actives.
    Format: "Image 1 = {nom} (the user/AI assistant)"
    """
    global _user_representation_active, _ia_representation_active, _current_user_name
    
    parts = []
    image_num = 1
    
    # Récupérer les noms depuis identity_manager ou settings
    user_name = _current_user_name or "User"
    
    # Récupérer le nom de l'IA depuis identity_manager
    ia_name = "Assistant"
    try:
        from identity_manager import IdentityManager
        identity_mgr = IdentityManager()
        current_profile = identity_mgr.get_current_profile()
        ia_name = current_profile.get('ai_name', 'Assistant')
    except Exception:
        pass
    
    if _user_representation_active:
        user_path = _get_representation_image_path(is_user=True)
        if user_path:
            parts.append(f"Image {image_num} = {user_name} (the user, use their face and appearance)")
            image_num += 1
    
    if _ia_representation_active:
        ia_path = _get_representation_image_path(is_user=False)
        if ia_path:
            parts.append(f"Image {image_num} = {ia_name} (the AI assistant, use her appearance)")
    
    return "\n".join(parts)


def _has_active_representations() -> bool:
    """Vérifie si au moins une représentation est active."""
    global _user_representation_active, _ia_representation_active
    return _user_representation_active or _ia_representation_active


def _create_compressed_avatar_if_needed(is_user: bool) -> bool:
    """
    Crée une version compressée 400x400 de l'avatar si elle n'existe pas déjà.
    
    Args:
        is_user: True pour User, False pour IA
    
    Returns:
        True si compression réussie ou déjà existante, False en cas d'erreur
    """
    import base64
    from io import BytesIO
    
    # Vérifier si version compressée existe déjà
    compressed_path = _get_representation_image_path(is_user=is_user, compressed=True)
    if compressed_path and compressed_path.exists():
        print(f"[REPR-COMPRESS] ✅ Version compressée existe déjà: {compressed_path.name}")
        return True
    
    # Récupérer l'avatar original
    original_path = _get_representation_image_path(is_user=is_user, compressed=False)
    if not original_path or not original_path.exists():
        print(f"[REPR-COMPRESS] ⚠️ Aucun avatar original trouvé")
        return False
    
    try:
        # Vérifier que PIL est disponible
        try:
            from PIL import Image
        except ImportError:
            print("[REPR-COMPRESS] ❌ PIL/Pillow non installé")
            return False
        
        # Charger l'image originale
        with open(original_path, 'rb') as f:
            img_bytes = f.read()
        
        image = Image.open(BytesIO(img_bytes))
        original_size = f"{image.width}x{image.height}"
        
        # Récupérer la taille de compression configurée
        max_size = _get_vision_compression_size()
        if max_size == 0:
            max_size = 400  # Fallback
        
        # Calculer nouvelles dimensions
        ratio = min(max_size / image.width, max_size / image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        print(f"[REPR-COMPRESS] 🔧 {original_size} → {new_width}x{new_height} (max {max_size}px)")
        
        # Redimensionner
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Récupérer la qualité JPEG configurée
        sm_quality = _ensure_settings_manager()
        jpeg_quality = 85  # Défaut
        if sm_quality:
            img_config_quality = sm_quality.settings.get('image_generation', {})
            jpeg_quality = img_config_quality.get('vision_jpeg_quality', 85)
        
        # Convertir en JPEG avec qualité configurée
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Sauvegarder version compressée
        output_path = original_path.parent / f"{original_path.stem}_compressed.jpg"
        image.save(output_path, format='JPEG', quality=jpeg_quality, optimize=True)
        
        # Stats
        original_size_kb = len(img_bytes) / 1024
        compressed_size_kb = output_path.stat().st_size / 1024
        reduction_pct = (1 - compressed_size_kb / original_size_kb) * 100
        
        print(f"[REPR-COMPRESS] ✅ Sauvegardé: {output_path.name} ({compressed_size_kb:.0f}KB, -{reduction_pct:.0f}%)")
        return True
        
    except Exception as e:
        import traceback
        print(f"[REPR-COMPRESS] ❌ ERREUR: {e}")
        traceback.print_exc()
        return False


def _toggle_user_representation():
    """Toggle l'état du bouton User representation."""
    global _user_representation_active, _user_repr_button_ref
    
    # Vérifier si l'image existe
    user_path = _get_representation_image_path(is_user=True, compressed=False)
    
    if not user_path and not _user_representation_active:
        # Pas d'image et on veut activer → ouvrir dialog upload
        _show_representation_upload_dialog(is_user=True)
        return
    
    # Toggle l'état
    _user_representation_active = not _user_representation_active
    
    # Si activation, créer version compressée si nécessaire
    if _user_representation_active:
        _create_compressed_avatar_if_needed(is_user=True)
    
    # Mettre à jour le style du bouton
    if _user_repr_button_ref:
        if _user_representation_active:
            _user_repr_button_ref.classes(add='active pressed')
            _notify_safe("👤 Représentation User activée", 'info')
        else:
            _user_repr_button_ref.classes(remove='active pressed')
            _notify_safe("👤 Représentation User désactivée", 'info')
    
    print(f"[REPR] User representation: {'ON' if _user_representation_active else 'OFF'}")


def _toggle_ia_representation():
    """Toggle l'état du bouton IA representation."""
    global _ia_representation_active, _ia_repr_button_ref
    
    # Vérifier si l'image existe
    ia_path = _get_representation_image_path(is_user=False, compressed=False)
    
    if not ia_path and not _ia_representation_active:
        # Pas d'image et on veut activer → ouvrir dialog upload
        _show_representation_upload_dialog(is_user=False)
        return
    
    # Toggle l'état
    _ia_representation_active = not _ia_representation_active
    
    # Si activation, créer version compressée si nécessaire
    if _ia_representation_active:
        _create_compressed_avatar_if_needed(is_user=False)
    
    # Mettre à jour le style du bouton
    if _ia_repr_button_ref:
        if _ia_representation_active:
            _ia_repr_button_ref.classes(add='active pressed')
            _notify_safe("🤖 Représentation IA activée", 'info')
        else:
            _ia_repr_button_ref.classes(remove='active pressed')
            _notify_safe("🤖 Représentation IA désactivée", 'info')
    
    print(f"[REPR] IA representation: {'ON' if _ia_representation_active else 'OFF'}")


def _show_representation_upload_dialog(is_user: bool):
    """Affiche la popup d'upload pour créer une image de représentation."""
    target_dir = REPR_USER_DIR if is_user else REPR_IA_DIR
    title = "👤 Photo Utilisateur" if is_user else "🤖 Photo IA"
    
    def _handle_repr_upload(upload_event, dialog):
        """Gère l'upload et sauvegarde dans le bon dossier."""
        try:
            # Créer le dossier si nécessaire
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Supprimer les anciennes images
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
                for old_file in target_dir.glob(ext):
                    old_file.unlink()
            
            # Sauvegarder la nouvelle image avec le nom original
            file_path = target_dir / upload_event.name
            with open(file_path, 'wb') as f:
                f.write(upload_event.content.read())
            
            print(f"[REPR] Image sauvegardée: {file_path}")
            _notify_safe(f"✅ {'Photo User' if is_user else 'Photo IA'} enregistrée!", 'positive')
            
            dialog.close()
            
            # Activer automatiquement le bouton après upload
            if is_user:
                _toggle_user_representation()
            else:
                _toggle_ia_representation()
                
        except Exception as e:
            print(f"[REPR] Erreur upload: {e}")
            _notify_safe(f"❌ Erreur: {e}", 'negative')
    
    with ui.dialog().classes('popup-overlay') as dialog:
        with ui.card().classes('popup-content'):
            ui.html(f'<div class="popup-title">{title}</div>')
            
            ui.label('Cette image sera utilisée pour vous représenter dans les générations.').classes('text-sm text-gray-400 mb-2')
            ui.label(f'Dossier: {target_dir}').classes('text-xs text-gray-500 mb-4')
            
            with ui.element().style('border: 2px dashed #4a4a4a; border-radius: 8px; padding: 40px; text-align: center; margin: 20px 0;'):
                ui.label('Glissez une image ou cliquez pour sélectionner').classes('text-gray-400')
                ui.upload(
                    on_upload=lambda e: _handle_repr_upload(e, dialog),
                    multiple=False,
                    max_file_size=10*1024*1024
                ).classes('mt-4')
            
            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Annuler', on_click=dialog.close).classes('action-button')
    
    dialog.open()


def _input_overlay():
    global _input_field, _user_repr_button_ref, _ia_repr_button_ref, _stop_button_ref
    
    with ui.element('div').classes('input-overlay'):
        # ===== NOUVEAU LAYOUT GRID 3x2 =====
        with ui.element('div').classes('input-grid-container'):
            
            # === COLONNE GAUCHE (2 rangées) ===
            with ui.element('div').classes('input-left-col'):
                # Rangée 1: Boutons User/IA
                with ui.element('div').classes('input-left-top'):
                    # Bouton User representation (person icon)
                    _user_repr_button_ref = ui.button(
                        icon='person',
                        on_click=_toggle_user_representation
                    ).classes('action-button repr-toggle').props('title="Représentation Utilisateur pour I2I"')
                    
                    # Bouton IA representation (psychology icon - cerveau)
                    _ia_repr_button_ref = ui.button(
                        icon='psychology',
                        on_click=_toggle_ia_representation
                    ).classes('action-button repr-toggle').props('title="Représentation IA pour I2I"')
                
                # Rangée 2: Bouton pièce jointe
                with ui.element('div').classes('input-left-bottom'):
                    ui.button(icon='attach_file', on_click=_show_file_upload_dialog).classes('action-button').props('title="Joindre un fichier"')
            
            # === COLONNE CENTRE (Textarea, span 2 rangées) ===
            with ui.element('div').classes('input-center-col'):
                _input_field = ui.textarea(placeholder='Écrire un message...').props('autogrow').classes('input-field')
                input_field = _input_field  # Alias local pour compatibilité
                
                # 🚀 PREANALYSIS: Déclencher pré-analyses au focus (optimisation latence)
                if PREANALYSIS_AVAILABLE:
                    _input_field.on('focus', trigger_preanalysis_on_typing)
                
                # 🎙️ MODULE VOICE: Activer/désactiver le mode vocal au focus/blur
                if VOICE_MODULE_AVAILABLE:
                    _input_field.on('focus', lambda e: _on_input_focus())
                    _input_field.on('blur', lambda e: _on_input_blur())
                
                # Envoi avec Entrée (Shift+Entrée pour nouvelle ligne)
                def _keydown(e):
                    if e.args.get('key') == 'Enter' and not e.args.get('shiftKey'):
                        asyncio.create_task(_send_chat_message(input_field))
                
                input_field.on('keydown.enter', _keydown)
                input_field.props('onkeydown="if (event.key === \'Enter\' && !event.shiftKey) event.preventDefault();"')
            
            # === COLONNE DROITE (2 rangées) ===
            with ui.element('div').classes('input-right-col'):
                # Rangée 1: Bouton Envoyer
                with ui.element('div').classes('input-right-top'):
                    ui.button('Envoyer', icon='send', on_click=lambda: asyncio.create_task(_send_chat_message(input_field))).classes('send-button')
                
                # Rangée 2: Mémo, Micro, Stop
                with ui.element('div').classes('input-right-bottom'):
                    ui.button(icon='auto_awesome', on_click=lambda: asyncio.create_task(_manual_memorize_current_input(input_field))).classes('action-button').props('title="Mémorisation manuelle"')
                    
                    mic_button = ui.button(
                        icon='mic', 
                        on_click=lambda: asyncio.create_task(_start_audio_recording(input_field, mic_button))
                    ).classes('action-button mic-button').props('title="Enregistrer un message vocal"')
                    
                    _stop_button_ref = ui.button(icon='stop', on_click=lambda: asyncio.create_task(_request_stop())).classes('action-button stop-button').props('title="Arrêter l\'opération en cours"')
        
        # Conteneur pour l'onglet fichier, positionné sous la boîte de messagerie
        global _file_tab_container
        _file_tab_container = ui.element('div').classes('file-tab-overlay')
        
        # Initialiser l'affichage de l'onglet fichier s'il y en a un
        _update_file_tab_display()


def _process_pending_notifications():
    """Traite les notifications en attente depuis le contexte principal."""
    global _pending_notifications
    if _pending_notifications:
        message, notification_type = _pending_notifications.pop(0)
        ui.notify(message, type=notification_type)


# ============================================================================
# PERCEPTION PAGE - Importée depuis ogma_perception.py (REFACTORING)
# ============================================================================
from ogma_perception import perception_page as _perception_page_impl

@ui.page('/perception')
def perception_page():
    """Page Perception - Déléguée au module ogma_perception.py"""
    _perception_page_impl()


async def _async_awakening(notif):
    """
    Éveil asynchrone d'OGMA : Initialise les composants lourds en tâche de fond.
    Permet à l'utilisateur d'avoir l'interface immédiatement.
    
    Args:
        notif: Référence à la notification NiceGUI créée dans main_page()
    """
    from datetime import datetime
    print(f"[INIT] 🚀 Début de l'éveil asynchrone à {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Vague 1 : Fondations (Settings)
        notif.message = 'Chargement des paramètres... ⚙️'
        _ensure_settings_manager()
        await asyncio.sleep(0.1)
        
        # Vague 2 : Intelligence IA principale (Chat)
        notif.message = 'Éveil de l\'IA principale (Cerveau Conversationnel)...'
        _ensure_chat_controller()
        await asyncio.sleep(0.1)
        
        # Vague 3 : Intelligence Archiviste (Raisonnement)
        notif.message = 'Éveil de l\'Archiviste (Cerveau Analytique)...'
        _ensure_archiviste_controller()
        await asyncio.sleep(0.1)

        # Vague 4 : Mémoire FAISS/SQLite (Lourd)
        notif.message = 'Restauration de la mémoire émotionnelle... 🧬'
        _ensure_memory_manager()
        await asyncio.sleep(0.1)

        # Vague 5 : Système Audio & Vocal
        notif.message = 'Activation des sens (Audio & Voix)... 🎙️'
        _ensure_audio_manager()
        # Initialisation Voice Manager si activé
        sm = _ensure_settings_manager()
        voice_enabled = sm.settings.get('voice', {}).get('enabled', False)
        if VOICE_MODULE_AVAILABLE and voice_enabled:
            global _voice_manager
            _voice_manager = initialize_voice_manager(sm, _audio_manager)
            loop = asyncio.get_running_loop()
            _voice_manager.set_main_loop(loop)
            # Configurer les callbacks pour connecter VoiceManager avec l'UI
            _voice_manager.set_callbacks(
                on_state_change=_update_voice_indicator,
                on_transcription=_update_voice_transcription,
                on_message_ready=_queue_voice_message,
                on_status_text=_update_voice_status,
                get_current_text=lambda: _input_field.value if _input_field else ""
            )
            print("[VOICE] ✅ Callbacks UI configurés")
        await asyncio.sleep(0.1)

        # Vague 6 : Extensions (Journal, Biographie, Dream)
        notif.message = 'Initialisation des extensions cognitives... 🧩'
        
        # Journal de Bord
        try:
            _initialize_journal_extension()
            archi = _ensure_archiviste_controller()
            if archi:
                from extensions.journal_de_bord import update_archiviste, is_available
                if is_available():
                    update_archiviste(archi)
            
            # Auto-expiration des etats par TTL categorie (humeur 12h, technique 7j, etc.)
            try:
                from extensions.journal_de_bord.auto_resolution import auto_expire_by_category
                from extensions.journal_de_bord import _journal_instance
                _jm = _journal_instance.json_manager if _journal_instance else None
                if _jm:
                    _expire_result = auto_expire_by_category(_jm)
                    if _expire_result["expired_count"] > 0:
                        print(f"[INIT] Auto-expire: {_expire_result['expired_count']} etats expires au demarrage")
            except Exception as e:
                print(f"[INIT] Auto-expire etats: {e}")
        except Exception as e:
            print(f"[INIT] Journal: {e}")
        
        # Biographie Profil
        try:
            _initialize_biography_extension()
        except Exception as e:
            print(f"[INIT] ⚠️ Biography: {e}")
        
        # Dream Engine
        try:
            from extensions.dream_engine import is_available as dream_available, initialize_dream_engine
            from extensions.dream_engine.dream_ui import start_inactivity_timer, _inactivity_timer
            if dream_available():
                success = initialize_dream_engine(
                    chat_controller=_ensure_chat_controller(),
                    archiviste_controller=_ensure_archiviste_controller(),
                    memory_manager=_ensure_memory_manager(),
                    settings_manager=_ensure_settings_manager()
                )
                if success:
                    # Lire la config pour vérifier enabled + timeout
                    _sm = _ensure_settings_manager()
                    _dream_cfg = _sm.settings.get('dream_engine', {}) if _sm else {}
                    _dream_enabled = _dream_cfg.get('enabled', True)
                    _timeout_min = _dream_cfg.get('inactivity_timeout_minutes', 10)
                    # Ne pas démarrer si désactivé dans les settings
                    if not _dream_enabled:
                        print(f"[INIT] ⏸️ Dream Engine désactivé (settings) - timer non démarré")
                    # Ne pas redémarrer si le timer tourne déjà (double appel au démarrage)
                    elif _inactivity_timer is None or _inactivity_timer.done():
                        asyncio.create_task(start_inactivity_timer(timeout_minutes=_timeout_min))
                    else:
                        print(f"[INIT] ⏩ Dream Engine timer déjà actif - pas de redémarrage")
        except Exception as e:
            print(f"[INIT] ⚠️ Dream Engine: {e}")
        
        # Flux Cognitif - Transparence pensées IA
        try:
            from extensions.flux_cognitif import initialize_flux_cognitif
            flux = initialize_flux_cognitif()
            if flux:
                print("[INIT] ✅ Flux Cognitif initialisé")
        except Exception as e:
            print(f"[INIT] ⚠️ Flux Cognitif: {e}")
        
        # Telegram Connector
        try:
            from extensions.telegram_connector import (
                initialize_telegram_connector,
                is_telegram_available,
                is_telegram_configured,
                start_telegram_bot,
                get_config as get_telegram_config
            )
            from extensions.text2img import get_text2img_manager, is_available as text2img_available
            
            if is_telegram_available():
                # Récupérer le text2img_manager si disponible
                t2i_manager = get_text2img_manager() if text2img_available() else None
                # Récupérer le web_navigator si disponible
                web_nav = get_web_navigator_instance()
                
                success = initialize_telegram_connector(
                    chat_controller=_ensure_chat_controller(),
                    archiviste_controller=_ensure_archiviste_controller(),
                    memory_manager=_ensure_memory_manager(),
                    settings_manager=_ensure_settings_manager(),
                    audio_manager=_ensure_audio_manager() if hasattr(_ensure_audio_manager, '__call__') else None,
                    text2img_manager=t2i_manager,
                    web_navigator=web_nav
                )
                if success:
                    tg_config = get_telegram_config()
                    if tg_config.auto_start and tg_config.is_configured():
                        asyncio.create_task(start_telegram_bot())
                        print("[INIT] ✅ Telegram Connector démarré automatiquement")
                    else:
                        print("[INIT] ✅ Telegram Connector initialisé (démarrage manuel)")
        except (ImportError, Exception):
            print("[INIT] ⚠️ Telegram Connector: python-telegram-bot non installé")
        except Exception as e:
            print(f"[INIT] ⚠️ Telegram Connector: {e}")
        
        # Cognitive Mirror (initialisation légère)
        try:
            _ensure_cognitive_mirror()
            print("[INIT] ✅ Cognitive Mirror initialisé")
        except Exception as e:
            print(f"[INIT] ⚠️ Cognitive Mirror: {e}")
        
        # Capability Advisor (initialisation sans création UI - UI se fait au clic)
        try:
            if CAPABILITY_ADVISOR_AVAILABLE:
                _ensure_capability_advisor()  # Init seule, pas de get_ui_components()
                print("[INIT] ✅ Capability Advisor initialisé")
        except Exception as e:
            print(f"[INIT] ⚠️ Capability Advisor: {e}")
        
        # Extensions UI sync
        try:
            _sync_extensions_ui_globals()
            print("[INIT] ✅ Extensions UI synchronisées")
        except Exception as e:
            print(f"[INIT] ⚠️ Extensions UI: {e}")
        
        await asyncio.sleep(0.1)
        
        # Vague 7 : Synchronisation finale
        notif.message = 'Synchronisation finale du système... ✨'
        if OGMA_CORE_AVAILABLE:
            from modules.ogma_core.compat import sync_globals_to_core
            sync_globals_to_core(globals())

        # MISE À JOUR DU STATUS IA (Header) - Crucial pour éviter le F5
        from ogma_ui_conversations import _update_ia_status_indicators
        await _update_ia_status_indicators()
        
        # Réveil réussi
        notif.message = 'OGMA est pleinement opérationnel. Bienvenue ! 🌸'
        notif.spinner = False
        notif.type = 'positive'
        print(f"[INIT] ✅ Éveil terminé avec succès à {datetime.now().strftime('%H:%M:%S')}")
        await asyncio.sleep(4)
        notif.dismiss()

    except Exception as e:
        print(f"[INIT] ❌ Erreur critique durant l'éveil : {e}")
        import traceback
        traceback.print_exc()
        notif.message = f'⚠️ Erreur lors du réveil : {e}'
        notif.spinner = False
        notif.type = 'negative'
        await asyncio.sleep(10)
        notif.dismiss()


def _show_login_popup():
    """
    Popup de connexion obligatoire (non fermable).
    S'affiche au lancement si aucune session active détectée.
    """
    login_dialog = ui.dialog().props('persistent')  # Non fermable par ESC/clic extérieur
    
    with login_dialog, ui.card().classes('q-pa-lg login-card').style('min-width: 400px; max-width: 500px; background: #0e1828 !important; color: #cde4f5 !important; border: 1px solid #ffcc00 !important; border-radius: 16px !important; box-shadow: 0 0 6px rgba(255,204,0,0.65), 0 0 22px rgba(255,204,0,0.28), 0 0 50px rgba(255,204,0,0.10) !important;'):
        ui.label('Connexion OGMA').classes('text-h5 text-center mb-2').style('color: #00d4f5 !important; font-family: Orbitron, monospace; letter-spacing: 0.05em;')
        ui.label('Identifiez-vous pour continuer').classes('text-center mb-6').style('color: rgba(205, 228, 245, 0.65) !important;')
        
        # Pré-remplir avec identity_manager (prioritaire) ou settings.json (fallback)
        sm = _ensure_settings_manager()
        default_name = ''
        try:
            from identity_manager import get_identity_manager
            identity_mgr = get_identity_manager()
            current_identity = identity_mgr.get_current_identity()
            default_name = current_identity.get('user_name', '')
            print(f"[SESSION] 📋 Prénom depuis identity_manager: {default_name}")
        except Exception as e:
            print(f"[SESSION] ⚠️ identity_manager non disponible: {e}")
            # Fallback sur settings.json
            if sm:
                default_name = sm.settings.get('profile', {}).get('user_name', '')
                print(f"[SESSION] 📋 Prénom depuis settings.json: {default_name}")
        
        name_input = ui.input('Votre prénom').classes('w-full').props('outlined autofocus')
        name_input.value = default_name
        
        error_label = ui.label('').classes('text-red text-center text-sm').style('min-height: 20px;')
        
        def validate_login():
            """Valide et enregistre la connexion"""
            name = name_input.value.strip()
            
            # Validation basique
            if not name:
                error_label.text = 'Le prénom est requis'
                return
            
            if len(name) < 2:
                error_label.text = 'Le prénom doit contenir au moins 2 caractères'
                return
            
            if len(name) > 30:
                error_label.text = 'Le prénom est trop long (maximum 30 caractères)'
                return
            
            # Effacer erreur
            error_label.text = ''
            
            # 1. Sauvegarder cookie session
            app.storage.user['ogma_user'] = {
                'name': name,
                'login_time': datetime.now().isoformat()
            }
            
            # 2. Sauvegarder identity_manager (système principal de profils)
            try:
                from identity_manager import get_identity_manager
                identity_mgr = get_identity_manager()
                current_profile_id = identity_mgr.get_current_profile_id()
                if current_profile_id and current_profile_id in identity_mgr._data['profiles']:
                    identity_mgr._data['profiles'][current_profile_id]['user_name'] = name
                    identity_mgr.save_identities()
                    print(f"[SESSION] ✅ identity_manager mis à jour: {name}")
                else:
                    print(f"[SESSION] ⚠️ Profil actif non trouvé dans identity_manager")
            except Exception as e:
                print(f"[SESSION] ⚠️ Erreur identity_manager: {e}")
            
            # 3. Sauvegarder settings.json (synchronisation)
            if sm:
                if 'profile' not in sm.settings:
                    sm.settings['profile'] = {}
                sm.settings['profile']['user_name'] = name
                sm.save_settings()
                print(f"[SESSION] ✅ settings.json mis à jour: {name}")
            
            # 4. Variables globales session
            global _current_user_name, _user_authenticated
            _current_user_name = name
            _user_authenticated = True
            
            print(f"[SESSION] ✅ Login réussi: {name}")
            
            # 5. Rafraîchir l'UI du modal Profile (si déjà ouvert)
            try:
                # Forcer rafraîchissement du modal profil pour afficher le nouveau nom
                import sys
                ogma_profile = sys.modules.get('ogma_profile')
                if ogma_profile and hasattr(ogma_profile, '_profile_modal_instance'):
                    # Le modal sera rafraîchi automatiquement à sa prochaine ouverture
                    print(f"[SESSION] 🔄 UI Profil marquée pour rafraîchissement")
            except Exception as e:
                print(f"[SESSION] ⚠️ Erreur rafraîchissement UI: {e}")
            
            # 6. Fermeture popup
            login_dialog.close()
            
            # 7. Notification bienvenue
            ui.notify(f'Bienvenue {name} ! 🎉', type='positive', position='top')
            
            # 8. Recharger la page pour appliquer changements UI (header, etc.)
            ui.run_javascript('window.location.reload()')
        
        # Permettre validation avec Entrée
        name_input.on('keydown.enter', validate_login)
        
        ui.button('Se connecter', on_click=validate_login).classes('w-full mt-4').props('color=primary size=lg')
    
    login_dialog.open()


def main_page():
    from datetime import datetime
    import time
    _page_start_time = time.time()
    # (debug rechargement désactivé)
    
    # === VÉRIFICATION SESSION UTILISATEUR (POPUP LOGIN) ===
    stored_user = app.storage.user.get('ogma_user')
    
    global _current_user_name, _user_authenticated
    
    if stored_user and stored_user.get('name'):
        # Auto-login silencieux
        _current_user_name = stored_user['name']
        _user_authenticated = True
        print(f"[SESSION] ✅ Auto-login: {_current_user_name}")
        ui.notify(f"Session restaurée - Bienvenue {_current_user_name} 👋", 
                  type='info', position='top', timeout=2000)
    else:
        # Pas de session → Popup obligatoire
        print("[SESSION] ⚪ Aucune session détectée - Popup login requis")
        _show_login_popup()
    # === FIN VÉRIFICATION SESSION ===
    
    # 1. CONSTRUCTION DE L'INTERFACE IMMÉDIATE (Squelette)
    
    # Styles et mode sombre (après le print pour mesurer le timing)
    _link_styles()
    ui.dark_mode()

    global _conv_area, _chat_inner
    
    # Header
    try:
        _header()
    except Exception as e:
        print(f"[DEBUG-MAIN] ERREUR _header(): {e}")

    # Créer une notification élégante custom avec spinner moderne
    with ui.element('div').classes('ogma-loading-overlay').style('''
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
        border-radius: 16px;
        padding: 20px 28px;
        box-shadow: 0 12px 48px rgba(102, 126, 234, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(12px);
        display: flex;
        align-items: center;
        gap: 16px;
        min-width: 320px;
        animation: slideInUp 0.4s ease-out;
    ''') as awakening_container:
        # Spinner élégant (gears, dots, infinity, orbit, etc.)
        awakening_spinner = ui.spinner('dots', size='lg', color='white')
        # Message
        with ui.element('div').style('flex: 1;'):
            awakening_message = ui.label('Réveil d\'OGMA...').style('''
                color: white;
                font-size: 15px;
                font-weight: 500;
                letter-spacing: 0.3px;
                margin: 0;
            ''')
    
    # Animation CSS
    ui.add_head_html('''
    <style>
    @keyframes slideInUp {
        from { transform: translateY(100px); opacity: 0; }
        to   { transform: translateY(0); opacity: 1; }
    }
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to   { opacity: 0; transform: translateY(20px); }
    }
    .ogma-loading-overlay.success {
        background: linear-gradient(135deg, rgba(17,153,142,0.95) 0%, rgba(56,239,125,0.95) 100%) !important;
        box-shadow: 0 12px 48px rgba(56,239,125,0.5) !important;
    }
    .ogma-loading-overlay.error {
        background: linear-gradient(135deg, rgba(235,51,73,0.95) 0%, rgba(244,92,67,0.95) 100%) !important;
        box-shadow: 0 12px 48px rgba(235,51,73,0.5) !important;
    }

    /* ════════════════ CYBER SCAN OVERLAY ════════════════ */
    /* Ligne laser horizontale qui balaie l'écran toutes les 10s */
    @keyframes global-scan {
        0%   { top: -2px; opacity: 0; }
        3%   { opacity: 0.7; }
        97%  { opacity: 0.3; }
        100% { top: 100vh; opacity: 0; }
    }
    /* Scintillement des coins (vignette dynamique) */
    @keyframes corner-pulse {
        0%, 100% { opacity: 0.4; }
        50%       { opacity: 0.2; }
    }
    #cyber-scan-overlay {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 9990;
        overflow: hidden;
    }
    #cyber-scan-line {
        position: absolute;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(0,212,245,0.5) 20%,
            rgba(0,212,245,0.8) 50%,
            rgba(0,212,245,0.5) 80%,
            transparent 100%
        );
        filter: blur(0.5px);
        box-shadow: 0 0 8px rgba(0,212,245,0.4);
        /* animation désactivée */
        opacity: 0;
        display: none;
    }
    /* Coins cyber */
    .cyber-corner {
        position: fixed;
        width: 40px;
        height: 40px;
        pointer-events: none;
        z-index: 9991;
        animation: corner-pulse 4s ease-in-out infinite;
    }
    .cyber-corner.tl { top:6px; left:6px; border-top:2px solid rgba(0,212,245,0.4); border-left:2px solid rgba(0,212,245,0.4); }
    .cyber-corner.tr { top:6px; right:6px; border-top:2px solid rgba(0,212,245,0.4); border-right:2px solid rgba(0,212,245,0.4); animation-delay:1s; }
    .cyber-corner.bl { bottom:6px; left:6px; border-bottom:2px solid rgba(0,212,245,0.4); border-left:2px solid rgba(0,212,245,0.4); animation-delay:2s; }
    .cyber-corner.br { bottom:6px; right:6px; border-bottom:2px solid rgba(0,212,245,0.4); border-right:2px solid rgba(0,212,245,0.4); animation-delay:3s; }
    </style>
    <div id="cyber-scan-overlay"><div id="cyber-scan-line"></div></div>
    <div class="cyber-corner tl"></div>
    <div class="cyber-corner tr"></div>
    <div class="cyber-corner bl"></div>
    <div class="cyber-corner br"></div>
    ''')
    
    # Créer un objet compatible avec l'API notification
    class CustomNotification:
        def __init__(self, container, message_label, spinner_element):
            self.container = container
            self.message_label = message_label
            self._spinner = spinner_element
            self._message = ''
            self._type = 'info'
        
        @property
        def message(self):
            return self._message
        
        @message.setter
        def message(self, value):
            self._message = value
            self.message_label.set_text(value)
        
        @property
        def type(self):
            return self._type
        
        @type.setter
        def type(self, value):
            self._type = value
            if value == 'positive':
                self.container.classes(add='success')
            elif value == 'negative':
                self.container.classes(add='error')
        
        @property
        def spinner(self):
            return self._spinner.visible
        
        @spinner.setter
        def spinner(self, visible):
            self._spinner.set_visibility(visible)
        
        def dismiss(self):
            # Animation de sortie avec JavaScript (pas de timer car contexte async)
            self.container.run_method('style.animation', 'fadeOut 0.3s ease-out')
            # Supprimer après 300ms
            import asyncio
            async def delayed_delete():
                await asyncio.sleep(0.3)
                try:
                    self.container.delete()
                except Exception:
                    pass  # Ignoré si déjà supprimé
            asyncio.create_task(delayed_delete())
    
    awakening_notif = CustomNotification(awakening_container, awakening_message, awakening_spinner)

    # Lancement de l'éveil asynchrone en tâche de fond (Stratégie Gemini)
    # L'utilisateur voit déjà le header et le style pendant que la mémoire charge
    asyncio.create_task(_async_awakening(awakening_notif))
    
    # Définition de la fonction de drainage de la queue avant utilisation
    def _drain_status_queue():
        global _status_queue
        if _status_queue is None:
            return
        try:
            messages_processed = 0
            for _ in range(8):
                msg = _status_queue.get_nowait()
                messages_processed += 1

                # Process legitimate status messages (from memory_manager, core_logic, etc.)
                if isinstance(msg, str):
                    # Standard status message from system components
                    print(f"[QUEUE] {msg}")

            # Log for debug timer (only if messages processed)
            if messages_processed > 0:
                print(f"[QUEUE] Timer processed {messages_processed} message(s)")
        except queue.Empty:
            pass  # Normal, queue empty
        except Exception as e:
            # Silencieux sur les erreurs de client déconnecté (streaming en cours)
            if "not connected" not in str(e).lower():
                print(f"[QUEUE] Erreur: {e}")
    
    # 🔧 Wrapper pour timers tolérants aux déconnexions pendant streaming
    def safe_timer_wrapper(func):
        """Wrapper qui ignore les erreurs de client non connecté"""
        def wrapped():
            try:
                func()
            except Exception as e:
                if "not connected" not in str(e).lower() and "deleted" not in str(e).lower():
                    print(f"[TIMER] Erreur: {e}")
        return wrapped
    
    # Timer pour traiter les notifications audio en arrière-plan
    ui.timer(0.2, safe_timer_wrapper(_process_pending_notifications))
    
    # Timer pour traiter la status_queue (messages système)
    ui.timer(0.6, safe_timer_wrapper(_drain_status_queue))
    
    # Timer pour traiter les messages Subconscience
    ui.timer(0.5, safe_timer_wrapper(_process_subconscience_messages))  # Vérifier toutes les 500ms
    
    # Timer pour traiter les mises à jour vocales (indicateur, transcription)
    ui.timer(0.15, safe_timer_wrapper(_process_voice_updates))  # Fréquent pour réactivité
    
    # Timer pour mettre à jour les indicateurs d'état IA toutes les 12 secondes
    # RÉACTIVÉ SANS TIMER AUTOMATIQUE - Mise à jour manuelle seulement
    def _update_ia_status_timer():
        try:
            # Créer une tâche pour la fonction async
            asyncio.create_task(_update_ia_status_indicators())
        except Exception as e:
            print(f"[IA-STATUS-TIMER] Erreur: {e}")
    
    # ui.timer(12.0, _update_ia_status_timer)  # TIMER AUTO DÉSACTIVÉ
    
    # Mise à jour initiale des indicateurs après 2 secondes (laisser le temps à l'interface de se charger)
    ui.timer(2.0, _update_ia_status_timer, once=True)  # UNE SEULE FOIS au démarrage
    
    # Boutons flottants (shutdown + hamburger + paramètres + logo)
    with ui.element('div').classes('floating-buttons'):
        # Bouton Shutdown - À gauche du hamburger
        shutdown_btn = ui.button(icon='power_settings_new').classes('settings-floating-btn text-red-500').props('title="Fermer OGMA"').style('background: rgba(239, 68, 68, 0.1);')
        
        def _show_shutdown_confirmation():
            """Affiche le dialog de confirmation de fermeture"""
            with ui.dialog() as confirm_dialog, ui.card().classes('q-dark p-6').style('min-width: 400px;'):
                ui.label('Confirmer la fermeture d\'OGMA ?').classes('text-lg font-bold text-red-400 mb-2')
                ui.label('Tous les processus backend seront arrêtés.').classes('text-sm text-gray-400 mb-4')
                
                with ui.row().classes('gap-2 mt-4 w-full justify-end'):
                    ui.button('Annuler', on_click=confirm_dialog.close).props('outline').classes('text-gray-300')
                    
                    def shutdown_ogma():
                        """Arrêt propre d'OGMA avec déconnexion"""
                        confirm_dialog.close()
                        
                        # 1. DÉCONNEXION - Effacer session utilisateur
                        global _current_user_name, _user_authenticated
                        try:
                            if app.storage.user.get('ogma_user'):
                                logged_user = app.storage.user['ogma_user'].get('name', 'Utilisateur')
                                app.storage.user.clear()
                                print(f"[SESSION] Déconnexion de {logged_user}")
                            
                            _current_user_name = None
                            _user_authenticated = False
                        except Exception as e:
                            print(f"[SESSION] ⚠️ Erreur déconnexion: {e}")
                        
                        # 2. NOTIFICATION
                        ui.notify(
                            'Déconnexion et fermeture d\'OGMA...',
                            type='warning',
                            spinner=True,
                            close=False,
                            timeout=None
                        )
                        
                        # 3. SHUTDOWN
                        import sys
                        import os
                        print("[SHUTDOWN] Arrêt propre demandé par l'utilisateur")
                        
                        # Laisser le temps à la notification de s'afficher
                        import asyncio
                        async def delayed_shutdown():
                            await asyncio.sleep(0.5)
                            print("[SHUTDOWN] Fermeture en cours...")
                            
                            # 📓 JOURNAL DE BORD - Analyse états à la fermeture
                            try:
                                from extensions.journal_de_bord import get_json_manager
                                from extensions.journal_de_bord.shutdown_state_analyzer import initialize_shutdown_analyzer, run_shutdown_analysis
                                jdb_manager = get_json_manager()
                                if jdb_manager and _archiviste_controller:
                                    initialize_shutdown_analyzer(jdb_manager, _archiviste_controller)
                                    print("[SHUTDOWN] Analyse etats journal de bord...")
                                    result = await run_shutdown_analysis()
                                    if result.get("resolved_states"):
                                        print(f"[SHUTDOWN] Etats resolus: {result['resolved_states']}")
                            except ImportError:
                                pass  # Extension non installée
                            except Exception as e:
                                print(f"[SHUTDOWN] Erreur analyse journal (non bloquant): {e}")
                            
                            # 🧠 EGO COMPILER - Compilation incrémentale avant shutdown
                            try:
                                from scripts.ego_compiler import compile_ego_incremental
                                print("[SHUTDOWN] Lancement compilation ego...")
                                await compile_ego_incremental()
                            except Exception as e:
                                print(f"[SHUTDOWN] Erreur compilation ego (non bloquant): {e}")
                                import traceback
                                traceback.print_exc()
                            
                            os._exit(0)  # Arrêt immédiat et propre
                        
                        asyncio.create_task(delayed_shutdown())
                    
                    ui.button('Fermer OGMA', on_click=shutdown_ogma).classes('bg-red-600 text-white')
            
            confirm_dialog.open()
        
        shutdown_btn.on('click', _show_shutdown_confirmation)
        
        toggle_btn = ui.button(icon='menu').classes('sidebar-toggle').props('title="Masquer/Afficher les conversations"')
        # Bouton paramètres flottant (copie des paramètres de la sidebar)
        settings_dialog = _settings_hub_modal()
        settings_btn = ui.button(icon='settings').classes('settings-floating-btn').props('title="Paramètres généraux"')
        settings_btn.on('click', settings_dialog.open)
        ogma_title = ui.label('OGMA').classes('ogma-title').style('font-size: 1.3rem; font-weight: 700; letter-spacing: 0.12em; margin-left: 10px; opacity: 0.85; color: #a07c0a; cursor: pointer;')
        ogma_title.on('click', lambda: ui.run_javascript('location.reload(true)'))
        ogma_title.props('title="Rafraîchir OGMA (Ctrl+Shift+R)"')
    
    # Disposition: barre latérale à gauche + panneau de chat à droite
    with ui.element('div').classes('app-body') as app_body:
        sidebar_element = _sidebar()
        # PANNEAU PRINCIPAL: occupe toute la largeur restante, la scrollbar sera à droite
        with ui.element('main').classes('chat-panel'):
            with ui.element('div').props('data-role="chat-viewport"') as viewport:
                viewport.style('display:flex; flex-direction:column; height:100%; width:100%; padding:0; margin:0;')
                with ui.element('div').classes('conversation-area').props('data-role="chat-scroll"') as scroller:
                    # LAYER 1: viewport plein écran
                    with ui.element('div').classes('chat-viewport-layer'):
                        # LAYER 2: centrage à largeur fixe
                        with ui.element('div').classes('chat-centering-layer'):
                            # LAYER 3: contenu des messages
                            with ui.element('div').classes('chat-inner').props('data-role="chat-container"') as container:
                                _chat_inner = container


                                if not _chat_history:
                                    ui.label('Tapez un message pour commencer...').style('color: var(--text-muted); text-align:center; padding: 16px;')
            # Bouton flottant "aller en bas" (apparaît seulement si non en bas)
            with ui.element('div').classes('down-button-overlay'):
                _down_btn = ui.button(icon='south').classes('scroll-bottom-button')
                _down_btn.props('id="scrollBottomBtn"')
                def _go_bottom():
                    try:
                        ui.run_javascript(r'''(()=>{ const el=document.querySelector('[data-role="chat-scroll"]'); if(el){ el.scrollTo({top: el.scrollHeight, behavior: 'smooth'});} window.OGMA_autoScroll=true; })();''')
                    except Exception:
                        pass
                _down_btn.on('click', _go_bottom)
            
            # Footer intégré avec messagerie (remplace overlay)
            with ui.element('footer').classes('message-input-footer'):
                _input_overlay()
            
            # 🎙️ MODULE VOICE: L'indicateur est créé dans le header (ogma_headers.py)
            # Ne rien faire ici - la référence _voice_indicator est définie dans le header
            
            # Layer 5: bande fixe en bas (alignée à la colonne chat) pour matérialiser la limite basse
            ui.element('div').classes('chat-bottom-fixed').props('aria-hidden="true" data-role="chat-bottom-fixed"')
    
    # 🪞 COGNITIVE MIRROR: Initialisation de l'overlay avec conteneur UI
    try:
        cognitive_mirror = _ensure_cognitive_mirror()
        if cognitive_mirror:
            # v2.1: IntrospectionEngine avec ui_box
            if hasattr(cognitive_mirror, 'ui_box') and cognitive_mirror.ui_box:
                print("[OGMA] 🪞 Introspection v2.1 - UI Box disponible")
            # v1/v2.0: CognitiveMirrorExtension avec ui_components
            elif hasattr(cognitive_mirror, 'ui_components') and cognitive_mirror.ui_components:
                cognitive_mirror.ui_components.create_overlay()
                print("[OGMA] 🪞 Overlay Cognitive Mirror v1 initialisé")
    except Exception as e:
        print(f"[OGMA] WARN Erreur initialisation overlay Cognitive Mirror: {e}")
    
    # Logique toggle sidebar (animation volet horizontal avec recentrage du contenu)
    def _toggle_sidebar():
        ui.run_javascript('''
            const sidebar = document.querySelector('.sidebar');
            const mainContent = document.querySelector('.chat-panel');
            if (!sidebar) return;

            const isCollapsed = sidebar.getAttribute('data-collapsed') === 'true';

            if (isCollapsed) {
                // Ouvrir le volet - état normal avec sidebar visible
                document.documentElement.style.setProperty('--sidebar-width', '360px');
                sidebar.style.transform = 'translateX(0)';
                sidebar.style.transition = 'transform 0.3s ease-in-out';
                sidebar.setAttribute('data-collapsed', 'false');
                localStorage.setItem('ogma_sidebar_collapsed', 'false');
            } else {
                // Fermer le volet
                sidebar.style.transform = 'translateX(-100%)';
                sidebar.style.transition = 'transform 0.3s ease-in-out';
                sidebar.setAttribute('data-collapsed', 'true');
                localStorage.setItem('ogma_sidebar_collapsed', 'true');

                // Mettre à jour la variable CSS pour que le grid se réajuste
                setTimeout(() => {
                    document.documentElement.style.setProperty('--sidebar-width', '0px');
                }, 50);
            }
        ''')
    
    toggle_btn.on('click', _toggle_sidebar)
    
    # UI layout complete
    
    # Initialisation sidebar — CSS démarre déjà collapsed (--sidebar-width:0, transform:translateX(-100%))
    # Ce bloc renforce juste la cohérence de l'attribut data-collapsed
    try:
        ui.run_javascript('''
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.setAttribute('data-collapsed', 'true');
                document.documentElement.style.setProperty('--sidebar-width', '0px');
            }
        ''')
    except Exception:
        pass
    
    # Initialisation du suivi de scroll: détecte si on est en bas et affiche/masque le bouton + ajuste le padding bas dynamiquement
    try:
        ui.run_javascript(r'''
(()=>{
    const scrollEl = document.querySelector('[data-role="chat-scroll"]');
    const btn = document.getElementById('scrollBottomBtn');
    const overlayEl = document.querySelector('.input-overlay');
    const inputWrap = overlayEl ? overlayEl.querySelector('.input-container') : null;
    if(scrollEl){
        const atBottom = ()=> (scrollEl.scrollHeight - scrollEl.scrollTop - scrollEl.clientHeight <= 150);
        let lastScrollTop = scrollEl.scrollTop;
        
        const update = ()=>{
            const isAtBottom = atBottom();
            const currentScrollTop = scrollEl.scrollTop;
            
            if(btn){ btn.style.display = isAtBottom ? 'none' : 'flex'; }
            
            // Gestion de l'auto-scroll pendant le streaming
            if (window.OGMA_streaming) {
                // Si l'utilisateur scrolle vers le haut de plus de 20px, on débraye l'auto-scroll
                if (currentScrollTop < lastScrollTop - 20 && !isAtBottom) {
                    if (window.OGMA_autoScroll) {
                        window.OGMA_autoScroll = false;
                        console.log('[OGMA] Auto-scroll débrayé (scroll manuel)');
                    }
                } 
                // Si l'utilisateur revient vers le bas, on ré-embraye
                else if (isAtBottom) {
                    window.OGMA_autoScroll = true;
                }
            } else {
                window.OGMA_autoScroll = isAtBottom;
            }
            lastScrollTop = currentScrollTop;
        };
        scrollEl.addEventListener('scroll', update, {passive:true});
        update();
    }
    // Ajuste dynamiquement la hauteur réservée au bas via la valeur CSS --composer-height-px
    if(overlayEl){
        const applyPad = ()=>{
            let h = overlayEl.getBoundingClientRect().height || 0;
            if(!h && typeof getComputedStyle === 'function'){
                // fallback si mesure initiale 0: utiliser min-height par défaut
                const root = document.documentElement;
                const defVal = getComputedStyle(root).getPropertyValue('--composer-height-px') || '160px';
                const n = parseFloat(defVal);
                h = isNaN(n) ? 160 : n;
            }
            document.documentElement.style.setProperty('--composer-height-px', (h) + 'px');
        };
        const ro = new ResizeObserver(applyPad);
        ro.observe(overlayEl);
        if(inputWrap){ ro.observe(inputWrap); }
        // Première application après frame puis sur resize fenêtre
        requestAnimationFrame(applyPad);
        window.addEventListener('resize', applyPad, {passive:true});
        window.OGMA_resizeObserver = ro;
    }
})();
''')
    except Exception:
        pass


def run_ogma(host: str = 'localhost', port: int = 8080):
    # Configuration session storage pour éviter les rechargements
    from nicegui import app
    from pathlib import Path
    
    # Assets statiques si le dossier existe
    static_dir = Path(__file__).parent / 'static'
    if static_dir.exists():
        app.add_static_files('/static', str(static_dir))
    
    # Route pour les images générées (évite encodage base64 lourd)
    generated_images_dir = Path(__file__).parent / 'data' / 'generated_images'
    if generated_images_dir.exists():
        app.add_static_files('/generated', str(generated_images_dir))
        print(f"[STATIC] 🖼️ Images générées servies depuis: {generated_images_dir}")
    
    # Page principale avec options de stabilité de session
    @ui.page('/')
    def index():
        return main_page()
    
    # Gestion propre de la fermeture
    import atexit
    import logging
    
    # Réduire les logs d'erreur NiceGUI pour les erreurs de client
    logging.getLogger('nicegui').setLevel(logging.WARNING)
    
    def cleanup_on_exit():
        """Nettoyage lors de la fermeture de l'application"""
        try:
            global _audio_manager
            if _audio_manager and hasattr(_audio_manager, 'cleanup'):
                _audio_manager.cleanup()
            
            # 🧠 EGO COMPILER - Compilation incrémentale à la fermeture
            try:
                import asyncio
                from scripts.ego_compiler import compile_ego_incremental
                print("[CLEANUP] 🧠 Lancement compilation ego incrémentale...")
                asyncio.run(compile_ego_incremental())
            except Exception as e:
                print(f"[CLEANUP] ⚠️ Erreur compilation ego (non bloquant): {e}")
            
            print("[CLEANUP] Nettoyage terminé")
        except Exception as e:
            print(f"[CLEANUP] Erreur lors du nettoyage: {e}")
    
    atexit.register(cleanup_on_exit)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🔍 DEBUG: Hooks de connexion/déconnexion pour tracer les problèmes WebSocket
    # ═══════════════════════════════════════════════════════════════════════════
    from nicegui import app
    from datetime import datetime
    
    @app.on_connect
    async def on_client_connect(client):
        print(f"🟢 [WS-DEBUG] Client CONNECTÉ: {client.id} à {datetime.now().strftime('%H:%M:%S.%f')}")
        # 🛡️ TRACKING: Enregistrer l'activité à la connexion
        try:
            track_client_activity(client.id)
        except Exception:
            pass
    
    @app.on_disconnect  
    async def on_client_disconnect(client):
        print(f"🔴 [WS-DEBUG] Client DÉCONNECTÉ: {client.id} à {datetime.now().strftime('%H:%M:%S.%f')}")
        print(f"🔴 [WS-DEBUG] ⚠️ Déconnexion détectée - peut causer un rechargement!")
    
    print("[DEBUG] 🔍 Hooks WebSocket connect/disconnect installés")
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Démarrer avec gestion d'erreur améliorée
    try:
        ui.run(
            title='OGMA - IA Conversationnelle', 
            host=host, 
            port=port, 
            reload=False, 
            show=True, 
            dark=True,
            reconnect_timeout=600.0,  # 10 minutes pour éviter déconnexions pendant réponses IA longues
            storage_secret='ogma-session-secret-v1',  # Secret pour session stable (évite rechargements)
            binding_refresh_interval=0.3,  # Rafraîchissement UI rapide pour keepalive WebSocket
            favicon='🤖'
        )
    except KeyboardInterrupt:
        print("[INFO] Arrêt de l'application...")
        cleanup_on_exit()
    except Exception as e:
        print(f"[ERROR] Erreur durant l'exécution: {e}")
        cleanup_on_exit()


# ═══════════════════════════════════════════════════════════════════════════════
# 📡 API EXTERNE - Fonction pour consommateurs externes (Telegram, API, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

async def process_external_message(
    user_text: str,
    source: str = "external",
    user_name: str = "Utilisateur",
    include_memories: bool = True,
    save_memories: bool = True,
    external_history: list = None
) -> Tuple[str, bool]:
    """
    Fonction headless pour traiter un message externe avec tout le contexte OGMA.
    Utilise les mêmes pipelines que l'interface web principale.
    
    Args:
        user_text: Le message de l'utilisateur
        source: Source du message ("telegram", "api", etc.)
        user_name: Nom de l'utilisateur
        include_memories: Inclure la recherche mémoire dans le contexte
        save_memories: Traiter et sauvegarder les marqueurs #MEM dans la réponse
        external_history: Historique de conversation externe [{"role": "user/assistant", "content": "..."}]
        
    Returns:
        Tuple[str, bool]: (réponse IA, si un souvenir a été mémorisé)
    """
    import uuid
    import re
    from datetime import datetime
    
    print(f"[EXTERNAL-API] Traitement message de {user_name} via {source}")
    print(f"[EXTERNAL-API] ============================================")
    print(f"[EXTERNAL-API] Message: {user_text[:100]}...")
    
    # 1. Récupérer les composants OGMA (singletons partagés)
    sm = _ensure_settings_manager()
    mem = _ensure_memory_manager()
    ctrl = _ensure_chat_controller()
    archiviste_ctrl = _ensure_archiviste_controller()
    
    # Vérification singletons
    print(f"[EXTERNAL-API] Memory Manager: {mem}")
    if mem:
        print(f"[EXTERNAL-API] → Base mémoire: {mem._db_path if hasattr(mem, '_db_path') else 'N/A'}")
    print(f"[EXTERNAL-API] Chat Controller: {ctrl}")
    print(f"[EXTERNAL-API] Archiviste Controller: {archiviste_ctrl}")
    
    if not ctrl:
        return "Erreur: Contrôleur IA non disponible.", False
    
    messages = []
    ego_injection = None
    context_note = None
    detailed_memories = []
    
    # 2. Utiliser le système PREANALYSIS pour obtenir tout le contexte optimisé
    if PREANALYSIS_AVAILABLE and include_memories:
        try:
            print("[EXTERNAL-API] Utilisation PREANALYSIS pour contexte complet...")
            
            # Récupérer contexte optimisé (ego + mémoires en parallèle)
            optimized_ctx = await get_optimized_context_for_message(
                user_message=user_text,
                conversation_history=external_history or [],  # Historique réel (Telegram, etc.)
                memory_manager=mem,
                archiviste_controller=archiviste_ctrl
            )
            
            if optimized_ctx.get('optimized'):
                ego_injection = optimized_ctx.get('ego_injection', '')
                if ego_injection:
                    print(f"[EXTERNAL-API] Ego optimisé obtenu ({len(ego_injection)} chars)")
            else:
                print("[EXTERNAL-API] PREANALYSIS non optimisé, fallback")
                
        except Exception as e:
            print(f"[EXTERNAL-API] Erreur PREANALYSIS: {e}")
    
    # 3. Fallback: construction manuelle du contexte
    if ego_injection is None:
        try:
            # Tenter activation ego via le système boolean
            from modules.logic.ego_activation import activate_ego_groups
            if archiviste_ctrl:
                ego_injection = await activate_ego_groups(user_text, archiviste_ctrl, is_new_session=True)
                if ego_injection:
                    print(f"[EXTERNAL-API] Ego boolean activé ({len(ego_injection)} chars)")
        except ImportError:
            print("[EXTERNAL-API] Module ego_activation non disponible")
        except Exception as e:
            print(f"[EXTERNAL-API] Erreur ego activation: {e}")
    
    # 4. Construire les messages système
    
    # 4a. Horodatage
    current_datetime = datetime.now()
    horodatage = current_datetime.strftime("Il est %H:%M le %A %d %B %Y")
    jours_fr = {'Monday': 'lundi', 'Tuesday': 'mardi', 'Wednesday': 'mercredi', 
                'Thursday': 'jeudi', 'Friday': 'vendredi', 'Saturday': 'samedi', 'Sunday': 'dimanche'}
    mois_fr = {'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
               'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
               'September': 'septembre', 'October': 'octobre', 'November': 'novembre', 'December': 'décembre'}
    for eng, fr in jours_fr.items():
        horodatage = horodatage.replace(eng, fr)
    for eng, fr in mois_fr.items():
        horodatage = horodatage.replace(eng, fr)
    
    messages.append({'role': 'system', 'content': f"[HORODATAGE] {horodatage}"})
    
    # 4b. Instructions de base (ego prompt complet depuis settings)
    base_instructions = sm.settings.get('prompts', {}).get('instructions', '')
    
    # Fusionner ego injection si disponible
    if ego_injection:
        base_instructions = f"{ego_injection}\n\n{base_instructions}"
        print(f"[EXTERNAL-API] Ego fusionné aux instructions")
    
    if base_instructions:
        messages.append({'role': 'system', 'content': base_instructions})
    
    # 4c. Récupérer les mémoires pertinentes
    if include_memories and mem:
        try:
            optimizer = _ensure_memory_optimizer()
            
            if optimizer:
                print("[EXTERNAL-API] ============================================")
                print("[EXTERNAL-API] RECHERCHE MEMOIRE - Smart Stop optimizer")
                print(f"[EXTERNAL-API] → Query: {user_text[:80]}...")
                optimized_mem = await optimizer.get_optimized_context(
                    message=user_text,
                    k_personal=5,
                    k_conversation=5
                )
                
                if optimized_mem:
                    context_note = optimized_mem.synthesis
                    detailed_memories = optimized_mem.memories_personal + optimized_mem.memories_conversation
                    
                    print(f"[EXTERNAL-API] → Souvenirs trouvés: {len(detailed_memories)}")
                    for i, m in enumerate(detailed_memories[:3], 1):
                        print(f"[EXTERNAL-API]   {i}. {m.get('title', 'N/A')[:50]}")
                    
                    if context_note:
                        messages.append({'role': 'system', 'content': f"[CONTEXTE MEMORIEL - Synthèse Archiviste]\n{context_note}"})
                        print(f"[EXTERNAL-API] → Synthèse injectée ({len(context_note)} chars)")
                    
                    if detailed_memories:
                        memories_text = "[SOUVENIRS DETAILLES]\n"
                        for i, m in enumerate(detailed_memories[:5], 1):
                            title = m.get('title', 'Sans titre')
                            if m.get('send_full_text', False):
                                content = m.get('text_original', '')[:400]
                                memories_text += f"{i}. **{title}** (TEXTE INTEGRAL):\n   {content}\n"
                            else:
                                summary = m.get('summary', '')[:200]
                                memories_text += f"{i}. {title}: {summary}\n"
                        messages.append({'role': 'system', 'content': memories_text})
                else:
                    print("[EXTERNAL-API] → AUCUN souvenir trouvé par optimizer")
            else:
                # Fallback recherche directe
                print("[EXTERNAL-API] FALLBACK - Recherche mémoire directe (optimizer non dispo)")
                search_results = await mem.search_memories(query=user_text, limit=5)
                print(f"[EXTERNAL-API] → Résultats directs: {len(search_results) if search_results else 0}")
                if search_results:
                    memory_text = "[SOUVENIRS PERTINENTS]\n"
                    for m in search_results[:3]:
                        if isinstance(m, dict):
                            text = m.get('text', m.get('content', m.get('summary', '')))[:300]
                        else:
                            text = str(m)[:300]
                        memory_text += f"- {text}\n"
                    messages.append({'role': 'system', 'content': memory_text})
                    
        except Exception as e:
            print(f"[EXTERNAL-API] ERREUR mémoire: {e}")
            import traceback
            traceback.print_exc()
    
    # 4d. Contexte Journal de Bord si disponible
    try:
        from extensions.journal_de_bord import is_journal_available, get_context_provider
        if is_journal_available():
            provider = get_context_provider()
            if provider:
                journal_ctx = provider.get_morning_context()
                if journal_ctx:
                    messages.append({'role': 'system', 'content': f"[JOURNAL DE BORD]\n{journal_ctx}"})
                    print(f"[EXTERNAL-API] Journal contexte injecté")
    except Exception:
        pass
    
    # 4e. Contexte Rêve si pertinent
    try:
        from extensions.dream_engine import get_last_dream_context, is_available as dream_available
        if dream_available():
            dream_ctx = get_last_dream_context()
            if dream_ctx and not dream_ctx.get('mentioned', False):
                dream_summary = dream_ctx.get('summary', '')
                if dream_summary:
                    messages.append({'role': 'system', 'content': f"[DERNIER REVE - Tu peux en parler si pertinent]\n{dream_summary}"})
                    print(f"[EXTERNAL-API] Rêve contexte injecté")
    except Exception:
        pass
    
    # 5. Injecter l'historique de conversation externe si fourni
    if external_history:
        for hist_msg in external_history:
            role = hist_msg.get('role', '')
            content = hist_msg.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})
        print(f"[EXTERNAL-API] Historique injecté: {len(external_history)} messages")

    # 5b. Directive style source (Telegram = format mobile SMS)
    # Placée juste avant le message user = poids maximal pour le LLM
    if source == "telegram":
        telegram_style = (
            f"[CANAL: TELEGRAM - FORMAT MOBILE]\n"
            f"Tu réponds via Telegram à {user_name}. Contraintes de format IMPÉRATIVES :\n"
            f"- LONGUEUR : réponse courte type WhatsApp/SMS — 2 à 4 phrases maximum, comme un message qu'on envoie sur son téléphone\n"
            f"- Ne rédige JAMAIS un long texte : si ta réponse dépasse 5 lignes, tu l'as ratée, recommence plus court\n"
            f"- Style conversationnel naturel : fluide, direct, sans structure formelle\n"
            f"- PAS de titres, PAS de listes à puces, PAS de markdown complexe\n"
            f"- Gras (**mot**) autorisé avec parcimonie pour l'emphase\n"
            f"- Emojis bienvenus mais modérés (1-3 max par message)\n"
            f"- Si le sujet demande vraiment plus, divise en plusieurs messages successifs courts\n"
            f"- Garde ta personnalité et ton ton habituels, juste en version compacte SMS"
        )
        messages.append({'role': 'system', 'content': telegram_style})
        print(f"[EXTERNAL-API] Directive style Telegram injectée (juste avant message user)")

    # 5c. Ajouter le message utilisateur
    messages.append({'role': 'user', 'content': user_text})
    
    # Résumé contexte final
    print(f"[EXTERNAL-API] ============================================")
    print(f"[EXTERNAL-API] CONTEXTE FINAL: {len(messages)} messages")
    for i, msg in enumerate(messages):
        role = msg.get('role', '?')
        content = msg.get('content', '')
        preview = content[:80].replace('\n', ' ') if content else ''
        print(f"[EXTERNAL-API]   {i+1}. [{role}] {preview}...")
    print(f"[EXTERNAL-API] ============================================")
    
    # 6. Appel API
    try:
        response, error = await ctrl.call_chat_api(
            messages=messages,
            max_tokens=ctrl.max_tokens,
            context_length=ctrl.context_length,
            temperature=ctrl.temperature
        )
        
        if error:
            print(f"[EXTERNAL-API] Erreur API: {error}")
            return f"Erreur: {error}", False
            
        if not response:
            return "Je n'ai pas pu générer de réponse.", False
            
    except Exception as e:
        print(f"[EXTERNAL-API] Exception API: {e}")
        import traceback
        traceback.print_exc()
        return f"Erreur technique: {str(e)}", False
    
    # 7. Traitement des marqueurs mémoire (#MEM / phrases magiques)
    ai_memorized = False
    
    if save_memories and mem:
        # Réutiliser la fonction d'extraction existante
        def extract_magic_memories(s: str) -> list:
            if not s:
                return []
            patterns = [
                r"(?:\*\*|__)?il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
                r"(?:\*\*|__)?m[ée]morise(?:s)?\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
            ]
            results = []
            for pat in patterns:
                found = re.findall(pat, s, flags=re.IGNORECASE | re.DOTALL)
                for m in found:
                    content = m.strip()
                    if content:
                        content = re.sub(r'^[:\-\s\.]+', '', content)
                        content = re.sub(r'(\*\*|__)$', '', content).strip()
                        content = re.sub(r'</?[A-ZÉÈÊa-zéèê_]+>', '', content).strip()
                        if content and len(content) > 10:
                            results.append(content)
            return results
        
        magic_memories = extract_magic_memories(response)
        if magic_memories:
            print(f"[EXTERNAL-API] {len(magic_memories)} souvenir(s) à mémoriser")
            for content in magic_memories:
                try:
                    mem_id = f"telegram-{uuid.uuid4()}"
                    conversation_context = f"Message Telegram de {user_name}: {user_text[:200]}"
                    ok = await mem.add_memory(
                        mem_id,
                        content,
                        chat_controller=ctrl,
                        conversation_context=conversation_context,
                        interlocutor=user_name
                    )
                    if ok:
                        ai_memorized = True
                        print(f"[EXTERNAL-API] Souvenir mémorisé: {content[:50]}...")
                except Exception as e:
                    print(f"[EXTERNAL-API] Erreur mémorisation: {e}")
        
        # Traitement ego traits
        ego_pattern = r"(?:\*\*|__)?ceci\s+est\s+une\s+part\s+de\s+moi\s+maintenant(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)"
        if ego_match := re.search(ego_pattern, response, re.DOTALL | re.IGNORECASE):
            ego_content = ego_match.group(1).strip()
            ego_content = re.sub(r'\*\*(.*?)\*\*', r'\1', ego_content)
            ego_content = re.sub(r'[*_`]', '', ego_content)
            if ego_content and mem:
                try:
                    memory_id = await mem.store_ego_trait(
                        ego_content,
                        chat_controller=ctrl,
                        conversation_context=f"Via {source}",
                        interlocutor=user_name
                    )
                    if memory_id:
                        ai_memorized = True
                        print(f"[EXTERNAL-API] Ego trait mémorisé: {ego_content[:50]}...")
                except Exception as e:
                    print(f"[EXTERNAL-API] Erreur ego trait: {e}")
    
    print(f"[EXTERNAL-API] Réponse générée ({len(response)} chars), mémorisé={ai_memorized}")
    
    return response, ai_memorized


def get_external_api():
    """Retourne la fonction process_external_message pour utilisation externe."""
    return process_external_message


if __name__ == "__main__":
    run_ogma()


