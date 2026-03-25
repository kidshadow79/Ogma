"""
Package: utils
Description: Utilitaires généraux pour OGMA (Phase 1 refactoring)
Date: 2025-11-02
"""

# Import des constantes critiques depuis utils.py (module racine)
# ASTUCE: Utiliser importlib pour éviter conflit de nom avec package utils/
import importlib.util
from pathlib import Path

# Charger utils.py racine en évitant conflit nom
_utils_root_path = Path(__file__).parent.parent / "utils.py"
spec = importlib.util.spec_from_file_location("utils_root", _utils_root_path)
utils_root = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_root)

# Exposer les constantes critiques
DATA_DIR = utils_root.DATA_DIR
EGO_COMPILED_FILE = utils_root.EGO_COMPILED_FILE

# Import helpers pour extensions et callbacks (logic_callbacks.py)
get_ego_summary_from_compiled = utils_root.get_ego_summary_from_compiled
save_conversation = utils_root.save_conversation
save_conversations_index = utils_root.save_conversations_index
load_conversations_index = utils_root.load_conversations_index
get_conversations = utils_root.get_conversations
load_conversation = utils_root.load_conversation
delete_conversation_file = utils_root.delete_conversation_file
rename_conversation_file = utils_root.rename_conversation_file
estimate_tokens = utils_root.estimate_tokens
search_conversations = utils_root.search_conversations
get_conversation_context = utils_root.get_conversation_context

# Imports des modules refactorisés
from .formatting_utils import (
    format_size,
    format_datetime,
    truncate_filename,
    get_file_icon
)
from .message_parsers import parse_thinking_format, parse_introspection_format
from .backend_utils import map_backend_for_controller

__all__ = [
    # Constantes (depuis utils.py racine)
    'DATA_DIR',
    'EGO_COMPILED_FILE',
    # Helpers pour extensions et logic_callbacks (depuis utils.py racine)
    'get_ego_summary_from_compiled',
    'save_conversation',
    'save_conversations_index',
    'load_conversations_index',
    'get_conversations',
    'load_conversation',
    'delete_conversation_file',
    'rename_conversation_file',
    'estimate_tokens',
    'search_conversations',
    'get_conversation_context',
    # Fonctions refactorisées
    'format_size',
    'format_datetime',
    'truncate_filename',
    'get_file_icon',
    'parse_thinking_format',
    'parse_introspection_format',
    'map_backend_for_controller'
]
