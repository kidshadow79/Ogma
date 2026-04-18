"""
signal_collector.py
-------------------
Scanner de signaux biographiques pour le système de biographie OGMA.

Collecte les entrées non traitées (bio_processed=false/0) depuis 3 sources :
1. Mémoires SQLite (user_tag IS NOT NULL AND bio_processed = 0)
2. Cognitive cache (entrées JSON avec user_tag et bio_processed=false)
3. Résumés de conversations (entrées summaries avec user_tag et bio_processed=false)

Regroupe par user_tag et retourne une structure normalisée
pour alimenter la Phase 1 (génération biographique).
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# Chemins racine
_ROOT = Path(__file__).parent.parent.parent
_MEMORY_DB = _ROOT / "data" / "memory" / "memories.db"
_CACHE_DIR = _ROOT / "data" / "cognitive_cache"
_CONV_DIR = _ROOT / "data" / "conversations"


def collect_signals(user_tag: str) -> Dict:
    """
    Collecte tous les signaux biographiques non traités pour un utilisateur.

    Args:
        user_tag: Nom de l'utilisateur (ex: "Yohan")

    Returns:
        Dict avec structure:
        {
            "user_tag": "Yohan",
            "collected_at": "ISO_DATE",
            "signals": [
                {"source": "memory", "source_id": "...", "date": "...", "content": "..."},
                {"source": "cognitive_cache", "source_id": "...", "date": "...", "content": "..."},
                {"source": "summary", "source_id": "...", "date": "...", "content": "..."},
            ],
            "counts": {"memory": N, "cognitive_cache": N, "summary": N, "total": N}
        }
    """
    if not user_tag:
        return {"user_tag": None, "signals": [], "counts": {"total": 0}}

    signals = []

    # Source 1: Mémoires SQLite
    memory_signals = _collect_from_memory(user_tag)
    signals.extend(memory_signals)

    # Source 2: Cognitive cache
    cache_signals = _collect_from_cache(user_tag)
    signals.extend(cache_signals)

    # Source 3: Résumés de conversations
    summary_signals = _collect_from_summaries(user_tag)
    signals.extend(summary_signals)

    # Trier par date (plus ancien d'abord)
    signals.sort(key=lambda s: s.get("date", ""))

    counts = {
        "memory": len(memory_signals),
        "cognitive_cache": len(cache_signals),
        "summary": len(summary_signals),
        "total": len(signals)
    }

    print(f"[SIGNAL-COLLECTOR] Collecte pour '{user_tag}': "
          f"{counts['memory']} mémoires, {counts['cognitive_cache']} cache, "
          f"{counts['summary']} résumés = {counts['total']} signaux")

    return {
        "user_tag": user_tag,
        "collected_at": datetime.now().isoformat(),
        "signals": signals,
        "counts": counts
    }


def mark_signals_processed(signals: List[Dict]) -> int:
    """
    Marque les signaux comme traités (bio_processed=true/1).
    Appelé APRÈS intégration réussie dans la biographie.

    Args:
        signals: Liste de signaux retournés par collect_signals()

    Returns:
        Nombre de signaux marqués avec succès
    """
    marked = 0

    # Grouper par source pour traitement batch
    memory_ids = [s["source_id"] for s in signals if s["source"] == "memory"]
    cache_entries = [(s["source_id"], s.get("conv_id")) for s in signals if s["source"] == "cognitive_cache"]
    summary_entries = [(s["source_id"], s.get("conv_id")) for s in signals if s["source"] == "summary"]

    # Marquer mémoires SQLite
    if memory_ids:
        marked += _mark_memory_processed(memory_ids)

    # Marquer cache cognitif
    if cache_entries:
        marked += _mark_cache_processed(cache_entries)

    # Marquer résumés
    if summary_entries:
        marked += _mark_summaries_processed(summary_entries)

    print(f"[SIGNAL-COLLECTOR] {marked}/{len(signals)} signaux marqués bio_processed=true")
    return marked


# ===========================================================================
# Sources de collecte
# ===========================================================================

def _collect_from_memory(user_tag: str) -> List[Dict]:
    """Collecte les mémoires SQLite non traitées pour un user_tag."""
    signals = []
    if not _MEMORY_DB.exists():
        return signals

    try:
        with sqlite3.connect(_MEMORY_DB) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT id, created_at, text_original, title, summary, score_impact
                   FROM memories
                   WHERE user_tag = ? AND bio_processed = 0
                   ORDER BY created_at ASC""",
                (user_tag,)
            )
            for row in cursor:
                content = row["summary"] or row["text_original"] or ""
                if content.strip():
                    signals.append({
                        "source": "memory",
                        "source_id": row["id"],
                        "date": row["created_at"] or "",
                        "content": content.strip(),
                        "title": row["title"] or "",
                        "score": row["score_impact"] or 0.0
                    })
    except Exception as e:
        print(f"[SIGNAL-COLLECTOR] Erreur lecture mémoires SQLite: {e}")

    return signals


def _collect_from_cache(user_tag: str) -> List[Dict]:
    """Collecte les entrées cognitive cache non traitées pour un user_tag."""
    signals = []
    if not _CACHE_DIR.exists():
        return signals

    try:
        for cache_file in _CACHE_DIR.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                conv_id = data.get("conv_id", cache_file.stem)

                for entry in data.get("entries", []):
                    if (entry.get("user_tag") == user_tag
                            and not entry.get("bio_processed", False)
                            and entry.get("active", True)):
                        content = entry.get("content", "").strip()
                        if content:
                            signals.append({
                                "source": "cognitive_cache",
                                "source_id": entry.get("id", ""),
                                "conv_id": conv_id,
                                "date": entry.get("created_at", ""),
                                "content": content,
                                "type": entry.get("type", "observation")
                            })
            except (json.JSONDecodeError, Exception) as e:
                print(f"[SIGNAL-COLLECTOR] Erreur lecture cache {cache_file.name}: {e}")
    except Exception as e:
        print(f"[SIGNAL-COLLECTOR] Erreur scan dossier cache: {e}")

    return signals


def _collect_from_summaries(user_tag: str) -> List[Dict]:
    """Collecte les résumés de conversations taggés et non traités."""
    signals = []
    if not _CONV_DIR.exists():
        return signals

    try:
        for conv_file in _CONV_DIR.glob("*.json"):
            if conv_file.name == "index.json":
                continue

            try:
                data = json.loads(conv_file.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    continue

                summaries_data = data.get("summaries", {})
                ranges = summaries_data.get("ranges", [])

                for i, summary in enumerate(ranges):
                    if (summary.get("user_tag") == user_tag
                            and not summary.get("bio_processed", False)):
                        text = summary.get("text", "").strip()
                        if text:
                            signals.append({
                                "source": "summary",
                                "source_id": f"{conv_file.stem}:range:{i}",
                                "conv_id": conv_file.stem,
                                "date": summary.get("created_at", ""),
                                "content": text
                            })
            except (json.JSONDecodeError, Exception) as e:
                print(f"[SIGNAL-COLLECTOR] Erreur lecture conv {conv_file.name}: {e}")
    except Exception as e:
        print(f"[SIGNAL-COLLECTOR] Erreur scan conversations: {e}")

    return signals


# ===========================================================================
# Marquage post-traitement
# ===========================================================================

def _mark_memory_processed(memory_ids: List[str]) -> int:
    """Marque des mémoires comme bio_processed=1 dans SQLite."""
    if not _MEMORY_DB.exists() or not memory_ids:
        return 0

    try:
        with sqlite3.connect(_MEMORY_DB) as conn:
            placeholders = ",".join("?" * len(memory_ids))
            conn.execute(
                f"UPDATE memories SET bio_processed = 1 WHERE id IN ({placeholders})",
                memory_ids
            )
            conn.commit()
        return len(memory_ids)
    except Exception as e:
        print(f"[SIGNAL-COLLECTOR] Erreur marquage mémoires: {e}")
        return 0


def _mark_cache_processed(entries: List[tuple]) -> int:
    """Marque des entrées cache comme bio_processed=true dans leurs JSON."""
    marked = 0
    # Grouper par conv_id pour minimiser les lectures/écritures
    by_conv = {}
    for entry_id, conv_id in entries:
        by_conv.setdefault(conv_id, []).append(entry_id)

    for conv_id, entry_ids in by_conv.items():
        try:
            # Sécuriser le nom de fichier
            safe_id = "".join(c for c in conv_id if c.isalnum() or c in "-_.")
            cache_file = _CACHE_DIR / f"{safe_id}.json"
            if not cache_file.exists():
                continue

            data = json.loads(cache_file.read_text(encoding="utf-8"))
            ids_set = set(entry_ids)

            for entry in data.get("entries", []):
                if entry.get("id") in ids_set:
                    entry["bio_processed"] = True
                    marked += 1

            # Écriture atomique
            import os
            temp = cache_file.with_suffix(".tmp")
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp, cache_file)
        except Exception as e:
            print(f"[SIGNAL-COLLECTOR] Erreur marquage cache {conv_id}: {e}")

    return marked


def _mark_summaries_processed(entries: List[tuple]) -> int:
    """Marque des résumés comme bio_processed=true dans les JSON de conversations."""
    marked = 0
    # Grouper par conv_id
    by_conv = {}
    for source_id, conv_id in entries:
        # source_id = "conv_stem:range:N"
        parts = source_id.split(":range:")
        if len(parts) == 2:
            range_idx = int(parts[1])
            by_conv.setdefault(conv_id, []).append(range_idx)

    for conv_id, range_indices in by_conv.items():
        try:
            conv_file = _CONV_DIR / f"{conv_id}.json"
            if not conv_file.exists():
                continue

            data = json.loads(conv_file.read_text(encoding="utf-8"))
            ranges = data.get("summaries", {}).get("ranges", [])
            indices_set = set(range_indices)

            for i, summary in enumerate(ranges):
                if i in indices_set:
                    summary["bio_processed"] = True
                    marked += 1

            # Écriture atomique
            import os
            temp = conv_file.with_suffix(".tmp")
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp, conv_file)
        except Exception as e:
            print(f"[SIGNAL-COLLECTOR] Erreur marquage résumé {conv_id}: {e}")

    return marked
