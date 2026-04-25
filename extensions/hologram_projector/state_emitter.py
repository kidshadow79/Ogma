"""
Hologram Projector — State Emitter
====================================

Singleton qui centralise l'état courant du hologramme et diffuse
les changements à tous les clients WebSocket connectés.

Approche : queue thread-safe drainée par un worker asyncio (NiceGUI event loop).
Cela garantit le bon fonctionnement depuis n'importe quel contexte
(thread async NiceGUI, thread Python audio_task, etc.)

API publique :
    update_emotion(emotion: str, intensity: float = 1.0)
    update_speaking(is_speaking: bool)
    set_enabled(value: bool)
    is_enabled() -> bool
    get_state() -> dict
    register_client(ws) / unregister_client(ws)
    drain_broadcast_queue()   <- appelé par le worker asyncio
"""

import asyncio
import json
import queue
from typing import Set

# ─── État courant ───────────────────────────────────────────────
_state = {
    "emotion":     "neutre",
    "intensity":   1.0,
    "is_speaking": False,
}

# ─── Clients WebSocket connectés ────────────────────────────────
_clients: Set = set()

# ─── Activation de l'extension ──────────────────────────────────
_enabled: bool = True

# ─── Queue thread-safe pour les broadcasts ──────────────────────
# Toute mise à jour (depuis n'importe quel thread) pousse ici.
# Le worker asyncio (NiceGUI event loop) draine la queue.
_broadcast_queue: queue.Queue = queue.Queue()


# ─── Enregistrement / désinscription des clients WS ────────────

def register_client(websocket):
    _clients.add(websocket)


def unregister_client(websocket):
    _clients.discard(websocket)


# ─── Broadcast (coroutine) ───────────────────────────────────────

async def _broadcast(payload: dict):
    """Envoie l'état JSON à tous les clients connectés."""
    if not _clients:
        return
    message = json.dumps(payload)
    dead = set()
    for ws in list(_clients):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _clients.discard(ws)


async def drain_broadcast_queue():
    """
    Draine la queue des broadcasts en attente.
    Appelée en boucle par le worker asyncio lancé au startup de NiceGUI.
    """
    while not _broadcast_queue.empty():
        try:
            payload = _broadcast_queue.get_nowait()
            await _broadcast(payload)
        except queue.Empty:
            break
        except Exception:
            break


def _enqueue(payload: dict):
    """Pousse un payload dans la queue (thread-safe, non-bloquant)."""
    try:
        _broadcast_queue.put_nowait(payload)
    except Exception:
        pass


# ─── API publique ────────────────────────────────────────────────

def set_enabled(value: bool):
    global _enabled
    _enabled = value
    _enqueue({**dict(_state), "enabled": value})


def is_enabled() -> bool:
    return _enabled


def update_emotion(emotion: str, intensity: float = 1.0):
    """
    Met a jour l emotion et diffuse aux clients WebSocket.
    emotion : cle du EMOTION_MAP dans hologram.html
              (joie, tristesse, attachement, saturation, peur, neutre)
    intensity : 0.0-1.0 (reserve pour usage futur)
    """
    if not _enabled:
        return
    _state["emotion"]   = emotion
    _state["intensity"] = intensity
    _enqueue({**dict(_state), "enabled": _enabled})


def update_speaking(is_speaking: bool):
    """Met a jour l etat parole et diffuse aux clients WebSocket."""
    if not _enabled:
        return
    _state["is_speaking"] = is_speaking
    _enqueue({**dict(_state), "enabled": _enabled})


def send_envelope(data: list, interval_ms: int = 50):
    """
    Envoie l'enveloppe RMS réelle du TTS aux clients.
    data      : liste de float [0.0-1.0] espacés de interval_ms ms
    interval_ms : durée de chaque frame en millisecondes
    Le client rejoue l'enveloppe frame par frame en sync avec l'audio.
    """
    if not _enabled or not data:
        return
    _enqueue({"type": "envelope", "data": data, "interval_ms": interval_ms})


def get_state() -> dict:
    return dict(_state)