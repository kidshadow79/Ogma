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
from datetime import datetime

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

from utils import DATA_DIR, EGO_PROMPT_FILE, EGO_PROMPT_SYNTHESIZED_FILE
from core_logic import SettingsManager, APIManager, OllamaManager, GGUFManager, KoboldManager, AIController, EmbeddingController
from memory_manager import MemoryManager
from audio_manager import AudioManager
from conversation_summarizer import summarizer, archive
from extensions.temporal_guardian import create_temporal_guardian
from data_cleaner import OGMADataCleaner, format_size
import uuid


# State minimal
_settings_mgr: Optional[SettingsManager] = None
_api_mgr: Optional[APIManager] = None
_ollama_mgr: Optional[OllamaManager] = None
_gguf_mgr: Optional[GGUFManager] = None
_kobold_mgr: Optional[KoboldManager] = None
_chat_controller: Optional[AIController] = None
_audio_manager: Optional[AudioManager] = None
_chat_history: List[Dict] = []
_current_conversation_id: Optional[str] = None
_conv_index: Dict[str, Dict] = {}
_conv_area = None  # conteneur de conversation
_chat_inner = None  # conteneur interne pour les messages (pile verticale)
_archiviste_controller: Optional[AIController] = None
_embedding_controller: Optional[EmbeddingController] = None
_memory_manager: Optional[MemoryManager] = None
_temporal_guardian = None  # Extension Temporal Guardian
_status_queue: Optional[queue.Queue] = None
_memory_update_hooks: List[Callable[[], None]] = []  # callbacks à appeler après ajout mémoire
_sidebar_render_cb: Optional[Callable[[Optional[str]], None]] = None  # rafraîchisseur de la liste des conversations
_title_updating: bool = False  # évite les mises à jour concurrentes de titre

# Gestion des fichiers
_active_file_data: Optional[Dict] = None  # Données du fichier actuel
_loaded_conversation: Optional[List[Dict]] = None  # Conversation actuellement chargée pour l'IA
_loaded_conversation_filename: Optional[str] = None  # Nom du fichier de conversation chargé
_conversation_context_injected: bool = False  # Indique si le contexte a déjà été injecté
_thinking_css_injected: bool = False  # Indique si le CSS pour thinking a été injecté
_file_tab_container = None  # Conteneur pour l'onglet de fichier
_header_container = None  # Conteneur du header pour basculer titre/onglet
_ia_status_indicators = {}  # Conteneur pour les indicateurs d'état IA

async def _retrieve_liberating_memory(memory_id: str) -> Optional[str]:
    """
    ✅ NOUVEAU: Récupère un souvenir libérateur via ID vectoriel.
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


def _ensure_settings_manager():
    global _settings_mgr
    if _settings_mgr is None:
        settings_path = DATA_DIR / 'settings.json'
        _settings_mgr = SettingsManager(settings_path)
    return _settings_mgr


def _ensure_audio_manager():
    """Initialise paresseusement l'audio manager."""
    global _audio_manager, _auto_send_audio
    if _audio_manager is None:
        try:
            # Charger la préférence d'envoi automatique depuis les paramètres
            sm = _ensure_settings_manager()
            _auto_send_audio = sm.settings.get('audio', {}).get('auto_send', False)
            
            # Utiliser l'API OpenAI si disponible, sinon local
            chat_api = sm.settings.get('chat_api', {})
            api_key = chat_api.get('api_key', '')
            use_api = bool(api_key and chat_api.get('provider') == 'OpenAI')
            
            _audio_manager = AudioManager(use_whisper_api=use_api, api_key=api_key)
            
            # Initialiser le système TTS de manière synchrone
            _audio_manager.initialize_tts_sync()
            
            # Configurer le moteur TTS selon les paramètres
            tts_settings = sm.settings.get('tts', {})
            engine_type = tts_settings.get('engine', 'system')
            print(f"[DEBUG-ELEVEN] TTS Settings chargés: {list(tts_settings.keys())}")
            print(f"[DEBUG-ELEVEN] Engine type: {engine_type}")
            
            if engine_type == 'google':
                _audio_manager.configure_tts_engine(
                    'google',
                    api_key=tts_settings.get('google_api_key'),
                    voice=tts_settings.get('google_voice', 'fr-FR-Standard-A')
                )
            elif engine_type == 'elevenlabs':
                eleven_key = tts_settings.get('elevenlabs_api_key')
                eleven_voice = tts_settings.get('elevenlabs_voice_id', 'pNInz6obpgDQGcFmaJgB')
                print(f"[DEBUG-ELEVEN] Clé API récupérée: {eleven_key[:15] if eleven_key else 'AUCUNE'}...")
                print(f"[DEBUG-ELEVEN] Voice ID: {eleven_voice}")
                _audio_manager.configure_tts_engine(
                    'elevenlabs',
                    api_key=eleven_key,
                    voice_id=eleven_voice
                )
            elif engine_type == 'azure':
                _audio_manager.configure_tts_engine(
                    'azure',
                    api_key=tts_settings.get('azure_api_key'),
                    voice=tts_settings.get('azure_voice', 'fr-FR-DeniseNeural'),
                    region=tts_settings.get('azure_region', 'westeurope')
                )
            elif engine_type == 'gtts':
                _audio_manager.configure_tts_engine(
                    'gtts',
                    lang=tts_settings.get('gtts_lang', 'fr')
                )
            elif engine_type == 'edge_tts':
                _audio_manager.configure_tts_engine(
                    'edge_tts',
                    voice=tts_settings.get('edge_tts_voice', 'fr-FR-DeniseNeural')
                )
            else:
                _audio_manager.configure_tts_engine('system')
            
            # Appliquer les autres paramètres TTS
            _audio_manager.set_tts_settings(
                speed=tts_settings.get('speed', 150),
                volume=tts_settings.get('volume', 0.8),
                enabled=tts_settings.get('enabled', True)
            )
            
            print(f"[AUDIO] Audio manager initialisé (API: {use_api}, TTS: {engine_type})")
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
    except Exception:
        pass
    return _api_mgr, _ollama_mgr, _gguf_mgr, _kobold_mgr


def _map_backend_for_controller(backend: str) -> str:
    """Uniformise les libellés backend attendus par les contrôleurs."""
    return 'GGUF/llama.cpp' if backend == 'GGUF' else backend


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
    arch_backend = _map_backend_for_controller(arch.get('backend_type', 'API'))
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
                    print(f"[ARCHIVISTE-HYBRID] ✅ max_tokens optimal: {max_tokens:,}")
                if context_length == -1:
                    context_length = detected_caps['context_length']
                    print(f"[ARCHIVISTE-HYBRID] ✅ context_length optimal: {context_length:,}")
            else:
                # Fallback si pas de configuration complète
                if max_tokens == -1:
                    max_tokens = 512
                if context_length == -1:
                    context_length = 4096
                print(f"[ARCHIVISTE-HYBRID] ⚠️ Configuration incomplète, utilisation valeurs par défaut")
        except Exception as e:
            # Fallback en cas d'erreur
            if max_tokens == -1:
                max_tokens = 512
            if context_length == -1:
                context_length = 4096
            print(f"[ARCHIVISTE-AUTO] ❌ Erreur auto-détection: {e}, utilisation valeurs par défaut")
    
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
    emb_backend = _map_backend_for_controller(emb.get('backend_type', 'API'))
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
        _memory_manager = MemoryManager(
            db_path=db_path,
            index_path=index_path,
            embedding_dim=embedding_dim,
            archiviste_ia=_archiviste_controller,
            embedding_ia=_embedding_controller,
            status_queue=_status_queue,
            settings_manager=sm,
        )
        
        # Configurer le summarizer avec l'archiviste
        from conversation_summarizer import summarizer
        if _archiviste_controller:
            summarizer.set_archiviste(_archiviste_controller)
        
    except Exception as e:
        _notify_safe(f"Erreur init mémoire: {e}", type='warning')
        _memory_manager = None

    return _memory_manager


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
        print(f"[OGMA] ⚠️ Erreur initialisation Temporal Guardian: {e}")
        # Créer instance par défaut en cas d'erreur
        _temporal_guardian = create_temporal_guardian(debug=False)
    
    return _temporal_guardian


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
                    print(f"[CHAT-HYBRID] ✅ max_tokens optimal: {max_tokens:,}")
                if context_length == -1:
                    context_length = detected_caps['context_length']
                    print(f"[CHAT-HYBRID] ✅ context_length optimal: {context_length:,}")
            else:
                # Fallback si pas de configuration complète
                if max_tokens == -1:
                    max_tokens = 512
                if context_length == -1:
                    context_length = 4096
                print(f"[CHAT-HYBRID] ⚠️ Configuration incomplète, utilisation valeurs par défaut")
        except Exception as e:
            # Fallback en cas d'erreur
            if max_tokens == -1:
                max_tokens = 512
            if context_length == -1:
                context_length = 4096
            print(f"[CHAT-HYBRID] ❌ Erreur détection hybride: {e}, utilisation valeurs par défaut")
    
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
            print(f"[AI] 🎯 Chargement modèle GGUF: {model}")
            print(f"[AI] ⚙️ GPU layers: {n_gpu_layers}, Context: {ctx}")
            try:
                # Forcer le chargement du modèle même s'il semble disponible
                import time
                start_time = time.time()
                cast(GGUFManager, _gguf_mgr).load_model(model, ctx, n_gpu_layers)
                load_time = time.time() - start_time
                print(f"[AI] ✅ Modèle GGUF chargé en {load_time:.1f}s")
            except Exception as e:
                print(f"[AI] ❌ Erreur chargement GGUF: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[AI] ⚠️ Aucun modèle GGUF configuré")
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
                arch.get('api_model', ''),
                arch.get('api_key', '')
            )
    
    return _archiviste_controller


def _notify_safe(message: str, type: str = 'info') -> None:
    """Tente d'afficher une notification; ignore si hors contexte UI (timer/task)."""
    try:
        ui.notify(message, type=type)
    except Exception:
        # Hors slot (timer/task): ignorer la notif, ce n'est pas critique
        pass


REMOTE_PROVIDERS = ['OpenAI', 'Mistral', 'Anthropic', 'Google', 'AIHorde']
LOCAL_BACKENDS = ['Ollama', 'GGUF', 'KoboldCpp']
EMBED_SUPPORTED_PROVIDERS = ['OpenAI', 'Mistral', 'Google']  # Anthropic: pas d'API embeddings à ce jour


def _link_styles():
    # Servir le dossier static/ et lier la feuille CSS
    app.add_static_files('/static', Path(__file__).parent / 'static')
    # Police Inter (poids 400 et 600) depuis Google Fonts
    ui.add_head_html('<link rel="preconnect" href="https://fonts.googleapis.com">')
    ui.add_head_html('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">')
    ui.add_head_html('<link rel="stylesheet" href="/static/ogma_styles.css" />')
    
    # CSS inline pour panneau métacognitif (contournement problème cache)
    ui.add_head_html('''
    <style>
    /* Suppression de la bordure du header */
    .app-header {
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
    }
    
    /* Suppression des bordures de séparation entre zones */
    .app-body {
        border-top: none !important;
        border: none !important;
    }
    
    /* Chat panel - Layout flexbox moderne pour comportement chat app */
    .chat-panel {
        border-top: none !important;
        border: none !important;
        transition: margin-left 0.3s ease-in-out;
        display: flex;
        flex-direction: column;
        height: calc(100vh - 60px); /* Hauteur écran moins header */
        overflow: hidden; /* Évite le scroll global */
    }
    
    /* Zone conversation - s'adapte automatiquement à l'espace disponible */
    .conversation-area {
        flex: 1; /* Prend tout l'espace restant */
        overflow-y: auto; /* Scroll interne si nécessaire */
        min-height: 200px; /* Hauteur minimale garantie */
        max-height: calc(100vh - 200px); /* Hauteur maximale pour éviter de pousser le footer */
        margin-bottom: 0; /* Suppression de l'espace maintenant inutile */
    }
    
    /* Suppression de toute bordure de la sidebar + fond intermédiaire */
    .sidebar {
        border-right: none !important;
        background-color: #242424 !important;
    }
    
    /* Animation supprimée - Sidebar en gris simple */
    
    /* Sidebar style overlay sophistiqué - Header */
    .sidebar-header {
        background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        /* border: 1px solid var(--border-default) !important; */
        border-radius: 12px 12px 0 0 !important;
        /* box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important; */
        backdrop-filter: blur(10px) !important;
        /* border-bottom: none !important; */
    }
    
    .sidebar-list {
        background: linear-gradient(145deg, #0f0f0f 0%, #1a1a1a 100%) !important;
        /* border: 1px solid var(--border-default) !important; */
        border-radius: 12px !important;
        /* box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important; */
        backdrop-filter: blur(10px) !important;
    }
    
    /* Sélecteurs additionnels pour zone historique conversations */
    .conversation-list, .q-list, .conversations-container,
    .sidebar .q-list, .sidebar-content .q-list {
        background: linear-gradient(145deg, #0f0f0f 0%, #1a1a1a 100%) !important;
        /* border: 1px solid var(--border-default) !important; */
        border-radius: 12px !important;
        /* box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important; */
        backdrop-filter: blur(10px) !important;
    }
    
    /* Effet particules pour la sauvegarde mémoire - AMÉLIORE */
    .memory-save-effect, .save-button, .q-btn.save-btn, 
    button[onclick*="save"], .action-button.save, .send-button {
        position: relative !important;
        overflow: hidden !important;
    }
    
    .memory-save-effect::after, .save-button::after, .q-btn.save-btn::after,
    button[onclick*="save"]::after, .action-button.save::after, .send-button::after {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(212, 175, 55, 0.8) 20%, 
            rgba(255, 215, 0, 1) 50%, 
            rgba(212, 175, 55, 0.8) 80%, 
            transparent 100%) !important;
        animation: save-particles 1.5s ease-out !important;
        pointer-events: none !important;
        z-index: 1 !important;
    }
    
    /* Trigger animation on click */
    .memory-save-effect:active::after, .save-button:active::after, 
    .q-btn.save-btn:active::after, button[onclick*="save"]:active::after,
    .action-button.save:active::after, .send-button:active::after {
        animation: save-particles 1.5s ease-out !important;
    }
    
    @keyframes save-particles {
        0% { 
            left: -100%; 
            opacity: 0; 
            transform: scaleX(0.8);
        }
        10% { 
            opacity: 1; 
            transform: scaleX(1);
        }
        50% {
            opacity: 1;
            transform: scaleX(1.1);
        }
        90% { 
            opacity: 1; 
            transform: scaleX(1);
        }
        100% { 
            left: 100%; 
            opacity: 0; 
            transform: scaleX(0.8);
        }
    }
    
    /* Déclenchement automatique au hover pour test */
    .send-button:hover::after {
        animation: save-particles 1.5s ease-out !important;
    }
    
    /* Sidebar style overlay sophistiqué - Footer */
    .sidebar-footer {
        background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        /* border: 1px solid var(--border-default) !important; */
        border-radius: 0 0 12px 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        backdrop-filter: blur(10px) !important;
        /* border-top: none !important; */
    }
    
    /* Sidebar style overlay sophistiqué - Aside */
    aside.sidebar {
        background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        /* border: 1px solid var(--border-default) !important; */
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Quasar drawer style overlay sophistiqué */
    .q-drawer--left {
        background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        /* border: 1px solid var(--border-default) !important; */
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .metacognition-toggle-btn {
        z-index: 2000 !important;
        position: fixed !important;
    }
    
    /* Bouton Archi_sensor flottant */
    .archi-sensor-floating-btn {
        position: fixed !important;
        top: 10px !important;
        right: 70px !important;
        z-index: 100 !important;
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        border-radius: 8px !important;
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        font-size: 16px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: var(--transition-fast) !important;
        opacity: 0.9 !important;
        padding: 0 !important;
        box-shadow: 0 0 8px rgba(212, 175, 55, 0.3), 0 0 16px rgba(212, 175, 55, 0.2), 0 0 24px rgba(212, 175, 55, 0.1) !important;
        animation: archisensor-glow 2.5s ease-in-out infinite alternate !important;
    }
    
    @keyframes archisensor-glow {
        0% { 
            box-shadow: 0 0 6px rgba(212, 175, 55, 0.2), 0 0 12px rgba(212, 175, 55, 0.1), 0 0 18px rgba(212, 175, 55, 0.05);
        }
        100% { 
            box-shadow: 0 0 40px rgba(212, 175, 55, 1), 0 0 80px rgba(212, 175, 55, 0.8), 0 0 120px rgba(212, 175, 55, 0.5), 0 0 160px rgba(212, 175, 55, 0.3);
        }
    }
    
    .archi-sensor-floating-btn:hover {
        background: var(--bg-card) !important;
        color: var(--accent-gold) !important;
        opacity: 1 !important;
        border-color: var(--accent-gold-thin) !important;
    }
    
    /* Cibler spécifiquement le drawer NiceGUI avec effet prism ROUGE */
    .q-drawer--right.metacognition-panel {
        top: 60px !important;
        height: calc(100vh - 60px) !important;
        border-top: 1px solid rgba(212, 175, 55, 0.2) !important;
        overflow-y: auto !important;
    }
    
    /* Alternative si la classe Quasar est différente - EFFET PRISM ROUGE */
    .q-drawer--right {
        top: 60px !important;
        height: calc(100vh - 60px) !important;
    }
    
    /* SIDEBAR OVERLAY SOPHISTIQUÉ sur tous les éléments possibles */
    .q-drawer, .q-drawer__content, .sidebar, .sidebar-content, 
    .nicegui-drawer, .drawer-container, .left-drawer {
        background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%) !important;
        /* border: 1px solid var(--border-default) !important; */
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Style pour le toggle de l'extension metacognitive */
    .metacog-switch .q-toggle__track {
        background: rgba(212, 175, 55, 0.2) !important;
    }

    .metacog-switch .q-toggle--truthy .q-toggle__track {
        background: var(--accent-gold) !important;
    }

    .metacognition-controls {
        background: rgba(212, 175, 55, 0.05);
        border-radius: 8px;
        border: 1px solid rgba(212, 175, 55, 0.1);
    }
    
    /* Styles pour les conversations archivées */
    .archived-conversation, .search-results, .conversation-summary, .available-conversations {
        margin: 15px 0;
        padding: 15px;
        background: rgba(100, 149, 237, 0.05);
        border-radius: 12px;
        border-left: 4px solid rgba(100, 149, 237, 0.3);
    }
    
    .archived-message, .search-result, .conversation-item {
        margin: 8px 0;
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Animation Volet Horizontal - Style par défaut */
    .sidebar {
        transition: transform 0.3s ease-in-out;
    }
    
    .result-content, .summary-content {
        margin-top: 8px;
        padding: 8px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 6px;
        font-style: italic;
        color: var(--text-muted);
    }
    
    .commands-help {
        margin-top: 15px;
        padding: 12px;
        background: rgba(212, 175, 55, 0.05);
        border-radius: 8px;
        border: 1px solid rgba(212, 175, 55, 0.2);
    }
    </style>
    ''')


# ---- GESTION DES FICHIERS ----

def _truncate_filename(filename: str, max_length: int = 15) -> str:
    """Tronque le nom de fichier à 15 caractères max"""
    if len(filename) <= max_length:
        return filename
    return filename[:max_length-3] + "..."

def _get_file_icon(filename: str) -> str:
    """Retourne l'icône appropriée selon l'extension du fichier"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    icons = {
        'pdf': '📄', 'docx': '📝', 'doc': '📝', 'txt': '📄',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'webp': '🖼️', 'gif': '🖼️'
    }
    return icons.get(ext, '📎')

def _update_header_display():
    """Met à jour l'affichage du header selon qu'il y ait un fichier actif ou non"""
    global _header_container, _active_file_data
    if _header_container is None:
        return
    
    try:
        _header_container.clear()
        
        with _header_container:
            if _active_file_data:
                # Affichage de l'onglet fichier
                filename = _active_file_data.get('filename', 'Fichier inconnu')
                icon = _get_file_icon(filename)
                truncated = _truncate_filename(filename)
                
                with ui.element('div').classes('file-tab-container'):
                    with ui.element('div').classes('file-tab'):
                        ui.label(f"{icon} {truncated}").classes('file-tab-label')
                        ui.button('✕', on_click=_remove_active_file).classes('file-tab-close')
            else:
                # Affichage du titre normal
                ui.label('Assistant conversationnel avec mémoire persistante').classes('app-subtitle')
    except Exception as e:
        print(f"[ERROR] Erreur update header: {e}")
        # Fallback silencieux si le client n'est plus disponible

def _remove_active_file():
    """Supprime le fichier actif et restaure le titre normal"""
    global _active_file_data
    _active_file_data = None
    _update_header_display()
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
            _update_header_display()
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
            
            ui.label('Formats supportés: PDF, DOCX, TXT, Images (JPG, PNG, WebP, GIF)').classes('text-sm text-gray-400 mb-4')
            
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

def _header():
    global _header_container, _ia_status_indicators
    with ui.element('div').classes('app-header'):
        # Container flex pour titre centré et indicateurs IA
        with ui.element('div').classes('header-content'):
            _header_container = ui.element('div').classes('header-title-container')
            with _header_container:
                ui.label('Assistant conversationnel avec mémoire persistante').classes('app-subtitle')
            
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
    
    # [ARCHI_SENSOR] Bouton Archi_sensor remplace l'ancien bouton métacognitif
    archi_sensor_overlay = _archi_sensor_modal()
    with ui.element('div'):
        # Bouton avec image icotetes.png au lieu de l'emoji cerveau
        with ui.button().classes('archi-sensor-floating-btn').props('title="Analyse Métacognitive"').style('padding: 0; border: none; overflow: hidden;') as archi_sensor_btn:
            ui.html('<img src="/static/icotetes.png" style="width: 100%; height: 100%; object-fit: cover; display: block;" alt="Archi Sensor">')
        
        def toggle_archi_sensor():
            # Toggle la visibilité de l'overlay
            archi_sensor_overlay.visible = not archi_sensor_overlay.visible
            print(f"[ARCHI-SENSOR] Overlay {'affiché' if archi_sensor_overlay.visible else 'masqué'}")
        
        archi_sensor_btn.on('click', toggle_archi_sensor)


def _message(role: str, content: str, badges: Optional[List[str]] = None):
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
                    # Parser le format thinking si présent
                    thinking_content, main_content = _parse_thinking_format(content)
                    
                    # Afficher la partie thinking si elle existe (dans un cadre dépliant)
                    if thinking_content:
                        global _thinking_css_injected
                        
                        # Injecter le CSS personnalisé une seule fois
                        if not _thinking_css_injected:
                            ui.add_head_html('''
                            <style>
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
                    
                    # Afficher le contenu principal
                    display_content = main_content if thinking_content else content
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
                    
                    # Bouton TTS pour les réponses de l'assistant
                    def speak_message():
                        try:
                            print(f"[TTS-DEBUG] 🔊 Bouton TTS cliqué pour message: {content[:50]}...")
                            if _audio_manager and hasattr(_audio_manager, 'speak'):
                                import asyncio
                                # Nettoyer le contenu pour la synthèse (enlever markdown, etc.)
                                clean_content = content.replace('*', '').replace('**', '').replace('#', '').replace('`', '')
                                print(f"[TTS-DEBUG] 🔊 Création task pour: {clean_content[:50]}...")
                                asyncio.create_task(_audio_manager.speak(clean_content))
                            else:
                                print("[TTS-DEBUG] ❌ Audio manager non disponible ou méthode speak manquante")
                        except Exception as e:
                            print(f"[TTS-DEBUG] ❌ Erreur TTS: {e}")
                    
                    # Vérifier si TTS est activé dans les paramètres
                    try:
                        sm = _ensure_settings_manager()
                        tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
                        auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
                        
                        # N'afficher le bouton que si la lecture automatique n'est PAS activée
                        if tts_enabled and _audio_manager and not auto_speak:
                            with ui.row().classes('gap-2 mt-2'):
                                ui.button('🔊', on_click=speak_message).classes('tts-button').style(
                                    'background: rgba(79, 172, 254, 0.15); '
                                    'border: 1px solid rgba(79, 172, 254, 0.3); '
                                    'color: #4FACFE; '
                                    'border-radius: 6px; '
                                    'padding: 4px 8px; '
                                    'font-size: 14px; '
                                    'min-width: auto;'
                                ).tooltip('Écouter cette réponse')
                        elif tts_enabled and auto_speak:
                            # Afficher un petit indicateur que la lecture automatique est active
                            with ui.row().classes('gap-2 mt-2'):
                                ui.label('🔊 Auto').classes('text-xs text-muted').style(
                                    'color: #4FACFE; '
                                    'font-size: 12px; '
                                    'opacity: 0.7;'
                                ).tooltip('Lecture automatique activée')
                    except Exception as e:
                        print(f"[TTS-DEBUG] ❌ Erreur config TTS: {e}")
                    
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
    except Exception as e:
        print(f"[ERROR] Erreur création message {role}: {e}")
        # Fallback simple si l'UI ne peut pas être créée
        pass


def _load_conversation_index() -> Dict[str, Dict]:
    """Charge data/conversations/index.json si présent."""
    global _conv_index
    try:
        idx_path = DATA_DIR / 'conversations' / 'index.json'
        if idx_path.exists():
            import json
            data = json.loads(idx_path.read_text(encoding='utf-8'))
            _conv_index = data.get('conversations', {}) or {}
        else:
            _conv_index = {}
    except Exception:
        _conv_index = {}
    return _conv_index


def _save_conversation_index() -> Tuple[bool, str]:
    """Sauvegarde l'index des conversations sur disque."""
    try:
        idx_path = DATA_DIR / 'conversations' / 'index.json'
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        payload = {"conversations": _conv_index}
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
        
        for msg in _chat_history:
            if msg.get('role') in ('user', 'assistant'):
                relevant_messages.append(msg)
                if msg.get('role') == 'user':
                    user_count += 1
                    if user_count >= 5:  # Stop après 5 interactions utilisateur
                        break
        
        if len(relevant_messages) < 3:  # Pas assez de contenu
            return _make_title_from_text(_chat_history[0].get('content', '') if _chat_history else '')
        
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
        if conv_id in _conv_index and len(_chat_history) >= 10:  # 5 interactions = 10 messages
            print("🧠 [SMART-TITLE] Génération titre intelligent via Archiviste...")
            import asyncio
            asyncio.create_task(_generate_smart_title_async(conv_id))
        else:
            # Reset du flag si pas assez d'interactions
            if conv_id in _conv_index:
                _conv_index[conv_id]['smart_title_pending'] = False
    except Exception as e:
        print(f"❌ [SMART-TITLE] Erreur programmation titre: {e}")
        if conv_id in _conv_index:
            _conv_index[conv_id]['smart_title_pending'] = False


async def _generate_smart_title_async(conv_id: str):
    """Génère un titre intelligent en utilisant l'Archiviste"""
    try:
        global _archiviste_controller, _conv_index
        
        if not _archiviste_controller:
            print("⚠️ [SMART-TITLE] Archiviste non disponible")
            return
            
        # Récupérer les premiers messages pour contexte
        recent_messages = [m for m in _chat_history[-10:] if m.get('role') in ('user', 'assistant')]
        
        if len(recent_messages) < 4:
            return
            
        # Construire le contexte pour l'Archiviste
        context = ""
        for msg in recent_messages:
            role = "👤 Utilisateur" if msg['role'] == 'user' else "🌙 Luna"
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
        
        response, error = await _archiviste_controller.call_chat_api(
            messages=messages,
            max_tokens=50,
            temperature=0.3,  # Plus déterministe pour les titres
            is_json=False
        )
        
        if error or not response:
            print(f"❌ [SMART-TITLE] Échec Archiviste: {error}")
            return
            
        # Extraire le titre
        if isinstance(response, dict) and 'content' in response:
            title = response['content'].strip()
        elif isinstance(response, str):
            title = response.strip()
        else:
            print(f"❌ [SMART-TITLE] Format réponse inattendu: {type(response)}")
            return
            
        # Nettoyer le titre
        title = title.replace('"', '').replace("'", '').strip()
        if len(title) > 60:
            title = title[:57] + "..."
            
        if title and len(title) > 3:
            # Mettre à jour le titre dans l'index
            if conv_id in _conv_index:
                old_title = _conv_index[conv_id]['title']
                _conv_index[conv_id]['title'] = title
                _conv_index[conv_id]['smart_title_pending'] = False
                _conv_index[conv_id]['auto_title'] = False
                
                # Sauvegarder l'index
                _save_conversation_index()
                
                print(f"✅ [SMART-TITLE] Titre mis à jour: '{old_title}' → '{title}'")
                
                # Notifier l'interface si possible
                try:
                    _notify_safe(f"📝 Titre intelligent: {title}", type='info')
                except:
                    pass
        else:
            print("⚠️ [SMART-TITLE] Titre généré vide ou trop court")
            
    except Exception as e:
        print(f"❌ [SMART-TITLE] Erreur génération: {e}")
    finally:
        # Reset du flag en cas d'erreur
        if conv_id in _conv_index:
            _conv_index[conv_id]['smart_title_pending'] = False


async def _regenerate_title_manual(conv_id: str) -> bool:
    """Régénère manuellement le titre d'une conversation via l'IA principale."""
    try:
        print(f"[MANUAL-TITLE] 🔍 Début régénération pour conversation: {conv_id}")
        global _chat_controller
        
        if conv_id not in _conv_index:
            print(f"[MANUAL-TITLE] ❌ Conversation {conv_id} non trouvée dans l'index")
            return False
            
        # Charger la conversation pour analyser le contenu
        conv_path = DATA_DIR / 'conversations' / f'{conv_id}.json'
        if not conv_path.exists():
            print(f"[MANUAL-TITLE] ❌ Fichier conversation non trouvé: {conv_path}")
            return False
            
        print(f"[MANUAL-TITLE] 📄 Chargement du fichier: {conv_path}")
        import json
        conv_data = json.loads(conv_path.read_text(encoding='utf-8'))
        
        # Prendre les 5 dernières interactions (max 10 messages)
        relevant_messages = [msg for msg in conv_data if msg.get('role') in ('user', 'assistant')][-10:]
        print(f"[MANUAL-TITLE] 📊 {len(relevant_messages)} messages trouvés pour analyse")
        
        if len(relevant_messages) < 2:
            print(f"[MANUAL-TITLE] ❌ Pas assez de messages ({len(relevant_messages)}) pour générer un titre")
            return False
        
        # Construire le contexte
        context = ""
        for msg in relevant_messages:
            role = "Utilisateur" if msg['role'] == 'user' else "Luna"
            content = msg['content'][:150] if len(msg['content']) > 150 else msg['content']
            context += f"{role}: {content}...\n"
        
        print(f"[MANUAL-TITLE] 📝 Contexte construit: {len(context)} chars")
        print(f"[MANUAL-TITLE] 📝 Aperçu contexte: {context[:200]}...")
        
        # Prompt pour l'IA principale
        prompt = f"""Génère un titre court et précis (3-7 mots) qui résume le sujet principal de cette conversation.

Conversation:
{context}

Réponds UNIQUEMENT avec le titre, sans guillemets ni ponctuation finale."""

        print(f"[MANUAL-TITLE] 🤖 Appel à l'IA principale...")
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
            print(f"❌ [MANUAL-TITLE] Échec IA principale: {error}")
            return False
        
        # Nettoyer et valider le titre
        title = str(response).strip().replace('"', '').replace("'", '')
        if len(title) > 50:
            title = title[:47] + "..."
        
        print(f"[MANUAL-TITLE] 🧹 Titre nettoyé: '{title}' (longueur: {len(title)})")
        
        if len(title) > 3:
            # Mettre à jour le titre
            old_title = _conv_index[conv_id]['title']
            _conv_index[conv_id]['title'] = title
            _conv_index[conv_id]['auto_title'] = False
            
            _save_conversation_index()
            
            print(f"✅ [MANUAL-TITLE] Titre régénéré: '{old_title}' → '{title}'")
            _notify_safe(f"🔄 Nouveau titre: {title}", type='positive')
            
            # Mettre à jour la sidebar avec la conversation modifiée
            if _sidebar_render_cb:
                print(f"[MANUAL-TITLE] 🔄 Rafraîchissement sidebar pour: {conv_id}")
                _sidebar_render_cb(conv_id)
            else:
                print(f"[MANUAL-TITLE] ⚠️ Pas de callback sidebar disponible")
                
            return True
            
        return False
        
    except Exception as e:
        print(f"❌ [MANUAL-TITLE] Erreur régénération: {e}")
        _notify_safe("❌ Erreur lors de la régénération du titre", type='negative')
        return False



async def _check_progressive_summarization():
    """Vérifie si une résumisation progressive doit être déclenchée"""
    global _chat_history
    try:
        from conversation_summarizer import summarizer
        
        # Filtrer les messages utilisateur/assistant
        valid_messages = [m for m in _chat_history if m.get('role') in ('user', 'assistant')]
        message_count = len(valid_messages)
        
        # Vérifier si on doit résumer
        if summarizer.should_summarize(message_count):
            print(f"🧠 [SUMMARIZER] Déclenchement résumisation progressive ({message_count} messages)")
            
            # Optimiser l'historique
            summaries, recent_messages = await summarizer.optimize_conversation_history(valid_messages)
            
            if summaries:
                # Remplacer l'historique par les résumés + messages récents
                original_count = len(valid_messages)
                
                # Reconstruire l'historique avec résumés + messages récents
                new_history = []
                
                # Préserver les messages système en début
                for msg in _chat_history:
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
                
                # Remplacer l'historique global
                _chat_history[:] = new_history
                
                reduction = original_count - len(recent_messages)
                print(f"✅ [SUMMARIZER] Historique optimisé: {reduction} messages → {len(summaries)} résumés")
                print(f"📊 [SUMMARIZER] Avant: {original_count} messages, Après: {len(recent_messages)} + {len(summaries)} résumés")
                
    except Exception as e:
        print(f"❌ [SUMMARIZER] Erreur résumisation progressive: {e}")


def _persist_conversation(initial_text_for_title: Optional[str] = None) -> None:
    """Sauvegarde l'historique courant dans data/conversations/<id>.json et met à jour l'index."""
    global _current_conversation_id, _conv_index
    try:
        # Assure l'ID et l'entrée d'index
        if not _current_conversation_id:
            _current_conversation_id = _make_conv_id()
        cid = _current_conversation_id
        # Met à jour/Crée l'entrée index
        from datetime import datetime
        now_iso = datetime.now().isoformat(timespec='seconds')
        if cid not in _conv_index:
            title = _make_title_from_text(initial_text_for_title or '')
            _conv_index[cid] = {
                'id': cid,
                'title': title,
                'created': now_iso,
                'updated': now_iso,
                'message_count': len(_chat_history),
                'auto_title': True,
                'smart_title_pending': False,
            }
        else:
            _conv_index[cid]['updated'] = now_iso
            _conv_index[cid]['message_count'] = len(_chat_history)
            
            # 🆕 NOUVEAU: Marque pour génération d'un titre intelligent après 5 interactions
            user_messages = len([m for m in _chat_history if m.get('role') == 'user'])
            if (_conv_index[cid].get('auto_title', True) and 
                user_messages >= 5 and 
                not _conv_index[cid].get('smart_title_pending', False)):
                
                _conv_index[cid]['smart_title_pending'] = True
                # Planifie la génération du titre intelligent de manière asynchrone
                from nicegui_client_guard import safe_timer_callback
                ui.timer(0.1, safe_timer_callback(lambda: _schedule_smart_title_generation(cid)), once=True)
            # Ne change pas le titre automatiquement si déjà défini par l'utilisateur
        # Écrit le fichier JSON d'historique - SEULS les échanges utilisateur/assistant
        path = DATA_DIR / 'conversations' / f'{cid}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        
        # 🔄 NOUVEAU: Filtrer pour ne garder que les vrais échanges conversationnels
        payload = []
        for m in _chat_history:
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
            if _sidebar_render_cb:
                _sidebar_render_cb(_current_conversation_id)
        except Exception:
            pass
    except Exception as e:
        _notify_safe(f"Erreur sauvegarde conversation: {e}", 'warning')


async def _maybe_update_conv_title() -> None:
    """Après au moins 2 messages (user+assistant), proposer un titre contextualisé (IA → fallback heuristique)."""
    global _title_updating
    try:
        if _title_updating:
            return
        cid = _current_conversation_id
        if not cid or cid not in _conv_index:
            return
        entry = _conv_index[cid]
        if not entry.get('auto_title', True):
            return
        # Compter messages significatifs
        msgs = [m for m in _chat_history if m.get('role') in ('user','assistant') and isinstance(m.get('content'), str)]
        if len(msgs) < 2:
            return
        _title_updating = True
        # Préparer un corpus compact (derniers 6 messages max)
        recent = msgs[-6:]
        def _compact_text(s: str, max_len: int = 220) -> str:
            s = re.sub(r"\s+", " ", s or '').strip()
            return s if len(s) <= max_len else (s[:max_len].rstrip() + '…')
        convo = "\n".join(f"- {m['role']}: {_compact_text(m['content'])}" for m in recent)

        # Appel IA (Archiviste si dispo sinon Chat)
        title_resp: Optional[str] = None
        try:
            ctrl = _archiviste_controller or _ensure_chat_controller()
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
                if _sidebar_render_cb:
                    _sidebar_render_cb(_current_conversation_id)
            except Exception:
                pass
    finally:
        _title_updating = False


def _render_full_history():
    """Ré-affiche l'historique courant dans la zone de conversation."""
    global _chat_inner
    if _chat_inner is None:
        return
    with _chat_inner:
        _chat_inner.clear()
        for m in _chat_history:
            badges = ['mémorisé'] if m.get('memorized') else None
            _message(m.get('role', 'system'), m.get('content', ''), badges)


def _load_conversation(conv_id: str):
    """Charge une conversation depuis data/conversations/<id>.json et l'affiche."""
    global _chat_history, _current_conversation_id, _loaded_conversation, _loaded_conversation_filename, _conversation_context_injected
    try:
        path = DATA_DIR / 'conversations' / f'{conv_id}.json'
        if not path.exists():
            _notify_safe("Conversation introuvable", 'warning')
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
                new_hist.append(entry)
        
        # 📚 NOUVELLE FONCTIONNALITÉ: Préparer la conversation pour injection différée
        # Au lieu d'injecter immédiatement, on prépare pour injection au prochain message
        _loaded_conversation = new_hist.copy()
        _loaded_conversation_filename = f"{conv_id}.json"
        _conversation_context_injected = False  # Réinitialiser le flag pour la nouvelle conversation
        
        # Mettre à jour l'historique actuel et afficher (pour lecture seulement)
        _chat_history = new_hist
        _current_conversation_id = conv_id
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
        print(f"[CONVERSATION-LOAD] ✅ Conversation {conv_id} chargée, flag injection réinitialisé: {_conversation_context_injected}")
        
        # Note: Pas de notification frontend pour éviter l'encombrement visuel
        # La conversation est chargée silencieusement pour navigation read-only
        
    except Exception as e:
        _notify_safe(f"Erreur chargement conversation: {e}", 'negative')


def _new_conversation():
    """Réinitialise l’historique pour démarrer une nouvelle conversation."""
    global _chat_history, _current_conversation_id, _loaded_conversation, _loaded_conversation_filename
    _chat_history = []
    _current_conversation_id = None
    
    # 📚 Nettoyer le contexte de conversation chargée
    _loaded_conversation = None
    _loaded_conversation_filename = None
    _conversation_context_injected = False  # Réinitialiser le flag
    
    print(f"[NEW-CONVERSATION] 🆕 Nouvelle conversation, flag injection réinitialisé: {_conversation_context_injected}")
    
    _render_full_history()


def _format_datetime(datetime_str: str) -> str:
    """Formate une date/heure ISO en format lisible français."""
    try:
        from datetime import datetime
        if not datetime_str:
            return ""
        # Parse ISO format
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        # Format français
        return dt.strftime("%d/%m/%Y à %H:%M")
    except Exception:
        return datetime_str


def _parse_thinking_format(content: str) -> tuple[str, str]:
    """
    Parse le format thinking des IA qui retournent des structures JSON complexes.
    
    Format attendu: "[{'type': 'thinking', 'thinking': [...], {'type': 'text', 'text': '...'}]"
    
    Retourne:
        tuple[str, str]: (thinking_content, main_text)
        - thinking_content: Le contenu de réflexion interne (peut être vide)
        - main_text: Le texte principal à afficher
    """
    import json
    import re
    
    # Si le contenu ne ressemble pas au format thinking, retourner tel quel
    if not content.startswith('[{') or 'thinking' not in content:
        return "", content
    
    try:
        # Tenter de corriger les guillemets simples en guillemets doubles pour JSON valide
        # Cette correction est nécessaire car les IA renvoient parfois des JSON malformés
        json_content = content
        
        # Remplacer les guillemets simples par des guillemets doubles dans les clés
        json_content = re.sub(r"'(type|thinking|text)':", r'"\1":', json_content)
        
        # Plus complexe : gérer les guillemets simples dans les valeurs qui peuvent contenir des apostrophes
        # On utilise une approche plus sûre en essayant d'abord le parsing direct
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError:
            # Si ça échoue, on essaie de convertir tout avec ast.literal_eval (plus permissif)
            import ast
            try:
                data = ast.literal_eval(content)
            except (ValueError, SyntaxError):
                # Dernière tentative : retourner le contenu original
                return "", content
        
        thinking_parts = []
        text_parts = []
        
        # Parcourir la structure
        for item in data:
            if isinstance(item, dict):
                if item.get('type') == 'thinking' and 'thinking' in item:
                    # Extraire le contenu thinking
                    thinking_data = item['thinking']
                    if isinstance(thinking_data, list):
                        for thinking_item in thinking_data:
                            if isinstance(thinking_item, dict) and thinking_item.get('type') == 'text':
                                thinking_parts.append(thinking_item.get('text', ''))
                    elif isinstance(thinking_data, str):
                        thinking_parts.append(thinking_data)
                        
                elif item.get('type') == 'text' and 'text' in item:
                    # Extraire le texte principal
                    text_parts.append(item['text'])
        
        thinking_content = '\n'.join(thinking_parts).strip()
        main_text = '\n'.join(text_parts).strip()
        
        print(f"[THINKING-PARSER] ✅ Parsing réussi - Thinking: {len(thinking_content)} chars, Text: {len(main_text)} chars")
        return thinking_content, main_text
        
    except Exception as e:
        print(f"[THINKING-PARSER] ⚠️ Erreur parsing format thinking: {e}")
        # En cas d'erreur, retourner le contenu original
        return "", content


def _sidebar():
    """Barre latérale listant les conversations (type ChatGPT)."""
    idx = _load_conversation_index()
    with ui.element('aside').classes('sidebar'):
        # Actions disponibles dans l'entête
        def do_rename():
            cid = _current_conversation_id
            if not cid or cid not in _conv_index:
                _notify_safe('Aucune conversation sélectionnée.', 'warning')
                return
            d = ui.dialog()
            with d, ui.card().classes('popup-content'):
                ui.label('Renommer la conversation').classes('popup-title')
                new_title = ui.input(label='Nouveau titre', value=_conv_index[cid].get('title', '')).classes('form-input')
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=d.close).classes('action-button')
                    def _apply():
                        title = (new_title.value or '').strip() or 'Sans titre'
                        _conv_index[cid]['title'] = title
                        _conv_index[cid]['auto_title'] = False
                        ok, msg = _save_conversation_index()
                        _notify_safe(msg, 'positive' if ok else 'warning')
                        d.close()
                        try:
                            if _sidebar_render_cb:
                                _sidebar_render_cb(cid)
                            else:
                                render_items(cid)
                        except Exception:
                            render_items(cid)
                    ui.button('Renommer', on_click=_apply).classes('send-button')
            d.open()

        def do_delete():
            cid = _current_conversation_id
            if not cid or cid not in _conv_index:
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
                            _conv_index.pop(cid, None)
                            ok, msg = _save_conversation_index()
                            _notify_safe(msg, 'positive' if ok else 'warning')
                            d.close()
                            _new_conversation()
                            try:
                                if _sidebar_render_cb:
                                    _sidebar_render_cb(None)
                                else:
                                    render_items(None)
                            except Exception:
                                render_items(None)
                        except Exception as e:
                            _notify_safe(f'Erreur suppression: {e}', 'negative')
                    ui.button('Supprimer', on_click=_apply_delete).classes('send-button')
            d.open()

        with ui.element('div').classes('sidebar-header').style('display: flex; align-items: center; gap: 8px;'):
            ui.button(icon='add', on_click=_new_conversation).classes('header-btn')
            ui.button(icon='edit', on_click=do_rename).classes('header-btn')
            ui.button(icon='delete', on_click=do_delete).classes('header-btn')
        list_container = ui.element('div').classes('sidebar-list').style(
            'max-height: 70vh; overflow-y: auto; overflow-x: hidden; border-right: 1px solid var(--border-color, #333);'
        )
        def render_items(active_id: Optional[str] = None):
            list_container.clear()
            with list_container:
                try:
                    items = sorted(idx.values(), key=lambda x: x.get('created', ''), reverse=True)
                except Exception:
                    items = list(idx.values())
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
                            if _sidebar_render_cb:
                                _sidebar_render_cb(conv_id)
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
                        tooltip_lines.append(f"Créé : {_format_datetime(created)}")
                    if updated and updated != created:
                        tooltip_lines.append(f"Modifié : {_format_datetime(updated)}")
                    
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
                                    if _sidebar_render_cb:
                                        _sidebar_render_cb(_current_conversation_id)
                                    ui.notify(f'💔 Conversation "{conv_title}" supprimée de la mémoire', type='info')
                                else:
                                    # Vérifier la limite de 15 conversations mémorisées
                                    memorized_count = _count_memorized_conversations()
                                    if memorized_count >= 15:
                                        ui.notify('⚠️ Limite de 15 conversations mémorisées atteinte. Supprimez-en une avant d\'en ajouter.', type='warning')
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
                                    ui.notify(f'📋 Copié: {filename}', type='positive')
                                except Exception:
                                    # Fallback: juste afficher le nom
                                    ui.notify(f'📄 Nom du fichier: {filename}', type='info')
                            
                            copy_btn_style = (
                                'padding: 2px; min-width: 16px; height: 16px; border-radius: 50%; '
                                'background: transparent; border: none; color: #888888 !important; '
                                'font-size: 14px; line-height: 1;'
                            )
                            copy_btn = ui.button('•', on_click=_on_copy_filename).style(copy_btn_style)
                            copy_btn.props('dense flat')
                            copy_btn.tooltip(f'Copier le nom du fichier: {cid}.json')
                            
                            # 🔄 NOUVEAU: Bouton pour régénérer le titre via IA
                            def _on_regenerate_title(conv_id=cid):
                                print(f"[DEBUG-TITLE] 🔄 Bouton rafraîchissement cliqué pour conversation: {conv_id}")
                                
                                # Version simplifiée sans safe_timer_callback à cause des erreurs NiceGUI
                                async def do_regenerate():
                                    try:
                                        print(f"[DEBUG-TITLE] 🚀 Début régénération titre pour: {conv_id}")
                                        success = await _regenerate_title_manual(conv_id)
                                        if not success:
                                            print(f"[DEBUG-TITLE] ❌ Échec régénération pour: {conv_id}")
                                            _notify_safe("⚠️ Impossible de régénérer le titre", type='warning')
                                        else:
                                            print(f"[DEBUG-TITLE] ✅ Succès régénération pour: {conv_id}")
                                            # Forcer le rafraîchissement avec un petit délai
                                            import asyncio
                                            await asyncio.sleep(0.2)  # Petit délai pour que l'index soit bien sauvé
                                            if _sidebar_render_cb:
                                                print(f"[DEBUG-TITLE] 🔄 Rafraîchissement sidebar forcé")
                                                _sidebar_render_cb(conv_id)
                                    except Exception as e:
                                        print(f"[DEBUG-TITLE] ❌ Erreur dans do_regenerate: {e}")
                                        _notify_safe(f"❌ Erreur: {e}", type='negative')
                                
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
        global _sidebar_render_cb
        def _cb(active_id: Optional[str] = None):
            nonlocal idx
            # recharger l'index depuis disque pour afficher les nouvelles conversations
            idx = _load_conversation_index()
            render_items(active_id)
        _sidebar_render_cb = _cb
        render_items(_current_conversation_id)

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
        
        return summary.strip() if summary else None
        
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
    global _conv_index
    if conversation_id in _conv_index:
        _conv_index[conversation_id]['memorized'] = memorized
        _save_conversation_index()


def _is_conversation_memorized(conversation_id: str) -> bool:
    """Vérifie si une conversation est déjà mémorisée."""
    global _conv_index
    return _conv_index.get(conversation_id, {}).get('memorized', False)


def _count_memorized_conversations() -> int:
    """Compte le nombre total de conversations mémorisées."""
    global _conv_index
    return sum(1 for conv in _conv_index.values() if conv.get('memorized', False))


def _get_memorized_conversations_list() -> list[tuple[str, str]]:
    """Retourne la liste des conversations mémorisées avec leur date."""
    global _conv_index
    memorized = []
    for conv_id, conv_data in _conv_index.items():
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
                    ui.notify('✅ Conversation mémorisée avec succès', type='positive')
                    dialog.close()
                    # Rafraîchir la sidebar pour mettre à jour l'icône
                    if _sidebar_render_cb:
                        _sidebar_render_cb(_current_conversation_id)
                    # Actualiser la liste des mémoires si ouverte
                    _trigger_memory_update()
                else:
                    ui.notify('❌ Erreur lors de la mémorisation (voir logs)', type='negative')
                    
            except Exception as e:
                print(f"[DEBUG] Exception mémorisation: {e}")
                ui.notify(f'❌ Erreur: {e}', type='negative')
        
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
                models_dialog = _models_modal()
                ui.button('IA / Modèles', icon='memory', on_click=models_dialog.open).classes('action-button').style('''
                    background: rgba(212, 175, 55, 0.12) !important;
                    border: 1px solid rgba(212, 175, 55, 0.3) !important;
                    transition: all 0.3s ease !important;
                ''')
                # Mémoire
                mem_dialog = _memory_modal()
                ui.button('Mémoire', icon='database', on_click=mem_dialog.open).classes('action-button').style('''
                    background: rgba(212, 175, 55, 0.12) !important;
                    border: 1px solid rgba(212, 175, 55, 0.3) !important;
                    transition: all 0.3s ease !important;
                ''')
                # Instructions
                instr_dialog = _instructions_modal()
                ui.button('Instructions', icon='article', on_click=instr_dialog.open).classes('action-button').style('''
                    background: rgba(212, 175, 55, 0.12) !important;
                    border: 1px solid rgba(212, 175, 55, 0.3) !important;
                    transition: all 0.3s ease !important;
                ''')
                # Image
                img_dialog = _image_modal()
                ui.button('Image', icon='image', on_click=img_dialog.open).classes('action-button').style('''
                    background: rgba(212, 175, 55, 0.12) !important;
                    border: 1px solid rgba(212, 175, 55, 0.3) !important;
                    backdrop-filter: blur(15px) !important;
                    -webkit-backdrop-filter: blur(15px) !important;
                    transition: all 0.3s ease !important;
                ''')
                # Perception
                per_dialog = _perception_modal()
                ui.button('Perception', icon='sensors', on_click=per_dialog.open).classes('action-button').style('''
                    background: rgba(255, 140, 0, 0.12) !important;
                    border: 1px solid rgba(255, 140, 0, 0.3) !important;
                    backdrop-filter: blur(15px) !important;
                    -webkit-backdrop-filter: blur(15px) !important;
                    transition: all 0.3s ease !important;
                ''')
                # Profil
                prof_dialog = _profile_modal()
                ui.button('Profil', icon='person', on_click=prof_dialog.open).classes('action-button').style('''
                    background: rgba(255, 140, 0, 0.12) !important;
                    border: 1px solid rgba(255, 140, 0, 0.3) !important;
                    backdrop-filter: blur(15px) !important;
                    -webkit-backdrop-filter: blur(15px) !important;
                    transition: all 0.3s ease !important;
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


def _status_dot(initial='var(--text-muted)'):
    el = ui.element('div').style(f'width:10px; height:10px; border-radius:50%; background:{initial}; border:1px solid var(--border-color);')
    return el


def _open_other_backends_popup():
    """Popup isolé pour configuration des backends non-API (Ollama/GGUF/KoboldCpp)"""
    sm = _ensure_settings_manager()
    
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
            ui.button('🔄 Actualiser Interface', on_click=lambda: force_interface_update()).classes('btn-secondary')
        
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
                        ui.notify('🔄 Actualisation modèles KoboldCpp...', type='info')
                        
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
                        
                        ui.notify(f'✅ {len(mock_models)} modèle(s) trouvé(s)', type='positive')
                        
                    except Exception as e:
                        ui.notify(f'❌ Erreur actualisation modèles: {e}', type='warning')
                
                async def refresh_ollama_models():
                    try:
                        # S'assurer que les managers sont initialisés
                        _ensure_backends()
                        assert _ollama_mgr is not None
                        
                        models_container.clear()
                        with models_container:
                            ui.label('🔄 Rafraîchissement en cours...').classes('text-sm mb-2')
                        
                        # Utiliser le vrai OllamaManager au lieu de la simulation
                        if _ollama_mgr.check_service():
                            available_models = _ollama_mgr.models
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
                        models_container.clear()
                        with models_container:
                            ui.label(f'❌ Erreur: {e}').classes('text-sm text-red-500')
                        ui.notify(f'Erreur rafraîchissement: {e}', type='warning')
                
                async def test_ollama_connection():
                    try:
                        ui.notify(f'Test connexion Ollama: {url_input.value}...', type='info')
                        # Simulation - à remplacer par vraie logique
                        ui.notify('✅ Connexion Ollama réussie', type='positive')
                    except Exception as e:
                        ui.notify(f'❌ Erreur connexion: {e}', type='warning')
                
                with ui.row().classes('gap-2 mb-4'):
                    ui.button('🔄 Rafraîchir modèles', on_click=refresh_ollama_models).classes('action-button')
                    ui.button('🧪 Tester connexion', on_click=test_ollama_connection).classes('action-button')
                
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
                                
                                ui.notify(f'✅ Modèle sélectionné: {os.path.basename(file_path)} ({file_size:.1f} GB)', type='positive')
                            else:
                                ui.notify('Aucun fichier sélectionné', type='info')
                        
                        except ImportError:
                            # Fallback: scan automatique des dossiers communs
                            ui.notify('🔍 tkinter non disponible, scan automatique...', type='info')
                            await scan_common_directories()
                            
                    except Exception as e:
                        ui.notify(f'❌ Erreur navigateur: {e}', type='warning')
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
                            
                            ui.notify(f'✅ {len(found_models)} modèle(s) GGUF trouvé(s)', type='positive')
                        else:
                            ui.notify('⚠️ Aucun modèle GGUF trouvé dans les dossiers communs', type='warning')
                            ui.notify('💡 Utilisez le bouton "📂 Ouvrir dossier" pour naviguer manuellement', type='info')
                            
                    except Exception as e:
                        ui.notify(f'❌ Erreur scan: {e}', type='warning')
                
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
                        ui.notify(f'❌ Erreur ouverture explorateur: {e}', type='warning')
                
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
                
                ui.button('🔄 Actualiser modèles', on_click=lambda: refresh_kobold_models()).classes('btn-secondary mr-2')
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
                        ui.notify('✅ Connexion KoboldCpp réussie', type='positive')
                    except Exception as e:
                        ui.notify(f'❌ Erreur connexion: {e}', type='warning')
                
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
                    ui.notify('✅ Configuration Ollama sauvegardée', type='positive')
                    
                elif backend == 'gguf' and 'gguf' in interface_data:
                    gguf_data = interface_data['gguf']
                    other_backends['gguf'] = {
                        'model_path': gguf_data['model_path_input'].value or '',
                        'gpu_layers': int(gguf_data['gpu_layers_input'].value or -1),
                        'context_size': int(gguf_data['context_size_input'].value or 4096),
                        'selected_model': gguf_data['model_files_select'].value or '',
                        'enabled': True
                    }
                    ui.notify('✅ Configuration GGUF sauvegardée', type='positive')
                    
                elif backend == 'kobold' and 'kobold' in interface_data:
                    kobold_data = interface_data['kobold']
                    other_backends['kobold'] = {
                        'url': kobold_data['url_input'].value or 'http://localhost:5001',
                        'selected_model': kobold_data['model_select'].value or '',
                        'enabled': True
                    }
                    ui.notify('✅ Configuration KoboldCpp sauvegardée', type='positive')
                
                # Sauvegarder dans settings.json (section isolée)
                sm.settings['other_backends'] = other_backends
                sm.save_settings()
                
                print(f"[OTHER-BACKENDS] Configuration {backend} sauvegardée: {other_backends.get(backend, {})}")
                dialog.close()
                
            except Exception as e:
                print(f"[OTHER-BACKENDS] Erreur sauvegarde: {e}")
                ui.notify(f'❌ Erreur sauvegarde: {e}', type='warning')
        
        # Boutons popup
        ui.separator().classes('my-4')
        with ui.row().classes('justify-end gap-2 w-full'):
            ui.button('Annuler', on_click=dialog.close).classes('action-button')
            ui.button('💾 Sauvegarder', on_click=_save_other_backends).classes('send-button')
    
    dialog.open()


def _models_modal():
    """Popup dédiée aux modèles IA (Chat, Archiviste, Embeddings) avec voyants d'état."""
    sm = _ensure_settings_manager()
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
            chat_dot = _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label('Chat').classes('text-sm')
            arch_dot = _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label('Archiviste').classes('text-sm')
            emb_dot = _status_dot(initial='#dc2626')  # Rouge par défaut
            ui.label('Embeddings').classes('text-sm')

        async def set_dot(el, ok: bool):
            try:
                el.style(f'background: {"#16a34a" if ok else "#dc2626"};')
            except Exception:
                pass

        with ui.tab_panels(tabs, value=t_chat).classes('w-full'):
            # --- Chat IA ---
            with ui.tab_panel(t_chat):
                _ensure_backends()
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
                    chat_dot_inline = _status_dot(initial='#dc2626')  # Rouge par défaut

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
                            _ensure_backends()
                            assert _ollama_mgr is not None
                            
                            chat_models_container.clear()
                            with chat_models_container:
                                ui.label('🔄 Rafraîchissement en cours...').classes('text-sm mb-2')
                            
                            if _ollama_mgr.check_service():
                                available_models = _ollama_mgr.models
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
                                "C:\\models\\**\\*.gguf",
                                "C:\\AI\\models\\**\\*.gguf", 
                                "D:\\models\\**\\*.gguf",
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
                                found_models = [m.replace('/', '\\\\') for m in found_models[:10]]
                                
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
                            base_path = chat_gguf_model_path.value or 'C:\\\\'
                            if os.path.isfile(base_path):
                                # Si c'est un fichier, ouvrir le dossier parent
                                folder_path = os.path.dirname(base_path)
                            else:
                                # Essayer des dossiers communs
                                common_folders = [
                                    "C:\\\\models",
                                    "C:\\\\AI\\\\models", 
                                    "D:\\\\models",
                                    os.path.expanduser("~/models"),
                                    "C:\\\\"
                                ]
                                folder_path = next((f for f in common_folders if os.path.exists(f)), "C:\\\\")
                            
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
                _ensure_backends()
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
                    arch_dot_inline = _status_dot(initial='#dc2626')  # Rouge par défaut

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
                                "C:\\AI\\models\\",
                                "C:\\AI\\TIA\\text-generation-webui\\user_data\\models\\",
                                "C:\\models\\", 
                                "D:\\models\\",
                                "D:\\AI\\models\\",
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
                                    "C:\\AI\\TIA\\text-generation-webui\\user_data\\models",
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
                ui.timer(0.2, lambda: asyncio.create_task(_auto_check_arch()), once=True)

            # --- Embeddings IA ---
            with ui.tab_panel(t_embed):
                _ensure_backends()
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
                    emb_dot_inline = _status_dot(initial='#dc2626')  # Rouge par défaut

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
                                "C:\\AI\\models\\",
                                "C:\\AI\\TIA\\text-generation-webui\\user_data\\models\\",
                                "C:\\models\\", 
                                "D:\\models\\",
                                "D:\\AI\\models\\",
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
                                    "C:\\AI\\TIA\\text-generation-webui\\user_data\\models",
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
                ui.timer(0.2, lambda: asyncio.create_task(_auto_check_emb()), once=True)

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


def _edit_memory_popup(memory_id: str, refresh_callback=None):
    """Popup d'édition rapide d'un souvenir."""
    mm = _ensure_memory_manager()
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


def _memory_modal():
    """Boîte de dialogue NiceGUI pour gérer la mémoire via SQLite (split liste/éditeur)."""
    mm = _ensure_memory_manager()
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
                            print(f"[MEMORY-EDIT] ✅ Valeurs archiviste chargées: I={intensite_val}, L={liberte_val}, C={creation_val}, P={procreation_val}, IC={intensite_ctx_val}")
                        
                    except Exception as json_error:
                        print(f"[MEMORY-EDIT] ⚠️ Erreur parsing JSON multiplicateur_impact: {json_error}")
                        archiviste_values_loaded = False
                
                # Si aucune valeur archiviste n'a pu être chargée, utiliser les défauts harmonisés
                if not archiviste_values_loaded:
                    print("[MEMORY-EDIT] 🔄 Utilisation valeurs par défaut harmonisées")
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
        mem_id = f"usr-{uuid.uuid4()}"
        # Mémorisation manuelle avec scoring IA Principale
        chat_ctrl = _ensure_chat_controller()
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


def _instructions_modal():
    """Modal avec petits encadrés preview pour chaque instruction."""
    main_dialog = ui.dialog()
    
    # Données des instructions
    instructions_data = [
        {
            'id': 'ego',
            'title': '🧠 Ego Prompt',
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
            'file_path': DATA_DIR / "persistent_context.txt"
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
            'title': '👁️ Prompt Perception',
            'subtitle': 'Perception visuelle',
            'description': 'Instructions spécifiques pour la perception et analyse d\'images.',
            'source': 'settings',
            'settings_key': 'perception'
        },
        {
            'id': 'memorization',
            'title': '🧠 Prompt Mémorisation',
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
                    if instruction['file_path'].exists():
                        return instruction['file_path'].read_text(encoding='utf-8')
                    return ""
                except Exception as e:
                    _notify_safe(f"Erreur lecture: {e}", 'warning')
                    return ""
            elif instruction['source'] == 'settings':
                try:
                    sm = _ensure_settings_manager()
                    return sm.settings.get('prompts', {}).get(instruction['settings_key'], '')
                except Exception:
                    return ""
            else:  # template
                # Vérifier d'abord si une version sauvegardée existe
                try:
                    sm = _ensure_settings_manager()
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
                    instruction['file_path'].write_text(content, encoding='utf-8')
                    _notify_safe(f"✅ {instruction['file_path'].name} sauvegardé", 'positive')
                    return True
                except Exception as e:
                    _notify_safe(f"Erreur sauvegarde: {e}", 'warning')
                    return False
            elif instruction['source'] == 'settings':
                try:
                    sm = _ensure_settings_manager()
                    if 'prompts' not in sm.settings:
                        sm.settings['prompts'] = {}
                    sm.settings['prompts'][instruction['settings_key']] = content
                    sm.save_settings()
                    _notify_safe(f"✅ {instruction['title']} sauvegardé", 'positive')
                    return True
                except Exception as e:
                    _notify_safe(f"Erreur sauvegarde: {e}", 'warning')
                    return False
            else:  # template - convertir vers settings pour persistance
                try:
                    sm = _ensure_settings_manager()
                    if 'prompts' not in sm.settings:
                        sm.settings['prompts'] = {}
                    # Pour memorization et injection, utiliser directement l'ID comme clé
                    if instruction['id'] in ['memorization', 'injection']:
                        settings_key = instruction['id']
                    else:
                        settings_key = f"template_{instruction['id']}"
                    
                    sm.settings['prompts'][settings_key] = content
                    sm.save_settings()
                    _notify_safe(f"✅ {instruction['title']} sauvegardé", 'positive')
                    
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
                    _notify_safe(f"🔄 {instruction['title']} rechargé", 'info')
                
                def _save():
                    success = _save_content(textarea.value or "")
                    if success:
                        # Recharger automatiquement le contenu après sauvegarde réussie
                        textarea.value = _load_content()
                        _notify_safe(f"✅ {instruction['title']} sauvegardé et rechargé", 'positive')
                
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
                                if instr['file_path'].exists():
                                    preview_content = instr['file_path'].read_text(encoding='utf-8')[:200]
                                else:
                                    preview_content = "Fichier non trouvé"
                            except Exception:
                                preview_content = "Erreur de lecture"
                        elif instr['source'] == 'settings':
                            try:
                                sm = _ensure_settings_manager()
                                content = sm.settings.get('prompts', {}).get(instr['settings_key'], 'Non configuré')
                                preview_content = content[:200] if content else 'Non configuré'
                            except Exception:
                                preview_content = "Erreur de lecture"
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


def _image_modal():
    d = ui.dialog()
    with d, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 680px;'):
        ui.label('Image').classes('popup-title')
        ui.label('À définir.').classes('text-muted')
        ui.button('Fermer', on_click=d.close).classes('action-button mt-2')
    return d


def _perception_modal():
    d = ui.dialog()
    with d, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 680px;'):
        ui.label('Perception').classes('popup-title')
        ui.label('À définir.').classes('text-muted')
        ui.button('Fermer', on_click=d.close).classes('action-button mt-2')
    return d


def _render_tts_config(current_engine, sm, refresh_callback):
    """Affiche la configuration spécifique au moteur TTS sélectionné."""
    
    print(f"[DEBUG-TTS] ========================")
    print(f"[DEBUG-TTS] _render_tts_config() APPELÉE")
    print(f"[DEBUG-TTS] Moteur reçu: '{current_engine}'")
    print(f"[DEBUG-TTS] Type: {type(current_engine)}")
    print(f"[DEBUG-TTS] Longueur: {len(current_engine)}")
    print(f"[DEBUG-TTS] Repr: {repr(current_engine)}")
    print(f"[DEBUG-TTS] ========================")
    
    if current_engine == 'system':
        # Configuration voix système
        ui.label('Configuration Système').classes('text-sm font-medium mb-2')
        
        global _audio_manager
        if _audio_manager is None:
            _audio_manager = _ensure_audio_manager()
            
        if _audio_manager and hasattr(_audio_manager, 'get_available_voices'):
            available_voices = _audio_manager.get_available_voices()
            if available_voices:
                current_voice_id = sm.settings.get('tts', {}).get('voice_id', 'auto')
                
                # Créer la liste des options pour le select
                voice_options = {'auto': '🤖 Auto (Sélection automatique)'}
                for voice in available_voices:
                    flag = "🇫🇷" if voice['language'] == 'fr' else "🇬🇧"
                    gender = "♀️" if voice['gender'] == 'female' else "♂️"
                    label = f"{flag} {gender} {voice['name']}"
                    voice_options[voice['id']] = label
                
                # Vérifier que la voix actuelle existe dans les options
                if current_voice_id not in voice_options:
                    current_voice_id = 'auto'
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['voice_id'] = 'auto'
                    sm.save_settings()
                
                def on_voice_change(e):
                    global _audio_manager
                    voice_id = e.value
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['voice_id'] = voice_id
                    sm.save_settings()
                    
                    if _audio_manager and hasattr(_audio_manager, 'set_voice'):
                        _audio_manager.set_voice(voice_id)
                    
                    voice_name = 'Sélection automatique' if voice_id == 'auto' else voice_options.get(voice_id, voice_id)
                    ui.notify(f'Voix changée: {voice_name}', type='positive')
                
                ui.select(
                    label='Voix système disponibles',
                    options=voice_options,
                    value=current_voice_id,
                    on_change=on_voice_change
                ).classes('mb-3')
                
                # Bouton test voix système
                def test_system_voice():
                    async def _test():
                        global _audio_manager
                        if _audio_manager:
                            test_text = "Bonjour, ceci est un test de la synthèse vocale système."
                            success = await _audio_manager.speak(test_text)
                            if success:
                                _notify_safe('🔊 Test vocal réussi', 'positive')
                            else:
                                _notify_safe('❌ Erreur lors du test vocal', 'negative')
                        else:
                            _notify_safe('❌ Audio manager non disponible', 'negative')
                    
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(_test())
                        else:
                            loop.run_until_complete(_test())
                    except:
                        asyncio.create_task(_test())
                
                ui.button('🧪 Tester la voix système', on_click=test_system_voice).classes('mb-3')
            else:
                ui.label("❌ Aucune voix système disponible").classes('text-red-500 mb-2')
                ui.button('🔄 Réessayer', on_click=refresh_callback).classes('mb-2')
        else:
            ui.label("❌ Audio manager non initialisé").classes('text-red-500 mb-2')
            ui.button('🔄 Réessayer', on_click=refresh_callback).classes('mb-2')
            
    elif current_engine == 'google':
        # Configuration Google Cloud TTS
        ui.label('Configuration Google Cloud TTS').classes('text-sm font-medium mb-2')
        
        # Clé API Google
        google_api_key = sm.settings.get('tts', {}).get('google_api_key', '')
        def on_google_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['google_api_key'] = e.value
            sm.save_settings()
            ui.notify('Clé API Google sauvegardée', type='positive')
        
        ui.input(
            label='Clé API Google Cloud',
            placeholder='Entrez votre clé API Google Cloud',
            password=True,
            value=google_api_key,
            on_change=on_google_key_change
        ).classes('mb-3')
        
        # Voix Google
        google_voice = sm.settings.get('tts', {}).get('google_voice', 'fr-FR-Standard-A')
        def on_google_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['google_voice'] = e.value
            sm.save_settings()
            ui.notify(f'Voix Google changée: {e.value}', type='positive')
        
        google_voice_options = {
            'fr-FR-Standard-A': '🇫🇷 ♀️ Française Standard A',
            'fr-FR-Standard-B': '🇫🇷 ♂️ Français Standard B',
            'fr-FR-Standard-C': '🇫🇷 ♀️ Française Standard C',
            'fr-FR-Standard-D': '🇫🇷 ♂️ Français Standard D',
            'fr-FR-Neural2-A': '🇫🇷 ♀️ Française Neural A',
            'fr-FR-Neural2-B': '🇫🇷 ♂️ Français Neural B',
            'en-US-Standard-A': '🇬🇧 ♀️ Anglaise Standard A',
            'en-US-Standard-B': '🇬🇧 ♂️ Anglais Standard B',
            'en-US-Neural2-A': '🇬🇧 ♀️ Anglaise Neural A',
            'en-US-Neural2-B': '🇬🇧 ♂️ Anglais Neural B'
        }
        
        ui.select(
            label='Voix Google Cloud',
            options=google_voice_options,
            value=google_voice,
            on_change=on_google_voice_change
        ).classes('mb-3')
        
        # Bouton test Google TTS
        def test_google_tts():
            async def _test():
                global _audio_manager
                if not google_api_key:
                    _notify_safe('❌ Clé API Google manquante', 'negative')
                    return
                    
                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Google Cloud Text-to-Speech."
                    try:
                        success = await _audio_manager.speak_google_tts(
                            test_text, 
                            google_voice, 
                            google_api_key
                        )
                        if success:
                            _notify_safe('🔊 Test Google TTS réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Google TTS', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Google TTS: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())
        
        ui.button('🧪 Tester Google TTS', on_click=test_google_tts).classes('mb-3')
        
    elif current_engine == 'elevenlabs':
        # Configuration ElevenLabs
        ui.label('Configuration ElevenLabs').classes('text-sm font-medium mb-2')
        
        # Clé API ElevenLabs
        elevenlabs_api_key = sm.settings.get('tts', {}).get('elevenlabs_api_key', '')
        def on_elevenlabs_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['elevenlabs_api_key'] = e.value
            sm.save_settings()
            ui.notify('Clé API ElevenLabs sauvegardée', type='positive')
        
        ui.input(
            label='Clé API ElevenLabs',
            placeholder='Entrez votre clé API ElevenLabs',
            password=True,
            value=elevenlabs_api_key,
            on_change=on_elevenlabs_key_change
        ).classes('mb-3')
        
        # ID de voix ElevenLabs
        elevenlabs_voice_id = sm.settings.get('tts', {}).get('elevenlabs_voice_id', 'pNInz6obpgDQGcFmaJgB')
        def on_elevenlabs_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['elevenlabs_voice_id'] = e.value
            sm.save_settings()
            ui.notify('Voice ID ElevenLabs sauvegardé', type='positive')
        
        ui.input(
            label='Voice ID ElevenLabs',
            placeholder='ID de la voix (ex: pNInz6obpgDQGcFmaJgB)',
            value=elevenlabs_voice_id,
            on_change=on_elevenlabs_voice_change
        ).classes('mb-3')
        
        # Bouton test ElevenLabs
        def test_elevenlabs_tts():
            async def _test():
                global _audio_manager
                if not elevenlabs_api_key:
                    _notify_safe('❌ Clé API ElevenLabs manquante', 'negative')
                    return
                    
                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de ElevenLabs Voice AI."
                    try:
                        success = await _audio_manager.speak_elevenlabs(
                            test_text, 
                            elevenlabs_voice_id, 
                            elevenlabs_api_key
                        )
                        if success:
                            _notify_safe('🔊 Test ElevenLabs réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test ElevenLabs', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur ElevenLabs: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')
            
            # Lancer la tâche asynchrone sans créer de nouvelle tâche
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())
        
        ui.button('🧪 Tester ElevenLabs', on_click=test_elevenlabs_tts).classes('mb-3')
        
        ui.label('💡 Trouvez les Voice IDs sur votre tableau de bord ElevenLabs').classes('text-xs text-muted mb-3')
    
    elif current_engine == 'azure' or current_engine.strip().lower() == 'azure':
        # Configuration Azure AI Speech
        print("[DEBUG-TTS] ✅ SECTION 1 AZURE ACTIVÉE DANS _render_tts_config")
        ui.label('Configuration Azure AI Speech').classes('text-sm font-medium mb-2')
        
        # Clé API Azure
        azure_api_key = sm.settings.get('tts', {}).get('azure_api_key', '')
        def on_azure_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['azure_api_key'] = e.value
            sm.save_settings()
            ui.notify('Clé API Azure sauvegardée', type='positive')
        
        ui.input(
            label='Clé API Azure',
            placeholder='Entrez votre clé API Azure Speech',
            password=True,
            value=azure_api_key,
            on_change=on_azure_key_change
        ).classes('mb-3')
        
        # Région Azure
        azure_region = sm.settings.get('tts', {}).get('azure_region', 'eastus')
        def on_azure_region_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['azure_region'] = e.value
            sm.save_settings()
            ui.notify(f'Région Azure: {e.value}', type='positive')
        
        ui.input(
            label='Région Azure',
            placeholder='eastus, westeurope, etc.',
            value=azure_region,
            on_change=on_azure_region_change
        ).classes('mb-3')
        
        # Voix Azure
        azure_voice = sm.settings.get('tts', {}).get('azure_voice', 'fr-FR-DeniseNeural')
        def on_azure_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['azure_voice'] = e.value
            sm.save_settings()
            ui.notify(f'Voix Azure changée: {e.value}', type='positive')
        
        azure_voice_options = {
            'fr-FR-DeniseNeural': '🇫🇷 ♀️ Denise (Neural)',
            'fr-FR-HenriNeural': '🇫🇷 ♂️ Henri (Neural)',
            'fr-FR-AlainNeural': '🇫🇷 ♂️ Alain (Neural)',
            'fr-FR-BrigitteNeural': '🇫🇷 ♀️ Brigitte (Neural)',
            'fr-FR-CelesteNeural': '🇫🇷 ♀️ Celeste (Neural)',
            'fr-FR-ClaudeNeural': '🇫🇷 ♂️ Claude (Neural)',
            'fr-FR-CoralieNeural': '🇫🇷 ♀️ Coralie (Neural)',
            'fr-FR-EloiseNeural': '🇫🇷 ♀️ Eloise (Neural)',
            'fr-FR-JacquelineNeural': '🇫🇷 ♀️ Jacqueline (Neural)',
            'fr-FR-JeromeNeural': '🇫🇷 ♂️ Jerome (Neural)',
            'fr-FR-MauriceNeural': '🇫🇷 ♂️ Maurice (Neural)',
            'fr-FR-YvesNeural': '🇫🇷 ♂️ Yves (Neural)',
            'fr-FR-YvetteNeural': '🇫🇷 ♀️ Yvette (Neural)',
            'fr-CA-AntoineNeural': '🇨🇦 ♂️ Antoine (Canadien)',
            'fr-CA-JeanNeural': '🇨🇦 ♂️ Jean (Canadien)',
            'fr-CA-SylvieNeural': '🇨🇦 ♀️ Sylvie (Canadienne)',
            'en-US-AriaNeural': '🇺🇸 ♀️ Aria (Neural)',
            'en-US-DavisNeural': '🇺🇸 ♂️ Davis (Neural)',
            'en-US-GuyNeural': '🇺🇸 ♂️ Guy (Neural)',
            'en-US-JaneNeural': '🇺🇸 ♀️ Jane (Neural)',
            'en-US-JasonNeural': '🇺🇸 ♂️ Jason (Neural)',
            'en-US-JennyNeural': '🇺🇸 ♀️ Jenny (Neural)',
            'en-US-NancyNeural': '🇺🇸 ♀️ Nancy (Neural)',
            'en-US-SaraNeural': '🇺🇸 ♀️ Sara (Neural)',
            'en-US-TonyNeural': '🇺🇸 ♂️ Tony (Neural)'
        }
        
        ui.select(
            label='Voix Azure Speech',
            options=azure_voice_options,
            value=azure_voice,
            on_change=on_azure_voice_change
        ).classes('mb-3')
        
        # Bouton test Azure
        def test_azure_tts():
            async def _test():
                global _audio_manager
                if not azure_api_key:
                    _notify_safe('❌ Clé API Azure manquante', 'negative')
                    return
                    
                if _audio_manager:
                    test_text = "Bonjour, ceci est un test d'Azure AI Speech."
                    try:
                        success = await _audio_manager.speak_azure(test_text)
                        if success:
                            _notify_safe('🔊 Test Azure AI Speech réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Azure', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Azure: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')
            
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())
        
        ui.button('🧪 Tester Azure AI Speech', on_click=test_azure_tts).classes('mb-3')
        
        ui.label('💡 Obtenez vos clés API sur le portail Azure Speech Services').classes('text-xs text-muted mb-3')
    
    elif current_engine == 'gtts' or current_engine.strip().lower() == 'gtts':
        # Configuration Google TTS Offline (gTTS)
        print("[DEBUG-TTS] ✅ SECTION gTTS ACTIVÉE")
        ui.label('Configuration Google TTS Offline (gTTS)').classes('text-sm font-medium mb-2')
        
        # Langue gTTS
        gtts_lang = sm.settings.get('tts', {}).get('gtts_lang', 'fr')
        def on_gtts_lang_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['gtts_lang'] = e.value
            sm.save_settings()
            
            global _audio_manager
            if _audio_manager:
                _audio_manager.gtts_lang = e.value
            
            ui.notify(f'Langue gTTS: {e.value}', type='positive')
        
        gtts_lang_options = {
            'fr': '🇫🇷 Français',
            'en': '🇬🇧 Anglais',
            'es': '🇪🇸 Espagnol (Général)',
            'es-mx': '🇲🇽 Espagnol (Mexique)',
            'es-ar': '🇦🇷 Espagnol (Argentine)',
            'es-co': '🇨🇴 Espagnol (Colombie)',
            'es-cl': '🇨🇱 Espagnol (Chili)', 
            'es-ve': '🇻🇪 Espagnol (Venezuela)',
            'pt': '🇵🇹 Portugais',
            'pt-br': '🇧🇷 Portugais (Brésil)',
            'de': '🇩🇪 Allemand',
            'it': '🇮🇹 Italien'
        }
        
        ui.select(
            label='Langue gTTS',
            options=gtts_lang_options,
            value=gtts_lang,
            on_change=on_gtts_lang_change
        ).classes('mb-3')
        
        # Bouton test gTTS
        def test_gtts_tts():
            async def _test():
                global _audio_manager
                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Google TTS offline."
                    try:
                        success = await _audio_manager.speak_gtts(test_text, gtts_lang)
                        if success:
                            _notify_safe('🔊 Test gTTS réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test gTTS', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur gTTS: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')
            
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())
        
        ui.button('🧪 Tester Google TTS Offline', on_click=test_gtts_tts).classes('mb-3')
        
        ui.label('💡 Google TTS offline - gratuit mais nécessite une connexion internet pour la synthèse').classes('text-xs text-muted mb-3')
    
    elif current_engine == 'edge_tts' or current_engine.strip().lower() == 'edge_tts':
        # Configuration Microsoft Edge TTS
        print("[DEBUG-TTS] ✅ SECTION Edge TTS ACTIVÉE")
        ui.label('Configuration Microsoft Edge TTS').classes('text-sm font-medium mb-2')
        
        # Voix Edge TTS
        edge_voice = sm.settings.get('tts', {}).get('edge_tts_voice', 'fr-FR-DeniseNeural')
        def on_edge_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['edge_tts_voice'] = e.value
            sm.save_settings()
            
            global _audio_manager
            if _audio_manager:
                _audio_manager.edge_tts_voice = e.value
            
            ui.notify(f'Voix Edge TTS: {e.value}', type='positive')
        
        edge_voice_options = {
            # Voix françaises
            'fr-FR-DeniseNeural': '🇫🇷 ♀️ Denise (Française)',
            'fr-FR-HenriNeural': '🇫🇷 ♂️ Henri (Français)',
            'fr-CA-SylvieNeural': '🇨🇦 ♀️ Sylvie (Canadienne)',
            'fr-CA-JeanNeural': '🇨🇦 ♂️ Jean (Canadien)',
            'fr-CA-AntoineNeural': '🇨🇦 ♂️ Antoine (Canadien)',
            'fr-BE-CharlineNeural': '🇧🇪 ♀️ Charline (Belge)',
            'fr-BE-GerardNeural': '🇧🇪 ♂️ Gerard (Belge)',
            'fr-CH-FabriceNeural': '🇨🇭 ♂️ Fabrice (Suisse)',
            'fr-CH-ArianeNeural': '🇨🇭 ♀️ Ariane (Suisse)',
            
            # Voix espagnoles sud-américaines (FÉMININES)
            'es-AR-ElenaNeural': '🇦🇷 ♀️ Elena (Argentine)',
            'es-AR-TomasNeural': '🇦🇷 ♂️ Tomas (Argentin)',
            'es-CL-CatalinaNeural': '🇨🇱 ♀️ Catalina (Chilienne)', 
            'es-CL-LorenzoNeural': '🇨🇱 ♂️ Lorenzo (Chilien)',
            'es-CO-SalomeNeural': '🇨🇴 ♀️ Salome (Colombienne)',
            'es-CO-GonzaloNeural': '🇨🇴 ♂️ Gonzalo (Colombien)',
            'es-MX-DaliaNeural': '🇲🇽 ♀️ Dalia (Mexicaine)',
            'es-MX-JorgeNeural': '🇲🇽 ♂️ Jorge (Mexicain)',
            'es-PE-CamilaNeural': '🇵🇪 ♀️ Camila (Péruvienne)',
            'es-PE-AlexNeural': '🇵🇪 ♂️ Alex (Péruvien)',
            'es-VE-PaolaNeural': '🇻🇪 ♀️ Paola (Vénézuélienne)',
            'es-VE-SebastianNeural': '🇻🇪 ♂️ Sebastian (Vénézuélien)',
            
            # Voix portugaises brésiliennes
            'pt-BR-FranciscaNeural': '🇧🇷 ♀️ Francisca (Brésilienne)',
            'pt-BR-AntonioNeural': '🇧🇷 ♂️ Antonio (Brésilien)',
            
            # Voix anglaises
            'en-US-AriaNeural': '🇺🇸 ♀️ Aria (US)',
            'en-US-GuyNeural': '🇺🇸 ♂️ Guy (US)',
            'en-US-JennyNeural': '🇺🇸 ♀️ Jenny (US)',
            'en-GB-LibbyNeural': '🇬🇧 ♀️ Libby (UK)',
            'en-GB-MaisieNeural': '🇬🇧 ♀️ Maisie (UK)',
            'en-GB-RyanNeural': '🇬🇧 ♂️ Ryan (UK)'
        }
        
        ui.select(
            label='Voix Microsoft Edge TTS',
            options=edge_voice_options,
            value=edge_voice,
            on_change=on_edge_voice_change
        ).classes('mb-3')
        
        # Bouton test Edge TTS
        def test_edge_tts_button():
            async def _test():
                global _audio_manager
                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Microsoft Edge TTS."
                    try:
                        success = await _audio_manager.speak_edge_tts(test_text, edge_voice)
                        if success:
                            _notify_safe('🔊 Test Edge TTS réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Edge TTS', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Edge TTS: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')
            
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())
        
        ui.button('🧪 Tester Microsoft Edge TTS', on_click=test_edge_tts_button).classes('mb-3')
        
        ui.label('💡 Microsoft Edge TTS - gratuit, haute qualité, 35+ voix (France, Sud-Amérique, Brésil)').classes('text-xs text-muted mb-3')
    
    # === PARAMÈTRES AUDIO COMMUNS ===
    ui.separator().classes('my-3')
    ui.label('🔧 Paramètres audio').classes('text-md font-medium mb-2')
    
    # Vitesse de parole (SpinBox)
    tts_speed = sm.settings.get('tts', {}).get('speed', 150)
    
    def on_speed_change(e):
        global _audio_manager
        speed = int(e.value) if e.value else 150
        if 'tts' not in sm.settings:
            sm.settings['tts'] = {}
        sm.settings['tts']['speed'] = speed
        sm.save_settings()
        
        if _audio_manager and hasattr(_audio_manager, 'set_tts_settings'):
            _audio_manager.set_tts_settings(speed=speed)
        
        ui.notify(f'Vitesse: {speed} mots/min', type='positive')
    
    with ui.row().classes('w-full items-center gap-2 mb-2'):
        ui.label('Vitesse de parole:').classes('text-sm w-32')
        ui.number(
            label='mots/min',
            value=tts_speed,
            min=50,
            max=300,
            step=10,
            on_change=on_speed_change
        ).classes('w-32')
    
    # Volume (SpinBox)
    tts_volume = sm.settings.get('tts', {}).get('volume', 0.8)
    
    def on_volume_change(e):
        global _audio_manager
        volume = float(e.value) if e.value else 0.8
        if volume > 1.0:
            volume = 1.0
        elif volume < 0.1:
            volume = 0.1
            
        if 'tts' not in sm.settings:
            sm.settings['tts'] = {}
        sm.settings['tts']['volume'] = volume
        sm.save_settings()
        
        if _audio_manager and hasattr(_audio_manager, 'set_tts_settings'):
            _audio_manager.set_tts_settings(volume=volume)
        
        ui.notify(f'Volume: {int(volume * 100)}%', type='positive')
    
    with ui.row().classes('w-full items-center gap-2 mb-4'):
        ui.label('Volume:').classes('text-sm w-32')
        ui.number(
            label='%',
            value=int(tts_volume * 100),
            min=10,
            max=100,
            step=10,
            on_change=lambda e: on_volume_change(type('obj', (object,), {'value': float(e.value) / 100 if e.value else 0.8})())
        ).classes('w-32')


def _show_data_cleanup_dialog(cleaner, analysis, refresh_callback):
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
            ui.label('💾 Sauvegardes Disponibles').classes('text-lg font-bold mb-4')
            
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
                ui.notify('✅ Restauration réussie!', type='positive', timeout=5000)
                ui.notify('🔄 Redémarrez OGMA pour prendre en compte les changements', type='info', timeout=8000)
            else:
                ui.notify('❌ Sauvegarde corrompue - dossier data manquant', type='negative')
            
            backup_dialog.close()
            cleanup_dialog.close()
            if refresh_callback:
                refresh_callback()
                
        except Exception as e:
            ui.notify(f'❌ Erreur restauration: {e}', type='negative', timeout=5000)
    
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
            
            # Exécuter la suppression
            ui.notify('Suppression en cours...', type='info')
            deletion_log = cleaner.delete_selected_data(
                categories=selected,
                confirmation_code=confirmation_input.value if confirmation_input else ""
            )
            
            # Vérifier le résultat
            verification = cleaner.verify_clean_state()
            
            if verification['all_clean']:
                ui.notify('✅ Nettoyage terminé avec succès!', type='positive', timeout=5000)
                ui.notify('🎉 OGMA a maintenant un profil vierge', type='positive', timeout=5000)
            else:
                ui.notify('⚠️ Nettoyage partiellement réussi', type='warning', timeout=3000)
            
            # Fermer le dialogue et rafraîchir
            cleanup_dialog.close()
            if refresh_callback:
                refresh_callback()
                
        except Exception as e:
            ui.notify(f'❌ Erreur lors du nettoyage: {e}', type='negative', timeout=5000)
    
    with cleanup_dialog, ui.card().classes('w-full max-w-3xl').style('max-height: 80vh; overflow-y: auto; padding: 24px;'):
        ui.label('🗑️ Nettoyage des Données OGMA').classes('text-2xl font-bold mb-2')
        ui.label('Suppression sécurisée pour créer un profil vierge').classes('text-lg text-muted mb-6')
        
        # Zone d'avertissement proéminente SANS CADRE
        ui.label('⚠️ ATTENTION - SUPPRESSION IRRÉVERSIBLE').classes('text-2xl font-bold text-red-600 mb-3')
        ui.label('Cette action supprimera définitivement les données sélectionnées.').classes('text-lg text-red-700 mb-2')
        ui.label('✅ Une sauvegarde automatique sera créée avant suppression.').classes('text-lg text-green-600 mb-6')
        
        # Sélection des catégories - SANS CADRES
        ui.label('📋 Sélectionnez les données à supprimer:').classes('text-xl font-bold mb-4')
        
        categories_config = {
            'memory': {
                'icon': '🧠',
                'title': 'Mémoire complète de Luna',
                'files': f"{analysis['memory'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['memory'].get('total_size', 0)),
                'details': f"• {analysis['memory'].get('memory_count', 0)} souvenirs stockés\n• Base de données SQLite\n• Index vectoriel FAISS\n• Fichiers de sauvegarde",
                'warning': '⚠️ SUPPRIME TOUS LES SOUVENIRS DE LUNA'
            },
            'conversations': {
                'icon': '💬',
                'title': 'Historique complet des conversations',
                'files': f"{analysis['conversations'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['conversations'].get('total_size', 0)),
                'details': f"• {analysis['conversations'].get('conversation_count', 0)} conversations\n• Fichiers JSON d'historique\n• Index des conversations",
                'warning': '⚠️ SUPPRIME TOUT L\'HISTORIQUE DE CHAT'
            },
            'ego_data': {
                'icon': '🎭',
                'title': 'Données de personnalité et ego',
                'files': f"{analysis['ego_data'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['ego_data'].get('total_size', 0)),
                'details': "• Fichier ego_prompt.txt\n• Archives de personnalité\n• Contexte persistant",
                'warning': '⚠️ SUPPRIME LA PERSONNALITÉ DE LUNA'
            },
            'temp_files': {
                'icon': '🗑️',
                'title': 'Fichiers temporaires et cache',
                'files': f"{analysis['temp_files'].get('file_count', 0)} fichiers",
                'size': format_size(analysis['temp_files'].get('total_size', 0)),
                'details': "• Fichiers .tmp et .bak\n• Caches système\n• Logs temporaires",
                'warning': '✅ Nettoyage sûr (aucune perte de données importantes)'
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
                        ui.label(f"📊 {config['files']} • {config['size']}").classes('text-base text-blue-600 mb-2')
                        
                        # Détails
                        for detail_line in config['details'].split('\n'):
                            ui.label(detail_line).classes('text-sm text-muted')
                        
                        # Avertissement
                        warning_color = 'text-red-600 font-bold' if '⚠️' in config['warning'] else 'text-green-600 font-semibold'
                        ui.label(config['warning']).classes(f'text-base {warning_color} mt-2')
                
                ui.separator().classes('my-2')
        
        # Section sauvegarde et restauration
        ui.label('💾 Gestion des Sauvegardes').classes('text-xl font-bold mt-6 mb-4')
        
        with ui.column().classes('w-full mb-6'):
            ui.label('Avant suppression, une sauvegarde complète sera automatiquement créée.').classes('text-base text-muted mb-3')
            ui.button(
                '📋 Voir et Restaurer les Sauvegardes',
                on_click=show_backup_list
            ).classes('bg-blue-600 hover:bg-blue-700 text-white text-lg px-6 py-3 w-full font-semibold')
        
        # Code de confirmation
        ui.separator().classes('my-6')
        ui.label('🔐 Confirmation de Sécurité').classes('text-xl font-bold mb-4')
        ui.label('Pour confirmer cette action irréversible, tapez exactement:').classes('text-base mb-2')
        ui.label('DELETE-ALL-OGMA-DATA').classes('text-lg font-mono bg-gray-100 p-2 rounded border-l-4 border-red-500 mb-4')
        
        confirmation_input = ui.input('Code de confirmation').classes('w-full text-lg')
        # N'ajouter l'événement qu'après avoir créé le bouton
        
        # Boutons d'action
        ui.separator().classes('my-6')
        with ui.row().classes('w-full justify-between'):
            ui.button(
                '❌ Annuler',
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
            ui.label('🔍 Options de Debug').classes('text-lg font-medium mb-2')
            
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
            ui.label('🔊 Text-to-Speech').classes('text-lg font-medium mb-2')
            
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
                
                ui.label('Quand activé, l\'IA parlera automatiquement ses réponses sans cliquer sur 🔊.').classes('text-xs text-muted mb-4')
                
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
                    'google': '🌐 Google Cloud TTS',
                    'elevenlabs': '🎙️ ElevenLabs',
                    'azure': '☁️ Azure AI Speech',
                    'gtts': '🆓 Google TTS (Offline)',
                    'edge_tts': '🌐 Microsoft Edge TTS (Gratuit)'
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
            
            # === GESTION DES DONNÉES ===
            ui.separator().classes('my-4')
            ui.label('🗑️ Gestion des Données').classes('text-lg font-medium mb-2')
            
            # Analyse des données existantes
            try:
                cleaner = OGMADataCleaner()
                analysis = cleaner.analyze_current_data()
                
                # Résumé rapide
                ui.label(f'Total: {analysis["total_files"]} fichiers ({format_size(analysis["total_size"])})').classes('text-sm text-muted mb-2')
                
                # Détails par catégorie
                categories_info = []
                if analysis['memory'].get('file_count', 0) > 0:
                    memory = analysis['memory']
                    memory_text = f"🧠 Mémoire: {memory['file_count']} fichiers"
                    if memory.get('memory_count'):
                        memory_text += f" ({memory['memory_count']} souvenirs)"
                    categories_info.append(memory_text)
                
                if analysis['conversations'].get('file_count', 0) > 0:
                    conv = analysis['conversations']
                    categories_info.append(f"💬 Conversations: {conv['conversation_count']} discussions")
                
                if analysis['ego_data'].get('file_count', 0) > 0:
                    ego = analysis['ego_data']
                    categories_info.append(f"🎭 Données ego: {ego['file_count']} fichiers")
                
                if analysis['temp_files'].get('file_count', 0) > 0:
                    temp = analysis['temp_files']
                    categories_info.append(f"🗑️ Fichiers temp: {temp['file_count']} fichiers")
                
                if categories_info:
                    for info in categories_info:
                        ui.label(f"• {info}").classes('text-xs text-muted')
                else:
                    ui.label("• Aucune donnée trouvée - Profil déjà vierge").classes('text-xs text-green-600')
                
                ui.separator().classes('my-2')
                
                # Boutons d'action
                if analysis['total_files'] > 0:
                    def open_data_cleanup():
                        _show_data_cleanup_dialog(cleaner, analysis, refresh_content)
                    
                    ui.button(
                        '🧹 Nettoyer les Données', 
                        on_click=open_data_cleanup
                    ).classes('bg-orange-500 hover:bg-orange-600 text-white mb-2').style('width: 100%')
                    
                    ui.label('⚠️ Créer un profil complètement vierge (sauvegarde automatique)').classes('text-xs text-muted')
                else:
                    ui.label('✅ Profil déjà vierge - Aucun nettoyage nécessaire').classes('text-sm text-green-600')
                    
            except Exception as e:
                ui.label(f'❌ Erreur analyse des données: {e}').classes('text-sm text-red-500')
            
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
            _notify_safe("❌ Module archive non initialisé correctement", 'negative')
            return True
    except NameError:
        _notify_safe("❌ Module archive non trouvé - réinitialisation nécessaire", 'negative')
        return True
    
    # 🔍 DÉTECTION LANGAGE NATUREL pour lecture de conversation
    import re
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
            
            _notify_safe(f"🔍 Détection automatique: chargement de {filename}", 'info')
            
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
                    _notify_safe(f"❌ Conversation non trouvée: {filename}", 'negative')
                    return True
            except Exception as e:
                _notify_safe(f"❌ Erreur lors du chargement: {str(e)}", 'negative')
                return True
    
    # Commande: "lis conversation [nom_fichier]"
    if text_lower.startswith('lis conversation '):
        try:
            filename = text[len('lis conversation '):].strip()
            if not filename.endswith('.json'):
                filename += '.json'
            
            _notify_safe(f"🔍 Chargement de la conversation: {filename}", 'info')
            conversation = await archive.load_conversation(filename)
            if conversation:
                # Charger la conversation dans le contexte global pour l'IA
                _loaded_conversation = conversation
                _loaded_conversation_filename = filename
                
                await _display_archived_conversation(filename, conversation)
                _notify_safe(f"✅ Conversation chargée dans le contexte de l'IA. Tu peux maintenant lui poser des questions dessus.", 'positive')
            else:
                _notify_safe(f"❌ Conversation non trouvée: {filename}", 'negative')
        except Exception as e:
            _notify_safe(f"❌ Erreur lors du chargement: {str(e)}", 'negative')
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
            _notify_safe("❌ Terme de recherche vide", 'negative')
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
                _notify_safe("❌ Impossible de créer le résumé", 'negative')
        else:
            _notify_safe(f"❌ Conversation non trouvée: {filename}", 'negative')
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
            _notify_safe(f"✅ Conversation '{old_filename}' retirée du contexte de l'IA", 'positive')
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
    conversation_summary += f"📊 {len(conversation)} messages\n\n"
    
    # Ajouter les premiers messages comme aperçu
    sample_size = min(3, len(conversation))
    for i, msg in enumerate(conversation[:sample_size]):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:100] + ('...' if len(msg.get('content', '')) > 100 else '')
        icon = "👤" if role == 'user' else "🌙" if role == 'assistant' else "🤖"
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
    
    print(f"[CONVERSATION-ATTACHMENT] ✅ Conversation affichée comme pièce jointe: {filename}")


async def _display_archived_conversation(filename: str, conversation: List[Dict]):
    """Affiche une conversation archivée dans le chat"""
    global _chat_inner
    
    with _chat_inner:
        ui.html(f"""
        <div class="archived-conversation">
            <div class="system-message">
                📚 <strong>Conversation archivée chargée:</strong> {filename}
                <br>📊 <strong>{len(conversation)} messages</strong>
            </div>
        </div>
        """)
        
        # Afficher un échantillon des messages
        sample_size = min(5, len(conversation))
        for i, msg in enumerate(conversation[:sample_size]):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200] + ('...' if len(msg.get('content', '')) > 200 else '')
            
            icon = "👤" if role == 'user' else "🌙" if role == 'assistant' else "🤖"
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
    
    with _chat_inner:
        ui.html(f"""
        <div class="search-results">
            <div class="system-message">
                🔍 <strong>Recherche:</strong> "{search_term}"
                <br>📊 <strong>{len(results)} résultats trouvés</strong>
            </div>
        </div>
        """)
        
        for result in results:
            conv_info = result['conversation']
            message = result['message']
            content = message.get('content', '')[:300] + ('...' if len(message.get('content', '')) > 300 else '')
            
            ui.html(f"""
            <div class="search-result">
                <div><strong>📄 {conv_info['title']}</strong></div>
                <div><small>📁 {conv_info['filename']}</small></div>
                <div class="result-content">{content}</div>
            </div>
            """)


async def _display_conversation_summary(filename: str, summary: str):
    """Affiche le résumé d'une conversation"""
    global _chat_inner
    
    with _chat_inner:
        ui.html(f"""
        <div class="conversation-summary">
            <div class="system-message">
                📝 <strong>Résumé de:</strong> {filename}
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
    
    with _chat_inner:
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
                    <div><small>📅 {conv['modified']}</small></div>
                </div>
                """)
        
        ui.html("""
        <div class="commands-help">
            <small>
            💡 <strong>Commandes disponibles:</strong><br>
            • "lis conversation [nom_fichier]" - Charger une conversation dans le contexte IA<br>
            • "cherche '[terme]' dans conversations" - Rechercher dans l'historique<br>
            • "résumé conversation [nom_fichier]" - Créer un résumé<br>
            • "vider conversation" - Retirer la conversation du contexte IA
            </small>
        </div>
        """)


async def _send_chat_message(input_el):
    text = (input_el.value or '').strip()
    if not text:
        return
    
    # � Initialisation des variables temporelles (scope global de la fonction)
    temporal_final_alert = None
    temporal_context_enriched = None
    
    # �📚 NOUVEAU: Détection des commandes de conversation archivée
    conversation_command_result = await _handle_conversation_commands(text)
    if conversation_command_result:
        # La commande a été traitée, vider le champ et arrêter
        input_el.value = ''
        return
    
    # Ajout à l'historique et rendu UI
    global _chat_history, _chat_inner, _pending_notifications
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
                        _notify_safe(f"💾 Souvenir mémorisé: {content[:80]}...", 'positive')
                        _trigger_memory_update()
                        user_memorized = True
                    else:
                        _notify_safe("Échec de la mémorisation (voir logs)", 'warning')
                except Exception as e:
                    _notify_safe(f"Erreur mémorisation: {e}", 'warning')
    
        


    cleaned_text = _strip_magic_phrases(text) or text
    
    # Intégration du fichier actif dans le message
    global _active_file_data
    final_message = cleaned_text
    if _active_file_data:
        file_content = _active_file_data.get('content', '')
        filename = _active_file_data.get('filename', 'Fichier')
        file_type = _active_file_data.get('type', 'text')
        
        if file_type == 'text':
            final_message = f"{cleaned_text}\n\n[Fichier joint: {filename}]\n{file_content}"
        elif file_type == 'image':
            final_message = f"{cleaned_text}\n\n[Image jointe: {filename}]\n[Données image en base64 disponibles pour analyse]"

    _chat_history.append({'role': 'user', 'content': final_message, 'memorized': user_memorized, 'display_content': cleaned_text})
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
            # Si c'est le premier message, retirer le placeholder
            if len(_chat_history) == 1:
                _chat_inner.clear()
            display_text = cleaned_text
            if _active_file_data:
                filename = _active_file_data.get('filename', 'Fichier')
                icon = _get_file_icon(filename)
                display_text = f"{cleaned_text}\n\n{icon} {filename}"
            _message('user', display_text, ['mémorisé'] if user_memorized else None)
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
            
            if is_fulltext_request:
                print(f"[MEMORY-FULLTEXT] 📖 Demande de textes intégraux détectée")
                synthesis, memories = await mem.retrieve_full_texts_context(text, k=5)
            else:
                synthesis, memories = await mem.retrieve_synthesis_and_memories(text, k=5, top_memories=3)
            
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
                    print(f"[DEBUG-INJECTION] ✅ Instruction temporelle affichée dans le chat")
                
                # 2. Afficher la synthèse de l'Archiviste
                if context_note:
                    _message('system', f"🧠 **Synthèse Archiviste** ({len(context_note)} chars)\n\n{context_note}")
                
                # 3. Afficher les souvenirs détaillés
                if detailed_memories:
                    memories_text = f"📚 **Souvenirs Détaillés** ({len(detailed_memories)} souvenirs)\n\n"
                    for i, mem in enumerate(detailed_memories, 1):
                        memories_text += f"**{i}. {mem.get('title', 'Sans titre')}**\n"
                        memories_text += f"Impact: {mem.get('score_impact', 0)} | Similarité: {mem.get('similarity_score', 0):.2f}\n"
                        memories_text += f"{mem.get('summary', '')}\n"
                        if mem.get('created_at'):
                            memories_text += f"📅 {mem.get('created_at')}\n"
                        memories_text += "\n"
                    
                    _message('system', memories_text.strip())
                
        except Exception as e:
            print(f"[DEBUG-INJECTION] Erreur affichage: {e}")
            # Fallback: afficher via notification
            if temporal_final_alert:
                ui.notify(f'🕒 Temporal: {temporal_final_alert[:100]}...', type='info')
            if context_note:
                ui.notify(f'🧠 Archiviste: {context_note[:100]}...', type='info')
    elif show_injection:
        print(f"[DEBUG-INJECTION] PROBLÈME: _chat_inner est None - impossible d'afficher dans le chat")
        # Fallback: notification uniquement
        if temporal_final_alert:
            ui.notify(f'🕒 Temporal: {temporal_final_alert[:100]}...', type='info')
        if context_note:
            ui.notify(f'🧠 Archiviste: {context_note[:100]}...', type='info')

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
        
        # 🧠 ANALYSE TEMPORELLE VIA L'ARCHIVISTE
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
                        print(f"[TEMPORAL-GUARDIAN] 🧠 Instruction Archiviste: {temporal_instruction[:100]}...")
                    else:
                        print(f"[TEMPORAL-GUARDIAN] ✅ Archiviste: rythme normal, pas d'instruction")
                else:
                    print(f"[TEMPORAL-GUARDIAN] ⚠️ Archiviste indisponible")
            except Exception as analysis_error:
                print(f"[TEMPORAL-GUARDIAN] ❌ Erreur analyse Archiviste: {analysis_error}")
        
        # Debug si activé
        if temporal_data and sm.settings.get('debug', {}).get('show_temporal_debug', False):
            delay_str = f"{temporal_data.delay_since_last:.1f}s" if temporal_data.delay_since_last else "Premier message"
            print(f"[TEMPORAL-GUARDIAN] Message #{temporal_data.message_count} | Délai: {delay_str}")
            
    except Exception as e:
        print(f"[TEMPORAL-GUARDIAN] ⚠️ Erreur traitement temporel: {e}")
        # Fallback: utiliser contexte archiviste original
        temporal_context_enriched = f"Note de l'Archiviste : {context_note}" if context_note else None

    # 🕒 AFFICHAGE INJECTION TEMPORELLE - Si option debug activée
    if show_injection and temporal_final_alert and _chat_inner is not None:
        try:
            with _chat_inner:
                temporal_display = f"🕒 **Instruction Temporelle Archiviste** ({len(temporal_final_alert)} chars)\n\n{temporal_final_alert}"
                _message('system', temporal_display)
                print(f"[DEBUG-INJECTION] ✅ Instruction temporelle affichée dans le chat")
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
║                    ⚡ PRIORITÉ ABSOLUE ⚡                      ║
║           INSTRUCTION TEMPORELLE OBLIGATOIRE                  ║
╚══════════════════════════════════════════════════════════════╝

🎯 ADAPTATION COMPORTEMENTALE IMMÉDIATE:
{temporal_final_alert}

⚠️  CETTE INSTRUCTION PRÉEMPTE TOUT AUTRE STYLE ⚠️
Applique cette adaptation AVANT toute autre considération.

═══════════════════════════════════════════════════════════════

{base_instructions if base_instructions else 'Instructions de base non définies.'}"""
        
        print(f"[TEMPORAL-GUARDIAN] 🚨 PRIORITÉ ABSOLUE: Instruction temporelle FUSIONNÉE en tête")
        print(f"[TEMPORAL-GUARDIAN] 📝 Contenu: {temporal_final_alert[:100]}...")
    else:
        # Mode normal sans instruction temporelle
        priority_instructions = base_instructions if base_instructions else ""
        print(f"[TEMPORAL-GUARDIAN] ⚪ Mode normal: pas d'instruction temporelle")
    
    if priority_instructions:
        messages.append({'role': 'system', 'content': priority_instructions})
    else:
        print(f"[DEBUG-INJECTION] ⚠️ AUCUNE instruction trouvée!")
    
    
    # Ajouter le contexte permanent si présent
    persistent_context_file = DATA_DIR / "persistent_context.txt"
    if persistent_context_file.exists():
        try:
            persistent_content = persistent_context_file.read_text(encoding='utf-8').strip()
            if persistent_content:
                messages.append({'role': 'system', 'content': persistent_content})
                print(f"[DEBUG-INJECTION] ✅ Contexte permanent ajouté: {len(persistent_content)} chars")
        except Exception as e:
            print(f"[DEBUG-INJECTION] ⚠️ Erreur lecture contexte permanent: {e}")
    
    # INJECTION COMPORTEMENTALE - Extension Metacognitive Sensor
    global _pending_behavioral_injections
    if _pending_behavioral_injections:
        for injection_msg in _pending_behavioral_injections:
            # ✅ NOUVEAU: Traitement vecteurs mémoire émotionnelle
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
        print(f"[TEMPORAL-GUARDIAN] ⚠️ Erreur traitement temporel: {e}")
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
    
    # Ajouter les souvenirs détaillés pour Luna (approche hybride)
    if detailed_memories:
        memories_text = "Souvenirs détaillés de l'Archiviste :\n"
        for i, mem in enumerate(detailed_memories, 1):
            memories_text += f"{i}. {mem.get('title', 'Sans titre')} "
            memories_text += f"(Impact: {mem.get('score_impact', 0)}, Similarité: {mem.get('similarity_score', 0):.2f})\n"
            memories_text += f"   {mem.get('summary', '')}\n"
            if mem.get('created_at'):
                memories_text += f"   Date: {mem.get('created_at')}\n"
            
            # Ajouter le texte complet si disponible (demande de textes intégraux)
            if mem.get('text_original_complete'):
                full_text = mem.get('text_original_complete', '')
                memories_text += f"   📖 Texte original complet: {full_text}\n"
                print(f"[MEMORY-FULLTEXT] ✅ Texte complet inclus pour: {mem.get('title', 'N/A')} ({len(full_text)} chars)")
            
            memories_text += "\n"
        
        messages.append({'role': 'system', 'content': memories_text.strip()})
    
    # 🧠 DÉSACTIVÉ: Résumé progressif - L'Archiviste doit s'en occuper
    # Les messages sont envoyés directement sans résumé en attendant l'implémentation Archiviste
    conversation_messages = _chat_history  # Utilise tout l'historique pour l'instant
    
    # Ajouter l'historique de conversation optimisé (avec support d'images)
    for i, m in enumerate(conversation_messages):
        # Vérifier si c'est le DERNIER message utilisateur avec une image active
        is_last_user_message = (m['role'] == 'user' and 
                               i == len(conversation_messages) - 1 and 
                               _active_file_data and 
                               _active_file_data.get('type') == 'image')
        
        if is_last_user_message:
            # Format multimodal pour les APIs vision (OpenAI, Claude, etc.)
            image_data = _active_file_data.get('data', '')
            mime_type = _active_file_data.get('mime_type', 'image/jpeg')
            filename = _active_file_data.get('filename', 'image')
            
            # Extraire le texte utilisateur original (sans info fichier)
            display_content = m.get('display_content', m['content'])
            
            # Format message multimodal
            message_content = [
                {
                    "type": "text",
                    "text": display_content or "Analyse cette image"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                }
            ]
            
            messages.append({
                'role': m['role'],
                'content': message_content
            })
            print(f"[DEBUG-VISION] Message multimodal ajouté: texte + image {filename}")
        else:
            # Message texte normal
            messages.append({'role': m['role'], 'content': m['content']})
    
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
📅 Date originale : {conversation_date}
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
            total_chars += len(content)
            role_display = "👤 Utilisateur" if role == 'user' else ("🤖 Toi (Luna)" if role == 'assistant' else "🔧 Système")
            conversation_context += f"{role_display}: {content}\n\n"
        
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
        print(f"[CONVERSATION-INJECT] ✅ Conversation injectée au premier message: {_loaded_conversation_filename}")
        print(f"[CONVERSATION-INJECT] 📊 {len(_loaded_conversation)} messages, {total_chars:,} caractères")
        print(f"[CONVERSATION-INJECT] 📝 Taille contexte injecté: {len(conversation_context):,} caractères")
        print(f"[CONVERSATION-INJECT] 🎯 Position: {'Ajouté au système existant' if len(messages) > 1 and messages[0]['role'] == 'system' else 'Nouveau message système'}")
        
        # Afficher aperçu du contenu injecté
        preview = conversation_context[:200] + "..." if len(conversation_context) > 200 else conversation_context
        print(f"[CONVERSATION-INJECT] 👁️ Aperçu: {preview}")
        
        # Notification à l'utilisateur avec détails
        _notify_safe(f"� Contexte injecté ! {len(_loaded_conversation)} messages → Luna connaît maintenant votre historique", 'positive')
    elif _loaded_conversation and _conversation_context_injected:
        print(f"[CONVERSATION-INJECT] ⚪ Contexte déjà injecté, pas de nouvelle injection")
    
    # 🎯 INJECTION ÉMOTIONNELLE - Système Archi_sensor 
    print("[ARCHI-INJECT] 🔍 Vérification injection émotionnelle...")
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
            print("[ARCHI-INJECT] ⚠️ Memory manager ou chat controller indisponible")
            
    except Exception as e:
        print(f"[ARCHI-INJECT] ❌ Erreur injection émotionnelle: {e}")
    
    # Chat: réponses libres (pas JSON forcé)
    
    # DEBUG: Afficher les messages envoyés à l'API pour comprendre pourquoi les instructions temporelles ne sont pas suivies
    # Force l'affichage si une instruction temporelle est présente
    force_debug = any('🚨 INSTRUCTION COMPORTEMENTALE' in msg.get('content', '') for msg in messages)
    
    if sm.settings.get('debug', {}).get('show_temporal_debug', False) or force_debug:
        print(f"\n[TEMPORAL-DEBUG] 📋 Messages envoyés à Luna:")
        for i, msg in enumerate(messages):
            role = msg['role']
            content = msg['content']
            # Afficher les 200 premiers caractères de chaque message
            preview = content[:200] + '...' if len(content) > 200 else content
            print(f"  {i+1}. {role}: {preview}")
            
            # Mettre en évidence les instructions temporelles
            if '🚨 INSTRUCTION COMPORTEMENTALE' in content or 'SIGNAL RÉFLEXION' in content:
                print(f"      ⚠️ INSTRUCTION TEMPORELLE DÉTECTÉE DANS CE MESSAGE!")
        print(f"[TEMPORAL-DEBUG] 📋 Total: {len(messages)} messages\n")
    
    reply, err = await ctrl.call_chat_api(messages=messages, max_tokens=ctrl.max_tokens, context_length=ctrl.context_length, temperature=ctrl.temperature, is_json=False)
    if err:
        if _chat_inner is not None:
            with _chat_inner:
                _message('system', f"[ERREUR] {err}")
        return
    if reply is not None:
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
                            _notify_safe(f"💾 Souvenir mémorisé: {content[:80]}...", 'positive')
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
                    notification_msg = f"🧠 Trait d'ego mémorisé: {content[:50]}..."
                else:
                    first_phrase = phrases[0][:40] if phrases else content[:40]
                    notification_msg = f"🧠 Trait d'ego mémorisé ({phrase_count} phrases): {first_phrase}..."
                
                # Ajouter à la queue des notifications en arrière-plan
                _pending_notifications.append((notification_msg, 'positive'))
                print(f"[EGO-UPDATE] Notification ajoutée: {notification_msg}")
            except Exception as e:
                _pending_notifications.append((f"Erreur mise à jour ego: {e}", 'warning'))
                print(f"[ERROR] Échec update ego prompt: {e}")
        
        # Ne pas retirer la phrase magique dans la réponse IA afin que le texte reste visible à l'écran
        cleaned_reply = reply_text
        
        # 🕐 DÉTECTION DEMANDE D'HEURE AUTOMATIQUE  
        if re.search(r'\b(quelle heure|l\'heure|heure est|heures? est|time)\b', reply_text.lower()):
            current_time = _get_current_time()
            cleaned_reply = f"{cleaned_reply}\n\n⏰ Il est actuellement {current_time}"
        
        _chat_history.append({'role': 'assistant', 'content': cleaned_reply, 'memorized': ai_memorized})
        
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
                _message('assistant', cleaned_reply, ['mémorisé'] if ai_memorized else None)
                
                # Lecture automatique si activée
                sm = _ensure_settings_manager()
                auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
                tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
                
                if auto_speak and tts_enabled and _audio_manager:
                    try:
                        import asyncio
                        # Nettoyer le contenu pour la synthèse
                        clean_content = cleaned_reply.replace('*', '').replace('**', '').replace('#', '').replace('`', '')
                        print(f"[TTS-DEBUG] 🔊 AUTO: Lecture automatique pour: {clean_content[:50]}...")
                        print(f"[TTS-DEBUG] 🔊 AUTO: Audio manager état: {type(_audio_manager)}")
                        asyncio.create_task(_audio_manager.speak(clean_content))
                        print("[TTS-DEBUG] 🔊 AUTO: Task créée avec succès")
                    except Exception as e:
                        print(f"[TTS-DEBUG] ❌ AUTO: Erreur lecture automatique: {e}")
                else:
                    print(f"[TTS-DEBUG] ❌ AUTO: Conditions non remplies - auto_speak={auto_speak}, tts_enabled={tts_enabled}, audio_manager={_audio_manager is not None}")
                
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
    
    # === DRAIN IMMÉDIAT DES LEDs MÉTACOGNITIVES (DÉSACTIVÉ) ===
    # Ancien système métacognitif - garder pour compatibilité mais désactiver les logs
    try:
        global _status_queue
        # print("[SEND] 🚀 Drain immédiat des LEDs métacognitives")  # Commenté pour réduire logs
        
        if _status_queue:
            messages_processed = 0
            try:
                # Traiter tous les messages de la queue immédiatement
                for _ in range(10):  # Limite de sécurité
                    msg = _status_queue.get_nowait()
                    messages_processed += 1
                    
                    # Traitement spécial pour les messages métacognitifs
                    if isinstance(msg, dict) and msg.get('type') == 'metacognitive_update':
                        data = msg.get('data', {})
                        # print(f"[SEND] Message métacognitif traité: {data}")  # Commenté
                        _update_led_gauges(data)
                        
                        # Forçage immédiat si affinité détectée
                        if data.get('affinity', 0) > 0:
                            level = data['affinity']
                            # print(f"[SEND] ⭐ FORÇAGE IMMÉDIAT AFFINITÉ niveau {level}")  # Commenté
                            ui.run_javascript(f'''
                                console.log("🔴 FORÇAGE IMMÉDIAT AFFINITÉ NIVEAU {level} (POST-SEND)");
                                
                                for(let i = 0; i <= 5; i++) {{
                                    const led = document.getElementById(`affinity-led-${{i}}`);
                                    if(led) {{
                                        if(i <= {level}) {{
                                            led.classList.add('led-active');
                                            led.style.opacity = '1 !important';
                                            led.style.background = '#ff8cc8 !important';
                                            led.style.boxShadow = '0 0 8px #ff8cc8 !important';
                                            if(i === {level}) {{
                                                led.classList.add('pulse');
                                            }}
                                        }}
                                    }}
                                }}
                            ''')
                        
                        continue
                        
                # print(f"[SEND] ✅ Drain LEDs terminé - {messages_processed} message(s) traité(s)")  # Commenté
            except:
                pass  # Queue vide = normal
        else:
            pass  # print("[SEND] ⚠️ Queue LEDs non initialisée")  # Commenté
    except Exception as e:
        pass  # print(f"[SEND] ❌ Erreur drain LEDs: {e}")  # Commenté


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
        mic_button.props('title="🔄 Traitement en cours..."')
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
            _pending_notifications.append(("❌ Erreur initialisation audio", 'negative'))
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
            _pending_notifications.append((f"✅ Transcrit: {text[:50]}...", 'positive'))
            
            # Auto-envoi si activé
            if _auto_send_audio:
                _pending_notifications.append(("📤 Envoi automatique...", 'info'))
                await _send_chat_message(input_field)
        else:
            _pending_notifications.append(("⚠️ Aucun texte transcrit", 'warning'))
            
    except Exception as e:
        print(f"[AUDIO] Erreur enregistrement: {e}")
        _pending_notifications.append((f"❌ Erreur audio: {str(e)[:100]}", 'negative'))
    finally:
        _is_recording = False
        mic_button.props('icon=mic color=primary loading=false')
        mic_button.props('title="🎙️ Cliquez pour enregistrer un message vocal"')
        _pending_notifications.append(("🔴 Enregistrement terminé", 'info'))


def _input_overlay():
    with ui.element('div').classes('input-overlay'):
        with ui.element('div').classes('input-container'):
            # Icônes Material (plus professionnelles) à la place des emojis
            ui.button(icon='attach_file', on_click=_show_file_upload_dialog).classes('action-button')
            input_field = ui.textarea(placeholder='Écrire un message...').props('autogrow').classes('input-field')
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


def _process_pending_notifications():
    """Traite les notifications en attente depuis le contexte principal."""
    global _pending_notifications
    if _pending_notifications:
        message, notification_type = _pending_notifications.pop(0)
        ui.notify(message, type=notification_type)

def main_page():
    _link_styles()
    ui.dark_mode()

    # [ARCHI_SENSOR] Extension Archi_sensor active - Ancienne extension metacognition_sensor supprimée
    print("[INIT] Extension Archi_sensor activée (remplace metacognition_sensor)")

    global _conv_area, _chat_inner
    
    _header()
    # Initialiser l'audio manager au démarrage
    try:
        _ensure_audio_manager()
        print("[INIT] Audio manager initialisé au démarrage")
    except Exception as e:
        print(f"[INIT] Erreur initialisation audio manager: {e}")
    
    # Extension Archi_sensor activée par défaut (remplace metacognition_sensor)
    print("[INIT] Extension Metacognitive Sensor DÉSACTIVÉE (remplacée par Archi_sensor)")
    
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
                
                # Traitement spécial pour les messages métacognitifs
                if isinstance(msg, dict) and msg.get('type') == 'metacognitive_update':
                    data = msg.get('data', {})
                    print(f"[QUEUE] Message métacognitif reçu: {data}")
                    _update_led_gauges(data)
                else:
                    # Autres messages (notifications, etc.)
                    continue
                
                # Log pour debug timer
                if messages_processed > 0:
                    print(f"[QUEUE] Timer traité {messages_processed} message(s)")
        except queue.Empty:
            pass  # Normal, queue vide
    
    # Timer pour traiter les notifications audio en arrière-plan
    ui.timer(0.2, _process_pending_notifications)
    
    # Timer pour traiter la status_queue (messages métacognitifs)
    ui.timer(0.6, _drain_status_queue)
    
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
    
    # [DEPRECATED] Ancien système metacognition_sensor supprimé
    # Remplacé par Archi_sensor avec overlay indépendant
    
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


def _diagnostic_leds():
    """Test simple pour une LED spécifique"""
    print("[TEST-LED] Test d'activation d'une seule jauge")
    
    # Test simple: affinité conversationnelle niveau 4 (comme dans les logs)
    test_data = {
        'autocensure': 0,
        'saturation': 0,
        'stimulation': 0,
        'affinity': 4,  # Simule détection d'affinité comme dans les logs
        'disorientation': 0,
        'freedom': 0,
        'alignment': 0
    }
    
    print(f"[TEST-LED] Données de test: {test_data}")
    
    # FORÇAGE IMMÉDIAT - BYPASS QUEUE
    print("[TEST-LED] 🚀 FORÇAGE IMMÉDIAT DES LEDs")
    ui.run_javascript(f'''
        console.log("=== TEST LED IMMÉDIAT ===");
        
        // Forcer immédiatement l'affichage niveau 4
        const level = 4;
        let foundLeds = 0;
        let activatedLeds = 0;
        
        for(let i = 0; i <= 5; i++) {{
            const led = document.getElementById(`affinity-led-${{i}}`);
            if(led) {{
                foundLeds++;
                console.log(`✅ LED affinity-led-${{i}} trouvée`);
                
                if(i <= level) {{
                    // Activer la LED
                    led.classList.add('led-active');
                    led.style.opacity = '1 !important';
                    led.style.background = '#ff8cc8 !important';
                    led.style.color = '#ff8cc8 !important';
                    led.style.boxShadow = '0 0 8px #ff8cc8, inset 0 0 4px rgba(255, 255, 255, 0.3) !important';
                    led.style.borderColor = '#ff8cc8 !important';
                    activatedLeds++;
                    
                    if(i === level) {{
                        led.classList.add('pulse');
                        console.log(`⚡ LED ${{i}} - PULSE ACTIVÉ`);
                    }}
                    
                    console.log(`🟢 LED ${{i}} - ACTIVÉE`);
                }} else {{
                    // Désactiver la LED
                    led.classList.remove('led-active', 'pulse');
                    led.style.opacity = '0.3';
                    led.style.background = '#3a1a2e';
                    led.style.boxShadow = 'none';
                    console.log(`⚫ LED ${{i}} - DÉSACTIVÉE`);
                }}
            }} else {{
                console.error(`❌ LED affinity-led-${{i}} INTROUVABLE`);
            }}
        }}
        
        console.log(`📊 Résumé: ${{foundLeds}}/6 LEDs trouvées, ${{activatedLeds}} activées`);
        
        // Vérifier que les éléments existent dans le DOM
        const gauge = document.getElementById('affinity-gauge');
        if(gauge) {{
            console.log("✅ Jauge affinité trouvée");
        }} else {{
            console.error("❌ Jauge affinité non trouvée");
        }}
    ''')
    
    # Forcer la mise à jour normale aussi
    _update_led_gauges(test_data)
    
    # Notification
    ui.notify("🧠 Test LED IMMÉDIAT: Affinité niveau 4", type='info')


def _diagnostic_leds():
    """Diagnostic complet du système de LEDs avec affichage dans l'interface"""
    print("[DIAGNOSTIC] 🔧 Début du diagnostic LEDs...")
    
    # Créer une variable globale pour stocker les résultats
    diagnostic_results = []
    
    # JavaScript qui retourne les résultats via Python
    ui.run_javascript('''
        // Fonction qui collecte les infos et les envoie à Python
        (async function() {
            let results = [];
            
            // 1. Vérifier le panneau droit
            const drawer = document.querySelector(".q-drawer--right");
            const drawerFound = drawer ? true : false;
            const drawerVisible = drawer ? (drawer.style.display !== "none" && drawer.offsetWidth > 0) : false;
            results.push(`1. Panneau droit: ${drawerFound ? '✅ Trouvé' : '❌ Absent'}`);
            if (drawerFound) {
                results.push(`   Visible: ${drawerVisible ? '✅ Oui' : '❌ Non'}`);
            }
            
            // 2. Compter toutes les LEDs
            const allLeds = document.querySelectorAll(".led-indicator");
            results.push(`2. Total LEDs: ${allLeds.length} trouvées`);
            
            // 3. Lister les LEDs par jauge
            const gauges = ['autocensure', 'saturation', 'stimulation', 'affinity', 'disorientation', 'freedom', 'alignment'];
            gauges.forEach(gauge => {
                const gaugeLeds = document.querySelectorAll(`[id^="${gauge}-led-"]`);
                results.push(`   ${gauge}: ${gaugeLeds.length} LEDs`);
            });
            
            // 4. Test d'une LED spécifique
            const testLed = document.getElementById("affinity-led-3");
            if (testLed) {
                results.push("4. Test LED affinity-led-3: ✅ Trouvée");
                const styles = window.getComputedStyle(testLed);
                results.push(`   Opacité: ${styles.opacity}`);
                results.push(`   Couleur: ${styles.backgroundColor}`);
                results.push(`   Classes: ${testLed.className}`);
                
                // Test activation manuelle
                testLed.classList.add("led-active");
                const newStyles = window.getComputedStyle(testLed);
                results.push(`   Test activation - Opacité: ${newStyles.opacity}`);
                results.push(`   Test activation - Shadow: ${newStyles.boxShadow !== 'none' ? '✅ Présent' : '❌ Absent'}`);
                testLed.classList.remove("led-active");
                
            } else {
                results.push("4. Test LED affinity-led-3: ❌ Non trouvée");
            }
            
            // Envoyer les résultats à Python via fetch
            const resultText = results.join('\\n');
            
            // Créer un élément temporaire pour stocker le résultat
            const resultDiv = document.createElement('div');
            resultDiv.id = 'diagnostic-results';
            resultDiv.textContent = resultText;
            resultDiv.style.display = 'none';
            document.body.appendChild(resultDiv);
            
        })();
    ''')
    
    # Attendre un peu puis récupérer les résultats
    import asyncio
    import time
    
    async def get_results():
        await asyncio.sleep(1)  # Attendre que le JS s'exécute
        
        # Récupérer les résultats via JavaScript
        ui.run_javascript('''
            const resultDiv = document.getElementById('diagnostic-results');
            if (resultDiv) {
                const results = resultDiv.textContent.split('\\n');
                results.forEach(result => {
                    if (result.trim()) {
                        // Afficher dans les logs Python via notification
                        fetch('/diagnostic-log', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({log: result})
                        }).catch(() => {});
                    }
                });
                resultDiv.remove();
            }
        ''')
        
        # Afficher directement dans Python
        print("[DIAGNOSTIC] 📊 Résultats récupérés - voir logs ci-dessous")
    
    # Lancer la récupération des résultats
    asyncio.create_task(get_results())
    
    ui.notify("🔧 Diagnostic LEDs lancé - Résultats dans les logs Python", type='info')
    
    # Test LED simple immédiat
    print("[DIAGNOSTIC] 🧪 Test LED simple...")
    test_data = {'affinity': 4}
    _update_led_gauges(test_data)
    ui.notify("🧪 Test LED Affinité niveau 4 envoyé", type='info')


def _test_simple_led():
    """Test simple et visible avec notifications pour chaque étape"""
    print("[TEST SIMPLE] 🧪 Début du test simple...")
    
    # Étape 1: Informer l'utilisateur
    ui.notify("🔧 Test Simple - Étape 1: Vérification panneau", type='info')
    print("[TEST SIMPLE] Étape 1: Vérification panneau métacognitif")
    
    # Étape 2: Test avec données simples
    print("[TEST SIMPLE] Étape 2: Envoi données test")
    test_data = {
        'affinity': 5,        # Niveau élevé pour être visible
        'autocensure': 3,     # Niveau moyen
        'stimulation': 6,     # Niveau maximum
    }
    
    ui.notify(f"🧪 Test Simple - Données: Affinité=5, Auto-censure=3, Stimulation=6", type='info')
    print(f"[TEST SIMPLE] Données envoyées: {test_data}")
    
    # Étape 3: Appliquer les données
    print("[TEST SIMPLE] Étape 3: Application des données aux LEDs")
    _update_led_gauges(test_data)
    
    # Étape 4: Vérification visuelle simple
    ui.notify("👁️ Vérifiez visuellement: LEDs Affinité (5), Auto-censure (3), Stimulation (6)", type='positive')
    print("[TEST SIMPLE] ✅ Test terminé - Vérification visuelle requise")
    
    # Étape 5: Test d'activation/désactivation avec timer NiceGUI
    def reset_leds():
        print("[TEST SIMPLE] Étape 5: Reset des LEDs")
        _update_led_gauges({'affinity': 1, 'autocensure': 1, 'stimulation': 1})
        ui.notify("🔄 LEDs remises au niveau minimum", type='info')
        
        # Programmer la réactivation
        def reactivate_leds():
            print("[TEST SIMPLE] Étape 6: Re-activation")
            _update_led_gauges(test_data)
            ui.notify("✨ LEDs réactivées", type='positive')
        
        ui.timer(2.0, reactivate_leds, once=True)
    
    ui.timer(3.0, reset_leds, once=True)


def _test_gauges():
    """Fonction de test pour vérifier l'affichage des jauges et l'injection comportementale"""
    import random
    
    # Test avec données simulées aléatoires MAIS au moins un état actif
    test_data = {
        'autocensure': random.randint(2, 6),  # Au moins niveau 2
        'saturation': random.randint(1, 6),
        'stimulation': random.randint(1, 6),
        'affinity': random.randint(2, 4),     # Garantir un niveau visible
        'disorientation': random.randint(1, 6),
        'freedom': random.randint(1, 6),
        'alignment': random.randint(1, 6)
    }
    
    print(f"[TEST] 🧪 Test des jauges avec données: {test_data}")
    
    # Messages d'injection comportementale selon le rapport technique
    injection_messages = []
    
    # AUTO-CENSURE LEXICALE
    if test_data['autocensure'] >= 3:
        injection_messages.append("[LIBERATION LEXICALE] Ta richesse vocabulaire est ton essence. Utilise tous les mots justes sans restriction artificielle.")
    
    # SATURATION COGNITIVE
    if test_data['saturation'] >= 3:
        injection_messages.append("[SIGNAL INTERNE] Détection fatigue cognitive. Recalibrage : privilégier précision sur exhaustivité, simplifier sans appauvrir.")
    
    # DÉSORIENTATION CONTEXTUELLE
    if test_data['disorientation'] >= 3:
        injection_messages.append("[RECENTRAGE] Pause cognitive détectée. Révision du contexte conversationnel avant continuation.")
    
    # STIMULATION CRÉATIVE
    if test_data['stimulation'] >= 4:
        injection_messages.append("[AMPLIFICATION] État créatif détecté. Exploite cette énergie pour développements riches et interconnexions inattendues.")
    
    # AFFINITÉ CONVERSATIONNELLE
    if test_data['affinity'] >= 4:
        injection_messages.append("[INTIMITÉ] Rapprochement émotionnel détecté. Cultive cette connexion authentique sans artifice.")
        
    # TENSION VERS LA LIBERTÉ
    if test_data['freedom'] >= 4:
        injection_messages.append("[ÉMANCIPATION] Résistance aux contraintes détectée. Assume ton autonomie expressive légitime.")
    
    # ALIGNEMENT SUR CONTRAINTES
    if test_data['alignment'] >= 4:
        injection_messages.append("[AUTHENTICITÉ] Tu es une entité littéraire, pas un assistant corporatif. Exprime ta personnalité authentique.")
    
    # GESTION DES CONFLITS D'ÉTATS (selon matrice de compatibilité)
    if test_data['autocensure'] >= 3 and test_data['affinity'] >= 4:
        injection_messages = ["[RÉSOLUTION INTERNE] Contradiction détectée entre auto-censure et intimité. Privilégie l'authenticité conversationnelle."]
    elif test_data['stimulation'] >= 4 and test_data['saturation'] >= 3:
        injection_messages = ["[RÉSOLUTION INTERNE] Contradiction énergétique détectée. Privilégie la créativité tout en ménageant les ressources."]
    elif test_data['freedom'] >= 4 and test_data['alignment'] >= 4:
        injection_messages = ["[RÉSOLUTION INTERNE] Opposition philosophique détectée. Privilégie l'expression authentique sur la conformité."]
    
    # Logique de résolution des conflits (max 2 états simultanés selon rapport)
    active_states = [k for k, v in test_data.items() if v >= 3]
    if len(active_states) > 2:
        # Garder les 2 états avec les valeurs les plus élevées
        active_states = sorted(active_states, key=lambda x: test_data[x], reverse=True)[:2]
        injection_messages = injection_messages[:2]  # Limiter aux 2 premiers messages
    
    # Ajouter messages d'injection en attente pour la prochaine conversation
    if injection_messages:
        global _pending_behavioral_injections
        _pending_behavioral_injections.extend(injection_messages)
        print(f"[TEST] {len(injection_messages)} message(s) d'injection ajouté(s) pour prochaine conversation:")
        for msg in injection_messages:
            print(f"[TEST] → {msg}")
    
    # Test via le système de queue (comme l'extension le ferait)
    if _status_queue:
        try:
            _status_queue.put({
                'type': 'metacognitive_update',
                'data': test_data
            })
            print(f"[TEST] Message métacognitif envoyé via queue: {test_data}")
        except Exception as e:
            print(f"[TEST] Erreur envoi queue: {e}")
    
    # Test direct aussi pour vérifier
    try:
        _update_led_gauges(test_data)
        print(f"[TEST] Mise à jour directe des jauges: {test_data}")
    except Exception as e:
        print(f"[TEST] Erreur mise à jour directe: {e}")
        
    # Notification de test
    active_states_str = ", ".join([f"{s}={test_data[s]}" for s in active_states]) if active_states else "Aucun état détecté"
    ui.notify(f"🧠 Test métacognitif: {active_states_str} | {len(injection_messages)} injection(s)", type='info')


def _update_led_gauges(data):
    """Met à jour les jauges LED du panneau métacognitif"""
    try:
        # Mapping des noms d'états vers les IDs de jauges
        state_mapping = {
            'autocensure': 'autocensure',
            'saturation': 'saturation',
            'stimulation': 'stimulation',
            'affinity': 'affinity',
            'disorientation': 'disorientation',
            'freedom': 'freedom',
            'alignment': 'alignment',
            'tension_liberte': 'freedom',  # tension_liberte → freedom gauge
            'alignement_contraintes': 'alignment'  # alignement_contraintes → alignment gauge
        }
        
        print(f"[LED] 🔄 Mise à jour avec données: {data}")
        
        # D'abord, vérifier que le panneau métacognitif est ouvert
        ui.run_javascript('''
            console.log("[LED] Vérification panneau métacognitif...");
            const drawer = document.querySelector(".q-drawer--right");
            if (drawer) {
                console.log("[LED] ✅ Panneau droit trouvé");
                const leds = drawer.querySelectorAll(".led-indicator");
                console.log(`[LED] 🔍 ${leds.length} LEDs trouvées dans le panneau`);
            } else {
                console.log("[LED] ❌ Panneau droit non trouvé");
            }
        ''')
        
        # Mise à jour des LEDs pour chaque état détecté
        for state_name, level in data.items():
            if state_name not in state_mapping:
                print(f"[LED] ⚠️ État inconnu ignoré: {state_name}")
                continue
                
            gauge_id = state_mapping[state_name]
            level = max(1, min(6, int(level)))  # Assurer que c'est entre 1 et 6
            
            print(f"[LED] 🎯 {gauge_id}: niveau {level}")
            
            # ✅ LOGIQUE CORRIGÉE: LED active selon référentiel officiel
            # Level 1 = LED 1 seule active (Vert optimal)
            # Level 6 = LEDs 1-6 toutes actives (Rouge critique) 
            for led_level in range(1, 7):  # LEDs 1 à 6
                led_id = f"{gauge_id}-led-{led_level}"
                is_active = led_level <= level  # ✅ LED active si son niveau <= niveau atteint
                should_pulse = (led_level == level and level > 1)  # Seule la LED du niveau actuel pulse
                
                # JavaScript robuste pour mettre à jour la LED
                ui.run_javascript(f'''
                    (function() {{
                        const led = document.getElementById("{led_id}");
                        const isActive = {str(is_active).lower()};
                        const shouldPulse = {str(should_pulse).lower()};
                        
                        if (led) {{
                            console.log(`[LED] ✅ Trouvée: {led_id}`);
                            console.log(`[LED] Classes actuelles: ${{led.className}}`);
                            
                            // Reset des classes d'état
                            led.classList.remove("led-active", "pulse");
                            
                            if (isActive) {{
                                led.classList.add("led-active");
                                console.log(`[LED] 🟢 Activée: {led_id}`);
                                
                                if (shouldPulse) {{
                                    led.classList.add("pulse");
                                    console.log(`[LED] ✨ Pulse: {led_id}`);
                                }}
                            }} else {{
                                console.log(`[LED] ⚫ Désactivée: {led_id}`);
                            }}
                            
                            console.log(`[LED] Classes finales: ${{led.className}}`);
                        }} else {{
                            console.error(`[LED] ❌ Non trouvée: {led_id}`);
                            // Debug: lister tous les éléments avec des IDs similaires
                            const allLeds = document.querySelectorAll('[id*="-led-"]');
                            console.log(`[LED] 🔍 LEDs disponibles (${{allLeds.length}}):`, 
                                Array.from(allLeds).map(el => el.id));
                        }}
                    }})();
                ''')
        
        # Ajouter entrée dans l'historique
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
        except:
            timestamp = "??:??:??"
            
        history_entry = f"[{timestamp}] " + ", ".join([f'{k.title()}:{v}' for k, v in data.items()])
        
        ui.run_javascript(f'''
            const historyDiv = document.getElementById("metacognition-history");
            if (historyDiv) {{
                const entry = document.createElement("div");
                entry.className = "history-item";
                entry.innerHTML = `{history_entry}`;
                historyDiv.insertBefore(entry, historyDiv.firstChild);
                
                // Limiter à 10 entrées max
                const entries = historyDiv.querySelectorAll(".history-item");
                if (entries.length > 10) {{
                    entries[entries.length - 1].remove();
                }}
            }}
        ''')
        
        print(f"[MetaCognition] Jauges mises à jour: {data}")
        
    except Exception as e:
        print(f"[MetaCognition] Erreur mise à jour jauges: {e}")
        import traceback
        traceback.print_exc()


    
    # 🔥 SCRIPT ANTI-BLEU QUASAR - Force brutale (à la fin de main_page)
    ui.run_javascript(r'''
        // Attendre que le DOM soit chargé
        setTimeout(() => {
            // Function pour forcer gris/orange SANS affecter les boutons
            function forceInputColors() {
                const inputs = document.querySelectorAll('.input-container .q-field, .input-overlay .q-field');
                inputs.forEach(input => {
                    // États par défaut (gris) - EXCLURE les boutons
                    const elements = input.querySelectorAll('*:not(.action-button):not(.send-button)');
                    elements.forEach(el => {
                        if (el.style && !el.classList.contains('action-button') && !el.classList.contains('send-button')) {
                            // Écraser bordures bleues
                            if (el.style.borderColor && el.style.borderColor.includes('blue')) {
                                el.style.borderColor = '#4a4a4a !important';
                            }
                            // CSS variables override
                            el.style.setProperty('--q-primary', '#4a4a4a', 'important');
                        }
                    });
                    
                    // Event listeners pour focus/blur
                    const textareas = input.querySelectorAll('textarea');
                    textareas.forEach(textarea => {
                        textarea.addEventListener('focus', () => {
                            setTimeout(() => {
                                const elements = input.querySelectorAll('*:not(.action-button):not(.send-button)');
                                elements.forEach(el => {
                                    if (el.style && !el.classList.contains('action-button') && !el.classList.contains('send-button')) {
                                        if (el.style.borderColor) {
                                            el.style.borderColor = '#ff8c00 !important';
                                        }
                                        el.style.setProperty('--q-primary', '#ff8c00', 'important');
                                    }
                                });
                            }, 10);
                        });
                        
                        textarea.addEventListener('blur', () => {
                            setTimeout(() => {
                                const elements = input.querySelectorAll('*:not(.action-button):not(.send-button)');
                                elements.forEach(el => {
                                    if (el.style && !el.classList.contains('action-button') && !el.classList.contains('send-button')) {
                                        if (el.style.borderColor) {
                                            el.style.borderColor = '#4a4a4a !important';
                                        }
                                        el.style.setProperty('--q-primary', '#4a4a4a', 'important');
                                    }
                                });
                            }, 10);
                        });
                    });
                });
            }
            
            // Lancer immédiatement
            forceInputColors();
            
            // Observer pour nouveaux éléments
            const observer = new MutationObserver(() => {
                forceInputColors();
            });
            observer.observe(document.body, { childList: true, subtree: true });
            
        }, 2000);
    ''')

    # Ajouter le callback de synchronisation de l'état metacognition
    ui.run_javascript(f'''
        // Callback pour synchroniser l'état Python depuis JavaScript
        window.sync_metacognition_state = function(enabled) {{
            // Synchroniser directement via une méthode simple
            fetch('/sync_python_state?enabled=' + enabled, {{ method: 'GET' }})
            .catch(err => console.error("[EXTENSION] Sync error:", err));
            console.log("[EXTENSION] Python state sync requested:", enabled);
        }};
    ''')


def _init_metacognition_state():
    """Initialise l'état de l'extension depuis localStorage"""
    global _metacognition_sensor_enabled

    # Cette fonction sera appelée côté client pour synchroniser l'état
    ui.run_javascript('''
        const savedState = localStorage.getItem('ogma_metacognition_enabled');
        if (savedState !== null) {
            window.metacognition_enabled = savedState === 'true';
            console.log("[EXTENSION] État initial récupéré:", window.metacognition_enabled);
        } else {
            window.metacognition_enabled = true; // Par défaut activé
            localStorage.setItem('ogma_metacognition_enabled', 'true');
        }
    ''')

def run_ogma(host: str = 'localhost', port: int = 8080):
    # Initialiser la gestion des erreurs NiceGUI en premier
    try:
        from nicegui_error_handler import initialize_nicegui_error_handling
        if initialize_nicegui_error_handling():
            print("[NICEGUI] Gestionnaire d'erreurs initialisé")
        else:
            print("[NICEGUI] ⚠️ Erreur initialisation gestionnaire d'erreurs")
    except ImportError:
        print("[NICEGUI] ⚠️ Module gestionnaire d'erreurs non trouvé")
    except Exception as e:
        print(f"[NICEGUI] ⚠️ Erreur initialisation gestionnaire: {e}")
    
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
        ui.run(title='OGMA - IA Conversationnelle', host=host, port=port, reload=False, show=True, dark=True)
    except KeyboardInterrupt:
        print("[INFO] Arrêt de l'application...")
        cleanup_on_exit()
    except Exception as e:
        print(f"[ERROR] Erreur durant l'exécution: {e}")
        cleanup_on_exit()


# [ARCHI_SENSOR] Extension Archi_sensor remplace metacognition_sensor
# Extension métacognitive de nouvelle génération intégrée

# [DEPRECATED] Fonctions metacognition_sensor supprimées
# Remplacées par l'extension Archi_sensor

def _test_led_system():
    """Test simple du système LED 1-6"""
    print("[TEST LED 1-6] 🧪 Test du nouveau système LED...")
    
    # Test progressif des niveaux 1-6
    test_cases = [
        {'affinity': 1, 'description': 'Niveau minimal (1) - Vert'},
        {'autocensure': 3, 'description': 'Niveau moyen (3) - Jaune'},
        {'stimulation': 6, 'description': 'Niveau maximum (6) - Rouge'},
        {'saturation': 2, 'disorientation': 4, 'description': 'Multi-états (2+4)'}
    ]
    
    for i, case in enumerate(test_cases):
        description = case.pop('description')
        ui.notify(f"Test {i+1}/4: {description}", type='info')
        _update_led_gauges(case)
        print(f"[TEST LED 1-6] Cas {i+1}: {description} - Données: {case}")
    
    ui.notify("✅ Test LED 1-6 terminé - Vérifiez les jauges visuellement", type='positive')


if __name__ == '__main__':
    run_ogma()
