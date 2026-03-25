"""
OGMA CORE COMPATIBILITY BRIDGE
===============================

Ce module permet une transition progressive vers la structure modulaire.
Il synchronise les variables globales entre ogma_ng.py et modules.ogma_core.

Usage dans ogma_ng.py:
    from modules.ogma_core.compat import sync_globals_to_core, sync_globals_from_core
    
    # Après modification des globals dans ogma_ng.py:
    sync_globals_to_core()
    
    # Pour récupérer les modifications faites via les modules:
    sync_globals_from_core()
"""

from typing import Any, Dict

# Import du module globals
from . import globals as g


def sync_globals_to_core(ogma_globals: Dict[str, Any]) -> None:
    """
    Synchronise les variables globales d'ogma_ng.py vers ogma_core.globals.
    
    Args:
        ogma_globals: Le dictionnaire globals() d'ogma_ng.py
    """
    # Contrôleurs
    if '_settings_mgr' in ogma_globals:
        g._settings_mgr = ogma_globals['_settings_mgr']
    if '_api_mgr' in ogma_globals:
        g._api_mgr = ogma_globals['_api_mgr']
    if '_ollama_mgr' in ogma_globals:
        g._ollama_mgr = ogma_globals['_ollama_mgr']
    if '_gguf_mgr' in ogma_globals:
        g._gguf_mgr = ogma_globals['_gguf_mgr']
    if '_kobold_mgr' in ogma_globals:
        g._kobold_mgr = ogma_globals['_kobold_mgr']
    if '_chat_controller' in ogma_globals:
        g._chat_controller = ogma_globals['_chat_controller']
    if '_archiviste_controller' in ogma_globals:
        g._archiviste_controller = ogma_globals['_archiviste_controller']
    if '_embedding_controller' in ogma_globals:
        g._embedding_controller = ogma_globals['_embedding_controller']
    if '_memory_manager' in ogma_globals:
        g._memory_manager = ogma_globals['_memory_manager']
    if '_memory_optimizer' in ogma_globals:
        g._memory_optimizer = ogma_globals['_memory_optimizer']
    if '_audio_manager' in ogma_globals:
        g._audio_manager = ogma_globals['_audio_manager']
    
    # Extensions
    if '_temporal_guardian' in ogma_globals:
        g._temporal_guardian = ogma_globals['_temporal_guardian']
    if '_cognitive_mirror' in ogma_globals:
        g._cognitive_mirror = ogma_globals['_cognitive_mirror']
    if '_contextual_recall_ext' in ogma_globals:
        g._contextual_recall_ext = ogma_globals['_contextual_recall_ext']
    if '_file_writer_ext' in ogma_globals:
        g._file_writer_ext = ogma_globals['_file_writer_ext']
    if '_capability_advisor' in ogma_globals:
        g._capability_advisor = ogma_globals['_capability_advisor']
    if '_web_navigator_ext' in ogma_globals:
        g._web_navigator_ext = ogma_globals['_web_navigator_ext']
    
    # Historique conversation
    if '_chat_history' in ogma_globals:
        g._chat_history = ogma_globals['_chat_history']
    if '_chat_history_ui' in ogma_globals:
        g._chat_history_ui = ogma_globals['_chat_history_ui']
    if '_current_conversation_id' in ogma_globals:
        g._current_conversation_id = ogma_globals['_current_conversation_id']
    if '_conv_index' in ogma_globals:
        g._conv_index = ogma_globals['_conv_index']
    
    # Éléments UI
    if '_conv_area' in ogma_globals:
        g._conv_area = ogma_globals['_conv_area']
    if '_chat_inner' in ogma_globals:
        g._chat_inner = ogma_globals['_chat_inner']
    if '_input_field' in ogma_globals:
        g._input_field = ogma_globals['_input_field']
    if '_header_container' in ogma_globals:
        g._header_container = ogma_globals['_header_container']
    if '_file_tab_container' in ogma_globals:
        g._file_tab_container = ogma_globals['_file_tab_container']
    
    # État fichiers
    if '_active_file_data' in ogma_globals:
        g._active_file_data = ogma_globals['_active_file_data']
    if '_loaded_conversation' in ogma_globals:
        g._loaded_conversation = ogma_globals['_loaded_conversation']
    if '_status_queue' in ogma_globals:
        g._status_queue = ogma_globals['_status_queue']


def sync_globals_from_core() -> Dict[str, Any]:
    """
    Retourne un dictionnaire des variables globales depuis ogma_core.globals.
    Pour mise à jour des globals d'ogma_ng.py.
    
    Returns:
        Dict avec toutes les variables globales du module core
    """
    return {
        # Contrôleurs
        '_settings_mgr': g._settings_mgr,
        '_api_mgr': g._api_mgr,
        '_ollama_mgr': g._ollama_mgr,
        '_gguf_mgr': g._gguf_mgr,
        '_kobold_mgr': g._kobold_mgr,
        '_chat_controller': g._chat_controller,
        '_archiviste_controller': g._archiviste_controller,
        '_embedding_controller': g._embedding_controller,
        '_memory_manager': g._memory_manager,
        '_memory_optimizer': g._memory_optimizer,
        '_audio_manager': g._audio_manager,
        
        # Extensions
        '_temporal_guardian': g._temporal_guardian,
        '_cognitive_mirror': g._cognitive_mirror,
        '_contextual_recall_ext': g._contextual_recall_ext,
        '_file_writer_ext': g._file_writer_ext,
        '_capability_advisor': g._capability_advisor,
        '_web_navigator_ext': g._web_navigator_ext,
        
        # Historique
        '_chat_history': g._chat_history,
        '_chat_history_ui': g._chat_history_ui,
        '_current_conversation_id': g._current_conversation_id,
        '_conv_index': g._conv_index,
        
        # UI
        '_conv_area': g._conv_area,
        '_chat_inner': g._chat_inner,
        '_input_field': g._input_field,
        '_header_container': g._header_container,
        '_file_tab_container': g._file_tab_container,
        
        # État
        '_active_file_data': g._active_file_data,
        '_loaded_conversation': g._loaded_conversation,
        '_status_queue': g._status_queue,
    }


def get_controller(name: str) -> Any:
    """
    Récupère un contrôleur par son nom.
    
    Args:
        name: 'chat', 'archiviste', 'embedding', 'settings', 'audio', 'memory'
        
    Returns:
        Le contrôleur demandé ou None
    """
    controllers = {
        'chat': g._chat_controller,
        'archiviste': g._archiviste_controller,
        'embedding': g._embedding_controller,
        'settings': g._settings_mgr,
        'audio': g._audio_manager,
        'memory': g._memory_manager,
        'memory_optimizer': g._memory_optimizer,
    }
    return controllers.get(name)


def get_extension(name: str) -> Any:
    """
    Récupère une extension par son nom.
    
    Args:
        name: 'cognitive_mirror', 'file_writer', 'web_navigator', etc.
        
    Returns:
        L'instance de l'extension ou None
    """
    extensions = {
        'cognitive_mirror': g._cognitive_mirror,
        'file_writer': g._file_writer_ext,
        'web_navigator': g._web_navigator_ext,
        'temporal_guardian': g._temporal_guardian,
        'contextual_recall': g._contextual_recall_ext,
        'capability_advisor': g._capability_advisor,
    }
    return extensions.get(name)


print("[OGMA-COMPAT] ✅ Bridge de compatibilité chargé")
