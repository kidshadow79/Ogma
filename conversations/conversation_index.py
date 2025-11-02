"""
Module: conversation_index.py
Description: Gestion index conversations (data/conversations/index.json)
Extrait de: ogma_ng.py (lignes 2201-2230)
Date: 2025-11-02
"""

import json
from pathlib import Path
from typing import Dict, Tuple

# Import depuis utils (doit exister dans ogma_ng.py ou utils.py)
try:
    from utils import DATA_DIR
except ImportError:
    # Fallback si DATA_DIR n'est pas disponible
    DATA_DIR = Path(__file__).parent.parent / 'data'

CONVERSATIONS_DIR = DATA_DIR / 'conversations'
INDEX_FILE = CONVERSATIONS_DIR / 'index.json'


def load_conversation_index() -> Dict[str, Dict]:
    """
    Charge l'index des conversations depuis index.json.
    
    Returns:
        dict: Index conversations {conv_id: {title, created_at, last_modified, ...}}
        
    Examples:
        >>> index = load_conversation_index()
        >>> isinstance(index, dict)
        True
    """
    if not INDEX_FILE.exists():
        return {}
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONVERSATION-INDEX] WARN Erreur chargement index: {e}")
        return {}


def save_conversation_index(index_data: Dict[str, Dict]) -> Tuple[bool, str]:
    """
    Sauvegarde l'index des conversations.
    
    Args:
        index_data: Dictionnaire index complet
        
    Returns:
        tuple[bool, str]: (succès, message_erreur)
        
    Examples:
        >>> success, error = save_conversation_index({})
        >>> success
        True
    """
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        return (True, "")
    except Exception as e:
        error_msg = f"Erreur sauvegarde index: {e}"
        print(f"[CONVERSATION-INDEX] ERROR {error_msg}")
        return (False, error_msg)
