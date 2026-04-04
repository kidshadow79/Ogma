"""
cache_manager.py
----------------
Gestionnaire du cache cognitif OGMA.
Chaque conversation a son propre fichier JSON dans data/cognitive_cache/.
Écriture atomique (fichier temp + rename) pour éviter la corruption.
"""

import json
import uuid
import copy
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Chemin du dossier cache
_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cognitive_cache"

# Types d'entrées valides
VALID_TYPES = {"directive", "observation", "idea_pending", "context_anchor"}


def _ensure_cache_dir():
    """Crée le dossier cache s'il n'existe pas."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(conv_id: str) -> Path:
    """Retourne le chemin du fichier JSON pour une conversation."""
    # Sécuriser le nom de fichier (éviter les / ou .. malveillants)
    safe_id = "".join(c for c in conv_id if c.isalnum() or c in "-_.")
    return _CACHE_DIR / f"{safe_id}.json"


def load_cache(conv_id: str) -> Dict:
    """
    Charge le cache d'une conversation. Crée un cache vide si inexistant.

    Args:
        conv_id: Identifiant de la conversation (ex: 2026-04-04_14-23-11)

    Returns:
        Dict avec structure complète du cache
    """
    _ensure_cache_dir()
    path = _cache_path(conv_id)

    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validation minimale
            if "entries" not in data:
                data["entries"] = []
            return data
        except Exception as e:
            print(f"[COGNITIVE-CACHE] Erreur lecture {path.name}: {e} — cache vide retourné")

    # Cache vide par défaut
    return {
        "conv_id": conv_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "entries": []
    }


def save_cache(conv_id: str, data: Dict) -> bool:
    """
    Sauvegarde atomique du cache (temp + rename).

    Args:
        conv_id: Identifiant de la conversation
        data: Dict cache complet

    Returns:
        True si succès, False sinon
    """
    _ensure_cache_dir()
    path = _cache_path(conv_id)
    temp_path = path.with_suffix(".tmp")

    try:
        data["updated_at"] = datetime.now().isoformat()
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Rename atomique
        os.replace(temp_path, path)
        return True
    except Exception as e:
        print(f"[COGNITIVE-CACHE] Erreur sauvegarde {path.name}: {e}")
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def add_entry(conv_id: str, entry_type: str, content: str) -> Optional[str]:
    """
    Ajoute une entrée dans le cache.

    Args:
        conv_id: Identifiant de la conversation
        entry_type: Type parmi directive / observation / idea_pending / context_anchor
        content: Contenu de la pensée

    Returns:
        L'ID de l'entrée créée, ou None si échec
    """
    if not content or not content.strip():
        print("[COGNITIVE-CACHE] add_entry: contenu vide ignoré")
        return None

    # Normaliser le type
    entry_type = entry_type.lower().strip()
    if entry_type not in VALID_TYPES:
        print(f"[COGNITIVE-CACHE] Type inconnu '{entry_type}', forcé en 'observation'")
        entry_type = "observation"

    data = load_cache(conv_id)
    entry_id = f"cache-{uuid.uuid4().hex[:8]}"

    entry = {
        "id": entry_id,
        "type": entry_type,
        "content": content.strip(),
        "created_at": datetime.now().isoformat(),
        "active": True
    }

    data["entries"].append(entry)

    if save_cache(conv_id, data):
        print(f"[COGNITIVE-CACHE] ADD [{entry_type}] {content[:60]}")
        return entry_id
    return None


def delete_entry(conv_id: str, entry_id: str) -> bool:
    """
    Supprime une entrée du cache (désactivation logique).

    Args:
        conv_id: Identifiant de la conversation
        entry_id: ID de l'entrée à supprimer

    Returns:
        True si trouvée et supprimée
    """
    data = load_cache(conv_id)
    found = False

    for entry in data["entries"]:
        if entry.get("id") == entry_id:
            entry["active"] = False
            found = True
            print(f"[COGNITIVE-CACHE] DELETE {entry_id}")
            break

    if found:
        return save_cache(conv_id, data)

    print(f"[COGNITIVE-CACHE] DELETE: ID {entry_id} introuvable")
    return False


def update_entry(conv_id: str, entry_id: str, new_content: str) -> bool:
    """
    Modifie le contenu d'une entrée existante.

    Args:
        conv_id: Identifiant de la conversation
        entry_id: ID de l'entrée à modifier
        new_content: Nouveau contenu

    Returns:
        True si trouvée et modifiée
    """
    if not new_content or not new_content.strip():
        print("[COGNITIVE-CACHE] update_entry: contenu vide ignoré")
        return False

    data = load_cache(conv_id)
    found = False

    for entry in data["entries"]:
        if entry.get("id") == entry_id and entry.get("active", True):
            entry["content"] = new_content.strip()
            entry["updated_at"] = datetime.now().isoformat()
            found = True
            print(f"[COGNITIVE-CACHE] UPDATE {entry_id}: {new_content[:60]}")
            break

    if found:
        return save_cache(conv_id, data)

    print(f"[COGNITIVE-CACHE] UPDATE: ID {entry_id} introuvable ou inactif")
    return False


def clear_cache(conv_id: str) -> bool:
    """
    Désactive toutes les entrées actives du cache (CACHE_CLEAR).

    Args:
        conv_id: Identifiant de la conversation

    Returns:
        True si succès
    """
    data = load_cache(conv_id)
    count = 0

    for entry in data["entries"]:
        if entry.get("active", True):
            entry["active"] = False
            count += 1

    print(f"[COGNITIVE-CACHE] CLEAR: {count} entrée(s) désactivée(s)")
    return save_cache(conv_id, data)


def get_active_entries(conv_id: str) -> List[Dict]:
    """
    Retourne toutes les entrées actives du cache.

    Args:
        conv_id: Identifiant de la conversation

    Returns:
        Liste des entrées actives (peut être vide)
    """
    data = load_cache(conv_id)
    return [e for e in data.get("entries", []) if e.get("active", True)]


def get_summary_for_injection(conv_id: str) -> str:
    """
    Génère un texte formaté des entrées actives pour injection dans le system prompt.

    Args:
        conv_id: Identifiant de la conversation

    Returns:
        Texte formaté ou chaîne vide si cache vide
    """
    entries = get_active_entries(conv_id)

    if not entries:
        return ""

    lines = ["[CACHE COGNITIF ACTIF]"]

    # Grouper par type pour la lisibilité
    type_labels = {
        "directive": "Directive",
        "observation": "Observation secrète",
        "idea_pending": "Idée à aborder",
        "context_anchor": "Ancrage contexte"
    }

    by_type: Dict[str, List] = {}
    for entry in entries:
        t = entry.get("type", "observation")
        by_type.setdefault(t, []).append(entry)

    for entry_type, type_entries in by_type.items():
        label = type_labels.get(entry_type, entry_type)
        for e in type_entries:
            lines.append(f"- [{label}] ({e['id']}) {e['content']}")

    return "\n".join(lines)


def get_snapshot(conv_id: str) -> Dict:
    """
    Retourne une copie profonde du cache courant (pour Dream Engine).
    Le snapshot est figé — les modifications ultérieures du cache live ne l'affectent pas.

    Args:
        conv_id: Identifiant de la conversation

    Returns:
        Copie profonde du cache
    """
    data = load_cache(conv_id)
    snapshot = copy.deepcopy(data)
    snapshot["snapshot_at"] = datetime.now().isoformat()
    print(f"[COGNITIVE-CACHE] Snapshot créé: {len(get_active_entries(conv_id))} entrée(s) actives")
    return snapshot


def get_snapshot_summary(snapshot: Dict) -> str:
    """
    Génère un résumé texte d'un snapshot (pour Dream Engine prompts).

    Args:
        snapshot: Dict retourné par get_snapshot()

    Returns:
        Texte formaté pour injection dans le prompt de rêve
    """
    entries = [e for e in snapshot.get("entries", []) if e.get("active", True)]

    if not entries:
        return ""

    lines = ["[PENSÉES EN FOND — Cache Cognitif]"]
    for e in entries:
        lines.append(f"- [{e.get('type', '?')}] {e.get('content', '')}")

    return "\n".join(lines)
