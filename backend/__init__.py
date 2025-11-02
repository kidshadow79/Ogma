"""
Package: backend
Description: Communication avec backends IA (API, Ollama, GGUF, KoboldCpp)
Date: 2025-11-02
"""

from .backend_communication import (
    list_models,
    test_connection
)

from .ia_status import (
    check_global_ia_status,
    update_ia_status_indicators
)

__all__ = [
    'list_models',
    'test_connection',
    'check_global_ia_status',
    'update_ia_status_indicators'
]
