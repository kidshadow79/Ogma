"""
OGMA CORE GLOBALS - Variables globales centralisées
=====================================================

Centralise toutes les variables globales d'ogma_ng.py avec des accesseurs
pour éviter les problèmes d'import circulaire.

Pattern: Getter/Setter pour chaque variable globale importante.
"""

from typing import Optional, Dict, List, Any, Callable
import queue

# ============================================================================
# CONTRÔLEURS ET MANAGERS (initialisés par controllers.py)
# ============================================================================
_settings_mgr = None
_api_mgr = None
_ollama_mgr = None
_gguf_mgr = None
_kobold_mgr = None
_chat_controller = None
_archiviste_controller = None
_embedding_controller = None
_memory_manager = None
_memory_optimizer = None
_audio_manager = None

# ============================================================================
# EXTENSIONS
# ============================================================================
_temporal_guardian = None
_cognitive_mirror = None
_contextual_recall_ext = None
_file_writer_ext = None
_capability_advisor = None
_web_navigator_ext = None
_organic_planner = None
_journal_preformed_response = None
_preanalysis_optimizer = None  # Module preanalysis optimizer

# ============================================================================
# HISTORIQUE CONVERSATION
# ============================================================================
_chat_history: List[Dict] = []  # Historique pour l'IA (optimisé avec résumés)
_chat_history_ui: List[Dict] = []  # Historique pour l'interface (COMPLET)
_current_conversation_id: Optional[str] = None
_conv_index: Dict[str, Dict] = {}

# ============================================================================
# ÉLÉMENTS UI
# ============================================================================
_conv_area = None  # conteneur de conversation
_chat_inner = None  # conteneur interne pour les messages
_input_field = None  # champ de saisie
_file_tab_container = None
_header_container = None
_ia_status_indicators = {}
_introspection_box_content = []
_introspection_md_widget = None

# ============================================================================
# ÉTAT FICHIERS
# ============================================================================
_active_file_data: Optional[Dict] = None
_loaded_conversation: Optional[List[Dict]] = None
_loaded_conversation_filename: Optional[str] = None
_conversation_context_injected: bool = False
_orchestration_injected: bool = False
_thinking_css_injected: bool = False

# ============================================================================
# ÉTAT INTERNE
# ============================================================================
_status_queue: Optional[queue.Queue] = None
_memory_update_hooks: List[Callable[[], None]] = []
_sidebar_render_cb: Optional[Callable[[Optional[str]], None]] = None
_title_updating: bool = False
_auto_send_audio: bool = False
_pending_behavioral_injections: List = []


# ============================================================================
# ACCESSEURS CHAT HISTORY
# ============================================================================
def get_chat_history() -> List[Dict]:
    """Retourne l'historique de conversation pour l'IA."""
    return _chat_history

def get_chat_history_ui() -> List[Dict]:
    """Retourne l'historique complet pour l'interface."""
    return _chat_history_ui

def clear_chat_history():
    """Vide les deux historiques."""
    global _chat_history, _chat_history_ui
    _chat_history.clear()
    _chat_history_ui.clear()

def append_to_chat_history(message: Dict, ui_only: bool = False):
    """Ajoute un message aux historiques."""
    global _chat_history, _chat_history_ui
    _chat_history_ui.append(message)
    if not ui_only:
        _chat_history.append(message)


# ============================================================================
# ACCESSEURS CONVERSATION
# ============================================================================
def get_current_conversation_id() -> Optional[str]:
    return _current_conversation_id

def set_current_conversation_id(conv_id: Optional[str]):
    global _current_conversation_id
    _current_conversation_id = conv_id

def get_conv_index() -> Dict[str, Dict]:
    return _conv_index

def set_conv_index(index: Dict[str, Dict]):
    global _conv_index
    _conv_index = index


# ============================================================================
# ACCESSEURS ÉLÉMENTS UI
# ============================================================================
def get_conv_area():
    return _conv_area

def set_conv_area(area):
    global _conv_area
    _conv_area = area

def get_chat_inner():
    return _chat_inner

def set_chat_inner(inner):
    global _chat_inner
    _chat_inner = inner

def get_input_field():
    return _input_field

def set_input_field(field):
    global _input_field
    _input_field = field

def get_header_container():
    return _header_container

def set_header_container(container):
    global _header_container
    _header_container = container

def get_file_tab_container():
    return _file_tab_container

def set_file_tab_container(container):
    global _file_tab_container
    _file_tab_container = container


# ============================================================================
# ACCESSEURS FICHIERS
# ============================================================================
def get_active_file_data() -> Optional[Dict]:
    return _active_file_data

def set_active_file_data(data: Optional[Dict]):
    global _active_file_data
    _active_file_data = data

def get_loaded_conversation() -> Optional[List[Dict]]:
    return _loaded_conversation

def set_loaded_conversation(conv: Optional[List[Dict]]):
    global _loaded_conversation
    _loaded_conversation = conv

def get_loaded_conversation_filename() -> Optional[str]:
    return _loaded_conversation_filename

def set_loaded_conversation_filename(filename: Optional[str]):
    global _loaded_conversation_filename
    _loaded_conversation_filename = filename

def is_conversation_context_injected() -> bool:
    return _conversation_context_injected

def set_conversation_context_injected(value: bool):
    global _conversation_context_injected
    _conversation_context_injected = value

def is_orchestration_injected() -> bool:
    return _orchestration_injected

def set_orchestration_injected(value: bool):
    global _orchestration_injected
    _orchestration_injected = value


# ============================================================================
# ACCESSEURS STATUS ET HOOKS
# ============================================================================
def get_status_queue() -> Optional[queue.Queue]:
    global _status_queue
    if _status_queue is None:
        _status_queue = queue.Queue()
    return _status_queue

def register_memory_update_hook(callback: Callable[[], None]):
    """Enregistre un callback à appeler après ajout mémoire."""
    global _memory_update_hooks
    if callback not in _memory_update_hooks:
        _memory_update_hooks.append(callback)

def trigger_memory_update_hooks():
    """Déclenche tous les hooks de mise à jour mémoire."""
    for cb in list(_memory_update_hooks):
        try:
            cb()
        except Exception:
            pass

def get_sidebar_render_cb() -> Optional[Callable[[Optional[str]], None]]:
    return _sidebar_render_cb

def set_sidebar_render_cb(cb: Optional[Callable[[Optional[str]], None]]):
    global _sidebar_render_cb
    _sidebar_render_cb = cb

def is_title_updating() -> bool:
    return _title_updating

def set_title_updating(value: bool):
    global _title_updating
    _title_updating = value


# ============================================================================
# ACCESSEURS INTROSPECTION
# ============================================================================
def get_introspection_box_content() -> List:
    return _introspection_box_content

def clear_introspection_box_content():
    global _introspection_box_content
    _introspection_box_content.clear()

def append_introspection_content(content):
    global _introspection_box_content
    _introspection_box_content.append(content)

def get_introspection_md_widget():
    return _introspection_md_widget

def set_introspection_md_widget(widget):
    global _introspection_md_widget
    _introspection_md_widget = widget


# ============================================================================
# ACCESSEURS IA STATUS
# ============================================================================
def get_ia_status_indicators() -> Dict:
    return _ia_status_indicators

def set_ia_status_indicator(key: str, value):
    global _ia_status_indicators
    _ia_status_indicators[key] = value


# ============================================================================
# ACCESSEURS JOURNAL
# ============================================================================
def get_journal_preformed_response():
    return _journal_preformed_response

def set_journal_preformed_response(response):
    global _journal_preformed_response
    _journal_preformed_response = response


# ============================================================================
# ACCESSEURS AUTO SEND AUDIO
# ============================================================================
def get_auto_send_audio() -> bool:
    return _auto_send_audio

def set_auto_send_audio(value: bool):
    global _auto_send_audio
    _auto_send_audio = value


print("[OGMA-GLOBALS] ✅ Variables globales centralisées chargées")
