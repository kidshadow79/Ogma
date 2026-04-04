"""
cache_parser.py
---------------
Détecte et parse les phrases magiques du cache cognitif dans les réponses IA.

Syntaxe supportée (insensible à la casse, espaces tolérés) :
    CACHE_ADD:[type]:[contenu]
    CACHE_DELETE:[id]
    CACHE_UPDATE:[id]:[nouveau contenu]
    CACHE_CLEAR

Retourne une liste d'opérations à appliquer par le cache_manager.
"""

import re
from typing import List, Dict, Any

# Patterns regex pour chaque commande
_RE_ADD = re.compile(
    r'CACHE_ADD\s*:\s*([a-zA-Z_]+)\s*:\s*(.+?)(?=\nCACHE_|$)',
    re.IGNORECASE | re.DOTALL
)
_RE_DELETE = re.compile(
    r'CACHE_DELETE\s*:\s*(cache-[a-f0-9]{8})',
    re.IGNORECASE
)
_RE_UPDATE = re.compile(
    r'CACHE_UPDATE\s*:\s*(cache-[a-f0-9]{8})\s*:\s*(.+?)(?=\nCACHE_|$)',
    re.IGNORECASE | re.DOTALL
)
_RE_CLEAR = re.compile(
    r'CACHE_CLEAR',
    re.IGNORECASE
)

# Pattern unique pour détecter si le texte contient des commandes cache
_RE_HAS_CACHE = re.compile(r'CACHE_(ADD|DELETE|UPDATE|CLEAR)', re.IGNORECASE)


def has_cache_commands(text: str) -> bool:
    """
    Vérifie rapidement si le texte contient des commandes cache.
    Utilisé pour court-circuiter le parsing si inutile.

    Args:
        text: Texte de la réponse IA

    Returns:
        True si au moins une commande cache est présente
    """
    return bool(_RE_HAS_CACHE.search(text))


def parse_cache_commands(text: str) -> List[Dict[str, Any]]:
    """
    Parse toutes les commandes cache dans le texte de la réponse IA.

    Args:
        text: Texte complet de la réponse IA

    Returns:
        Liste d'opérations sous forme de dicts :
        [
            {'op': 'add', 'type': 'directive', 'content': '...'},
            {'op': 'delete', 'id': 'cache-abcd1234'},
            {'op': 'update', 'id': 'cache-abcd1234', 'content': '...'},
            {'op': 'clear'},
        ]
    """
    if not text or not has_cache_commands(text):
        return []

    operations = []

    # CACHE_CLEAR — priorité haute (si présent, on le traite en premier)
    if _RE_CLEAR.search(text):
        operations.append({'op': 'clear'})
        print("[CACHE-PARSER] Commande CACHE_CLEAR détectée")

    # CACHE_ADD
    for match in _RE_ADD.finditer(text):
        entry_type = match.group(1).strip().lower()
        content = match.group(2).strip()
        # Nettoyer les éventuels sauts de ligne parasites en fin de contenu
        content = content.split('\n')[0].strip()
        if content:
            operations.append({
                'op': 'add',
                'type': entry_type,
                'content': content
            })
            print(f"[CACHE-PARSER] CACHE_ADD [{entry_type}]: {content[:60]}")

    # CACHE_DELETE
    for match in _RE_DELETE.finditer(text):
        entry_id = match.group(1).strip()
        operations.append({
            'op': 'delete',
            'id': entry_id
        })
        print(f"[CACHE-PARSER] CACHE_DELETE: {entry_id}")

    # CACHE_UPDATE
    for match in _RE_UPDATE.finditer(text):
        entry_id = match.group(1).strip()
        content = match.group(2).strip()
        content = content.split('\n')[0].strip()
        if content:
            operations.append({
                'op': 'update',
                'id': entry_id,
                'content': content
            })
            print(f"[CACHE-PARSER] CACHE_UPDATE [{entry_id}]: {content[:60]}")

    return operations


def strip_cache_commands(text: str) -> str:
    """
    Supprime toutes les commandes cache du texte pour l'affichage utilisateur.
    Les commandes sont invisibles pour l'utilisateur.

    Args:
        text: Texte complet de la réponse IA

    Returns:
        Texte nettoyé, sans les commandes cache
    """
    if not text or not has_cache_commands(text):
        return text

    # Supprimer chaque type de commande
    cleaned = _RE_ADD.sub('', text)
    cleaned = _RE_DELETE.sub('', cleaned)
    cleaned = _RE_UPDATE.sub('', cleaned)
    cleaned = _RE_CLEAR.sub('', cleaned)

    # Nettoyer les lignes vides consécutives créées par les suppressions
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()
