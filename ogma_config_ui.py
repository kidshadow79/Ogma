"""
OGMA Configuration UI
====================
Interfaces de configuration et paramétrage OGMA.

CONTIENT :
- Interface de configuration TTS
- Paramètres audio et modèles
- Configuration des backends
- Interfaces de réglages système
"""

from nicegui import ui
import json
import os
from typing import Dict, List, Optional, Any
def _get_settings_manager():
    """Helper pour accéder au settings manager via import dynamique"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, '_ensure_settings_manager'):
            return ogma_ng._ensure_settings_manager()
        return None
    except Exception:
        return None

def _notify_safe(message: str, type: str = 'info'):
    """Helper pour les notifications via ui.notify"""
    ui.notify(message, type=type)

