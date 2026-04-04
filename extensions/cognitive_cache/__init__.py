"""
extensions/cognitive_cache/__init__.py
---------------------------------------
Extension Cache Cognitif OGMA — API publique (pattern singleton standard)

L'IA Principale écrit dans ce cache via des phrases magiques :
    CACHE_ADD:[type]:[contenu]
    CACHE_DELETE:[id]
    CACHE_UPDATE:[id]:[contenu]
    CACHE_CLEAR

Le cache est persisté par conversation (data/cognitive_cache/{conv_id}.json).
Max 10 conversations conservées (élagage à la fermeture).

Usage depuis ogma_ng.py :
    from extensions.cognitive_cache import (
        initialize_cognitive_cache,
        is_available,
        set_current_conv,
        apply_cache_operations,
        get_cache_summary,
        get_cache_snapshot,
        cleanup_cognitive_cache,
    )
"""

from typing import Optional, Dict, List, Any

# Imports internes
from .cache_manager import (
    load_cache, save_cache,
    add_entry, delete_entry, update_entry, clear_cache,
    get_active_entries, get_summary_for_injection,
    get_snapshot, get_snapshot_summary
)
from .cache_parser import (
    has_cache_commands, parse_cache_commands, strip_cache_commands
)
from .cache_cleanup import cleanup_old_caches, cleanup_old_caches_async, get_cache_stats

# ============================================================================
# ÉTAT INTERNE DU SINGLETON
# ============================================================================

_initialized: bool = False
_current_conv_id: Optional[str] = None


# ============================================================================
# API PUBLIQUE
# ============================================================================

def initialize_cognitive_cache(conv_id: Optional[str] = None) -> bool:
    """
    Initialise l'extension cache cognitif.
    Appelé dans _async_awakening() après la vague mémoire.

    Args:
        conv_id: ID de la conversation courante (optionnel au démarrage)

    Returns:
        True si initialisation réussie
    """
    global _initialized, _current_conv_id

    try:
        if conv_id:
            _current_conv_id = conv_id
        _initialized = True
        stats = get_cache_stats()
        print(
            f"[COGNITIVE-CACHE] Initialisé — "
            f"{stats['count']} fichier(s) en cache"
            + (f", conv courante: {_current_conv_id}" if _current_conv_id else "")
        )
        return True
    except Exception as e:
        print(f"[COGNITIVE-CACHE] Erreur initialisation: {e}")
        return False


def is_available() -> bool:
    """Vérifie si le cache cognitif est initialisé."""
    return _initialized


def set_current_conv(conv_id: str):
    """
    Définit la conversation courante.
    Appelé à chaque nouvelle conversation (_new_conversation).

    Args:
        conv_id: Nouvel identifiant de conversation
    """
    global _current_conv_id
    _current_conv_id = conv_id
    print(f"[COGNITIVE-CACHE] Conversation courante: {conv_id}")


def get_current_conv_id() -> Optional[str]:
    """Retourne l'ID de la conversation courante."""
    return _current_conv_id


def apply_cache_operations(text: str, conv_id: Optional[str] = None) -> List[Dict]:
    """
    Détecte et applique les commandes cache dans une réponse IA.
    Appelé en post-streaming dans _send_chat_message.

    Args:
        text: Texte complet de la réponse IA
        conv_id: ID de conversation (utilise _current_conv_id si None)

    Returns:
        Liste des opérations appliquées (pour logging flux cognitif)
    """
    if not _initialized:
        return []

    cid = conv_id or _current_conv_id
    if not cid:
        print("[COGNITIVE-CACHE] apply_cache_operations: aucun conv_id disponible")
        return []

    if not has_cache_commands(text):
        return []

    operations = parse_cache_commands(text)
    applied = []

    for op in operations:
        try:
            if op['op'] == 'clear':
                clear_cache(cid)
                applied.append(op)

            elif op['op'] == 'add':
                entry_id = add_entry(cid, op['type'], op['content'])
                if entry_id:
                    op['id'] = entry_id
                    applied.append(op)

            elif op['op'] == 'delete':
                if delete_entry(cid, op['id']):
                    applied.append(op)

            elif op['op'] == 'update':
                if update_entry(cid, op['id'], op['content']):
                    applied.append(op)

        except Exception as e:
            print(f"[COGNITIVE-CACHE] Erreur application op {op.get('op')}: {e}")

    return applied


def get_cache_summary(conv_id: Optional[str] = None) -> str:
    """
    Retourne le résumé du cache pour injection dans le system prompt.

    Args:
        conv_id: ID de conversation (utilise _current_conv_id si None)

    Returns:
        Texte formaté pour injection, ou chaîne vide si cache vide
    """
    if not _initialized:
        return ""

    cid = conv_id or _current_conv_id
    if not cid:
        return ""

    return get_summary_for_injection(cid)


def get_cache_snapshot(conv_id: Optional[str] = None) -> Dict:
    """
    Retourne un snapshot figé du cache pour le Dream Engine.

    Args:
        conv_id: ID de conversation (utilise _current_conv_id si None)

    Returns:
        Copie profonde du cache courant
    """
    cid = conv_id or _current_conv_id
    if not cid:
        return {"conv_id": None, "entries": [], "snapshot_at": None}

    return get_snapshot(cid)


def get_snapshot_text(snapshot: Dict) -> str:
    """
    Génère le texte d'un snapshot pour les prompts du Dream Engine.

    Args:
        snapshot: Dict retourné par get_cache_snapshot()

    Returns:
        Texte formaté pour injection dans le prompt de rêve
    """
    return get_snapshot_summary(snapshot)


def strip_commands_from_response(text: str) -> str:
    """
    Supprime les commandes cache du texte avant affichage utilisateur.

    Args:
        text: Réponse IA brute

    Returns:
        Texte nettoyé
    """
    return strip_cache_commands(text)


async def cleanup_cognitive_cache(max_conversations: int = 10) -> dict:
    """
    Élagage du cache : conserve les N conversations les plus récentes.
    Appelé dans delayed_shutdown() après compile_ego_incremental().

    Args:
        max_conversations: Nombre max de fichiers à conserver

    Returns:
        Dict avec stats de l'élagage
    """
    return await cleanup_old_caches_async(max_conversations)


def get_continuation_context(max_convs: int = 3) -> str:
    """
    Génère un résumé de continuité inter-sessions pour injection au démarrage.
    Récupère les entrées actives des N conversations les plus récentes.

    Args:
        max_convs: Nombre de conversations récentes à inclure

    Returns:
        Texte de continuité ou chaîne vide
    """
    from .cache_cleanup import _get_cache_files_sorted
    files = _get_cache_files_sorted()

    if not files:
        return ""

    # Prendre les N plus récentes
    recent = files[-max_convs:]
    all_entries = []

    for path, _ in reversed(recent):
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = [e for e in data.get("entries", []) if e.get("active", True)]
            # Ne garder que les directives et context_anchors inter-sessions
            persistent = [e for e in entries if e.get("type") in ("directive", "context_anchor")]
            all_entries.extend(persistent)
        except Exception:
            pass

    if not all_entries:
        return ""

    lines = ["[CONTINUITÉ COGNITIVE — Sessions précédentes]"]
    for e in all_entries[:5]:  # Max 5 entrées de continuité
        lines.append(f"- [{e.get('type', '?')}] {e.get('content', '')}")

    return "\n".join(lines)


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "initialize_cognitive_cache",
    "is_available",
    "set_current_conv",
    "get_current_conv_id",
    "apply_cache_operations",
    "get_cache_summary",
    "get_cache_snapshot",
    "get_snapshot_text",
    "strip_commands_from_response",
    "cleanup_cognitive_cache",
    "get_continuation_context",
]
