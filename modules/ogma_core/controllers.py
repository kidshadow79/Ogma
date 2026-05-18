"""
OGMA CORE CONTROLLERS - Fonctions d'initialisation lazy des contrôleurs
=========================================================================

Contient toutes les fonctions _ensure_*() pour l'initialisation paresseuse
des contrôleurs IA, managers et extensions.

Note: Ces fonctions accèdent aux variables globales via le module globals.py
et modifient l'état global de l'application.
"""

from typing import Optional, cast, TYPE_CHECKING, Any
import queue
from pathlib import Path
import sys

# Ajouter le chemin racine OGMA au path pour les imports
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

# DATA_DIR défini localement (comme dans ogma_ng.py)
DATA_DIR = _ROOT_DIR / "data"

# Imports OGMA de base
from core_logic import (
    SettingsManager, APIManager, OllamaManager, GGUFManager, 
    KoboldManager, AIController, EmbeddingController
)
from memory_manager import MemoryManager
from audio_manager_wrapper import get_audio_manager

# Import du module globals local
from . import globals as g


# ============================================================================
# SETTINGS MANAGER
# ============================================================================
def ensure_settings_manager() -> SettingsManager:
    """Initialise paresseusement le SettingsManager."""
    if g._settings_mgr is None:
        settings_path = DATA_DIR / 'settings.json'
        g._settings_mgr = SettingsManager(settings_path)
    return g._settings_mgr


# ============================================================================
# AUDIO MANAGER
# ============================================================================
def ensure_audio_manager():
    """Initialise paresseusement l'audio manager avec TTS sans conflit."""
    if g._audio_manager is None:
        try:
            # Charger la préférence d'envoi automatique depuis les paramètres
            sm = ensure_settings_manager()
            g._auto_send_audio = sm.settings.get('audio', {}).get('auto_send', False)
            
            # Utiliser le nouveau wrapper TTS sans conflit
            g._audio_manager = get_audio_manager()
            
            # Initialiser le TTS sans conflit (auto-détection des moteurs)
            g._audio_manager.initialize_tts()
            
            print("[AUDIO] 🎵 Audio manager TTS sans conflit initialisé")
        except Exception as e:
            print(f"[AUDIO] Erreur initialisation: {e}")
    return g._audio_manager


# ============================================================================
# BACKENDS (API, Ollama, GGUF, Kobold)
# ============================================================================
def ensure_backends():
    """Initialise paresseusement les gestionnaires de backends."""
    if g._api_mgr is None:
        g._api_mgr = APIManager()
    if g._ollama_mgr is None:
        g._ollama_mgr = OllamaManager()
    if g._gguf_mgr is None:
        g._gguf_mgr = GGUFManager()
    if g._kobold_mgr is None:
        g._kobold_mgr = KoboldManager()
    
    # Charger les URLs des services depuis les paramètres si disponibles
    try:
        sm = ensure_settings_manager()

        # Configurer les managers avec le settings_manager pour les paramètres dynamiques
        if hasattr(g._ollama_mgr, 'set_settings_manager'):
            g._ollama_mgr.set_settings_manager(sm)
        if hasattr(g._gguf_mgr, 'set_settings_manager'):
            g._gguf_mgr.set_settings_manager(sm)

        chat = sm.settings.get('chat_api', {})
        arch = sm.settings.get('reasoning_api', {})
        emb = sm.settings.get('embedding_api', {})
        ollama_url = (chat.get('ollama_url') or arch.get('ollama_url') or emb.get('ollama_url'))
        kobold_url = (chat.get('kobold_url') or arch.get('kobold_url'))
        if ollama_url:
            g._ollama_mgr.api_url = str(ollama_url).rstrip('/')
        if kobold_url:
            g._kobold_mgr.api_url = str(kobold_url).rstrip('/')

        # 🎨 Initialiser l'extension text2img si activée
        try:
            from extensions.text2img import initialize_text2img, is_available as text2img_available
            img_settings = sm.settings.get('image_generation', {})
            if img_settings.get('enabled', False) and not text2img_available():
                initialize_text2img(sm)
            
        except ImportError:
            pass
    except Exception as e:
        print(f"[ERROR] Erreur initialisation backends: {e}")
    
    return g._api_mgr, g._ollama_mgr, g._gguf_mgr, g._kobold_mgr


# ============================================================================
# MEMORY MANAGER
# ============================================================================
def ensure_memory_manager() -> Optional[MemoryManager]:
    """Instancie MemoryManager (SQLite/FAISS) + configure Archiviste & Embeddings."""
    if g._memory_manager is not None:
        return g._memory_manager

    ensure_backends()
    sm = ensure_settings_manager()

    # Queue statut pour logs backend → UI
    if g._status_queue is None:
        g._status_queue = queue.Queue()

    # Import backend utils
    from utils.backend_utils import map_backend_for_controller

    # Contrôleur Archiviste
    g._archiviste_controller = AIController(
        'archiviste', 
        cast(OllamaManager, g._ollama_mgr), 
        cast(GGUFManager, g._gguf_mgr), 
        cast(KoboldManager, g._kobold_mgr)
    )
    # ═══ DEBUG_TOKEN_TRACKING ═══
    g._archiviste_controller._is_archiviste = True  # 🔬 FLAG LOGGING
    # ═══════════════════════════════
    arch = sm.settings.get('reasoning_api', {})
    arch_backend = map_backend_for_controller(arch.get('backend_type', 'API'))
    g._archiviste_controller.set_active_backend(arch_backend)
    
    # Gestion des valeurs -1 pour auto-detect
    max_tokens = arch.get('max_tokens', 512)
    context_length = arch.get('context_length', 4096)
    
    # SYSTÈME HYBRIDE: API + spécifications officielles
    if max_tokens == -1 or context_length == -1:
        try:
            from hybrid_detection import hybrid_auto_detect_capabilities
            provider = arch.get('provider', 'Aucun').lower()
            model = arch.get('model', '') or arch.get('api_model', '')
            api_key = arch.get('api_key', '')
            
            if provider != 'aucun' and model and api_key:
                print(f"[ARCHIVISTE-HYBRID] 🔍 Détection hybride {provider}")
                detected_caps = hybrid_auto_detect_capabilities(provider, model, "reasoning", api_key)
                if max_tokens == -1:
                    max_tokens = detected_caps['max_tokens']
                    print(f"[ARCHIVISTE-HYBRID] OK max_tokens optimal: {max_tokens:,}")
                if context_length == -1:
                    context_length = detected_caps['context_length']
                    print(f"[ARCHIVISTE-HYBRID] OK context_length optimal: {context_length:,}")
            else:
                if max_tokens == -1:
                    max_tokens = 512
                if context_length == -1:
                    context_length = 4096
        except Exception as e:
            if max_tokens == -1:
                max_tokens = 512
            if context_length == -1:
                context_length = 4096
            print(f"[ARCHIVISTE-AUTO] ERROR Erreur auto-détection: {e}")
    
    g._archiviste_controller.max_tokens = int(max_tokens)
    g._archiviste_controller.context_length = int(context_length)
    g._archiviste_controller.temperature = float(arch.get('temperature', 0.7))
    
    # Backend spécifique
    if arch_backend == 'API':
        g._archiviste_controller.api_manager.configure(
            arch.get('provider', 'Aucun'), arch.get('api_key', ''), arch.get('api_model', '')
        )
    elif arch_backend == 'Ollama':
        url = arch.get('ollama_url') or 'http://localhost:11434'
        cast(OllamaManager, g._ollama_mgr).api_url = str(url).rstrip('/')
        cast(OllamaManager, g._ollama_mgr).check_service()
        g._archiviste_controller.ollama_model = arch.get('ollama_model', '')
    elif arch_backend == 'GGUF/llama.cpp':
        model = arch.get('gguf_model', '')
        gguf_cfg = sm.settings.get('other_backends', {}).get('gguf', {})
        n_gpu_layers = int(gguf_cfg.get('gpu_layers', -1))
        gguf_ctx = int(gguf_cfg.get('context_size', 4096))
        _gguf_mgr = cast(GGUFManager, g._gguf_mgr)
        _model_changed = _gguf_mgr.model_name != model
        _ctx_changed = _gguf_mgr._requested_ctx != gguf_ctx
        _is_loading = getattr(_gguf_mgr, '_is_loading', False)
        if model and not _is_loading and (not _gguf_mgr.is_available or _model_changed or _ctx_changed):
            if _model_changed or _ctx_changed:
                print(f"[GGUF-ARCH] Rechargement : modèle={'changé' if _model_changed else 'id.'}, ctx={'changé' if _ctx_changed else 'id.'}")
            _gguf_mgr._is_loading = True
            try:
                _gguf_mgr.load_model(model, gguf_ctx, n_gpu_layers)
            finally:
                _gguf_mgr._is_loading = False
        elif _is_loading:
            print(f"[GGUF-ARCH] Chargement deja en cours, skip")
        # Override context_length avec la valeur réelle du modèle GGUF
        g._archiviste_controller.context_length = gguf_ctx
        _max_raw = int(arch.get('max_tokens', 2048))
        if _max_raw <= 0:
            _max_raw = 2048
        g._archiviste_controller.max_tokens = min(_max_raw, gguf_ctx - 512)
        print(f"[GGUF-ARCH] context_length={gguf_ctx}, max_tokens={g._archiviste_controller.max_tokens}")
    elif arch_backend == 'KoboldCpp':
        url = arch.get('kobold_url') or 'http://localhost:5001'
        cast(KoboldManager, g._kobold_mgr).api_url = str(url).rstrip('/')
        cast(KoboldManager, g._kobold_mgr).check_service()

    # Contrôleur Embeddings
    g._embedding_controller = EmbeddingController(
        cast(OllamaManager, g._ollama_mgr), 
        cast(GGUFManager, g._gguf_mgr)
    )
    emb = sm.settings.get('embedding_api', {})
    emb_backend = map_backend_for_controller(emb.get('backend_type', 'API'))
    g._embedding_controller.configure(
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

    # --- Auto-détection dimension embedding ---
    embedding_dim = 1024  # Fallback par défaut
    if g._embedding_controller and g._embedding_controller.is_available:
        try:
            import asyncio
            import concurrent.futures

            async def _probe_embed():
                return await g._embedding_controller.create_embedding("test")

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as _ex:
                        _result = _ex.submit(asyncio.run, _probe_embed()).result(timeout=10)
                else:
                    _result = loop.run_until_complete(_probe_embed())
            except RuntimeError:
                _result = asyncio.run(_probe_embed())

            if _result and len(_result) > 0:
                embedding_dim = len(_result)
                print(f"[MEMORY-MANAGER] Dimension auto-detectee: {embedding_dim}D")
            else:
                raise ValueError("Embedding vide retourné")
        except Exception as _e:
            embedding_dim = 1024
            _warn = f"Détection dimension embedding impossible ({_e}) – fallback 1024D"
            print(f"[MEMORY-MANAGER] {_warn}")
            if not hasattr(g, '_startup_warnings'):
                g._startup_warnings = []
            g._startup_warnings.append(_warn)
    else:
        print("[MEMORY-MANAGER] Embedding controller non disponible – fallback 1024D")
    # --- Fin auto-détection ---

    # Instanciation MemoryManager
    try:
        print(f"[MEMORY-MANAGER] 🧠 Initialisation MemoryManager...")
        
        g._memory_manager = MemoryManager(
            db_path=db_path,
            index_path=index_path,
            embedding_dim=embedding_dim,
            archiviste_ia=g._archiviste_controller,
            embedding_ia=g._embedding_controller,
            status_queue=g._status_queue,
            settings_manager=sm,
        )
        
        print(f"[MEMORY-MANAGER] ✅ MemoryManager initialisé avec succès")
        
        # Configurer le summarizer avec l'archiviste
        from conversation_summarizer import summarizer
        if g._archiviste_controller:
            summarizer.set_archiviste(g._archiviste_controller)
        
    except Exception as e:
        print(f"[MEMORY-MANAGER] ❌ Erreur init mémoire: {e}")
        import traceback
        traceback.print_exc()
        g._memory_manager = None

    return g._memory_manager


# ============================================================================
# ARCHIVISTE & EMBEDDING CONTROLLERS
# ============================================================================
def ensure_archiviste_controller():
    """Retourne contrôleur Archiviste, reconfiguré à chaque appel depuis les settings."""
    if g._archiviste_controller is None:
        ensure_memory_manager()

    # Reconfigurer à chaque appel (comme ensure_chat_controller) pour prendre en compte
    # les changements de modèle effectués via l'UI sans redémarrage
    sm = ensure_settings_manager()
    arch = sm.settings.get('reasoning_api', {})
    from utils.backend_utils import map_backend_for_controller
    arch_backend = map_backend_for_controller(arch.get('backend_type', 'API'))
    g._archiviste_controller.set_active_backend(arch_backend)
    g._archiviste_controller.temperature = float(arch.get('temperature', 0.7))

    if arch_backend == 'API':
        provider = arch.get('provider', 'Aucun')
        api_key = arch.get('api_key', '')
        model = arch.get('api_model', '') or arch.get('model', '')
        print(f"[CTRL-ARCH] configure => provider={provider!r} model={model!r}")
        g._archiviste_controller.api_manager.configure(provider, api_key, model)
    elif arch_backend == 'Ollama':
        url = arch.get('ollama_url') or 'http://localhost:11434'
        cast(OllamaManager, g._ollama_mgr).api_url = str(url).rstrip('/')
        g._archiviste_controller.ollama_model = arch.get('ollama_model', '')

    return g._archiviste_controller


def ensure_embedding_controller():
    """Retourne contrôleur Embedding (créé par ensure_memory_manager)."""
    if g._embedding_controller is None:
        ensure_memory_manager()
    return g._embedding_controller


# ============================================================================
# CHAT CONTROLLER
# ============================================================================
def ensure_chat_controller() -> AIController:
    """Initialise paresseusement le contrôleur de chat."""
    ensure_backends()
    sm = ensure_settings_manager()
    
    if g._chat_controller is None:
        g._chat_controller = AIController(
            'chat', 
            cast(OllamaManager, g._ollama_mgr), 
            cast(GGUFManager, g._gguf_mgr), 
            cast(KoboldManager, g._kobold_mgr)
        )
    
    chat = sm.settings.get('chat_api', {})
    backend = chat.get('backend_type', 'API')
    ctrl_backend = 'GGUF/llama.cpp' if backend == 'GGUF' else backend
    g._chat_controller.set_active_backend(ctrl_backend)
    
    # Gestion des valeurs -1 pour auto-detect
    max_tokens = chat.get('max_tokens', 512)
    context_length = chat.get('context_length', 4096)
    
    if max_tokens == -1 or context_length == -1:
        if backend == 'Ollama':
            # Pour Ollama : détecter depuis le modèle lui-même via /api/show
            # On ne lance PAS la détection hybride API (évite d'hériter de 128k Mistral → OOM)
            ollama_url = (chat.get('ollama_url') or 'http://localhost:11434').rstrip('/')
            ollama_model_name = chat.get('ollama_model', '')
            ollama_mgr = cast(OllamaManager, g._ollama_mgr)
            ollama_mgr.api_url = ollama_url
            if ollama_model_name:
                real_ctx = ollama_mgr.get_model_context_length_sync(ollama_model_name)
                if real_ctx:
                    print(f"[OLLAMA-INIT] context_length auto → {real_ctx} (détecté depuis {ollama_model_name})")
                    if context_length == -1:
                        context_length = real_ctx
                    if max_tokens == -1:
                        max_tokens = min(4096, real_ctx - 512)
                else:
                    print(f"[OLLAMA-INIT] /api/show sans résultat → fallback 8192/4096")
                    if context_length == -1:
                        context_length = 8192
                    if max_tokens == -1:
                        max_tokens = 4096
            else:
                if context_length == -1:
                    context_length = 8192
                if max_tokens == -1:
                    max_tokens = 4096
        elif backend in ('GGUF', 'KoboldCpp'):
            # Pour GGUF/Kobold : ne pas lancer la détection hybride API non plus
            # Les vraies valeurs seront settées dans les blocs dédiés ci-dessous
            if max_tokens == -1:
                max_tokens = 2048
            if context_length == -1:
                context_length = 4096
        else:
            # Backend API : détection hybride normale
            try:
                from hybrid_detection import hybrid_auto_detect_capabilities
                provider = chat.get('provider', 'Aucun').lower()
                model = chat.get('api_model', '') or chat.get('model', '')
                api_key = chat.get('api_key', '')
                
                if provider != 'aucun' and model and api_key:
                    print(f"[CHAT-HYBRID] 🔍 Détection hybride {provider}")
                    detected_caps = hybrid_auto_detect_capabilities(provider, model, "chat", api_key)
                    if max_tokens == -1:
                        max_tokens = detected_caps['max_tokens']
                        print(f"[CHAT-HYBRID] OK max_tokens optimal: {max_tokens:,}")
                    if context_length == -1:
                        context_length = detected_caps['context_length']
                        print(f"[CHAT-HYBRID] OK context_length optimal: {context_length:,}")
                else:
                    if max_tokens == -1:
                        max_tokens = 512
                    if context_length == -1:
                        context_length = 4096
            except Exception as e:
                if max_tokens == -1:
                    max_tokens = 512
                if context_length == -1:
                    context_length = 4096
                print(f"[CHAT-HYBRID] ERROR Erreur détection hybride: {e}")
    
    g._chat_controller.max_tokens = int(max_tokens)
    g._chat_controller.context_length = int(context_length)
    g._chat_controller.temperature = float(chat.get('temperature', 0.7))
    
    # Configuration selon backend
    if backend == 'API':
        provider = chat.get('provider', 'Aucun')
        api_key = chat.get('api_key', '')
        model = chat.get('api_model', '') or chat.get('model', '')
        print(f"[CTRL-CHAT] configure => provider={provider!r} model={model!r}")
        g._chat_controller.api_manager.configure(provider, api_key, model)
        g._chat_controller.api_manager.openrouter_thinking = bool(chat.get('openrouter_thinking', False))
    elif backend == 'Ollama':
        url = chat.get('ollama_url') or 'http://localhost:11434'
        cast(OllamaManager, g._ollama_mgr).api_url = str(url).rstrip('/')
        cast(OllamaManager, g._ollama_mgr).check_service()
        g._chat_controller.ollama_model = chat.get('ollama_model', '')
    elif backend == 'GGUF':
        model = chat.get('gguf_model', '')
        gguf_cfg = sm.settings.get('other_backends', {}).get('gguf', {})
        n_gpu_layers = int(gguf_cfg.get('gpu_layers', -1))
        gguf_ctx = int(gguf_cfg.get('context_size', 4096))
        _gguf_mgr = cast(GGUFManager, g._gguf_mgr)
        _model_changed = _gguf_mgr.model_name != model
        _ctx_changed = _gguf_mgr._requested_ctx != gguf_ctx
        _gpu_changed = getattr(_gguf_mgr, '_requested_gpu', None) != n_gpu_layers
        _is_loading = getattr(_gguf_mgr, '_is_loading', False)
        if model and not _is_loading and (not _gguf_mgr.is_available or _model_changed or _ctx_changed):
            if _model_changed or _ctx_changed:
                print(f"[GGUF-CTRL] Rechargement : modèle={'changé' if _model_changed else 'id.'}, ctx={'changé' if _ctx_changed else 'id.'}")
            _gguf_mgr._is_loading = True
            try:
                _gguf_mgr.load_model(model, gguf_ctx, n_gpu_layers)
                _gguf_mgr._requested_gpu = n_gpu_layers
            finally:
                _gguf_mgr._is_loading = False
        elif _is_loading:
            print(f"[GGUF-CTRL] Chargement deja en cours, skip")
        # Override context_length et max_tokens avec les valeurs GGUF réelles
        # (évite d'utiliser les valeurs détectées pour Google/API qui peuvent dépasser n_ctx)
        g._chat_controller.context_length = gguf_ctx
        _max_raw = int(chat.get('max_tokens', 2048))
        if _max_raw <= 0:
            _max_raw = 2048
        g._chat_controller.max_tokens = min(_max_raw, gguf_ctx - 512)
        print(f"[GGUF-CTRL] context_length={gguf_ctx}, max_tokens={g._chat_controller.max_tokens}")
    elif backend == 'KoboldCpp':
        url = chat.get('kobold_url') or 'http://localhost:5001'
        cast(KoboldManager, g._kobold_mgr).api_url = str(url).rstrip('/')
        cast(KoboldManager, g._kobold_mgr).check_service()
    
    return g._chat_controller


# ============================================================================
# MEMORY OPTIMIZER
# ============================================================================
def ensure_memory_optimizer():
    """Initialise Archiviste Memory Optimizer (Solution A)."""
    if g._memory_optimizer is not None:
        print("[MEMORY-OPTIMIZER-DEBUG] ♻️ Optimizer déjà initialisé (réutilisé)")
        return g._memory_optimizer
    
    try:
        from archiviste_memory_optimizer import create_memory_optimizer
        
        archiviste = ensure_archiviste_controller()
        memory_mgr = ensure_memory_manager()
        embedding = ensure_embedding_controller()
        
        if not archiviste or not memory_mgr:
            print("[MEMORY-OPTIMIZER] ⚠️ Dépendances manquantes")
            return None
        
        g._memory_optimizer = create_memory_optimizer(
            archiviste_controller=archiviste,
            memory_manager=memory_mgr,
            embedding_controller=embedding
        )
        
        print("[MEMORY-OPTIMIZER] ✅ Archiviste Memory Optimizer initialisé")
        return g._memory_optimizer
        
    except ImportError as e:
        print(f"[MEMORY-OPTIMIZER] ⚠️ Module non disponible: {e}")
        return None
    except Exception as e:
        print(f"[MEMORY-OPTIMIZER] ❌ Erreur initialisation: {e}")
        return None


# ============================================================================
# TEMPORAL GUARDIAN
# ============================================================================
def ensure_temporal_guardian():
    """Initialise l'extension Temporal Guardian."""
    if g._temporal_guardian is not None:
        return g._temporal_guardian
    
    try:
        from extensions.temporal_guardian import create_temporal_guardian
        
        sm = ensure_settings_manager()
        temporal_config = sm.settings.get('temporal_guardian', {})
        debug_mode = sm.settings.get('debug', {}).get('show_temporal_debug', False)
        
        g._temporal_guardian = create_temporal_guardian(temporal_config, debug=debug_mode)
        
        if debug_mode:
            print("[OGMA] 🕒 Temporal Guardian initialisé")
        
    except Exception as e:
        print(f"[OGMA] WARN Erreur initialisation Temporal Guardian: {e}")
        from extensions.temporal_guardian import create_temporal_guardian
        g._temporal_guardian = create_temporal_guardian(debug=False)
    
    return g._temporal_guardian


# ============================================================================
# CONTEXTUAL RECALL
# ============================================================================
def ensure_contextual_recall():
    """Initialise l'extension Contextual Recall."""
    if g._contextual_recall_ext is not None:
        return g._contextual_recall_ext
    
    try:
        from extensions.contextual_recall import initialize_recall
        
        g._contextual_recall_ext = initialize_recall(
            conversations_path="data/conversations",
            debug=False
        )
        
        if g._contextual_recall_ext:
            print("[CONTEXTUAL-RECALL] ✅ Extension initialisée")
        
    except Exception as e:
        print(f"[CONTEXTUAL-RECALL] ⚠️ Erreur initialisation: {e}")
        g._contextual_recall_ext = None
    
    return g._contextual_recall_ext


# ============================================================================
# FILE WRITER
# ============================================================================
def ensure_file_writer():
    """Initialise l'extension File Writer."""
    if g._file_writer_ext is not None:
        return g._file_writer_ext
    
    try:
        from extensions.file_writer import initialize_file_writer
        
        g._file_writer_ext = initialize_file_writer(
            uploads_dir="data/uploads",
            debug=True
        )
        
        if g._file_writer_ext:
            print("[FILE-WRITER] ✅ Extension initialisée")
        
    except Exception as e:
        print(f"[FILE-WRITER] ⚠️ Erreur initialisation: {e}")
        g._file_writer_ext = None
    
    return g._file_writer_ext


# ============================================================================
# CAPABILITY ADVISOR
# ============================================================================
def ensure_capability_advisor():
    """Initialise l'extension Capability Advisor."""
    if g._capability_advisor is not None:
        return g._capability_advisor
    
    try:
        from extensions.capability_advisor import initialize_capability_advisor
        
        chat_ctrl = ensure_chat_controller()
        archi_ctrl = ensure_archiviste_controller()
        memory_mgr = ensure_memory_manager()
        
        if archi_ctrl and memory_mgr:
            g._capability_advisor = initialize_capability_advisor(
                chat_controller=chat_ctrl,
                archiviste_controller=archi_ctrl,
                memory_manager=memory_mgr
            )
            print("[CAPABILITY-ADVISOR] ✅ Instance créée avec succès")
        else:
            print("[CAPABILITY-ADVISOR] ⚠️ Controllers manquants")
    except ImportError as e:
        print(f"[CAPABILITY-ADVISOR] ⚠️ Module non disponible: {e}")
        g._capability_advisor = None
    except Exception as e:
        print(f"[CAPABILITY-ADVISOR] ❌ Erreur initialisation: {e}")
        g._capability_advisor = None
    
    return g._capability_advisor


# ============================================================================
# COGNITIVE MIRROR
# ============================================================================
def ensure_cognitive_mirror():
    """Initialise l'extension Cognitive Mirror."""
    if g._cognitive_mirror is not None:
        return g._cognitive_mirror
    
    try:
        from extensions.cognitive_mirror import (
            initialize_cognitive_mirror, 
            get_cognitive_mirror
        )
        
        chat_controller = ensure_chat_controller()
        archiviste_controller = ensure_archiviste_controller()
        memory_manager = ensure_memory_manager()
        
        if not all([chat_controller, archiviste_controller, memory_manager]):
            print("[COGNITIVE-MIRROR] ❌ Dépendances manquantes")
            return None
        
        settings_manager = ensure_settings_manager()
        success = initialize_cognitive_mirror(
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            ui_container=None,
            settings_manager=settings_manager
        )
        
        if success:
            g._cognitive_mirror = get_cognitive_mirror()
            print("[OGMA] 🧠 Cognitive Mirror initialisé")
        else:
            g._cognitive_mirror = None
        
    except ImportError:
        print("[COGNITIVE-MIRROR] ⚠️ Extension non disponible")
        g._cognitive_mirror = None
    except Exception as e:
        print(f"[COGNITIVE-MIRROR] ⚠️ Erreur initialisation: {e}")
        g._cognitive_mirror = None
    
    return g._cognitive_mirror


# ============================================================================
# ORGANIC PLANNER
# ============================================================================
def ensure_organic_planner():
    """Initialise l'extension Organic Planner."""
    if g._organic_planner is not None:
        return g._organic_planner
    
    try:
        from extensions.organic_planner import initialize_planner
        
        g._organic_planner = initialize_planner(db_path=str(DATA_DIR / "agenda.db"))
        
        if g._organic_planner:
            print("[OGMA] 📅 Organic Planner initialisé")
        
    except ImportError:
        print("[ORGANIC-PLANNER] ⚠️ Extension non disponible")
        g._organic_planner = None
    except Exception as e:
        print(f"[ORGANIC-PLANNER] ❌ Erreur initialisation: {e}")
        g._organic_planner = None
        
    return g._organic_planner


# ============================================================================
# CLOSE / CLEANUP
# ============================================================================
def close_memory_manager():
    """Ferme proprement le MemoryManager."""
    if g._memory_manager is not None:
        try:
            g._memory_manager.cleanup()
            print("[OGMA] MemoryManager fermé proprement")
        except Exception as e:
            print(f"[OGMA] Erreur fermeture MemoryManager: {e}")
        finally:
            g._memory_manager = None


# ============================================================================
# WEB NAVIGATOR
# ============================================================================
def get_web_navigator_instance():
    """Obtient l'instance unique de Web Navigator (pattern singleton)."""
    if g._web_navigator_ext is None:
        try:
            from extensions.web_navigator import WebNavigatorExtension
            g._web_navigator_ext = WebNavigatorExtension()
            print(f"[WEB-NAV-SINGLETON] ✅ Instance Web Navigator créée")
        except Exception as e:
            print(f"[WEB-NAV-SINGLETON] ❌ Erreur création instance: {e}")
            g._web_navigator_ext = None
    
    return g._web_navigator_ext


print("[OGMA-CONTROLLERS] ✅ Fonctions d'initialisation chargées")
