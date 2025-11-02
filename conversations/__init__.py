"""
Package: conversations
Description: Gestion des conversations OGMA
Date: 2025-11-02
"""

from .conversation_index import (
    load_conversation_index,
    save_conversation_index
)

from .conversation_utils import (
    make_conv_id,
    make_title_from_text
)

__all__ = [
    'load_conversation_index',
    'save_conversation_index',
    'make_conv_id',
    'make_title_from_text'
]
