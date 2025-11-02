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
        from nicegui_error_handler import initialize_nicegui_error_handling
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

from utils import DATA_DIR, EGO_PROMPT_FILE, EGO_PROMPT_SYNTHESIZED_FILE
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
    print("[REFACTOR] OK Composants UI importés depuis les modules spécialisés")
except ImportError as e:
    print(f"[REFACTOR] ERREUR import composants UI: {e}")
    # Fallback: continuer sans les composants déplacés


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
_conv_index: Dict[str, Dict] = {}
_conv_area = None  # conteneur de conversation
_chat_inner = None  # conteneur interne pour les messages (pile verticale)
_input_field = None  # champ de saisie des messages
_archiviste_controller: Optional[AIController] = None
_embedding_controller: Optional[EmbeddingController] = None
_memory_manager: Optional[MemoryManager] = None
_temporal_guardian = None  # Extension Temporal Guardian
_cognitive_mirror = None   # Extension Cognitive Mirror - Transparence cognitive
_contextual_recall_ext = None  # Extension Contextual Recall - Mémoire conversationnelle
_file_writer_ext = None  # Extension File Writer - Sauvegarde automatique .md
_journal_preformed_response = None  # Réponse journal prête à être injectée
_introspection_box_content = []  # Buffer messages introspection en cours
_introspection_md_widget = None  # Référence au widget markdown de la boîte
_status_queue: Optional[queue.Queue] = None
_memory_update_hooks: List[Callable[[], None]] = []  # callbacks à appeler après ajout mémoire
_sidebar_render_cb: Optional[Callable[[Optional[str]], None]] = None  # rafraîchisseur de la liste des conversations
_title_updating: bool = False  # évite les mises à jour concurrentes de titre

# Gestion des fichiers
_active_file_data: Optional[Dict] = None  # Données du fichier actuel
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

# Variable globale pour l'extension Web Navigator (éviter les recréations)
_web_navigator_ext = None

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


def get_web_navigator_instance():
    """Obtient l'instance unique de Web Navigator (pattern singleton)"""
    global _web_navigator_ext
    
    if _web_navigator_ext is None:
        try:
            from extensions.web_navigator import WebNavigatorExtension
            _web_navigator_ext = WebNavigatorExtension()
            print(f"[WEB-NAV-SINGLETON] ✅ Instance Web Navigator créée")
        except Exception as e:
            print(f"[WEB-NAV-SINGLETON] ❌ Erreur création instance: {e}")
            _web_navigator_ext = None
    
    return _web_navigator_ext


def _ensure_settings_manager():
    global _settings_mgr
    if _settings_mgr is None:
        settings_path = DATA_DIR / 'settings.json'
        _settings_mgr = SettingsManager(settings_path)
    return _settings_mgr


def _ensure_audio_manager():
    """Initialise paresseusement l'audio manager avec TTS sans conflit."""
    global _audio_manager, _auto_send_audio
    if _audio_manager is None:
        try:
            # Charger la préférence d'envoi automatique depuis les paramètres
            sm = _ensure_settings_manager()
            _auto_send_audio = sm.settings.get('audio', {}).get('auto_send', False)
            
            # Utiliser le nouveau wrapper TTS sans conflit
            _audio_manager = get_audio_manager()
            
            # Initialiser le TTS sans conflit (auto-détection des moteurs)
            _audio_manager.initialize_tts()
            
            print("[AUDIO] 🎵 Audio manager TTS sans conflit initialisé")
        except Exception as e:
            print(f"[AUDIO] Erreur initialisation: {e}")
    return _audio_manager


def _ensure_backends():
    """Initialise paresseusement les gestionnaires de backends."""
    global _api_mgr, _ollama_mgr, _gguf_mgr, _kobold_mgr
    if _api_mgr is None:
        _api_mgr = APIManager()
    if _ollama_mgr is None:
        _ollama_mgr = OllamaManager()
    if _gguf_mgr is None:
        _gguf_mgr = GGUFManager()
    if _kobold_mgr is None:
        _kobold_mgr = KoboldManager()
    
    # Charger les URLs des services depuis les paramètres si disponibles
    try:
        sm = _ensure_settings_manager()

        # Configurer les managers avec le settings_manager pour les paramètres dynamiques
        if hasattr(_ollama_mgr, 'set_settings_manager'):
            _ollama_mgr.set_settings_manager(sm)
        if hasattr(_gguf_mgr, 'set_settings_manager'):
            _gguf_mgr.set_settings_manager(sm)

        chat = sm.settings.get('chat_api', {})
        arch = sm.settings.get('reasoning_api', {})
        emb = sm.settings.get('embedding_api', {})
        ollama_url = (chat.get('ollama_url') or arch.get('ollama_url') or emb.get('ollama_url'))
        kobold_url = (chat.get('kobold_url') or arch.get('kobold_url'))
        if ollama_url:
            _ollama_mgr.api_url = str(ollama_url).rstrip('/')
        if kobold_url:
            _kobold_mgr.api_url = str(kobold_url).rstrip('/')

        # 🎨 Initialiser l'extension text2img si activée
        from extensions.text2img import initialize_text2img, is_available as text2img_available
        img_settings = sm.settings.get('image_generation', {})
        if img_settings.get('enabled', False) and not text2img_available():
            initialize_text2img(sm)
    except Exception as e:
        print(f"[ERROR] Erreur initialisation backends: {e}")
    return _api_mgr, _ollama_mgr, _gguf_mgr, _kobold_mgr

# NOTA: _map_backend_for_controller extrait vers utils/backend_utils.py

def _get_current_time() -> str:
    """Fonction pour que Luna puisse demander l'heure actuelle quand nécessaire."""
    from temporal_injector import TemporalInjector
    temporal_injector = TemporalInjector()
    return temporal_injector.get_current_time()


def _ensure_memory_manager() -> Optional[MemoryManager]:
    """Instancie MemoryManager (SQLite/FAISS) + configure Archiviste & Embeddings."""
    global _memory_manager, _archiviste_controller, _embedding_controller, _status_queue
    if _memory_manager is not None:
        return _memory_manager

    _ensure_backends()
    sm = _ensure_settings_manager()

    # Queue statut pour logs backend → UI (drain futur via ui.timer)
    if _status_queue is None:
        _status_queue = queue.Queue()

    # Messages d'injection comportementale en attente (Extension Metacognitive)
    global _pending_behavioral_injections
    if '_pending_behavioral_injections' not in globals():
        _pending_behavioral_injections = []

    # Contrôleur Archiviste
    _archiviste_controller = AIController('archiviste', cast(OllamaManager, _ollama_mgr), cast(GGUFManager, _gguf_mgr), cast(KoboldManager, _kobold_mgr))
    arch = sm.settings.get('reasoning_api', {})
    # map_backend_for_controller importé depuis utils.backend_utils
    arch_backend = map_backend_for_controller(arch.get('backend_type', 'API'))
    _archiviste_controller.set_active_backend(arch_backend)
    
    # Gestion des valeurs -1 pour auto-detect avec vraies capacités modèle
    max_tokens = arch.get('max_tokens', 512)
    context_length = arch.get('context_length', 4096)
    
    # SYSTÈME HYBRIDE: API + spécifications officielles pour auto-détection optimale
    if max_tokens == -1 or context_length == -1:
        try:
            from hybrid_detection import hybrid_auto_detect_capabilities
            provider = arch.get('provider', 'Aucun').lower()
            model = arch.get('model', '') or arch.get('api_model', '')
            api_key = arch.get('api_key', '')
            
            if provider != 'aucun' and model and api_key:
                print(f"[ARCHIVISTE-HYBRID] � Détection hybride {provider}")
                detected_caps = hybrid_auto_detect_capabilities(provider, model, "reasoning", api_key)
                if max_tokens == -1:
                    max_tokens = detected_caps['max_tokens']
                    print(f"[ARCHIVISTE-HYBRID] OK max_tokens optimal: {max_tokens:,}")
                if context_length == -1:
                    context_length = detected_caps['context_length']
                    print(f"[ARCHIVISTE-HYBRID] OK context_length optimal: {context_length:,}")
            else:
                # Fallback si pas de configuration complète
                if max_tokens == -1:
                    max_tokens = 512
                if context_length == -1:
                    context_length = 4096
                print(f"[ARCHIVISTE-HYBRID] WARN Configuration incomplète, utilisation valeurs par défaut")
        except Exception as e:
            # Fallback en cas d'erreur
            if max_tokens == -1:
                max_tokens = 512
            if context_length == -1:
                context_length = 4096
            print(f"[ARCHIVISTE-AUTO] ERROR Erreur auto-détection: {e}, utilisation valeurs par défaut")
    
    _archiviste_controller.max_tokens = int(max_tokens)
    _archiviste_controller.context_length = int(context_length)
    _archiviste_controller.temperature = float(arch.get('temperature', 0.7))
    # Backend spécifique
    if arch_backend == 'API':
        _archiviste_controller.api_manager.configure(
            arch.get('provider', 'Aucun'), arch.get('api_key', ''), arch.get('api_model', '')
        )
    elif arch_backend == 'Ollama':
        url = arch.get('ollama_url') or 'http://localhost:11434'
        cast(OllamaManager, _ollama_mgr).api_url = str(url).rstrip('/')
        cast(OllamaManager, _ollama_mgr).check_service()
        _archiviste_controller.ollama_model = arch.get('ollama_model', '')
    elif arch_backend == 'GGUF/llama.cpp':
        model = arch.get('gguf_model', '')
        # Utiliser la nouvelle structure other_backends.gguf
        gguf_cfg = sm.settings.get('other_backends', {}).get('gguf', {})
        n_gpu_layers = int(gguf_cfg.get('gpu_layers', -1))
        if model and not cast(GGUFManager, _gguf_mgr).is_available:
            cast(GGUFManager, _gguf_mgr).load_model(model, _archiviste_controller.context_length, n_gpu_layers)
    elif arch_backend == 'KoboldCpp':
        url = arch.get('kobold_url') or 'http://localhost:5001'
        cast(KoboldManager, _kobold_mgr).api_url = str(url).rstrip('/')
        cast(KoboldManager, _kobold_mgr).check_service()

    # Contrôleur Embeddings
    _embedding_controller = EmbeddingController(cast(OllamaManager, _ollama_mgr), cast(GGUFManager, _gguf_mgr))
    emb = sm.settings.get('embedding_api', {})
    # map_backend_for_controller importé depuis utils.backend_utils
    emb_backend = map_backend_for_controller(emb.get('backend_type', 'API'))
    _embedding_controller.configure(
        emb_backend,
        api_provider=emb.get('provider'),
        api_key=emb.get('api_key'),
        api_model=emb.get('api_model'),
        ollama_model=emb.get('ollama_model'),
        gguf_model=emb.get('gguf_model'),
    )

    # Dossiers et chemins
    mem_dir = DATA_DIR / 'memory'
    mem_dir.mkdir(parents=True, exist_ok=True)
    db_path = mem_dir / 'memories.db'
    index_path = mem_dir / 'faiss.index'

    # Dimension embeddings (par défaut 1024, conforme Mistral-embed)
    embedding_dim = 1024

    # Instanciation MemoryManager
    try:
        print(f"[MEMORY-MANAGER] 🧠 Initialisation MemoryManager...")
        print(f"[MEMORY-MANAGER] Paramètres:")
        print(f"  - db_path: {db_path}")
        print(f"  - index_path: {index_path}")
        print(f"  - embedding_dim: {embedding_dim}")
        print(f"  - archiviste_controller: {type(_archiviste_controller) if _archiviste_controller else None}")
        print(f"  - embedding_controller: {type(_embedding_controller) if _embedding_controller else None}")
        
        _memory_manager = MemoryManager(
            db_path=db_path,
            index_path=index_path,
            embedding_dim=embedding_dim,
            archiviste_ia=_archiviste_controller,
            embedding_ia=_embedding_controller,
            status_queue=_status_queue,
            settings_manager=sm,
        )
        
        print(f"[MEMORY-MANAGER] ✅ MemoryManager initialisé avec succès")
        
        # Configurer le summarizer avec l'archiviste
        from conversation_summarizer import summarizer
        if _archiviste_controller:
            summarizer.set_archiviste(_archiviste_controller)
        
    except Exception as e:
        print(f"[MEMORY-MANAGER] ❌ Erreur init mémoire: {e}")
        print(f"[MEMORY-MANAGER] Type erreur: {type(e)}")
        import traceback
        traceback.print_exc()
        _notify_safe(f"Erreur init mémoire: {e}", type='warning')
        _memory_manager = None

    return _memory_manager


def close_memory_manager():
    """Ferme proprement le MemoryManager pour permettre la suppression des fichiers."""
    global _memory_manager
    if _memory_manager is not None:
        try:
            _memory_manager.cleanup()
            print("[OGMA] MemoryManager fermé proprement")
        except Exception as e:
            print(f"[OGMA] Erreur fermeture MemoryManager: {e}")
        finally:
            _memory_manager = None


def _ensure_temporal_guardian():
    """Initialise l'extension Temporal Guardian pour gestion temporelle organique."""
    global _temporal_guardian
    if _temporal_guardian is not None:
        return _temporal_guardian
    
    try:
        # Récupérer la configuration depuis les settings si elle existe
        sm = _ensure_settings_manager()
        temporal_config = sm.settings.get('temporal_guardian', {})
        
        # Configuration par défaut avec debug activé si mode debug général
        debug_mode = sm.settings.get('debug', {}).get('show_temporal_debug', False)
        
        # Créer l'instance Temporal Guardian
        _temporal_guardian = create_temporal_guardian(temporal_config, debug=debug_mode)
        
        if debug_mode:
            print("[OGMA] 🕒 Temporal Guardian initialisé avec succès")
        
    except Exception as e:
        print(f"[OGMA] WARN Erreur initialisation Temporal Guardian: {e}")
        # Créer instance par défaut en cas d'erreur
        _temporal_guardian = create_temporal_guardian(debug=False)
    
    return _temporal_guardian


def _ensure_contextual_recall():
    """Initialise l'extension Contextual Recall pour accès mémoire conversationnelle."""
    global _contextual_recall_ext
    if _contextual_recall_ext is not None:
        return _contextual_recall_ext
    
    try:
        from extensions.contextual_recall import initialize_recall
        
        _contextual_recall_ext = initialize_recall(
            summaries_cache_path="data/summaries_cache",
            conversations_path="data/conversations",
            debug=False
        )
        
        if _contextual_recall_ext:
            print("[CONTEXTUAL-RECALL] ✅ Extension initialisée")
        
    except Exception as e:
        print(f"[CONTEXTUAL-RECALL] ⚠️ Erreur initialisation: {e}")
        _contextual_recall_ext = None
    
    return _contextual_recall_ext


def _ensure_file_writer():
    """Initialise l'extension File Writer pour sauvegarde automatique fichiers .md"""
    global _file_writer_ext
    if _file_writer_ext is not None:
        return _file_writer_ext
    
    try:
        from extensions.file_writer import initialize_file_writer
        
        _file_writer_ext = initialize_file_writer(
            uploads_dir="data/uploads",
            debug=False
        )
        
        if _file_writer_ext:
            print("[FILE-WRITER] ✅ Extension initialisée")
        
    except Exception as e:
        print(f"[FILE-WRITER] ⚠️ Erreur initialisation: {e}")
        _file_writer_ext = None
    
    return _file_writer_ext


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
                
                # L'ajouter à l'historique de conversation comme message système
                global current_conversation_id
                if current_conversation_id and current_conversation_id in conversations:
                    conversations[current_conversation_id].append({
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

def _process_subconscience_messages():
    """Timer pour traiter les messages Subconscience - un déroulé par message"""
    global _current_conversation_id, _chat_inner, _chat_history, _chat_history_ui
    
    # 🛡️ PROTECTION ANTI-CRASH NiceGUI - Vérification préalable
    try:
        if _chat_inner is None:
            return  # Pas d'interface disponible
        
        # Test de connexion client NiceGUI
        test_element = ui.element('span').style('display: none;')
        test_element.delete()  # Si ça marche, le client est connecté
        
    except Exception as client_check:
        error_msg = str(client_check).lower()
        if "deleted" in error_msg or "client" in error_msg or "belongs" in error_msg:
            print(f"[UI-PROTECTION] ⚠️ Client NiceGUI déconnecté - abandon traitement messages")
            return
        # Autres erreurs non critiques, continuer
    
    try:
        # Import dynamique pour éviter les dépendances circulaires
        from extensions.cognitive_mirror.core_cognitive_mirror import CognitiveMirrorCore
        
        # CRUCIAL: Vérifier si l'extension est activée
        if _cognitive_mirror is None or not _cognitive_mirror.is_enabled:
            return  # Extension OFF - pas de traitement
        
        messages = CognitiveMirrorCore.get_pending_messages()
        
        if not messages:
            return
            
        # Traiter chaque message individuellement
        for message in messages:
            try:
                role = message.get('role', 'assistant')
                content = message.get('content', '')
                original_role = message.get('original_role', 'unknown')
                
                # Créer le contenu introspection pour ce message
                if original_role == 'luna':
                    formatted_content = f"**Entité Numérique**\n\n{content}"
                    border_color = "59, 130, 246"  # Bleu pour entité principale
                elif original_role == 'archiviste':
                    formatted_content = f"**Archiviste**\n\n{content}"
                    border_color = "255, 140, 0"  # Orange pour Archiviste
                else:
                    # Pour toute autre IA principale, utiliser le terme générique
                    formatted_content = f"**Entité Numérique**\n\n{content}"
                    border_color = "59, 130, 246"  # Bleu par défaut

                introspection_content = f"<introspection>\n{formatted_content}\n</introspection>"

                # Afficher immédiatement le déroulé pour ce message
                if _chat_inner is not None:
                    # Importé depuis utils.message_parsers
                    parsed_introspection, main_content = parse_introspection_format(introspection_content)

                    if parsed_introspection:
                        # 🛡️ Protection UI pour la création d'éléments
                        container = safe_ui_operation(lambda: ui.element('div').classes('message-container'))
                        if container is None:
                            print(f"[UI-PROTECTION] Container création annulée - client déconnecté")
                            continue  # Passer au message suivant
                        
                        with _chat_inner, container:
                            message_div = safe_ui_operation(lambda: ui.element('div').classes('message-ai'))
                            if message_div is None:
                                print(f"[UI-PROTECTION] Message div création annulée - client déconnecté")
                                continue
                            
                            with message_div:
                                    # CSS introspection avec couleur dynamique selon rôle
                                    ui.add_head_html(f'''
                                    <style>
                                    .introspection-expansion-{original_role} {{
                                        margin: 8px 0 !important;
                                        border-radius: 6px !important;
                                        background: rgba({border_color}, 0.05) !important;
                                        border: 1px solid rgba({border_color}, 0.3) !important;
                                    }}
                                    .introspection-expansion-{original_role} .q-expansion-item__content {{
                                        padding: 8px 12px !important;
                                        font-size: 12px !important;
                                        font-style: italic !important;
                                        color: rgba(255, 255, 255, 0.8) !important;
                                        line-height: 1.4 !important;
                                        background: rgba({border_color}, 0.03) !important;
                                    }}
                                    .introspection-header-{original_role} {{
                                        color: rgba({border_color}, 0.8) !important;
                                        font-size: 12px !important;
                                        font-style: italic !important;
                                    }}
                                    </style>
                                    ''')
                                    
                                    # Créer l'expansion pour ce message avec classe spécifique au rôle
                                    with ui.expansion().classes(f'introspection-expansion-{original_role}') as introspection_expansion:
                                        introspection_expansion.props(f'label=""')
                                        with introspection_expansion.add_slot('header'):
                                            with ui.row().classes('gap-2').style('align-items: center; width: 100%;'):
                                                ui.html(f'<span class="introspection-header-{original_role}">introspection</span>')
                                                ui.space()  # Pousse le bouton à droite
                                                # Bouton d'arrêt de réflexion
                                                def _stop_reflection_now():
                                                    """Arrête immédiatement la réflexion et génère une synthèse"""
                                                    global _cognitive_mirror
                                                    try:
                                                        if _cognitive_mirror:
                                                            print("[STOP-BTN] 🛑 Arrêt forcé de la réflexion via bouton")
                                                            success = _cognitive_mirror.stop_reflection_session("user_button_stop")
                                                            if success:
                                                                ui.notify('🛑 Réflexion arrêtée', type='warning', position='top')
                                                            else:
                                                                ui.notify('ℹ️ Aucune réflexion en cours', type='info', position='top')
                                                    except Exception as e:
                                                        print(f"[STOP-BTN] ❌ Erreur arrêt: {e}")
                                                        ui.notify('❌ Erreur lors de l\'arrêt', type='negative', position='top')

                                                ui.button('⏹', on_click=_stop_reflection_now).props('flat dense size=xs').style('''
                                                    background: transparent;
                                                    color: rgba(255, 140, 0, 0.7);
                                                    min-width: 20px;
                                                    padding: 2px 6px;
                                                    opacity: 0.6;
                                                    font-size: 14px;
                                                ''').tooltip('Arrêter la réflexion')

                                        ui.html(parsed_introspection.replace('\n', '<br>')).style(
                                            'color: rgba(255, 255, 255, 0.8); '
                                            'font-size: 12px; '
                                            'font-style: italic; '
                                            'line-height: 1.4;'
                                        )
                                        
                                    if main_content:
                                        ui.html(main_content.replace('\n', '<br>'))
                        
                        # Ajouter aux deux historiques
                        msg = {'role': 'assistant', 'content': introspection_content}
                        _chat_history.append(msg)
                        _chat_history_ui.append(msg)
                        print(f"[SUBCONSCIENCE] OK Message {original_role} affiché dans déroulé séparé")
                
            except Exception as e:
                print(f"[SUBCONSCIENCE] WARN Erreur traitement message: {e}")
                
    except ImportError as e:
        # Extension Subconscience pas disponible - pas d'erreur
        pass
    except Exception as e:
        print(f"[SUBCONSCIENCE-TIMER] ERROR Erreur traitement messages: {e}")
        import traceback
        traceback.print_exc()


def _on_synthesis_ready(synthesis_text: str):
    """Callback pour afficher la synthèse de réflexion dans l'UI principale"""
    global _chat_inner
    print(f"[COGNITIVE-MIRROR] 📝 Réception synthèse ({len(synthesis_text)} chars)")

    try:
        if _chat_inner is not None:
            with _chat_inner:
                _message('assistant', synthesis_text)
                print("[COGNITIVE-MIRROR] ✅ Synthèse affichée dans chat principal")
        else:
            print("[COGNITIVE-MIRROR] ⚠️ Chat inner non disponible - synthèse non affichée")
    except Exception as e:
        print(f"[COGNITIVE-MIRROR] ❌ Erreur affichage synthèse: {e}")

async def _on_introspection_message_callback(role: str, content: str):
    """Callback pour affichage temps réel des messages d'introspection"""
    global _introspection_md_widget, _introspection_box_content
    
    try:
        print(f"[INTROSPECTION-CALLBACK] 📝 Nouveau message {role}: {content[:50]}...")
        
        if _introspection_md_widget is not None:
            # Ajouter le nouveau message au buffer
            if role == "analysis":
                # ÉTAPE 1: Analyse initiale
                formatted_message = f"📋 **ÉTAPE 1 - Analyse Initiale**\nIA Principale: {content}\n\n"
            elif role == "main_ai":
                # IA Principale dans le dialogue
                formatted_message = f"**IA Principale:** {content}\n\n"
            elif role == "archiviste":
                # Réponse Archiviste
                formatted_message = f"**Archiviste:** {content}\n\n"
            else:
                formatted_message = f"**{role.title()}:** {content}\n\n"
            
            _introspection_box_content.append(formatted_message)
            
            # Mettre à jour l'affichage
            full_content = "".join(_introspection_box_content)
            _introspection_md_widget.content = full_content
            print(f"[INTROSPECTION-CALLBACK] ✅ Affichage mis à jour ({len(_introspection_box_content)} messages)")
        
    except Exception as e:
        print(f"[INTROSPECTION-CALLBACK] ❌ Erreur affichage: {e}")


async def _on_message_ready(role: str, content: str):
    """Callback pour afficher un nouveau message d'introspection en temps réel"""
    global _introspection_box_content, _introspection_md_widget

    try:
        # Ajouter au buffer
        _introspection_box_content.append({"role": role, "content": content})

        # Formater le contenu selon les 5 étapes v2.0
        formatted_lines = []
        
        # Séparer les messages par type pour affichage structuré
        analysis_msg = None
        dialogue_msgs = []
        synthesis_msg = None
        
        for msg in _introspection_box_content:
            if msg["role"] == "analysis":
                analysis_msg = msg
            elif msg["role"] in ["main_ai", "archiviste"]:
                dialogue_msgs.append(msg)
            elif msg["role"] == "synthesis":
                synthesis_msg = msg

        # Analyse initiale (sans titre d'étape)
        if analysis_msg:
            formatted_lines.append("**IA Principale :**")
            formatted_lines.append(f"{analysis_msg['content']}")
            formatted_lines.append("")  # Saut de ligne

        # Dialogue (sans titre d'étape, formatage naturel)
        if dialogue_msgs:
            current_speaker = None
            for msg in dialogue_msgs:
                speaker = "**IA Principale :**" if msg["role"] == "main_ai" else "**Archiviste :**"
                
                # Saut de ligne entre différents intervenants
                if current_speaker and current_speaker != speaker:
                    formatted_lines.append("")
                
                formatted_lines.append(speaker)
                formatted_lines.append(f"{msg['content']}")
                formatted_lines.append("")  # Saut de ligne après chaque intervention
                current_speaker = speaker

        # Synthèse finale (sans titre d'étape)
        if synthesis_msg:
            if dialogue_msgs or analysis_msg:  # Saut supplémentaire avant synthèse
                formatted_lines.append("---")
                formatted_lines.append("")
            formatted_lines.append("**IA Principale :**")
            formatted_lines.append(f"{synthesis_msg['content']}")
            formatted_lines.append("")

        # Note: ÉTAPE 5 (réponse utilisateur) va maintenant dans la conversation principale uniquement
        
        full_content = "\n".join(formatted_lines)

        # Mettre à jour le widget si disponible
        if _introspection_md_widget:
            _introspection_md_widget.set_content(full_content)
            print(f"[INTROSPECTION] 💬 Message {role} affiché")
        else:
            print(f"[INTROSPECTION] ⚠️ Widget markdown non disponible")

    except Exception as e:
        print(f"[INTROSPECTION] ❌ Erreur affichage message: {e}")


def _ensure_cognitive_mirror():
    """Initialise l'extension Cognitive Mirror pour transparence cognitive."""
    global _cognitive_mirror
    if _cognitive_mirror is not None:
        return _cognitive_mirror
    
    if not COGNITIVE_MIRROR_AVAILABLE:
        print("[OGMA] WARN Cognitive Mirror non disponible")
        return None
    
    try:
        # Vérifier dépendances OGMA requises
        print("[COGNITIVE-MIRROR] 🔄 Vérification des dépendances...")
        chat_controller = _ensure_chat_controller()
        archiviste_controller = _ensure_archiviste_controller()
        memory_manager = _ensure_memory_manager()
        
        print(f"[COGNITIVE-MIRROR] Dépendances:")
        print(f"  - chat_controller: {type(chat_controller) if chat_controller else None}")
        print(f"  - archiviste_controller: {type(archiviste_controller) if archiviste_controller else None}")
        print(f"  - memory_manager: {type(memory_manager) if memory_manager else None}")
        
        if not all([chat_controller, archiviste_controller, memory_manager]):
            missing = []
            if not chat_controller: missing.append("chat_controller")
            if not archiviste_controller: missing.append("archiviste_controller")  
            if not memory_manager: missing.append("memory_manager")
            error_msg = f"Dépendances OGMA manquantes pour Cognitive Mirror: {missing}"
            print(f"[COGNITIVE-MIRROR] ❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Initialisation extension v2.0
        print("[COGNITIVE-MIRROR] 🚀 Initialisation extension v2.0...")
        success = initialize_cognitive_mirror(
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            ui_container=None  # Sera fourni lors création interface
        )
        
        print(f"[COGNITIVE-MIRROR] Résultat initialisation: {success}")
        
        if success:
            _cognitive_mirror = get_cognitive_mirror()
            print(f"[COGNITIVE-MIRROR] Instance récupérée: {type(_cognitive_mirror) if _cognitive_mirror else None}")
            
            # Configurer les callbacks v2.0 pour affichage temps réel
            if _cognitive_mirror and hasattr(_cognitive_mirror, 'on_message_ready'):
                _cognitive_mirror.on_message_ready = _on_introspection_message_callback
                print("[COGNITIVE-MIRROR] ✅ Callback affichage temps réel configuré")
            
            # Configurer autres callbacks si nécessaires (legacy)
            if _cognitive_mirror and hasattr(_cognitive_mirror, 'set_callbacks'):
                _cognitive_mirror.set_callbacks(
                    on_state_change=None,  # Optionnel pour l'instant
                    on_reflection_start=None,  # Optionnel
                    on_reflection_end=None,  # Optionnel
                    on_external_settings_change=_handle_cognitive_mirror_callback,
                    on_synthesis_ready=_on_synthesis_ready,  # Affichage synthèse
                    on_message_ready=_on_message_ready  # NOUVEAU: Affichage messages temps réel
                )
            
            print("[OGMA] BRAIN Cognitive Mirror initialisé avec callbacks")
            
            # DIAGNOSTIC DÉMARRAGE - Vérifier l'état initial
            print("🚨 [DIAGNOSTIC-DÉMARRAGE] État extension après initialisation:")
            print(f"   Type: {type(_cognitive_mirror)}")
            print(f"   ID: {id(_cognitive_mirror)}")
            print(f"   is_enabled: {_cognitive_mirror.is_enabled}")
            
            # Comparer avec l'instance globale de l'extension
            from extensions.cognitive_mirror import get_introspection_core
            global_core = get_introspection_core()
            if global_core:
                print(f"   Instance globale ID: {id(global_core)}")
                print(f"   Instance globale is_enabled: {global_core.is_enabled}")
                print(f"   Même instance? {_cognitive_mirror is global_core}")
                if hasattr(global_core, 'parameters'):
                    ext_enabled = global_core.parameters.get('extension_enabled', 'NOT_FOUND')
                    print(f"   Paramètre extension_enabled: {ext_enabled}")
        else:
            print("[OGMA] ERROR Échec initialisation Cognitive Mirror")
            _cognitive_mirror = None
        
    except Exception as e:
        print(f"[OGMA] WARN Erreur initialisation Cognitive Mirror: {e}")
        _cognitive_mirror = None
    
    return _cognitive_mirror


def _ensure_chat_controller() -> AIController:
    global _chat_controller
    _ensure_backends()
    sm = _ensure_settings_manager()
    if _chat_controller is None:
        _chat_controller = AIController('chat', cast(OllamaManager, _ollama_mgr), cast(GGUFManager, _gguf_mgr), cast(KoboldManager, _kobold_mgr))
    chat = sm.settings.get('chat_api', {})
    backend = chat.get('backend_type', 'API')
    # Mapper GGUF vers l’identifiant attendu par le contrôleur
    ctrl_backend = 'GGUF/llama.cpp' if backend == 'GGUF' else backend
    _chat_controller.set_active_backend(ctrl_backend)
    
    # Gestion des valeurs -1 pour auto-detect avec vraies capacités modèle
    max_tokens = chat.get('max_tokens', 512)
    context_length = chat.get('context_length', 4096)
    
    # SYSTÈME HYBRIDE: API + spécifications officielles pour auto-détection optimale
    if max_tokens == -1 or context_length == -1:
        try:
            from hybrid_detection import hybrid_auto_detect_capabilities
            provider = chat.get('provider', 'Aucun').lower()
            model = chat.get('api_model', '') or chat.get('model', '')
            api_key = chat.get('api_key', '')
            
            if provider != 'aucun' and model and api_key:
                print(f"[CHAT-HYBRID] � Détection hybride {provider}")
                detected_caps = hybrid_auto_detect_capabilities(provider, model, "chat", api_key)
                if max_tokens == -1:
                    max_tokens = detected_caps['max_tokens']
                    print(f"[CHAT-HYBRID] OK max_tokens optimal: {max_tokens:,}")
                if context_length == -1:
                    context_length = detected_caps['context_length']
                    print(f"[CHAT-HYBRID] OK context_length optimal: {context_length:,}")
            else:
                # Fallback si pas de configuration complète
                if max_tokens == -1:
                    max_tokens = 512
                if context_length == -1:
                    context_length = 4096
                print(f"[CHAT-HYBRID] WARN Configuration incomplète, utilisation valeurs par défaut")
        except Exception as e:
            # Fallback en cas d'erreur
            if max_tokens == -1:
                max_tokens = 512
            if context_length == -1:
                context_length = 4096
            print(f"[CHAT-HYBRID] ERROR Erreur détection hybride: {e}, utilisation valeurs par défaut")
    
    # Paramètres généraux
    _chat_controller.max_tokens = int(max_tokens)
    _chat_controller.context_length = int(context_length)
    _chat_controller.temperature = float(chat.get('temperature', 0.7))
    # Configuration selon backend
    if backend == 'API':
        provider = chat.get('provider', 'Aucun')
        api_key = chat.get('api_key', '')
        model = chat.get('api_model', '') or chat.get('model', '')  # Fallback pour compatibilité config.json
        _chat_controller.api_manager.configure(provider, api_key, model)
    elif backend == 'Ollama':
        # Config URL + modèles
        url = chat.get('ollama_url') or 'http://localhost:11434'
        cast(OllamaManager, _ollama_mgr).api_url = str(url).rstrip('/')
        cast(OllamaManager, _ollama_mgr).check_service()
        _chat_controller.ollama_model = chat.get('ollama_model', '')
    elif backend == 'GGUF':
        # Charger le modèle si nécessaire
        model = chat.get('gguf_model', '')
        # Utiliser la config other_backends.gguf au lieu de gguf_settings
        gguf_cfg = sm.settings.get('other_backends', {}).get('gguf', {})
        n_gpu_layers = int(gguf_cfg.get('gpu_layers', -1))
        context_size = int(gguf_cfg.get('context_size', 4096))
        ctx = context_size if context_size > 0 else _chat_controller.context_length
        if model:
            print(f"[AI] TARGET Chargement modèle GGUF: {model}")
            print(f"[AI] ⚙️ GPU layers: {n_gpu_layers}, Context: {ctx}")
            try:
                # Forcer le chargement du modèle même s'il semble disponible
                import time
                start_time = time.time()
                cast(GGUFManager, _gguf_mgr).load_model(model, ctx, n_gpu_layers)
                load_time = time.time() - start_time
                print(f"[AI] OK Modèle GGUF chargé en {load_time:.1f}s")
            except Exception as e:
                print(f"[AI] ERROR Erreur chargement GGUF: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[AI] WARN Aucun modèle GGUF configuré")
    elif backend == 'KoboldCpp':
        url = chat.get('kobold_url') or 'http://localhost:5001'
        cast(KoboldManager, _kobold_mgr).api_url = str(url).rstrip('/')
        cast(KoboldManager, _kobold_mgr).check_service()
    return _chat_controller

def _ensure_archiviste_controller() -> AIController:
    """Retourne le contrôleur Archiviste initialisé"""
    global _archiviste_controller
    _ensure_backends()
    sm = _ensure_settings_manager()
    if _archiviste_controller is None:
        _archiviste_controller = AIController('archiviste', cast(OllamaManager, _ollama_mgr), cast(GGUFManager, _gguf_mgr), cast(KoboldManager, _kobold_mgr))
        
        # Configuration basée sur reasoning_api dans settings
        arch = sm.settings.get('reasoning_api', {})
        arch_backend = arch.get('backend_type', 'API')
        ctrl_backend = 'GGUF/llama.cpp' if arch_backend == 'GGUF' else arch_backend
        _archiviste_controller.set_active_backend(ctrl_backend)
        
        # Configuration des paramètres
        max_tokens = arch.get('max_tokens', 2048)
        context_length = arch.get('context_length', 8192)
        _archiviste_controller.max_tokens = int(max_tokens)
        _archiviste_controller.context_length = int(context_length)
        _archiviste_controller.temperature = float(arch.get('temperature', 0.7))
        
        # Configuration API si disponible
        if arch_backend == 'API':
            _archiviste_controller.api_manager.configure(
                arch.get('provider', ''),
                arch.get('api_key', ''),
                arch.get('api_model', '')
            )
    
    return _archiviste_controller


def _notify_safe(message: str, type: str = 'info') -> None:
    """Tente d'afficher une notification; ignore si hors contexte UI (timer/task)."""
    try:
        ui.notify(message, type=type)
    except Exception:
        # Hors slot (timer/task): ignorer la notif, ce n'est pas critique
        pass


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
    global _file_tab_container, _active_file_data
    if _file_tab_container is None:
        return
    
    try:
        _file_tab_container.clear()
        
        with _file_tab_container:
            if _active_file_data:
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

def _remove_active_file():
    """Supprime le fichier actif et met à jour l'affichage"""
    global _active_file_data
    _active_file_data = None
    _update_file_tab_display()  # Met à jour l'onglet sous la messagerie
    try:
        ui.notify('Fichier supprimé de la conversation', type='info')
    except:
        print('[INFO] Fichier supprimé de la conversation')

async def _process_uploaded_file(upload_event):
    """Traite un fichier uploadé et l'active dans la conversation"""
    global _active_file_data
    
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
            _active_file_data = file_data
            _update_file_tab_display()  # Affiche l'onglet sous la messagerie
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

def _handle_upload_and_close(upload_event, dialog):
    """Traite l'upload et ferme le dialog"""
    asyncio.create_task(_process_uploaded_file_and_close(upload_event, dialog))

async def _process_uploaded_file_and_close(upload_event, dialog):
    """Traite l'upload de façon asynchrone et ferme le dialog"""
    await _process_uploaded_file(upload_event)
    dialog.close()

# JOURNAL DE BORD EXTENSION - Variables globales
_journal_instance = None
_journal_available = False

# BIOGRAPHIE PROFIL EXTENSION - Variables globales
_biography_manager = None
_biography_ui = None
_biography_available = False

def _initialize_biography_extension():
    """Initialise l'extension Biographie Profil si disponible"""
    global _biography_manager, _biography_ui, _biography_available, _memory_manager, _chat_controller

    print(f"[DEBUG-BIOGRAPHY-INIT] === DÉBUT INITIALISATION ===")
    print(f"[DEBUG-BIOGRAPHY-INIT] BIOGRAPHY_EXTENSION_AVAILABLE = {BIOGRAPHY_EXTENSION_AVAILABLE}")

    if not BIOGRAPHY_EXTENSION_AVAILABLE:
        print("[BIOGRAPHY-EXTENSION] ❌ Extension non disponible")
        return

    try:
        print("[DEBUG-BIOGRAPHY-INIT] Extension disponible, initialisation...")
        # Utiliser _ensure_settings_manager() comme dans le reste d'OGMA
        sm = _ensure_settings_manager()
        print(f"[DEBUG-BIOGRAPHY-INIT] Settings manager: {type(sm)}")
        print(f"[DEBUG-BIOGRAPHY-INIT] Memory manager: {type(_memory_manager)}")
        print(f"[DEBUG-BIOGRAPHY-INIT] Chat controller: {type(_chat_controller)}")

        success = initialize_biography_extension(sm, _memory_manager, _chat_controller)
        print(f"[DEBUG-BIOGRAPHY-INIT] initialize_biography_extension() retourne: {success}")

        if success:
            _biography_available = True
            from extensions.biographie_profil import get_biography_manager, get_biography_ui
            _biography_manager = get_biography_manager()
            _biography_ui = get_biography_ui()
            print(f"[DEBUG-BIOGRAPHY-INIT] _biography_manager: {type(_biography_manager)}")
            print(f"[DEBUG-BIOGRAPHY-INIT] _biography_ui: {type(_biography_ui)}")
            print("[BIOGRAPHY-EXTENSION] ✅ Extension biographie_profil initialisée")
        else:
            print("[BIOGRAPHY-EXTENSION] ❌ Échec initialisation extension")

        print(f"[DEBUG-BIOGRAPHY-INIT] _biography_available = {_biography_available}")
        print(f"[DEBUG-BIOGRAPHY-INIT] === FIN INITIALISATION ===")

    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ❌ Erreur initialisation: {e}")
        import traceback
        traceback.print_exc()

def _initialize_journal_extension():
    """Initialise l'extension Journal de Bord si disponible"""
    global _journal_instance, _journal_available, _archiviste_controller

    try:
        # Import extension journal
        from extensions.journal_de_bord import initialize_journal, is_available

        # Vérifier si déjà initialisé
        if is_available():
            _journal_available = True
            print("[JOURNAL-EXTENSION] OK Deja initialise et disponible")
            return True

        # Tentative d'initialisation (même sans Archiviste pour l'instant)
        print("[JOURNAL-EXTENSION] Tentative d'initialisation...")

        # Création d'un mock archiviste si pas disponible
        archiviste_to_use = _archiviste_controller
        if not archiviste_to_use:
            print("[JOURNAL-EXTENSION] Archiviste non disponible - mode degrade")
            # Créer un mock simple pour permettre l'initialisation
            class MockArchiviste:
                def call_chat_api(self, *args, **kwargs):
                    return "Résumé automatique indisponible (Archiviste non configuré)"
            archiviste_to_use = MockArchiviste()

        success = initialize_journal(
            archiviste_controller=archiviste_to_use,
            memory_manager=_memory_manager
        )

        if success:
            _journal_available = True
            print("[JOURNAL-EXTENSION] OK Extension initialisee avec succes")
            return True
        else:
            print("[JOURNAL-EXTENSION] ERREUR Echec initialisation")
            return False

    except ImportError as e:
        print(f"[JOURNAL-EXTENSION] ERREUR Extension non disponible: {e}")
        return False
    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERREUR initialisation: {e}")
        return False

def _inject_journal_header_button():
    """Injecte le bouton journal dans le header"""
    global _journal_available

    try:
        # Tentative d'initialisation si pas encore fait
        if not _journal_available:
            _initialize_journal_extension()

        # Si journal disponible, injecter bouton
        if _journal_available:
            from extensions.journal_de_bord import get_journal, open_journal_ui

            # Bouton journal dans le style OGMA
            ui.button(
                "JOURNAL Journal",
                on_click=lambda: open_journal_ui()
            ).classes(
                "journal-header-button bg-orange-600 hover:bg-orange-700 "
                "text-white font-medium px-3 py-2 rounded-md transition-all "
                "duration-200 shadow-sm hover:shadow-md"
            ).props('dense').style(
                "font-size: 14px; margin-left: 16px; "
                "background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); "
                "border: 1px solid #A0522D;"
            ).tooltip("Journal de Bord - Capturer et consulter vos conversations")

            print("[JOURNAL-EXTENSION] OK Bouton header injecté")
        else:
            print("[JOURNAL-EXTENSION] WARN Extension non disponible - bouton non injecté")

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur injection bouton: {e}")

def _inject_journal_context():
    """Injecte le contexte matinal en début de conversation"""
    global _journal_available

    try:
        # Forcer l'initialisation si pas encore disponible
        if not _journal_available:
            print("[JOURNAL-EXTENSION] Extension pas disponible - tentative initialisation...")
            _initialize_journal_extension()

        if _journal_available:
            from extensions.journal_de_bord import hook_conversation_start
            context = hook_conversation_start()

            if context:
                print("[JOURNAL-EXTENSION] JOURNAL Contexte matinal injecté")
                return context

        return ""

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur injection contexte: {e}")
        return ""

def _create_header_journal_button():
    """Crée le bouton journal flottant dans le header principal"""
    global _journal_available

    try:
        # Tentative d'initialisation si pas encore fait
        if not _journal_available:
            _initialize_journal_extension()

        # Si journal disponible, créer bouton flottant
        if _journal_available:
            with ui.element('div').style('position: fixed; top: 20px; left: 20px; z-index: 1000;'):
                with ui.button().classes('journal-floating-btn').props('title="Journal de Bord"').style(
                    'width: 50px; height: 50px; border-radius: 50%; '
                    'background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); '
                    'border: 2px solid #A0522D; box-shadow: 0 4px 12px rgba(139, 90, 43, 0.3); '
                    'display: flex; align-items: center; justify-content: center; '
                    'transition: all 0.3s ease; cursor: pointer; padding: 0;'
                ) as journal_btn:
                    # Icône livre ouvert
                    ui.html('<span style="font-size: 24px; color: white; font-weight: bold;">J</span>')

                def open_journal():
                    try:
                        from extensions.journal_de_bord import open_journal_ui
                        open_journal_ui()
                        print("[JOURNAL-EXTENSION] JOURNAL Modal journal ouvert depuis bouton header")
                    except Exception as e:
                        print(f"[JOURNAL-EXTENSION] ERROR Erreur ouverture modal: {e}")

                journal_btn.on('click', open_journal)

                # Style hover CSS
                ui.add_head_html("""
                <style>
                .journal-floating-btn:hover {
                    transform: translateY(-2px) scale(1.05);
                    box-shadow: 0 6px 20px rgba(139, 90, 43, 0.4);
                }
                </style>
                """)

            print("[JOURNAL-EXTENSION] OK Bouton journal flottant cree")
        else:
            print("[JOURNAL-EXTENSION] WARN Extension non disponible - bouton flottant non cree")

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur creation bouton flottant: {e}")

def _create_header_journal_button_inline():
    """Crée le bouton journal intégré dans le conteneur header"""
    global _journal_available

    try:
        # Tentative d'initialisation si pas encore fait
        if not _journal_available:
            _initialize_journal_extension()

        # Si journal disponible, créer bouton inline
        if _journal_available:
            with ui.button().classes('journal-header-btn').props('title="Journal de Bord"').style(
                'width: 50px; height: 50px; border-radius: 50%; '
                'background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); '
                'border: 2px solid #A0522D; box-shadow: 0 4px 12px rgba(139, 90, 43, 0.3); '
                'display: flex; align-items: center; justify-content: center; '
                'transition: all 0.3s ease; cursor: pointer; padding: 0; '
                'flex-shrink: 0; min-width: 50px; min-height: 50px; max-width: 50px; max-height: 50px;'
            ) as journal_btn:
                # Icône livre ouvert (sans emoji Unicode)
                ui.html('<span style="font-size: 20px; color: white; font-weight: bold;">J</span>')

                def open_journal():
                    try:
                        from extensions.journal_de_bord import open_journal_ui
                        open_journal_ui()
                        print("[JOURNAL-EXTENSION] JOURNAL Modal journal ouvert depuis bouton header")
                    except Exception as e:
                        print(f"[JOURNAL-EXTENSION] ERROR Erreur ouverture modal: {e}")

                journal_btn.on('click', open_journal)

            print("[OGMA-NG] OK Bouton journal cree dans header")
        else:
            print("[OGMA-NG] WARN Journal non disponible - bouton non cree")

    except Exception as e:
        print(f"[OGMA-NG] ERROR Erreur creation bouton journal: {e}")

def _create_header_biography_button_inline():
    """Crée le bouton biographie profil intégré dans le conteneur header - Pattern Journal"""
    global _biography_available

    try:
        print(f"[DEBUG-BIOGRAPHY-BUTTON] === DÉBUT CRÉATION BOUTON ===")
        print(f"[DEBUG-BIOGRAPHY-BUTTON] BIOGRAPHY_EXTENSION_AVAILABLE = {BIOGRAPHY_EXTENSION_AVAILABLE}")
        print(f"[DEBUG-BIOGRAPHY-BUTTON] _biography_available (initial) = {_biography_available}")

        # Tentative d'initialisation si pas encore fait
        if not _biography_available:
            print("[DEBUG-BIOGRAPHY-BUTTON] Initialisation nécessaire, appel _initialize_biography_extension()...")
            _initialize_biography_extension()
            print(f"[DEBUG-BIOGRAPHY-BUTTON] _biography_available (après init) = {_biography_available}")

        # Condition simplifiée comme journal de bord
        if _biography_available:
            print("[DEBUG-BIOGRAPHY-BUTTON] ✅ Extension disponible, création du bouton...")
            with ui.button().classes('biography-header-btn').props('title="Biographie Profil"').style(
                'width: 50px; height: 50px; border-radius: 50%; '
                'background: linear-gradient(135deg, #4A5568 0%, #718096 100%); '
                'border: 2px solid #2D3748; box-shadow: 0 4px 12px rgba(74, 85, 104, 0.3); '
                'display: flex; align-items: center; justify-content: center; '
                'transition: all 0.3s ease; cursor: pointer; padding: 0; margin-right: 10px; '
                'flex-shrink: 0; min-width: 50px; min-height: 50px; max-width: 50px; max-height: 50px;'
            ) as biography_btn:
                # Icône plume
                ui.html('<span style="font-size: 20px; color: white; font-weight: bold;">✒️</span>')

                # Callback simplifié avec import direct (pattern journal)
                def open_biography():
                    from extensions.biographie_profil import open_settings_modal
                    open_settings_modal()
                    print("[BIOGRAPHY-EXTENSION] Modal biographie ouvert depuis bouton header")

                biography_btn.on('click', open_biography)
            print("[OGMA-NG] ✅ Bouton biographie créé dans header")
        else:
            print("[DEBUG-BIOGRAPHY-BUTTON] ❌ Extension biographie NON disponible")

        print(f"[DEBUG-BIOGRAPHY-BUTTON] === FIN CRÉATION BOUTON ===")

    except Exception as e:
        print(f"[OGMA-NG] ERROR Erreur création bouton biographie: {e}")
        import traceback
        traceback.print_exc()

def _header():
    global _header_container, _ia_status_indicators
    print("[DEBUG-HEADER] Création du header...")

    with ui.element('div').classes('app-header'):
        # Container flex pour titre centré et indicateurs IA
        with ui.element('div').classes('header-content'):
            # [HEADER BUTTONS] Boutons à gauche - Version simplifiée
            with ui.element('div').style('display: flex; gap: 10px; align-items: center;'):
                print("[DEBUG-HEADER] Container boutons créé")

                # CRÉATION PRIORITAIRE DES BOUTONS BIOGRAPHIE/JOURNAL (DANS LE CONTAINER)
                print("[DEBUG-HEADER] === CRÉATION BOUTONS BIOGRAPHIE/JOURNAL ===")
                try:
                    print("[DEBUG-HEADER] Appel _create_header_biography_button_inline()...")
                    _create_header_biography_button_inline()
                    print("[DEBUG-HEADER] Bouton biographie OK")

                    print("[DEBUG-HEADER] Appel _create_header_journal_button_inline()...")
                    _create_header_journal_button_inline()
                    print("[DEBUG-HEADER] Bouton journal OK")
                except Exception as e:
                    print(f"[DEBUG-HEADER] ERROR création boutons biographie/journal: {e}")
                    import traceback
                    traceback.print_exc()

            # [ARCHI_SENSOR] Bouton Archi_sensor
            try:
                archi_sensor_overlay = _archi_sensor_modal()
                with ui.button().classes('archi-sensor-header-btn').props('title="Analyse Métacognitive"').style('padding: 0; border: none; overflow: hidden; width: 50px; height: 50px;') as archi_sensor_btn:
                    ui.html('<img src="/static/icotetes.png" style="width: 100%; height: 100%; object-fit: cover; display: block;" alt="Archi Sensor">')

                def toggle_archi_sensor():
                    archi_sensor_overlay.visible = not archi_sensor_overlay.visible
                    print(f"[ARCHI-SENSOR] Overlay {'affiché' if archi_sensor_overlay.visible else 'masqué'}")

                archi_sensor_btn.on('click', toggle_archi_sensor)
            except Exception as e:
                print(f"[DEBUG-HEADER] ERROR création archi_sensor: {e}")

            _header_container = ui.element('div').classes('header-title-container')
            with _header_container:
                # Titre supprimé pour économiser l'espace header
                pass
            
            # Indicateurs d'état IA dans le header
            with ui.element('div').classes('ia-status-container').style('display: flex; align-items: center; gap: 16px; margin-left: auto; margin-right: 16px;'):
                # IA PRINCIPALE (Chat)
                with ui.element('div').classes('ia-status-item').style('display: flex; align-items: center; gap: 6px;'):
                    _ia_status_indicators['chat_dot'] = _status_dot(initial='#dc2626')  # Rouge par défaut
                    with ui.element('div').style('display: flex; flex-direction: column; font-size: 12px;'):
                        ui.label('IA PRINCIPALE').classes('text-xs font-semibold').style('color: var(--text-primary); margin: 0; line-height: 1.2;')
                        _ia_status_indicators['chat_model'] = ui.label('Aucun modèle').classes('text-xs').style('color: var(--text-muted); margin: 0; line-height: 1.2;')

                # ARCHIVISTE
                with ui.element('div').classes('ia-status-item').style('display: flex; align-items: center; gap: 6px;'):
                    _ia_status_indicators['archiviste_dot'] = _status_dot(initial='#dc2626')  # Rouge par défaut
                    with ui.element('div').style('display: flex; flex-direction: column; font-size: 12px;'):
                        ui.label('ARCHIVISTE').classes('text-xs font-semibold').style('color: var(--text-primary); margin: 0; line-height: 1.2;')
                        _ia_status_indicators['archiviste_model'] = ui.label('Aucun modèle').classes('text-xs').style('color: var(--text-muted); margin: 0; line-height: 1.2;')

                # IA EMBED
                with ui.element('div').classes('ia-status-item').style('display: flex; align-items: center; gap: 6px;'):
                    _ia_status_indicators['embeddings_dot'] = _status_dot(initial='#dc2626')  # Rouge par défaut
                    with ui.element('div').style('display: flex; flex-direction: column; font-size: 12px;'):
                        ui.label('IA EMBED').classes('text-xs font-semibold').style('color: var(--text-primary); margin: 0; line-height: 1.2;')
                        _ia_status_indicators['embeddings_model'] = ui.label('Aucun modèle').classes('text-xs').style('color: var(--text-muted); margin: 0; line-height: 1.2;')
    
    # [BOUTONS HEADER] Les boutons sont maintenant intégrés directement dans le header principal




# Variable globale pour stocker l'index du message en cours d'édition
_editing_message_index = None































# NOTA: _format_datetime extrait vers utils/formatting_utils.py
# NOTA: _parse_thinking_format extrait vers utils/message_parsers.py
# NOTA: _parse_introspection_format extrait vers utils/message_parsers.py



# ==============================================================================
# MÉMORISATION DES CONVERSATIONS
# ==============================================================================





















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
                global _audio_manager
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['enabled'] = e.value
                sm.save_settings()
                
                if _audio_manager and hasattr(_audio_manager, 'set_tts_settings'):
                    _audio_manager.set_tts_settings(enabled=e.value)
                
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
                    global _audio_manager
                    if _audio_manager:
                        _audio_manager.configure_tts_engine(e.value)
                    
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












async def _send_chat_message(input_el=None, text_override: Optional[str] = None, skip_history_append: bool = False):
    global _chat_history, _chat_history_ui, _chat_inner, _pending_notifications, _editing_message_index, _pending_behavioral_injections, _journal_preformed_response
    import re  # Import au début pour éviter UnboundLocalError
    
    # 🚨 DÉDUPLICATION: Réinitialiser la session si c'est un nouveau chat
    if not _chat_history:
        reset_deduplication_session()
        print(f"[DEDUP] 🔄 Session de déduplication réinitialisée")

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

    # Variable pour stocker l'injection biographique
    biography_injection_content = None
    is_automatic_introspection = False

    # 🧠 INTROSPECTION v2.0: Vérification mode automatique (ALWAYS)
    try:
        if COGNITIVE_MIRROR_AVAILABLE:
            from extensions.cognitive_mirror import get_introspection, is_enabled
            
            if is_enabled():
                introspection_core = get_introspection()
                if introspection_core and hasattr(introspection_core, 'config'):
                    # Vérifier si mode "always" activé
                    mode = introspection_core.config.get('introspection_mode', 'on_demand')
                    if mode == 'always':
                        print("[INTROSPECTION] 🔄 Mode ALWAYS détecté - déclenchement automatique")
                        
                        # Déclencher introspection automatique pour ce message
                        # (sera traité plus loin dans le flux)
                        is_automatic_introspection = True
                    else:
                        is_automatic_introspection = False
                else:
                    is_automatic_introspection = False
            else:
                is_automatic_introspection = False
        else:
            is_automatic_introspection = False
    except Exception as e:
        print(f"[INTROSPECTION] ❌ Erreur vérification mode automatique: {e}")
        is_automatic_introspection = False

    # JOURNAL JOURNAL DE BORD: Détection phrases magiques
    print(f"[SEND-CHAT-DEBUG] Section journal: _journal_available = {_journal_available}")
    try:
        if _journal_available:
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
                    global _journal_preformed_response
                    _journal_preformed_response = magic_response
                    print(f"[JOURNAL-EXTENSION] REDIRECT Réponse sauvegardée pour injection IA")
                    
                    # Continuer le flux normal mais avec réponse prédéfinie
                    # La réponse sera injectée plus tard dans le processus

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur traitement phrase magique: {e}")

    # 📖 BIOGRAPHIE PROFIL: Détection phrases magiques et injection automatique
    print(f"[BIOGRAPHY-DEBUG] Début détection phrase magique pour: '{text}'")
    print(f"[BIOGRAPHY-DEBUG] _biography_available = {_biography_available}")
    try:
        if _biography_available:
            print(f"[BIOGRAPHY-DEBUG] Extension disponible, import...")
            from extensions.biographie_profil import get_biography_magic_phrases
            biography_magic = get_biography_magic_phrases()
            print(f"[BIOGRAPHY-DEBUG] biography_magic = {biography_magic}")

            if biography_magic:
                print(f"[BIOGRAPHY-DEBUG] Appel handle_magic_phrases...")
                # Vérifier si c'est une phrase magique utilisateur (mise à jour)
                magic_response = await biography_magic.handle_magic_phrases(text, is_ai_message=False)
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
                        print(f"[BIOGRAPHY-EXTENSION] 🔄 Injection automatique biographie - ajout au contexte")
                        # Stocker le contenu pour injection dans le contexte IA
                        biography_injection_content = content

    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ERROR Erreur traitement phrase magique: {e}")

    # 🧠 COGNITIVE MIRROR v2.0: Détection déclenchement introspection
    try:
        print(f"[INTROSPECTION] 🔍 Vérification: '{text[:50]}...' (auto={is_automatic_introspection})")

        if COGNITIVE_MIRROR_AVAILABLE:
            from extensions.cognitive_mirror import is_enabled
            
            if is_enabled():
                # Phrases magiques d'introspection (utilisateur)
                introspection_patterns = [
                    r"il\s+faut\s+que\s+tu\s+réfléchisses",
                    r"lance\s+(?:une\s+)?introspection",
                    r"déclenche\s+(?:une\s+)?introspection",
                    r"réfléchis\s+en\s+profondeur"
                ]

                is_magic_phrase_trigger = any(re.search(pattern, text, re.IGNORECASE) for pattern in introspection_patterns)
                
                # Déclenchement si phrase magique OU mode automatique
                is_introspection_trigger = is_magic_phrase_trigger or is_automatic_introspection

                if is_introspection_trigger:
                    trigger_type = "phrase magique" if is_magic_phrase_trigger else "mode automatique"
                    print(f"[INTROSPECTION] 🧠 Déclenchement par {trigger_type} - mode introspection v2")

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
                    from utils import get_ego_prompt
                    
                    # Récupérer ego prompt actuel
                    try:
                        current_ego_prompt = get_ego_prompt()
                    except:
                        current_ego_prompt = "Ego prompt non disponible"
                    
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
                        with ui.expansion().classes('thinking-expansion') as introspection_box:
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

                    # 6. Lancer introspection v2.0 (callbacks affichent messages)
                    try:
                        # Utiliser nouvelle API v2.0
                        from extensions.cognitive_mirror import get_introspection
                        introspection_core = get_introspection()
                        
                        if introspection_core:
                            introspection_result = await introspection_core.trigger_introspection_sync(
                                user_message=text,
                                conversation_context=conversation_context
                            )
                        else:
                            print("[INTROSPECTION] ❌ Core v2.0 non disponible")
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

                    return  # ← NE PAS CONTINUER vers génération Luna normale

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
                    _message('system', "🛑 **Réflexion interrompue** - Luna arrête sa phase d'introspection sur demande utilisateur")
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
    temporal_final_alert = None
    temporal_context_enriched = None
    
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
            print(f"🚨 [DEBUG] Extension activée: {cognitive_mirror.is_enabled}")
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
                print(f"🚨 [DEBUG] Instance globale is_enabled: {global_core.is_enabled}")
                print(f"🚨 [DEBUG] Même instance? {cognitive_mirror is global_core}")
                if hasattr(global_core, 'parameters'):
                    global_ext_enabled = global_core.parameters.get('extension_enabled', 'NOT_FOUND')
                    print(f"🚨 [DEBUG] Instance globale extension_enabled: {global_ext_enabled}")
            
            # v2.0: Plus de détection d'inactivité automatique
            # L'introspection se déclenche seulement par phrases magiques ou mode always
            if cognitive_mirror.is_enabled:
                print("[COGNITIVE-MIRROR] OK Extension v2.0 active - déclenchement à la demande")
            else:
                print("🚨 [DEBUG] Extension OFF - pas de traitement introspection")
        else:
            print("🚨 [DEBUG] Extension non trouvée")
    except Exception as e:
        print(f"[COGNITIVE-MIRROR] ERROR Erreur hook utilisateur: {e}")
        import traceback
        traceback.print_exc()
    
    # Ajout à l'historique et rendu UI
    # Détection "phrase magique" côté utilisateur et mémorisation
    def _extract_magic_memories(s: str) -> List[str]:
        if not s:
            return []
        # Variantes supportées:
        # - "il faut que je me souvienne de ça: ..."
        # - "mémorise ça: ..." / "memorise ca: ..." / "mémorises ça: ..."
        patterns = [
            r"il\s*faut\s*que\s*je\s*me\s*souvienne\s*de\s*(?:ça|ca)\s*[:\-]\s*(.+?)\s*(?=$|\n|\r)",
            r"m[ée]morise(?:s)?\s*(?:ça|ca)\s*[:\-]\s*(.+?)\s*(?=$|\n|\r)",
        ]
        results: List[str] = []
        for pat in patterns:
            results.extend([m.strip() for m in re.findall(pat, s, flags=re.IGNORECASE)])
        return results

    def _strip_magic_phrases(s: str) -> str:
        if not s:
            return s
        pattern = (
            r"(?:"
            r"il\s*faut\s*que\s*je\s*me\s*souvienne\s*de\s*(?:ça|ca)\s*[:\-]\s*.+?(?=$|\n|\r)"
            r"|m[ée]morise(?:s)?\s*(?:ça|ca)\s*[:\-]\s*.+?(?=$|\n|\r)"
            r"|il\s+faut\s+que\s+je\s+(?:te\s+)?vois"
            r"|je\s+veux\s+te\s+voir"
            r"|je\s+n'ai\s+plus\s+besoin\s+de\s+te\s+voir"
            r"|je\s+(?:peux|vais)\s+arrêter\s+de\s+te\s+(?:voir|regarder)"
            r"|je\s+ferme\s+(?:ma\s+)?vision"
            r"|je\s+coupe\s+(?:ma\s+)?caméra"
            r")"
        )
        return re.sub(pattern, "", s, flags=re.IGNORECASE).strip()


    magic = _extract_magic_memories(text)
    user_memorized = False
    if magic:
        mem = _ensure_memory_manager()
        if mem is not None:
            for content in magic:
                try:
                    mem_id = f"usr-{uuid.uuid4()}"
                    ok = await mem.add_memory(mem_id, content)
                    if ok:
                        _notify_safe(f"SAVE Souvenir mémorisé: {content[:80]}...", 'positive')
                        _trigger_memory_update()
                        user_memorized = True
                    else:
                        _notify_safe("Échec de la mémorisation (voir logs)", 'warning')
                except Exception as e:
                    _notify_safe(f"Erreur mémorisation: {e}", 'warning')
    
        


    cleaned_text = _strip_magic_phrases(text) or text
    
    # Intégration du fichier actif et image perception dans le message
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

    # 📖 BIOGRAPHIE PROFIL: Injection automatique première mention + préparation context IA
    biography_context = ""
    try:
        if _biography_available:
            from extensions.biographie_profil import get_biography_magic_phrases
            biography_magic = get_biography_magic_phrases()

            if biography_magic:
                # Injection automatique pour l'IA (première mention de noms)
                auto_injection = biography_magic._handle_auto_detection(cleaned_text)
                if auto_injection:
                    biography_context = f"\n\n{auto_injection}"
                    print(f"[BIOGRAPHY-EXTENSION] 🎯 Injection automatique ajoutée au contexte IA")

    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ERROR Erreur injection automatique: {e}")

    # Ajouter le contexte biographique au message IA si disponible
    if biography_context:
        if isinstance(ai_content, list):
            # Multimodal: ajouter au texte du premier élément
            ai_content[0]["text"] += biography_context
        else:
            # Texte simple: ajouter directement
            ai_content += biography_context

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
                print(f"[MEMORY-FULLTEXT] JOURNAL Demande de textes intégraux détectée")
                synthesis, memories = await mem.retrieve_full_texts_context(text, k=5)
            else:
                print(f"[MEMORY-HYBRID-OPT] � Architecture hybride optimisée (2 directs + 3 archiviste + synthèse)")
                synthesis, memories = await mem.retrieve_hybrid_optimized(text, k=12)
            
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
                # 1. Afficher l'instruction temporelle si présente
                if temporal_final_alert:
                    temporal_display = f"🕒 **Instruction Temporelle Archiviste** ({len(temporal_final_alert)} chars)\n\n{temporal_final_alert}"
                    _message('system', temporal_display)
                    print(f"[DEBUG-INJECTION] OK Instruction temporelle affichée dans le chat")
                
                # 2. Afficher la synthèse de l'Archiviste
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
            if temporal_final_alert:
                ui.notify(f'🕒 Temporal: {temporal_final_alert[:100]}...', type='info')
            if context_note:
                ui.notify(f'BRAIN Archiviste: {context_note[:100]}...', type='info')
    elif show_injection:
        print(f"[DEBUG-INJECTION] PROBLÈME: _chat_inner est None - impossible d'afficher dans le chat")
        # Fallback: notification uniquement
        if temporal_final_alert:
            ui.notify(f'🕒 Temporal: {temporal_final_alert[:100]}...', type='info')
        if context_note:
            ui.notify(f'BRAIN Archiviste: {context_note[:100]}...', type='info')

    # 🕒 TEMPORAL GUARDIAN - Gestion temporelle organique via l'Archiviste
    
    try:
        temporal_guardian = _ensure_temporal_guardian()
        
        # Préparer le prompt archiviste de base (sera enrichi avec contexte temporel)
        base_archiviste_prompt = f"Note de l'Archiviste : {context_note}" if context_note else ""
        
        # Traiter le message utilisateur avec Temporal Guardian
        temporal_result = temporal_guardian.process_user_message(
            user_message=final_message,
            archiviste_prompt=base_archiviste_prompt
        )
        
        # Récupérer le contexte temporel enrichi et les données brutes
        temporal_context_enriched = temporal_result.get("enriched_archiviste_prompt")
        temporal_data = temporal_result.get("temporal_data")
        
        # BRAIN ANALYSE TEMPORELLE VIA L'ARCHIVISTE
        # Déléguer l'analyse à l'Archiviste selon l'architecture OGMA
        if temporal_data:  # Analyser tous les messages, y compris le premier
            try:
                archiviste_ctrl = _ensure_archiviste_controller()
                if archiviste_ctrl:
                    # Demander à l'Archiviste d'analyser les données temporelles
                    temporal_instruction = await temporal_guardian.analyze_with_archiviste(
                        temporal_data, archiviste_ctrl
                    )
                    
                    if temporal_instruction and temporal_instruction.strip():
                        temporal_final_alert = temporal_instruction
                        print(f"[TEMPORAL-GUARDIAN] BRAIN Instruction Archiviste: {temporal_instruction[:100]}...")
                    else:
                        print(f"[TEMPORAL-GUARDIAN] OK Archiviste: rythme normal, pas d'instruction")
                else:
                    print(f"[TEMPORAL-GUARDIAN] WARN Archiviste indisponible")
            except Exception as analysis_error:
                print(f"[TEMPORAL-GUARDIAN] ERROR Erreur analyse Archiviste: {analysis_error}")
        
        # Debug si activé
        if temporal_data and sm.settings.get('debug', {}).get('show_temporal_debug', False):
            delay_str = f"{temporal_data.delay_since_last:.1f}s" if temporal_data.delay_since_last else "Premier message"
            print(f"[TEMPORAL-GUARDIAN] Message #{temporal_data.message_count} | Délai: {delay_str}")
            
    except Exception as e:
        print(f"[TEMPORAL-GUARDIAN] WARN Erreur traitement temporel: {e}")
        # Fallback: utiliser contexte archiviste original
        temporal_context_enriched = f"Note de l'Archiviste : {context_note}" if context_note else None

    # 🕒 AFFICHAGE INJECTION TEMPORELLE - Si option debug activée
    if show_injection and temporal_final_alert and _chat_inner is not None:
        try:
            with _chat_inner:
                temporal_display = f"🕒 **Instruction Temporelle Archiviste** ({len(temporal_final_alert)} chars)\n\n{temporal_final_alert}"
                _message('system', temporal_display)
                print(f"[DEBUG-INJECTION] OK Instruction temporelle affichée dans le chat")
        except Exception as e:
            print(f"[DEBUG-INJECTION] Erreur affichage temporal: {e}")
            ui.notify(f'🕒 Temporal: {temporal_final_alert[:100]}...', type='info')

    # Construire messages pour le backend (injecter la note de contexte en tête)
    messages: List[Dict] = []
    
    # 🚨 INJECTION PRIORITÉ ABSOLUE: Instructions de base + Instruction temporelle fusionnées
    sm = _ensure_settings_manager()
    base_instructions = sm.settings.get('prompts', {}).get('instructions', '')
    
    # Construire le message système prioritaire unifié
    if temporal_final_alert:
        # PRIORITÉ ABSOLUE: Instruction temporelle en tête des instructions de base
        priority_instructions = f"""╔══════════════════════════════════════════════════════════════╗
║                    FAST PRIORITÉ ABSOLUE FAST                      ║
║           INSTRUCTION TEMPORELLE OBLIGATOIRE                  ║
╚══════════════════════════════════════════════════════════════╝

TARGET ADAPTATION COMPORTEMENTALE IMMÉDIATE:
{temporal_final_alert}

WARN  CETTE INSTRUCTION PRÉEMPTE TOUT AUTRE STYLE WARN
Applique cette adaptation AVANT toute autre considération.

═══════════════════════════════════════════════════════════════

{base_instructions if base_instructions else 'Instructions de base non définies.'}"""
        
        print(f"[TEMPORAL-GUARDIAN] 🚨 PRIORITÉ ABSOLUE: Instruction temporelle FUSIONNÉE en tête")
        print(f"[TEMPORAL-GUARDIAN] EDIT Contenu: {temporal_final_alert[:100]}...")
    else:
        # Mode normal sans instruction temporelle
        priority_instructions = base_instructions if base_instructions else ""
        print(f"[TEMPORAL-GUARDIAN] ⚪ Mode normal: pas d'instruction temporelle")
    
    if priority_instructions:
        messages.append({'role': 'system', 'content': priority_instructions})
        # Enregistrer l'ego prompt pour déduplication
        register_ego_prompt_injection(priority_instructions)
        print(f"[DEDUP] 🔍 Ego prompt enregistré ({len(priority_instructions)} chars)")
    else:
        print(f"[DEBUG-INJECTION] WARN AUCUNE instruction trouvée!")
    
    # 🎥 INJECTION INSTRUCTIONS DE PERCEPTION si images détectées
    has_image = (perception_image_data is not None or 
                (_active_file_data and _active_file_data.get('type') == 'image'))
    
    if has_image:
        perception_instructions = sm.settings.get('prompts', {}).get('perception', '')
        if perception_instructions:
            perception_system_msg = f"Instructions spécifiques pour la perception visuelle :\n{perception_instructions}"
            messages.append({'role': 'system', 'content': perception_system_msg})
            print(f"[PERCEPTION-INJECT] ✅ Instructions de perception injectées ({len(perception_instructions)} chars)")
        else:
            print(f"[PERCEPTION-INJECT] WARN Aucune instruction de perception trouvée dans settings")
    else:
        print(f"[PERCEPTION-INJECT] ⚪ Pas d'image détectée, pas d'injection perception")
    
    # Ajouter le contexte permanent si présent
    persistent_context_file = DATA_DIR / "persistent_context.txt"
    if persistent_context_file.exists():
        try:
            persistent_content = persistent_context_file.read_text(encoding='utf-8').strip()
            if persistent_content:
                messages.append({'role': 'system', 'content': persistent_content})
                print(f"[DEBUG-INJECTION] OK Contexte permanent ajouté: {len(persistent_content)} chars")
        except Exception as e:
            print(f"[DEBUG-INJECTION] WARN Erreur lecture contexte permanent: {e}")
    
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
    
    # 🕒 TEMPORAL GUARDIAN - Gestion temporelle organique via l'Archiviste
    temporal_alert_for_main_ai = False
    
    try:
        temporal_guardian = _ensure_temporal_guardian()
        
        # Préparer le prompt archiviste de base (sera enrichi avec contexte temporel)
        base_archiviste_prompt = f"Note de l'Archiviste : {context_note}" if context_note else ""
        
        # Traiter le message utilisateur avec Temporal Guardian
        temporal_result = temporal_guardian.process_user_message(
            user_message=final_message,
            archiviste_prompt=base_archiviste_prompt
        )
        
        # Récupérer le contexte temporel enrichi et les données brutes
        temporal_context_enriched = temporal_result.get("enriched_archiviste_prompt")
        temporal_data = temporal_result.get("temporal_data")
        
        # Le traitement temporel est maintenant fait plus haut dans le flux
            
    except Exception as e:
        print(f"[TEMPORAL-GUARDIAN] WARN Erreur traitement temporel: {e}")
        # Fallback: utiliser contexte archiviste original
        temporal_context_enriched = f"Note de l'Archiviste : {context_note}" if context_note else None
    
    # Ajouter le contexte de l'Archiviste (enrichi avec données temporelles)
    if temporal_context_enriched:
        messages.append({'role': 'system', 'content': temporal_context_enriched})
    elif context_note:
        # Fallback si temporal guardian a échoué
        messages.append({'role': 'system', 'content': f"Note de l'Archiviste : {context_note}"})
    else:
        print(f"[DEBUG-INJECTION] Aucun contexte à injecter")
    
    # Ajouter les souvenirs détaillés pour Luna (logique mixte avec bypass)
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

    # Injection biographique automatique (si détectée)
    if biography_injection_content:
        print(f"[BIOGRAPHY-EXTENSION] 📋 Injection biographique dans le contexte système")
        messages.append({'role': 'system', 'content': biography_injection_content})

    # BRAIN DÉSACTIVÉ: Résumé progressif - L'Archiviste doit s'en occuper
    # Les messages sont envoyés directement sans résumé en attendant l'implémentation Archiviste
    conversation_messages = _chat_history  # Utilise tout l'historique pour l'instant
    
    # Ajouter l'historique de conversation optimisé (avec support d'images)
    for i, m in enumerate(conversation_messages):
        # Vérifier si c'est le DERNIER message utilisateur avec une image (fichier uploadé)
        is_last_user_message_with_file = (m['role'] == 'user' and
                                         i == len(conversation_messages) - 1 and
                                         _active_file_data and
                                         _active_file_data.get('type') == 'image')

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

            # Ajouter image uploadée si disponible
            if is_last_user_message_with_file:
                image_data = _active_file_data.get('data', '')
                mime_type = _active_file_data.get('mime_type', 'image/jpeg')
                filename = _active_file_data.get('filename', 'image')

                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                })
                print(f"[DEBUG-VISION] Image fichier ajoutée: {filename}")

            # Ajouter image de perception si disponible
            if is_last_user_message_with_perception:
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

            # Si le message n'était QUE de l'introspection, le sauter
            if not content_cleaned:
                continue

            messages.append({'role': m['role'], 'content': content_cleaned})
    
    for i, msg in enumerate(messages):
        role = msg['role']
        content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        print(f"  {i+1}. {role}: {content_preview}")

    # 📚 INJECTION CONVERSATION CHARGÉE - SEULEMENT AU PREMIER MESSAGE
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
        
        conversation_context = f"""

--- CONTEXTE : REPRISE DE CONVERSATION ARCHIVÉE ---
DATE Date originale : {conversation_date}
📁 Fichier : {_loaded_conversation_filename}

IMPORTANT : Tu reprends une conversation interrompue avec cet utilisateur. 
Voici l'historique complet de votre précédente discussion. Agis naturellement 
en tenant compte de ce contexte et de votre relation établie.

=== HISTORIQUE DE LA CONVERSATION ===
"""
        total_chars = 0
        for i, msg in enumerate(_loaded_conversation):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            # NETTOYAGE: Retirer les balises <introspection> pour éviter redéclenchement
            # Quand une conversation passée contient des introspections, elles ne doivent pas
            # être réinjectées car cela redéclencherait le système d'introspection
            content_cleaned = re.sub(r'<introspection>.*?</introspection>', '', content, flags=re.DOTALL)
            content_cleaned = content_cleaned.strip()

            # Si le message était UNIQUEMENT une introspection, le sauter complètement
            if not content_cleaned:
                continue

            total_chars += len(content_cleaned)
            role_display = "USER Utilisateur" if role == 'user' else ("AI Toi (Luna)" if role == 'assistant' else "SYSTEM Système")
            conversation_context += f"{role_display}: {content_cleaned}\n\n"
        
        conversation_context += """=== FIN DE L'HISTORIQUE ===

Tu connais maintenant le contexte complet de votre précédente interaction. 
Réponds naturellement en tenant compte de cette histoire partagée."""
        
        # Injecter dans le message système ou en créer un nouveau
        if messages and messages[0]['role'] == 'system':
            messages[0]['content'] += conversation_context
        else:
            messages.insert(0, {'role': 'system', 'content': conversation_context})
        
        # Marquer comme injecté pour éviter les injections répétées
        _conversation_context_injected = True
        
        # Logs détaillés
        print(f"[CONVERSATION-INJECT] OK Conversation injectée au premier message: {_loaded_conversation_filename}")
        print(f"[CONVERSATION-INJECT] STATS {len(_loaded_conversation)} messages, {total_chars:,} caractères")
        print(f"[CONVERSATION-INJECT] EDIT Taille contexte injecté: {len(conversation_context):,} caractères")
        print(f"[CONVERSATION-INJECT] TARGET Position: {'Ajouté au système existant' if len(messages) > 1 and messages[0]['role'] == 'system' else 'Nouveau message système'}")
        
        # Afficher aperçu du contenu injecté
        preview = conversation_context[:200] + "..." if len(conversation_context) > 200 else conversation_context
        print(f"[CONVERSATION-INJECT] 👁️ Aperçu: {preview}")
        
        # Notification à l'utilisateur avec détails
        _notify_safe(f"� Contexte injecté ! {len(_loaded_conversation)} messages → Luna connaît maintenant votre historique", 'positive')
    elif _loaded_conversation and _conversation_context_injected:
        print(f"[CONVERSATION-INJECT] ⚪ Contexte déjà injecté, pas de nouvelle injection")
    
    # 📔 INJECTION CONTEXTE JOURNAL DE BORD - Pour utilisateur principal uniquement
    print("[JOURNAL-INJECT] SEARCH Vérification injection contexte journal...")
    try:
        # Vérifier si c'est une nouvelle conversation (pas de contexte conversation chargée injecté)
        if not _conversation_context_injected:
            # Détection profil utilisateur via identity_manager
            from identity_manager import get_current_user_name
            user_name = get_current_user_name()
            
            # Injection uniquement si utilisateur principal identifié (pas "Utilisateur" par défaut)
            is_main_user = (user_name and user_name != "" and user_name != "Utilisateur")
            
            if is_main_user:
                print(f"[JOURNAL-INJECT] ✅ Utilisateur principal détecté: {user_name}")
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
                else:
                    print("[JOURNAL-INJECT] ⚪ Pas de contexte journal disponible")
            else:
                print(f"[JOURNAL-INJECT] ⚪ Profil anonyme ou par défaut ({user_name or 'anonyme'}) - pas d'injection journal")
        else:
            print("[JOURNAL-INJECT] SKIP Conversation chargée - pas d'injection journal")
    except Exception as e:
        print(f"[JOURNAL-INJECT] ERROR Erreur injection contexte journal: {e}")

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

    # TARGET INJECTION ÉMOTIONNELLE - Système Archi_sensor 
    print("[ARCHI-INJECT] SEARCH Vérification injection émotionnelle...")
    try:
        from logic_callbacks import run_archi_sensor_analysis
        
        # Convertir messages en format history pour Archi_sensor
        history = []
        for msg in messages:
            if msg['role'] in ['user', 'assistant']:
                history.append({"role": msg['role'], "content": msg['content']})
        
        # Récupérer memory_manager et contrôleurs
        memory_mgr = _ensure_memory_manager()
        chat_ctrl = _ensure_chat_controller()
        archiviste_ctrl = _ensure_archiviste_controller()
        
        if memory_mgr and archiviste_ctrl and len(history) > 0:
            # Appeler l'analyse Archi_sensor avec le contrôleur Archiviste
            emotional_injection = await run_archi_sensor_analysis(history, None, archiviste_ctrl, memory_mgr)
            
            if emotional_injection:
                print(f"[ARCHI-INJECT] 💫 Injection émotionnelle active : {emotional_injection[:100]}...")
                # Injecter le contexte émotionnel dans le premier message système
                if messages and messages[0]['role'] == 'system':
                    emotional_addon = f"\n\n--- GUIDANCE CONTEXTUELLE ---\n{emotional_injection}\n--- FIN GUIDANCE ---"
                    messages[0]['content'] += emotional_addon
            else:
                print("[ARCHI-INJECT] ⚪ Pas d'injection émotionnelle cette fois")
        else:
            print("[ARCHI-INJECT] WARN Memory manager ou chat controller indisponible")
            
    except Exception as e:
        print(f"[ARCHI-INJECT] ERROR Erreur injection émotionnelle: {e}")
    
    # 🧠 ORCHESTRATION COGNITIVE - Directives pour utilisation naturelle des contextes
    global _orchestration_injected
    print("[COGNITIF-ORCHESTRATION] APPLY Injection directives d'orchestration cognitive...")
    try:
        # Vérifier si l'orchestration a déjà été injectée dans cette session
        is_new_session = not _orchestration_injected
        print(f"[COGNITIF-ORCHESTRATION] DEBUG is_new_session={is_new_session}, _orchestration_injected={_orchestration_injected}")
        
        if is_new_session:
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
            print(f"[COGNITIF-ORCHESTRATION] ✨ Orchestration cognitive activée - Luna guidée pour usage naturel des contextes")
        else:
            print("[COGNITIF-ORCHESTRATION] SKIP Conversation en cours - pas de nouvelles directives")
            
    except Exception as e:
        print(f"[COGNITIF-ORCHESTRATION] ERROR Erreur orchestration cognitive: {e}")
    
    # Chat: réponses libres (pas JSON forcé)
    
    # DEBUG: Afficher les messages envoyés à l'API pour comprendre pourquoi les instructions temporelles ne sont pas suivies
    # Force l'affichage si une instruction temporelle est présente
    force_debug = any('🚨 INSTRUCTION COMPORTEMENTALE' in msg.get('content', '') for msg in messages)
    
    if sm.settings.get('debug', {}).get('show_temporal_debug', False) or force_debug:
        print(f"\n[TEMPORAL-DEBUG] CLIPBOARD Messages envoyés à Luna:")
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
    
    reply, err = await ctrl.call_chat_api(messages=messages, max_tokens=ctrl.max_tokens, context_length=ctrl.context_length, temperature=ctrl.temperature, is_json=False)
    if err:
        if _chat_inner is not None:
            with _chat_inner:
                _message('system', f"[ERREUR] {err}")
        return
    if reply is not None:
        # 🪞 COGNITIVE MIRROR: Hook après génération de la réponse IA
        print("[COGNITIVE-MIRROR] SEARCH Enrichissement contexte conversation...")
        try:
            cognitive_mirror = _ensure_cognitive_mirror()
            if cognitive_mirror and cognitive_mirror.is_enabled:
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

        # Hook Extension Archi_sensor (analyse post-réponse)
        try:
            from logic_callbacks import run_archi_sensor_analysis
            
            # Lancer l'analyse Archi_sensor si activé
            # Utiliser les contrôleurs appropriés
            conversation_id = _current_conversation_id
            archiviste_controller = _ensure_archiviste_controller()
            memory_manager = _ensure_memory_manager()
            
            injection_emotional = await run_archi_sensor_analysis(
                messages, conversation_id, archiviste_controller, memory_manager
            )
            
            if injection_emotional:
                print(f"[ARCHI-SENSOR] 💭 Injection émotionnelle générée: {len(injection_emotional)} chars")
                # Ajouter l'injection pour la prochaine interaction
                if _pending_behavioral_injections is None:
                    _pending_behavioral_injections = []
                _pending_behavioral_injections.append(injection_emotional)
            
        except ImportError:
            print("[ARCHI-SENSOR] Extension non disponible")
        except Exception as e:
            print(f"[ARCHI-SENSOR] Erreur analyse: {e}")


        # Détection "phrase magique" dans la réponse IA et mémorisation
        # S'assurer que reply est une chaîne avant l'analyse
        reply_text = reply if isinstance(reply, str) else str(reply) if reply else ""
        magic_ai = _extract_magic_memories(reply_text)
        ai_memorized = False
        if magic_ai:
            mem = _ensure_memory_manager()
            if mem is not None:
                for content in magic_ai:
                    try:
                        mem_id = f"ai-{uuid.uuid4()}"
                        # Nouveau système unifié: passer chat_controller pour scoring IA Principale
                        conversation_context = "\n".join([f"{msg['role']}: {msg.get('content', '')}" for msg in _chat_history[-3:] if isinstance(msg.get('content'), str)])
                        ok = await mem.add_memory(
                            mem_id, 
                            content,
                            chat_controller=_chat_controller,
                            conversation_context=conversation_context,
                            interlocutor="Yohan"
                        )
                        if ok:
                            _notify_safe(f"SAVE Souvenir mémorisé: {content[:80]}...", 'positive')
                            _trigger_memory_update()
                            ai_memorized = True
                        else:
                            _notify_safe("Échec de la mémorisation (voir logs)", 'warning')
                    except Exception as e:
                        _notify_safe(f"Erreur mémorisation: {e}", 'warning')
        
        # Détection phrase-clé ego prompt: "ceci est une part de moi maintenant" (multi-phrases)
        if ego_match := re.search(r'ceci est une part de moi maintenant\s*:\s*(.*?)(?=\n\n|\n\s*\n|$)', reply_text, re.DOTALL | re.IGNORECASE):
            content = ego_match.group(1).strip()
            # Nettoyer tous les formatages markdown (au cas où)
            content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Enlever ** mais garder le contenu
            content = re.sub(r'[*_`]', '', content)  # Enlever autres formatages  
            print(f"[EGO-UPDATE] Contenu capturé dans ogma_ng: '{content}'")
            try:
                # NOUVEAU SYSTÈME: Stocker le trait d'ego comme souvenir structurant
                import asyncio
                
                async def store_ego_trait_async():
                    try:
                        memory_id = await _memory_manager.store_ego_trait(
                            content, 
                            chat_controller=_chat_controller,
                            conversation_context="ego_trait_update",
                            interlocutor="self"
                        )
                        print(f"[EGO-UPDATE] Trait d'ego stocké avec ID: {memory_id}")
                        
                        # Organiser automatiquement l'ego prompt avec les IDs
                        from logic_callbacks import organize_ego_prompt_with_ids
                        await organize_ego_prompt_with_ids(_memory_manager)
                        print(f"[EGO-UPDATE] Ego prompt organisé automatiquement par l'archiviste")
                        
                        # Déclencher synthèse asynchrone du nouveau système
                        # DÉSACTIVÉ : On utilise maintenant ego_prompt.txt directement
                        # from utils import synthesize_ego_prompt_async
                        # print(f"[SYNTHESIS] Lancement synthèse asynchrone du nouveau système ego")
                        # Note: pas de chat_ai_controller ici, donc on skip la synthèse pour l'instant
                        
                        return memory_id
                    except Exception as e:
                        print(f"[ERROR] Échec stockage trait ego async: {e}")
                        return None
                
                # Lancer la tâche asynchrone
                asyncio.create_task(store_ego_trait_async())
                
                # Créer notification intelligente avec compteur de phrases
                phrases = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
                phrase_count = len(phrases)
                
                if phrase_count == 1:
                    notification_msg = f"BRAIN Trait d'ego mémorisé: {content[:50]}..."
                else:
                    first_phrase = phrases[0][:40] if phrases else content[:40]
                    notification_msg = f"BRAIN Trait d'ego mémorisé ({phrase_count} phrases): {first_phrase}..."
                
                # Ajouter à la queue des notifications en arrière-plan
                _pending_notifications.append((notification_msg, 'positive'))
                print(f"[EGO-UPDATE] Notification ajoutée: {notification_msg}")
            except Exception as e:
                _pending_notifications.append((f"Erreur mise à jour ego: {e}", 'warning'))
                print(f"[ERROR] Échec update ego prompt: {e}")
        
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
                        
                        # Ajouter le contexte web et demander une nouvelle réponse
                        web_context_message = {
                            'role': 'system',
                            'content': f"INFORMATIONS WEB RÉCUPÉRÉES:\n\n{web_response}\n\nMaintenant, réponds à la question de l'utilisateur en utilisant ces informations récentes que tu viens de récupérer sur internet."
                        }
                        
                        # Créer un nouveau set de messages avec le contexte web
                        regeneration_messages = messages + [web_context_message]
                        
                        # Régénérer la réponse
                        new_reply, new_err = await ctrl.call_chat_api(
                            messages=regeneration_messages, 
                            max_tokens=ctrl.max_tokens, 
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

        # 🖼️ GÉNÉRATION D'IMAGES - Détection et traitement via extension text2img
        try:
            from logic_callbacks import process_image_generation
            from extensions.text2img import get_text2img_manager, is_available as text2img_available

            sm = _ensure_settings_manager()

            if text2img_available():
                text2img_mgr = get_text2img_manager()
                cleaned_reply = await process_image_generation(
                    cleaned_reply,
                    sm,
                    text2img_mgr
                )
                print("[IMAGE] Traitement génération d'image terminé")
            else:
                print("[IMAGE] WARN Extension text2img non disponible")
        except ImportError as ie:
            print(f"[IMAGE] Extension génération d'images non disponible: {ie}")
        except Exception as e:
            print(f"[IMAGE] ERROR Erreur traitement génération: {e}")

        # 🕐 DÉTECTION DEMANDE D'HEURE AUTOMATIQUE (uniquement dans le message utilisateur)
        if re.search(r'\b(quelle heure|l\'heure|heure est|heures? est)\b', text.lower()):
            current_time = _get_current_time()
            cleaned_reply = f"{cleaned_reply}\n\nTIME Il est actuellement {current_time}"

        # 📝 FILE WRITER - Sauvegarde automatique fichiers .md
        print("[FILE-WRITER] Vérification demande création fichier...")
        try:
            file_writer = _ensure_file_writer()
            
            if file_writer:
                saved_path = file_writer.process_response(
                    user_message=text,
                    ai_response=cleaned_reply
                )
                
                if saved_path:
                    print(f"[FILE-WRITER] ✅ Fichier sauvegardé: {saved_path}")
                    # Notification utilisateur
                    _notify_safe(f"📁 Fichier sauvegardé: {Path(saved_path).name}", 'positive')
                else:
                    print("[FILE-WRITER] ⚪ Pas de fichier à sauvegarder")
            else:
                print("[FILE-WRITER] SKIP Extension non disponible")
        except Exception as e:
            print(f"[FILE-WRITER] ERROR Erreur traitement: {e}")

        # 🧹 NETTOYAGE HISTORIQUE - Remplacer HTML images par phrase magique pour réutilisation
        # Problème : Luna voit le format "🖼️ **Image générée :**" dans l'historique et le copie
        # sans prononcer la phrase magique, ce qui empêche les générations suivantes
        history_content = cleaned_reply
        
        # Pattern pour détecter les blocs d'images générées avec phrase magique cachée
        image_block_pattern = r'🖼️ \*\*Image générée :\*\* "(.*?)".*?<img src=.*?/>.*?🎨.*?via.*?💾.*?(?:Sauvegardée|Échec sauvegarde).*?(?:\n|$)'
        
        # Remplacer par la phrase magique simple pour que Luna puisse la réutiliser
        def replace_with_magic_phrase(match):
            description = match.group(1)
            return f"je dois créer une image de : {description}"
        
        history_content = re.sub(image_block_pattern, replace_with_magic_phrase, history_content, flags=re.DOTALL)
        
        if history_content != cleaned_reply:
            print(f"[IMAGE-HISTORY] ✂️ HTML image nettoyé de l'historique - phrase magique conservée")

        msg = {'role': 'assistant', 'content': history_content, 'memorized': ai_memorized}
        _chat_history.append(msg)
        
        # Pour l'UI, garder le HTML complet avec l'image
        msg_ui = {'role': 'assistant', 'content': cleaned_reply, 'memorized': ai_memorized}
        _chat_history_ui.append(msg_ui)
        
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
        # Titrage contextualisé après au moins 2 échanges
        try:
            import asyncio as _asyncio
            _asyncio.create_task(_maybe_update_conv_title())
        except Exception:
            pass
        if _chat_inner is not None:
            with _chat_inner:
                # Vérifier si on a une réponse journal prédéfinie à injecter
                if _journal_preformed_response:
                    print(f"[JOURNAL-EXTENSION] INJECT Affichage réponse journal prédéfinie")
                    _message('assistant', _journal_preformed_response, None, message_index=len(_chat_history)-1)
                    _journal_preformed_response = None  # Nettoyer après usage
                else:
                    _message('assistant', cleaned_reply, ['mémorisé'] if ai_memorized else None, message_index=len(_chat_history)-1)
                
                # Lecture automatique si activée
                sm = _ensure_settings_manager()
                auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
                tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
                
                if auto_speak and tts_enabled and _audio_manager:
                    try:
                        # Utiliser threading au lieu d'asyncio pour éviter RuntimeError
                        import threading
                        # Nettoyer le contenu pour la synthèse
                        clean_content = cleaned_reply.replace('*', '').replace('**', '').replace('#', '').replace('`', '')
                        print(f"[TTS-AUTO] 🔊 Lecture automatique: {clean_content[:50]}...")
                        
                        def audio_task():
                            _audio_manager.speak(clean_content)
                        
                        threading.Thread(target=audio_task, daemon=True).start()
                        print("[TTS-AUTO] ✅ Lecture automatique démarrée")
                    except Exception as e:
                        print(f"[TTS-AUTO] ❌ Erreur lecture automatique: {e}")
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
_auto_send_audio = False
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
            
            # Auto-envoi si activé
            if _auto_send_audio:
                _pending_notifications.append(("📤 Envoi automatique...", 'info'))
                await _send_chat_message(input_field)
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


def _input_overlay():
    global _input_field
    with ui.element('div').classes('input-overlay'):
        with ui.element('div').classes('input-container'):
            # Icônes Material (plus professionnelles) à la place des emojis
            ui.button(icon='attach_file', on_click=_show_file_upload_dialog).classes('action-button')
            _input_field = ui.textarea(placeholder='Écrire un message...').props('autogrow').classes('input-field')
            input_field = _input_field  # Alias local pour compatibilité
            ui.button(icon='auto_awesome', on_click=lambda: asyncio.create_task(_manual_memorize_current_input(input_field))).classes('action-button')
            
            # Nouveau bouton microphone
            mic_button = ui.button(
                icon='mic', 
                on_click=lambda: asyncio.create_task(_start_audio_recording(input_field, mic_button))
            ).classes('action-button mic-button').props('title="Enregistrer un message vocal"')
            
            # Envoi avec Entrée (Shift+Entrée pour nouvelle ligne)
            def _keydown(e):
                try:
                    k = (e.args or {}).get('key')
                    shift = bool((e.args or {}).get('shiftKey'))
                    if k == 'Enter' and not shift:
                        # empêcher l’insertion de saut de ligne et envoyer
                        asyncio.create_task(_send_chat_message(input_field))
                except Exception:
                    pass
            input_field.on('keydown', _keydown)

            # Raccourci paramètres IA (modèles)
            models_dialog = _models_modal()
            ui.button(icon='psychology', on_click=models_dialog.open).classes('action-button')
            ui.button('Envoyer', icon='send', on_click=lambda: asyncio.create_task(_send_chat_message(input_field))).classes('send-button')
        
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
# PERCEPTION PAGE - Page dédiée pour l'extension Perception
# ============================================================================

@ui.page('/perception')
def perception_page():
    """
    Page dédiée pour l'extension Perception avec affichage webcam en temps réel.
    Ouverte dans une fenêtre popup dédiée compacte (580×440).
    """
    print("[PERCEPTION-PAGE] 📹 Chargement page Perception...")
    
    ui.dark_mode()
    _link_styles()
    
    # JavaScript pour gérer la fenêtre popup
    ui.run_javascript('''
        // Focus initial sur la fenêtre popup
        window.focus();
        
        // Mémoriser position/taille si fenêtre déplacée/redimensionnée (localStorage)
        let saveWindowState = () => {
            localStorage.setItem('perceptionWindowX', window.screenX);
            localStorage.setItem('perceptionWindowY', window.screenY);
            localStorage.setItem('perceptionWindowW', window.outerWidth);
            localStorage.setItem('perceptionWindowH', window.outerHeight);
        };
        
        // Sauvegarder état toutes les 3 secondes si modifié
        setInterval(saveWindowState, 3000);
        
        // Au chargement, restaurer position/taille si sauvegardée
        window.addEventListener('load', () => {
            let savedX = localStorage.getItem('perceptionWindowX');
            let savedY = localStorage.getItem('perceptionWindowY');
            let savedW = localStorage.getItem('perceptionWindowW');
            let savedH = localStorage.getItem('perceptionWindowH');
            
            if (savedX && savedY) {
                window.moveTo(parseInt(savedX), parseInt(savedY));
            }
            if (savedW && savedH) {
                window.resizeTo(parseInt(savedW), parseInt(savedH));
            }
        });
    ''')
    
    # Récupérer l'instance perception_ui (singleton)
    from extensions.perception_ui import get_perception_ui
    perception_ui = get_perception_ui()
    
    if not perception_ui:
        with ui.column().classes('w-full h-screen items-center justify-center'):
            ui.label('❌ Extension Perception non disponible').classes('text-xl text-red-500')
        return
    
    # Layout principal (scrollable avec hauteur max)
    with ui.column().classes('w-full').style('padding: 20px; gap: 20px; max-height: 100vh; overflow-y: scroll;'):
        
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('🎥 Perception Agent').classes('text-3xl font-bold')
            
            with ui.row().classes('gap-2'):
                # Switch ON/OFF
                perception_toggle = ui.switch(
                    text='Extension',
                    value=perception_ui.is_enabled
                ).props('color="green"')
                
                # Bouton fermer popup
                ui.button(
                    'Fermer', 
                    icon='close',
                    on_click=lambda: ui.run_javascript('window.close();')
                ).props('outline color="negative"')
        
        # Container principal avec 2 colonnes (flex-wrap pour responsive)
        with ui.row().classes('w-full').style('gap: 20px; flex-wrap: wrap;'):
            
            # COLONNE GAUCHE: Webcam display (réduite de 40% comme demandé)
            with ui.column().style('flex: 1.2; min-width: 400px; max-width: 600px; gap: 12px;'):
                ui.label('👁️ Eye Vision').classes('text-xl font-semibold')
                
                # Webcam container (hauteur réduite)
                with ui.card().classes('w-full').style('background: #000; padding: 0; min-height: 300px; max-height: 400px;'):
                    webcam_display = ui.image().classes('w-full').style('object-fit: contain;')
                    webcam_placeholder = ui.label('📷 Webcam non active').classes('absolute-center text-gray-400')
                
                # Status bar
                with ui.row().classes('items-center gap-2'):
                    status_dot = ui.element('div').style('''
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        background: #dc2626;
                        box-shadow: 0 0 8px rgba(220, 38, 38, 0.6);
                    ''')
                    status_label = ui.label('Inactif').classes('text-sm')
                
                # Boutons action
                with ui.row().classes('gap-2'):
                    capture_btn = ui.button(
                        '📸 Capturer', 
                        icon='camera'
                    ).props('color="primary"')
                    
                    motion_btn = ui.button(
                        '🎬 Chronophoto',
                        icon='video_library'
                    ).props('color="purple" outline')
            
            # COLONNE DROITE: Contrôles (scrollable si nécessaire)
            with ui.column().style('flex: 1; min-width: 350px; max-width: 450px; gap: 16px;'):
                ui.label('⚙️ Paramètres').classes('text-xl font-semibold')
                
                with ui.card().classes('w-full'):
                    with ui.column().style('gap: 12px; padding: 12px;'):
                        
                        # Mode capture
                        ui.label('Mode de capture').classes('text-sm font-medium text-gray-400')
                        motion_toggle = ui.switch(
                            text='🎬 Mode Pellicule', 
                            value=perception_ui.current_config.get('motion_capture_enabled', False)
                        ).props('color="purple"')
                        
                        ui.separator()
                        
                        # Délai capture
                        ui.label('Délai avant capture').classes('text-sm font-medium text-gray-400')
                        with ui.row().classes('items-center justify-between w-full'):
                            ui.label('Délai:').classes('text-sm')
                            capture_delay_label = ui.label(
                                f"{perception_ui.current_config.get('capture_delay', 0.0):.1f}s"
                            ).classes('text-sm text-gray-400')
                        capture_delay_slider = ui.slider(
                            min=0.0, max=10.0, step=0.5,
                            value=perception_ui.current_config.get('capture_delay', 0.0)
                        ).props('label-always color="orange"').classes('w-full')
                        
                        # Paramètres chronophoto (conditionnels)
                        motion_params = ui.column().style('gap: 12px;')
                        with motion_params:
                            ui.separator()
                            ui.label('Paramètres Pellicule').classes('text-sm font-medium text-gray-400')
                            
                            # Intervalle entre images
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label('Intervalle:').classes('text-sm')
                                motion_interval_label = ui.label(
                                    f"{perception_ui.current_config.get('motion_interval', 0.5):.1f}s"
                                ).classes('text-sm text-gray-400')
                            motion_interval_slider = ui.slider(
                                min=0.1, max=5.0, step=0.1,
                                value=perception_ui.current_config.get('motion_interval', 0.5)
                            ).props('label-always color="purple"').classes('w-full')
                            
                            # Nombre d'images (jusqu'à 20)
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label('Nombre d\'images:').classes('text-sm')
                                frames_count_label = ui.label(
                                    f"{perception_ui.current_config.get('motion_frames_after', 6)}"
                                ).classes('text-sm text-gray-400')
                            frames_count_slider = ui.slider(
                                min=2, max=20, step=1,
                                value=perception_ui.current_config.get('motion_frames_after', 6)
                            ).props('label-always color="purple"').classes('w-full')
                            
                            # Durée totale calculée
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label('Durée totale:').classes('text-sm')
                                initial_duration = (
                                    perception_ui.current_config.get('motion_frames_after', 6) - 1
                                ) * perception_ui.current_config.get('motion_interval', 0.5)
                                duration_label = ui.label(f'{initial_duration:.1f}s').classes('text-sm text-gray-400')
                            
                            # Layout (jusqu'à 4x5)
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label('Layout:').classes('text-sm')
                                layout_select = ui.select(
                                    options={
                                        '2x2': '2×2 (4)', '3x2': '3×2 (6)', '2x3': '2×3 (6)',
                                        '4x2': '4×2 (8)', '2x4': '2×4 (8)',
                                        '3x3': '3×3 (9)', '4x3': '4×3 (12)', '3x4': '3×4 (12)',
                                        '4x4': '4×4 (16)', '5x4': '5×4 (20)', '4x5': '4×5 (20)',
                                        '1x10': '1×10', '10x1': '10×1', '1x20': '1×20', '20x1': '20×1'
                                    },
                                    value=perception_ui.current_config.get('motion_layout', '3x2')
                                ).classes('text-sm')
                            
                            # Options chronophoto avancées
                            ui.separator()
                            ui.label('Options affichage').classes('text-xs font-medium text-gray-500')
                            
                            timeline_toggle = ui.switch(
                                text='Timeline temporelle',
                                value=perception_ui.current_config.get('motion_timeline', False)
                            ).props('color="purple" dense').classes('text-xs')
                            
                            annotations_toggle = ui.switch(
                                text='Annotations temps',
                                value=perception_ui.current_config.get('motion_annotations', False)
                            ).props('color="purple" dense').classes('text-xs')
                        
                        ui.separator()
                        
                        # Sauvegarde captures
                        ui.label('Sauvegarde').classes('text-sm font-medium text-gray-400')
                        save_captures_toggle = ui.switch(
                            text='💾 Sauvegarder captures localement',
                            value=perception_ui.current_config.get('save_captures', False)
                        ).props('color="amber"')
                        ui.label('📁 Dossier: ./captures/').classes('text-xs text-gray-500')
                        
                        ui.separator()
                        
                        # Source caméra
                        ui.label('Source & Qualité').classes('text-sm font-medium text-gray-400')
                        with ui.row().classes('items-center justify-between w-full'):
                            ui.label('Caméra:').classes('text-sm')
                            camera_select = ui.select(
                                options={0: 'Caméra 0', 1: 'Caméra 1', 2: 'Caméra 2'},
                                value=perception_ui.current_config.get('webcam_index', 0)
                            ).classes('text-sm')
                        
                        # Résolution (désactivée en mode chirurgical)
                        with ui.row().classes('items-center justify-between w-full'):
                            ui.label('Résolution Stream:').classes('text-sm')
                            resolution_select = ui.select(
                                options={'320x240': '320p', '640x480': '480p', '1280x720': '720p', '1920x1080': '1080p'},
                                value=perception_ui.current_config.get('capture_resolution', '640x480')
                            ).classes('text-sm')
                        
                        # Indicateur mode actif
                        resolution_hint = ui.label(
                            '💡 En mode Normal, choisissez résolution selon besoin'
                        ).classes('text-xs text-gray-400 italic')
                        
                        # Paramètres avancés
                        with ui.expansion('Paramètres avancés', icon='settings').classes('w-full'):
                            with ui.column().style('gap: 12px; padding: 8px;'):
                                # Mode Chirurgical 🆕
                                with ui.row().classes('items-center justify-between w-full').style('background: #1e293b; padding: 12px; border-radius: 8px;'):
                                    with ui.column().style('gap: 4px;'):
                                        ui.label('🔬 Mode Chirurgical').classes('text-sm font-bold text-blue-400')
                                        ui.label('Optimisé pour voir détails et captures haute précision').classes('text-xs text-gray-400')
                                        ui.label('• Stream: 720p @ 80% qualité @ 15 FPS max').classes('text-xs text-gray-500')
                                        ui.label('• Captures: 1080p natif @ 95% qualité').classes('text-xs text-gray-500')
                                        ui.label('• CPU: Équivalent mode normal (moins de pixels/s)').classes('text-xs text-green-500')
                                    surgical_mode_switch = ui.switch(
                                        value=perception_ui.current_config.get('surgical_mode', False)
                                    ).props('color="blue"')
                                
                                ui.separator()
                                
                                # FPS Preview
                                ui.label('💡 FPS affichage = fluidité stream (15-30 recommandé)').classes('text-xs text-gray-400 italic')
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label('FPS Preview:').classes('text-xs')
                                    display_fps_label = ui.label(
                                        f"{perception_ui.current_config.get('display_fps', 15)} fps"
                                    ).classes('text-xs text-gray-400')
                                display_fps_slider = ui.slider(
                                    min=5, max=30, step=5,
                                    value=perception_ui.current_config.get('display_fps', 15)
                                ).props('label-always color="blue"').classes('w-full')
                                
                                # Qualité Stream 🆕
                                ui.label('💡 Qualité Stream = compromis fluidité/netteté (75% optimal)').classes('text-xs text-gray-400 italic')
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label('Qualité Stream:').classes('text-xs')
                                    stream_quality_label = ui.label(
                                        f"{perception_ui.current_config.get('stream_quality', 75)}%"
                                    ).classes('text-xs text-gray-400')
                                stream_quality_slider = ui.slider(
                                    min=60, max=90, step=5,
                                    value=perception_ui.current_config.get('stream_quality', 75)
                                ).props('label-always color="cyan"').classes('w-full')
                                
                                # Qualité JPEG Capture (renommé)
                                ui.label('💡 Qualité Capture IA = précision analyse (85-95% selon mode)').classes('text-xs text-gray-400 italic')
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label('Qualité Capture IA:').classes('text-xs')
                                    jpeg_quality_label = ui.label(
                                        f"{perception_ui.current_config.get('jpeg_quality', 85)}%"
                                    ).classes('text-xs text-gray-400')
                                jpeg_quality_slider = ui.slider(
                                    min=50, max=100, step=5,
                                    value=perception_ui.current_config.get('jpeg_quality', 85)
                                ).props('label-always color="green"').classes('w-full')
                
                # Bouton Sauvegarder en bas de la card
                with ui.row().classes('w-full justify-center').style('margin-top: 16px;'):
                    save_btn = ui.button(
                        '💾 Sauvegarder Configuration', 
                        icon='save'
                    ).props('color="positive"').classes('w-full')
    
    # ============================================================================
    # LOGIQUE MISE À JOUR WEBCAM avec ui.timer (natif NiceGUI)
    # ============================================================================
    
    import cv2
    import numpy as np
    from typing import Optional
    
    # Note: frame_to_base64 supprimée - JPEG encodé directement dans backend
    
    def update_webcam_display():
        """Mise à jour de l'affichage webcam - OPTIMISÉ: JPEG direct depuis backend"""
        try:
            if not perception_ui or not perception_ui.perception_agent:
                return
            
            # Récupérer JPEG base64 DIRECT depuis la queue (pas de re-traitement)
            if not perception_ui.perception_agent.visual_queue.empty():
                jpeg_base64 = perception_ui.perception_agent.visual_queue.get_nowait()
                
                if jpeg_base64:
                    webcam_display.set_source(f'data:image/jpeg;base64,{jpeg_base64}')
                    webcam_placeholder.set_visibility(False)
                else:
                    webcam_placeholder.set_visibility(True)
            
            # Mettre à jour le status
            if perception_ui.is_enabled and perception_ui.perception_agent:
                status = perception_ui.perception_agent.status
                if status == 'active':
                    status_dot.style('background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);')
                    status_label.set_text('Actif')
                elif status == 'warming_up':
                    status_dot.style('background: #eab308; box-shadow: 0 0 8px rgba(234, 179, 8, 0.6);')
                    status_label.set_text('Initialisation...')
                else:
                    status_dot.style('background: #dc2626; box-shadow: 0 0 8px rgba(220, 38, 38, 0.6);')
                    status_label.set_text('Inactif')
            else:
                status_dot.style('background: #dc2626; box-shadow: 0 0 8px rgba(220, 38, 38, 0.6);')
                status_label.set_text('Désactivé')
                
        except Exception as e:
            print(f"[PERCEPTION-PAGE] ⚠️ Erreur update: {e}")
    
    # Timer simple qui respecte le FPS configuré
    def simple_update():
        """Mise à jour simple basée sur FPS configuré"""
        try:
            update_webcam_display()
        except Exception as e:
            print(f"[PERCEPTION-PAGE] ⚠️ Erreur update: {e}")
    
    # Timer calé sur le FPS configuré (15 FPS = ~67ms entre frames)
    fps_target = perception_ui.current_config.get('display_fps', 15)
    update_interval = 1.0 / fps_target  # Ex: 15 FPS = 0.067s
    ui.timer(update_interval, simple_update)
    
    # Enregistrer les éléments UI
    perception_ui.register_ui_elements(webcam_display, status_dot)
    
    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================
    
    def on_toggle_perception(e):
        enabled = e.args if isinstance(e.args, bool) else perception_toggle.value
        if enabled:
            perception_ui.start_perception()
            ui.notify('✅ Perception activée', type='positive')
        else:
            perception_ui.stop_perception()
            ui.notify('🛑 Perception désactivée', type='info')
    
    def on_capture_click():
        if perception_ui and perception_ui.is_enabled:
            perception_ui.request_capture()
            ui.notify('📸 Capture en cours...', type='info')
        else:
            ui.notify('⚠️ Activez Perception d\'abord', type='warning')
    
    def on_motion_click():
        if perception_ui and perception_ui.is_enabled:
            if perception_ui.current_config.get('motion_capture_enabled'):
                perception_ui.request_motion_capture()
                ui.notify('🎬 Chronophotographie en cours...', type='info')
            else:
                ui.notify('⚠️ Activez le mode Pellicule d\'abord', type='warning')
        else:
            ui.notify('⚠️ Activez Perception d\'abord', type='warning')
    
    def on_motion_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else motion_toggle.value
        perception_ui.current_config['motion_capture_enabled'] = enabled
        motion_params.set_visibility(enabled)
        # Pas de sauvegarde auto - attendre bouton Sauvegarder
    
    def on_capture_delay_change(e):
        value = e.args if isinstance(e.args, (int, float)) else capture_delay_slider.value
        perception_ui.current_config['capture_delay'] = value
        capture_delay_label.set_text(f'{value:.1f}s')
        # Pas de sauvegarde auto
    
    def on_motion_interval_change(e):
        value = e.args if isinstance(e.args, (int, float)) else motion_interval_slider.value
        perception_ui.current_config['motion_interval'] = value
        motion_interval_label.set_text(f'{value:.1f}s')
        # Recalculer durée
        frames = perception_ui.current_config.get('motion_frames_after', 6)
        duration = (frames - 1) * value
        duration_label.set_text(f'{duration:.1f}s')
        # Pas de sauvegarde auto
    
    def on_frames_count_change(e):
        value = int(e.args) if isinstance(e.args, (int, float)) else int(frames_count_slider.value)
        perception_ui.current_config['motion_frames_after'] = value
        frames_count_label.set_text(f'{value}')
        # Recalculer durée
        interval = perception_ui.current_config.get('motion_interval', 0.5)
        duration = (value - 1) * interval
        duration_label.set_text(f'{duration:.1f}s')
        # Pas de sauvegarde auto
    
    def on_layout_change(e):
        value = e.args if isinstance(e.args, str) else layout_select.value
        perception_ui.current_config['motion_layout'] = value
        # Pas de sauvegarde auto
    
    def on_camera_change(e):
        value = e.args if isinstance(e.args, int) else camera_select.value
        perception_ui.current_config['webcam_index'] = value
        # Pas de sauvegarde auto - redémarrage uniquement au clic Sauvegarder
    
    def on_resolution_change(e):
        """Change la résolution du stream (mode Normal uniquement)"""
        value = e.args if isinstance(e.args, str) else resolution_select.value
        perception_ui.current_config['capture_resolution'] = value
        
        # En mode Normal, propager immédiatement (pas besoin restart webcam)
        surgical_mode = perception_ui.current_config.get('surgical_mode', False)
        if not surgical_mode and perception_ui.perception_agent:
            # Mettre à jour la config agent directement
            perception_ui.perception_agent.update_config({'capture_resolution': value})
            ui.notify(f'📐 Résolution stream: {value}', type='info')
        
        # Pas de sauvegarde auto - mais effet immédiat en mode Normal
    
    def on_display_fps_change(e):
        value = e.args if isinstance(e.args, (int, float)) else display_fps_slider.value
        perception_ui.current_config['display_fps'] = int(value)
        display_fps_label.set_text(f'{int(value)} fps')
        # Pas de sauvegarde auto - FPS s'adapte dynamiquement
    
    def on_jpeg_quality_change(e):
        value = e.args if isinstance(e.args, (int, float)) else jpeg_quality_slider.value
        perception_ui.current_config['jpeg_quality'] = int(value)
        jpeg_quality_label.set_text(f'{int(value)}%')
        # Pas de sauvegarde auto
    
    def on_surgical_mode_change(e):
        """Active/désactive le mode chirurgical avec optimisations auto"""
        enabled = e.args if isinstance(e.args, bool) else surgical_mode_switch.value
        perception_ui.current_config['surgical_mode'] = enabled
        
        # PROPAGER au backend immédiatement (effet immédiat sur stream)
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'surgical_mode': enabled})
        
        if enabled:
            # MODE CHIRURGICAL ACTIVÉ 🔬
            ui.notify('🔬 Mode Chirurgical: Stream 720p forcé, captures 1080p @ 95%', type='info')
            
            # DÉSACTIVER le slider résolution (forcé 720p en mode chirurgical)
            resolution_select.set_enabled(False)
            resolution_hint.set_text('🔬 Mode Chirurgical: Stream 720p fixe (optimisé détails)')
            
            # Auto-config optimale
            # 1. Qualité capture IA maximale
            if perception_ui.current_config.get('jpeg_quality', 85) < 95:
                perception_ui.current_config['jpeg_quality'] = 95
                jpeg_quality_slider.set_value(95)
                jpeg_quality_label.set_text('95%')
            
            # 2. Stream qualité bonne (80% pour voir détails)
            if perception_ui.current_config.get('stream_quality', 75) < 80:
                perception_ui.current_config['stream_quality'] = 80
                stream_quality_slider.set_value(80)
                stream_quality_label.set_text('80%')
            
            # 3. FPS modéré si trop élevé (économie CPU)
            current_fps = perception_ui.current_config.get('display_fps', 15)
            if current_fps > 15:
                ui.notify('💡 FPS réduit à 15 (optimal mode chirurgical)', type='info')
                perception_ui.current_config['display_fps'] = 15
                display_fps_slider.set_value(15)
                display_fps_label.set_text('15 fps')
        else:
            # MODE NORMAL RESTAURÉ
            ui.notify('📹 Mode Normal: Utilisez slider Résolution', type='info')
            
            # RÉACTIVER le slider résolution
            resolution_select.set_enabled(True)
            resolution_hint.set_text('💡 En mode Normal, choisissez résolution selon besoin')
            
            # Restaurer config normale
            if perception_ui.current_config.get('jpeg_quality', 85) == 95:
                perception_ui.current_config['jpeg_quality'] = 85
                jpeg_quality_slider.set_value(85)
                jpeg_quality_label.set_text('85%')
            
            if perception_ui.current_config.get('stream_quality', 75) == 80:
                perception_ui.current_config['stream_quality'] = 75
                stream_quality_slider.set_value(75)
                stream_quality_label.set_text('75%')
        
        # Pas de sauvegarde auto - attendre bouton Sauvegarder
    
    def on_stream_quality_change(e):
        """Change la qualité du stream preview"""
        value = e.args if isinstance(e.args, (int, float)) else stream_quality_slider.value
        perception_ui.current_config['stream_quality'] = int(value)
        stream_quality_label.set_text(f'{int(value)}%')
        # Pas de sauvegarde auto
    
    def save_config():
        """Sauvegarde la configuration et redémarre si nécessaire"""
        try:
            # Sauvegarder config AVANT (pour détecter changements)
            old_webcam_index = perception_ui.perception_agent.webcam_index if perception_ui.perception_agent else None
            old_surgical_mode = perception_ui.perception_agent.config.get('surgical_mode', False) if perception_ui.perception_agent else False
            
            # Sauvegarder la config
            perception_ui.update_config(perception_ui.current_config)
            
            # Détecter si changements critiques nécessitent restart
            new_webcam_index = perception_ui.current_config.get('webcam_index')
            new_surgical_mode = perception_ui.current_config.get('surgical_mode', False)
            
            needs_restart = False
            restart_reasons = []
            
            if old_webcam_index is not None and new_webcam_index != old_webcam_index:
                needs_restart = True
                restart_reasons.append(f'caméra {old_webcam_index}→{new_webcam_index}')
            
            if old_surgical_mode != new_surgical_mode:
                needs_restart = True
                mode_name = 'Chirurgical' if new_surgical_mode else 'Normal'
                restart_reasons.append(f'mode {mode_name}')
            
            if needs_restart and perception_ui.is_enabled:
                reason_str = ', '.join(restart_reasons)
                ui.notify(f'⚙️ Redémarrage agent ({reason_str})...', type='info')
                perception_ui.restart_perception_agent()
            else:
                ui.notify('✅ Configuration sauvegardée !', type='positive')
                
        except Exception as e:
            ui.notify(f'❌ Erreur sauvegarde: {e}', type='negative')
            print(f"[PERCEPTION-PAGE] Erreur save_config: {e}")
    
    def on_timeline_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else timeline_toggle.value
        perception_ui.current_config['motion_timeline'] = enabled
        # Pas de sauvegarde auto
    
    def on_annotations_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else annotations_toggle.value
        perception_ui.current_config['motion_annotations'] = enabled
        # Pas de sauvegarde auto
    
    def on_save_captures_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else save_captures_toggle.value
        perception_ui.current_config['save_captures'] = enabled
        if enabled:
            ui.notify('💾 Captures seront sauvegardées dans ./captures/', type='info')
        else:
            ui.notify('🚫 Captures non sauvegardées (mode preview uniquement)', type='info')
        # Pas de sauvegarde auto
    
    # Connecter les handlers
    perception_toggle.on('update:model-value', on_toggle_perception)
    capture_btn.on('click', on_capture_click)
    motion_btn.on('click', on_motion_click)
    motion_toggle.on('update:model-value', on_motion_toggle)
    capture_delay_slider.on('update:model-value', on_capture_delay_change)
    motion_interval_slider.on('update:model-value', on_motion_interval_change)
    frames_count_slider.on('update:model-value', on_frames_count_change)
    layout_select.on('update:model-value', on_layout_change)
    timeline_toggle.on('update:model-value', on_timeline_toggle)
    annotations_toggle.on('update:model-value', on_annotations_toggle)
    save_captures_toggle.on('update:model-value', on_save_captures_toggle)
    camera_select.on('update:model-value', on_camera_change)
    resolution_select.on('update:model-value', on_resolution_change)
    display_fps_slider.on('update:model-value', on_display_fps_change)
    stream_quality_slider.on('update:model-value', on_stream_quality_change)
    jpeg_quality_slider.on('update:model-value', on_jpeg_quality_change)
    surgical_mode_switch.on('update:model-value', on_surgical_mode_change)
    save_btn.on('click', save_config)  # Bouton sauvegarder
    
    # Initialiser visibilité motion params
    motion_params.set_visibility(perception_ui.current_config.get('motion_capture_enabled', False))
    
    print("[PERCEPTION-PAGE] ✅ Page Perception chargée")


def main_page():
    print("[DEBUG-MAIN] main_page() appelée !")
    _link_styles()
    ui.dark_mode()

    # [ARCHI_SENSOR] Extension Archi_sensor active
    print("[INIT] Extension Archi_sensor activée")

    global _conv_area, _chat_inner
    
    # 🪞 COGNITIVE MIRROR: Initialisation précoce au démarrage
    try:
        _ensure_cognitive_mirror()
        print("[INIT] BRAIN Cognitive Mirror préinitialisé")
    except Exception as e:
        print(f"[INIT] WARN Erreur préinitialisation Cognitive Mirror: {e}")

    # JOURNAL JOURNAL DE BORD: Initialisation précoce au démarrage
    try:
        # Initialisation différée - sera appelée quand l'Archiviste sera prêt
        print("[INIT] JOURNAL Journal de Bord - initialisation programmée")
        # Force la tentative d'initialisation
        _initialize_journal_extension()
    except Exception as e:
        print(f"[INIT] WARN Erreur initialisation Journal de Bord: {e}")

    # BIOGRAPHIE PROFIL EXTENSION - Initialisation
    try:
        print("[INIT] BIOGRAPHY Biographie Profil - initialisation programmée")
        _initialize_biography_extension()
    except Exception as e:
        print(f"[INIT] WARN Erreur initialisation Biographie Profil: {e}")

    print("[DEBUG-MAIN] Appel _header()...")
    try:
        _header()
        print("[DEBUG-MAIN] _header() terminé")
    except Exception as e:
        print(f"[DEBUG-MAIN] ERREUR dans _header(): {e}")
        import traceback
        traceback.print_exc()

    # Initialiser l'audio manager au démarrage
    try:
        _ensure_audio_manager()
        print("[INIT] Audio manager initialisé au démarrage")
    except Exception as e:
        print(f"[INIT] Erreur initialisation audio manager: {e}")
    
    # Initialiser le memory manager (avec archiviste + embedding)
    try:
        _ensure_memory_manager()
        print("[INIT] Memory manager initialisé au démarrage")
    except Exception as e:
        print(f"[INIT] Erreur initialisation memory manager: {e}")
    
    # Extension Archi_sensor activée par défaut
    print("[INIT] Archi_sensor extension initialized")
    
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

                # Process metacognitive updates from Archi-sensor
                if isinstance(msg, dict) and msg.get('type') == 'metacognitive_update':
                    data = msg.get('data', {})
                    print(f"[QUEUE] Archi-sensor update: {data}")
                    _update_led_gauges(data)

                # Process legitimate status messages (from memory_manager, core_logic, etc.)
                elif isinstance(msg, str):
                    # Standard status message from system components
                    print(f"[QUEUE] {msg}")

            # Log for debug timer (only if messages processed)
            if messages_processed > 0:
                print(f"[QUEUE] Timer processed {messages_processed} message(s)")
        except queue.Empty:
            pass  # Normal, queue empty
    
    # Timer pour traiter les notifications audio en arrière-plan
    ui.timer(0.2, _process_pending_notifications)
    
    # Timer pour traiter la status_queue (messages système)
    ui.timer(0.6, _drain_status_queue)
    
    # Timer pour traiter les messages Subconscience
    ui.timer(0.5, _process_subconscience_messages)  # Vérifier toutes les 500ms
    
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
    
    # Boutons flottants (hamburger + paramètres + logo)
    with ui.element('div').classes('floating-buttons'):
        toggle_btn = ui.button(icon='menu').classes('sidebar-toggle').props('title="Masquer/Afficher les conversations"')
        # Bouton paramètres flottant (copie des paramètres de la sidebar)
        settings_dialog = _settings_hub_modal()
        settings_btn = ui.button(icon='settings').classes('settings-floating-btn').props('title="Paramètres généraux"')
        settings_btn.on('click', settings_dialog.open)
        # Logo OGMA à droite des boutons (58px)
        ui.html('<img src="/static/OGMAlogopet.png" style="height: 58px; width: auto; opacity: 0.8; margin-left: 8px;" alt="OGMA Logo">')
    
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
            
            # Layer 5: bande fixe en bas (alignée à la colonne chat) pour matérialiser la limite basse
            ui.element('div').classes('chat-bottom-fixed').props('aria-hidden="true" data-role="chat-bottom-fixed"')
    
    # 🪞 COGNITIVE MIRROR: Initialisation de l'overlay avec conteneur UI
    try:
        cognitive_mirror = _ensure_cognitive_mirror()
        if cognitive_mirror and cognitive_mirror.ui_components:
            # Créer l'overlay dans le contexte UI principal
            cognitive_mirror.ui_components.create_overlay()
            print("[OGMA] 🪞 Overlay Cognitive Mirror initialisé")
    except Exception as e:
        print(f"[OGMA] WARN Erreur initialisation overlay Cognitive Mirror: {e}")
    
    # Logique toggle sidebar (animation volet horizontal avec recentrage du contenu)
    def _toggle_sidebar():
        ui.run_javascript('''
            const sidebar = document.querySelector('.sidebar');
            const mainContent = document.querySelector('.chat-panel');
            if (!sidebar) return;
            
            // Debug simplifié - plus besoin de tracker inputOverlay
            console.log('Toggle Debug - Avant:');
            if (mainContent) console.log('MainContent marginLeft:', getComputedStyle(mainContent).marginLeft);
            
            // Utiliser un attribut data pour un état fiable
            const isCollapsed = sidebar.getAttribute('data-collapsed') === 'true';
            
            if (isCollapsed) {
                // Ouvrir le volet - état normal avec sidebar visible
                sidebar.style.transform = 'translateX(0)';
                sidebar.style.transition = 'transform 0.3s ease-in-out';
                sidebar.setAttribute('data-collapsed', 'false');
                localStorage.setItem('ogma_sidebar_collapsed', 'false');
                
                // Contenu principal reste à sa position normale (centrée par défaut)
                if (mainContent) {
                    mainContent.style.marginLeft = '0px';
                    mainContent.style.transition = 'margin-left 0.3s ease-in-out';
                }
                
                // Note: input-overlay dans footer suit automatiquement mainContent
            } else {
                // Fermer le volet - contenu s'étend vers la gauche
                sidebar.style.transform = 'translateX(-100%)';
                sidebar.style.transition = 'transform 0.3s ease-in-out';
                sidebar.setAttribute('data-collapsed', 'true');
                localStorage.setItem('ogma_sidebar_collapsed', 'true');
                
                // Décaler le contenu vers la gauche pour occuper l'espace de la sidebar
                if (mainContent) {
                    mainContent.style.marginLeft = '-280px';
                    mainContent.style.transition = 'margin-left 0.3s ease-in-out';
                }
                
                // Note: input-overlay dans footer suit automatiquement mainContent
            }
            
            // Debug simplifié après toggle
            setTimeout(() => {
                console.log('Toggle Debug - Après:');
                if (mainContent) console.log('MainContent marginLeft:', getComputedStyle(mainContent).marginLeft);
                console.log('Input-overlay suit automatiquement dans footer');
            }, 100);
        ''')
    
    toggle_btn.on('click', _toggle_sidebar)
    
    # UI layout complete
    
    # Initialisation sidebar (restaure l'état depuis localStorage avec délai)
    try:
        ui.run_javascript('''
            setTimeout(() => {
                // Restaurer l'état du volet sidebar avec architecture footer intégrée
                const sidebar = document.querySelector('.sidebar');
                const mainContent = document.querySelector('.chat-panel');
                
                if (sidebar) {
                    const isCollapsed = localStorage.getItem('ogma_sidebar_collapsed') === 'true';
                    
                    // Initialiser l'attribut data-collapsed
                    sidebar.setAttribute('data-collapsed', isCollapsed.toString());
                    
                    if (isCollapsed) {
                        // Sidebar fermée - contenu s'étend vers la gauche
                        sidebar.style.transform = 'translateX(-100%)';
                        sidebar.style.transition = 'transform 0.3s ease-in-out';
                        
                        // Contenu principal décalé vers la gauche pour occuper l'espace
                        if (mainContent) {
                            mainContent.style.marginLeft = '-280px';
                            mainContent.style.transition = 'margin-left 0.3s ease-in-out';
                        }
                        
                        // Note: input-overlay dans footer suit automatiquement mainContent
                    } else {
                        // Sidebar ouverte - état normal (centré par défaut)
                        sidebar.style.transform = 'translateX(0)';
                        sidebar.style.transition = 'transform 0.3s ease-in-out';
                        
                        // Contenu principal à sa position normale
                        if (mainContent) {
                            mainContent.style.marginLeft = '0px';
                            mainContent.style.transition = 'margin-left 0.3s ease-in-out';
                        }
                        
                        // Note: input-overlay dans footer suit automatiquement mainContent
                    }
                }
            }, 100);
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
        const atBottom = ()=> (scrollEl.scrollHeight - scrollEl.scrollTop - scrollEl.clientHeight <= 24);
        const update = ()=>{
            if(btn){ btn.style.display = atBottom() ? 'none' : 'flex'; }
            window.OGMA_autoScroll = atBottom();
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


def _update_led_gauges(data):
    """DÉPLACÉE: Redirige vers ogma_displays._update_led_gauges()"""
    from ogma_displays import _update_led_gauges as update_leds
    return update_leds(data)


def run_ogma(host: str = 'localhost', port: int = 8080):
    # Page principale
    ui.page('/')(main_page)
    
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
            print("[CLEANUP] Nettoyage terminé")
        except Exception as e:
            print(f"[CLEANUP] Erreur lors du nettoyage: {e}")
    
    atexit.register(cleanup_on_exit)
    
    # Démarrer avec gestion d'erreur améliorée
    try:
        ui.run(
            title='OGMA - IA Conversationnelle', 
            host=host, 
            port=port, 
            reload=False, 
            show=True, 
            dark=True,
            reconnect_timeout=60.0  # 60s au lieu de 3s par défaut pour les réponses IA longues
        )
    except KeyboardInterrupt:
        print("[INFO] Arrêt de l'application...")
        cleanup_on_exit()
    except Exception as e:
        print(f"[ERROR] Erreur durant l'exécution: {e}")
        cleanup_on_exit()


# === FONCTIONS DÉPLACÉES VERS ogma_ui_components.py ===
# Fonctions alias pour compatibilité

def _diagnostic_leds(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._diagnostic_leds()"""
    from ogma_displays import _diagnostic_leds as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _test_simple_led(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._test_simple_led()"""
    from ogma_displays import _test_simple_led as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _test_gauges(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._test_gauges()"""
    from ogma_displays import _test_gauges as moved_func
    return moved_func(*args, **kwargs)


# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _test_led_system(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._test_led_system()"""
    from ogma_displays import _test_led_system as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
async def _manual_memorize_current_input(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._manual_memorize_current_input()"""
    from ogma_modals import _manual_memorize_current_input as moved_func
    return await moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _link_styles(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._link_styles()"""
    from ogma_displays import _link_styles as moved_func
    return moved_func(*args, **kwargs)

# FONCTIONS DÉPLACÉES vers ogma_tts_config.py
def _render_tts_config(*args, **kwargs):
    """DÉPLACÉE: Redirige vers ogma_tts_config._render_tts_config()"""
    from ogma_tts_config import _render_tts_config as moved_func
    return moved_func(*args, **kwargs)

# FONCTIONS DÉPLACÉES vers ogma_profile.py
def _profile_modal(*args, **kwargs):
    """DÉPLACÉE: Redirige vers ogma_profile._profile_modal()"""
    from ogma_profile import _profile_modal as moved_func
    return moved_func(*args, **kwargs)



def _create_edit_interface_moved(*args, **kwargs):
    """DÉPLACÉE: Redirige vers ogma_profile._create_edit_interface()"""
    from ogma_profile import _create_edit_interface as moved_func
    return moved_func(*args, **kwargs)

# FONCTIONS DÉPLACÉES vers ogma_headers.py
def _header(*args, **kwargs):
    """DÉPLACÉE: Redirige vers ogma_headers._header()"""
    from ogma_headers import _header as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _instructions_modal(*args, **kwargs):
    """DÉPLACÉE: Redirige vers ogma_modals._instructions_modal()"""
    from ogma_modals import _instructions_modal as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _settings_hub_modal(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._settings_hub_modal()"""
    from ogma_modals import _settings_hub_modal as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _archi_sensor_modal(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._archi_sensor_modal()"""
    from ogma_modals import _archi_sensor_modal as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _memory_modal(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._memory_modal()"""
    from ogma_modals import _memory_modal as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _edit_memory_popup(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._edit_memory_popup()"""
    from ogma_modals import _edit_memory_popup as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _memorization_popup(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._memorization_popup()"""
    from ogma_modals import _memorization_popup as moved_func
    return moved_func(*args, **kwargs)

# FONCTION DÉPLACÉE vers les nouveaux modules modulaires
def _open_other_backends_popup(*args, **kwargs):
    """DÉPLACÉE: Redirige vers le module approprié._open_other_backends_popup()"""
    from ogma_modals import _open_other_backends_popup as moved_func
    return moved_func(*args, **kwargs)


if __name__ == "__main__":
    run_ogma()
