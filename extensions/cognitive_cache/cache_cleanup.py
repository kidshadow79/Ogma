"""
cache_cleanup.py
----------------
Élagage du cache cognitif OGMA.
Conserve uniquement les N conversations les plus récentes.
Appelé dans delayed_shutdown(), APRÈS compile_ego_incremental().
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cognitive_cache"


def _get_cache_files_sorted() -> List[Tuple[Path, datetime]]:
    """
    Retourne la liste des fichiers cache triés par date de modification (plus récent en dernier).

    Returns:
        Liste de tuples (path, updated_at)
    """
    if not _CACHE_DIR.exists():
        return []

    files_with_dates = []

    for path in _CACHE_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Utiliser updated_at du JSON si disponible, sinon mtime du fichier
            updated_str = data.get("updated_at") or data.get("created_at")
            if updated_str:
                updated_at = datetime.fromisoformat(updated_str)
            else:
                updated_at = datetime.fromtimestamp(path.stat().st_mtime)
            files_with_dates.append((path, updated_at))
        except Exception as e:
            print(f"[CACHE-CLEANUP] Erreur lecture {path.name}: {e}")
            # Utiliser mtime comme fallback
            try:
                updated_at = datetime.fromtimestamp(path.stat().st_mtime)
                files_with_dates.append((path, updated_at))
            except Exception:
                pass

    # Trier par date croissante (plus ancien en premier)
    files_with_dates.sort(key=lambda x: x[1])
    return files_with_dates


def cleanup_old_caches(max_conversations: int = 10) -> dict:
    """
    Élagage du cache cognitif : conserve les N conversations les plus récentes.
    Supprime les fichiers JSON les plus anciens.

    Args:
        max_conversations: Nombre maximum de fichiers à conserver (défaut: 10)

    Returns:
        Dict avec stats : {'total': int, 'kept': int, 'deleted': int, 'errors': int}
    """
    stats = {'total': 0, 'kept': 0, 'deleted': 0, 'errors': 0}

    if not _CACHE_DIR.exists():
        print("[CACHE-CLEANUP] Dossier cognitive_cache inexistant, rien à faire")
        return stats

    files = _get_cache_files_sorted()
    stats['total'] = len(files)

    if len(files) <= max_conversations:
        stats['kept'] = len(files)
        print(f"[CACHE-CLEANUP] {len(files)} fichier(s) — sous la limite de {max_conversations}, aucun élagage")
        return stats

    # Calculer combien supprimer (les plus anciens = début de la liste)
    to_delete = files[:-max_conversations]
    to_keep = files[-max_conversations:]

    stats['kept'] = len(to_keep)

    for path, updated_at in to_delete:
        try:
            path.unlink()
            stats['deleted'] += 1
            print(f"[CACHE-CLEANUP] Supprimé: {path.name} (modifié le {updated_at.strftime('%Y-%m-%d %H:%M')})")
        except Exception as e:
            stats['errors'] += 1
            print(f"[CACHE-CLEANUP] Erreur suppression {path.name}: {e}")

    print(
        f"[CACHE-CLEANUP] Résultat: {stats['total']} total → "
        f"{stats['kept']} conservé(s), {stats['deleted']} supprimé(s), "
        f"{stats['errors']} erreur(s)"
    )
    return stats


async def cleanup_old_caches_async(max_conversations: int = 10) -> dict:
    """
    Version async de cleanup_old_caches pour appel dans delayed_shutdown().
    Délègue simplement à la version synchrone (opération I/O légère).

    Args:
        max_conversations: Nombre maximum de fichiers à conserver

    Returns:
        Dict avec stats
    """
    return cleanup_old_caches(max_conversations)


def get_cache_stats() -> dict:
    """
    Retourne des statistiques sur le cache actuel (pour debug/logs).

    Returns:
        Dict avec infos sur le cache
    """
    files = _get_cache_files_sorted()

    if not files:
        return {'count': 0, 'oldest': None, 'newest': None}

    return {
        'count': len(files),
        'oldest': files[0][1].isoformat() if files else None,
        'newest': files[-1][1].isoformat() if files else None,
        'files': [p.name for p, _ in files]
    }
