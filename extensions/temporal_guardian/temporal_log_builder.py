"""
Temporal Log Builder — Générateur de logs temporels pour OGMA
=============================================================

Produit un bloc JSON lisible par tout LLM avec les données temporelles réelles.
Python pur, zéro appel API.

Remplace l'ancien système Archiviste qui analysait les patterns temporels via API.
L'IA principale reçoit les données brutes et interprète elle-même.

Usage dans ogma_ng.py :
    from extensions.temporal_guardian.temporal_log_builder import (
        register_message_time,
        build_temporal_log
    )
    # Au début de _send_chat_message() :
    register_message_time()
    # Juste avant l'injection des instructions :
    log = build_temporal_log(conv_index=_conv_index, is_new_session=not bool(_current_conversation_id))
"""

import json
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# État session (module-level, persistant pendant toute la session Python)
# ---------------------------------------------------------------------------
_session_start: Optional[datetime] = None
_last_message_time: Optional[datetime] = None   # Temps du message PRÉCÉDENT (terminé)
_current_message_time: Optional[datetime] = None  # Temps du message EN COURS

# ---------------------------------------------------------------------------
# Tables de traduction français
# ---------------------------------------------------------------------------
_JOURS_FR = {
    'Monday': 'lundi', 'Tuesday': 'mardi', 'Wednesday': 'mercredi',
    'Thursday': 'jeudi', 'Friday': 'vendredi', 'Saturday': 'samedi', 'Sunday': 'dimanche'
}
_MOIS_FR = {
    'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
    'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
    'September': 'septembre', 'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
}


def _format_datetime_fr(dt: datetime) -> str:
    """Formate une datetime en français naturel : 'lundi 31 mars 2026 à 22h15'."""
    s = dt.strftime("%A %d %B %Y à %Hh%M")
    for eng, fr in _JOURS_FR.items():
        s = s.replace(eng, fr)
    for eng, fr in _MOIS_FR.items():
        s = s.replace(eng, fr)
    return s


def _format_delta(seconds: float) -> str:
    """Formate un delta en secondes en texte naturel lisible."""
    seconds = max(0.0, seconds)
    if seconds < 60:
        n = int(seconds)
        return f"{n} seconde{'s' if n > 1 else ''}"
    elif seconds < 3600:
        m = int(seconds / 60)
        s = int(seconds % 60)
        result = f"{m} minute{'s' if m > 1 else ''}"
        if s > 0:
            result += f" {s} seconde{'s' if s > 1 else ''}"
        return result
    elif seconds < 86400:
        h = int(seconds / 3600)
        m = int((seconds % 3600) / 60)
        result = f"{h} heure{'s' if h > 1 else ''}"
        if m > 0:
            result += f" {m} minute{'s' if m > 1 else ''}"
        return result
    else:
        d = int(seconds / 86400)
        h = int((seconds % 86400) / 3600)
        result = f"{d} jour{'s' if d > 1 else ''}"
        if h > 0:
            result += f" {h} heure{'s' if h > 1 else ''}"
        return result


def register_message_time() -> None:
    """
    À appeler au tout début de chaque traitement de message utilisateur.

    - Initialise _session_start si c'est le premier message de la session.
    - Sauvegarde _current_message_time → _last_message_time avant de mettre
      à jour, afin que build_temporal_log() calcule "depuis_derniere_interaction"
      comme l'écart réel depuis le message précédent.

    Appelé AVANT build_temporal_log() dans le flux _send_chat_message().
    """
    global _session_start, _last_message_time, _current_message_time
    now = datetime.now()
    if _session_start is None:
        _session_start = now
        print(f"[TEMPORAL-LOG] Session démarrée à {now.strftime('%H:%M:%S')}")
    _last_message_time = _current_message_time  # Sauvegarde AVANT d'écraser
    _current_message_time = now


def build_temporal_log(conv_index: dict, is_new_session: bool = False,
                       current_conversation_id: Optional[str] = None) -> str:
    """
    Génère le log temporel JSON prêt à l'injection dans le contexte système.

    Structure hiérarchique à 3 niveaux :
    - session  : depuis le lancement d'OGMA (processus Python)
    - message  : depuis le dernier message envoyé dans cette session
    - conversation : depuis la dernière conversation sauvegardée (historique)

    Args:
        conv_index:               Dict _conv_index de ogma_ng.
        is_new_session:           Conservé pour compatibilité (ignoré).
        current_conversation_id:  ID de la conv en cours, exclue de la recherche.

    Returns:
        Chaîne JSON indentée, entourée de balises --- CONTEXTE TEMPOREL ---.
    """
    now = datetime.now()
    session_start = _session_start or now

    # -- Niveau SESSION : depuis le lancement d'OGMA --
    session_block = {
        "definition": "Depuis le lancement d'OGMA (processus en cours)",
        "demarree_le": _format_datetime_fr(session_start),
        "duree_session": _format_delta((now - session_start).total_seconds()),
    }

    # -- Niveau MESSAGE : depuis le dernier message dans cette session --
    if _last_message_time:
        message_block = {
            "definition": "Depuis le message précédent envoyé dans cette session",
            "envoye_le": _format_datetime_fr(_last_message_time),
            "il_y_a": _format_delta((now - _last_message_time).total_seconds()),
        }
    else:
        message_block = {
            "definition": "Depuis le message précédent envoyé dans cette session",
            "envoye_le": None,
            "il_y_a": None,
            "note": "C'est le premier message de cette session"
        }

    # -- Niveau CONVERSATION : depuis la dernière conversation sauvegardée --
    conversation_block: dict = {
        "definition": "Depuis la fin de la dernière conversation sauvegardée dans l'historique",
    }
    if conv_index:
        try:
            past_convs = [
                v for k, v in conv_index.items()
                if k != current_conversation_id and v.get('updated')
            ]
            sorted_convs = sorted(
                past_convs,
                key=lambda x: x.get('updated', ''),
                reverse=True
            )
            if sorted_convs:
                last_dt = datetime.fromisoformat(sorted_convs[0]['updated'])
                conversation_block["terminee_le"] = _format_datetime_fr(last_dt)
                conversation_block["il_y_a"] = _format_delta((now - last_dt).total_seconds())
                conversation_block["titre"] = sorted_convs[0].get('title', '—')
            else:
                conversation_block["il_y_a"] = None
                conversation_block["note"] = "Aucune conversation précédente trouvée"
        except Exception as e:
            print(f"[TEMPORAL-LOG] ⚠️ Erreur calcul conversation: {e}")
            conversation_block["il_y_a"] = None
    else:
        conversation_block["il_y_a"] = None
        conversation_block["note"] = "Première utilisation"

    data = {
        "maintenant": _format_datetime_fr(now),
        "session": session_block,
        "message": message_block,
        "conversation": conversation_block,
    }

    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return f"--- CONTEXTE TEMPOREL ---\n{json_str}\n--- FIN CONTEXTE TEMPOREL ---"
