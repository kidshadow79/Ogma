"""
OGMA CORE - Module centralisé pour les variables globales et fonctions de base
================================================================================

Phase 1 du refactoring ogma_ng.py (8 décembre 2025)

Ce module contient:
- globals.py: Variables globales centralisées
- controllers.py: Fonctions _ensure_*() pour contrôleurs IA
- extensions_loader.py: Chargement lazy des extensions
- utils.py: Fonctions utilitaires générales

Usage:
    from modules.ogma_core import (
        get_chat_controller,
        get_memory_manager,
        get_settings_manager,
        # etc.
    )
"""

from .globals import (
    # Variables globales accessibles
    get_chat_history,
    get_chat_history_ui,
    get_current_conversation_id,
    set_current_conversation_id,
    get_conv_area,
    set_conv_area,
    get_chat_inner,
    set_chat_inner,
    get_input_field,
    set_input_field,
    get_active_file_data,
    set_active_file_data,
    clear_chat_history,
    append_to_chat_history,
    get_status_queue,
    register_memory_update_hook,
    trigger_memory_update_hooks,
    get_sidebar_render_cb,
    set_sidebar_render_cb,
)

from .controllers import (
    ensure_settings_manager,
    ensure_audio_manager,
    ensure_backends,
    ensure_memory_manager,
    ensure_archiviste_controller,
    ensure_embedding_controller,
    ensure_chat_controller,
    ensure_memory_optimizer,
    ensure_temporal_guardian,
    ensure_contextual_recall,
    ensure_file_writer,
    ensure_capability_advisor,
    ensure_cognitive_mirror,
    close_memory_manager,
    get_web_navigator_instance,
)

from .extensions_loader import (
    is_extension_available,
    get_available_extensions,
    load_extension,
    unload_extension,
    unload_all_extensions,
    get_extension_status,
    print_extension_status,
)

from .utils import (
    safe_ui_operation,
    notify_safe,
    get_current_time,
)

__version__ = "1.0.0"
__author__ = "OGMA Team"

print("[OGMA-CORE] ✅ Module centralisé chargé")
