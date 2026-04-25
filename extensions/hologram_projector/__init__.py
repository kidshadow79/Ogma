"""
Hologram Projector - Extension OGMA
=====================================

Diffuse une page /hologram + WebSocket /hologram/ws sur le serveur NiceGUI.
Le telephone mobile ouvre http://[IP_LAN]:8080/hologram et projette
le blob anime via une pyramide de Pepper's Ghost.

API publique :
    initialize_hologram()           -> demarre le serveur
    is_available() -> bool
    update_emotion(name, intensity) -> change la couleur du blob
    update_speaking(bool)           -> fait vibrer le blob quand OGMA parle
    get_ui_components() -> dict     -> bouton header toggle
    cleanup()
"""

from typing import Optional

_initialized: bool = False
_available:   bool = False


def initialize_hologram() -> bool:
    global _initialized, _available
    if _initialized:
        return _available
    from .hologram_server import register_routes
    _available   = register_routes()
    _initialized = True
    return _available


def is_available() -> bool:
    return _available


def update_emotion(emotion: str, intensity: float = 1.0):
    if not _available:
        return
    try:
        from .state_emitter import update_emotion as _update
        _update(emotion, intensity)
    except Exception as e:
        print(f"[HOLOGRAM] Erreur update_emotion: {e}")


def update_speaking(is_speaking: bool):
    print(f"[HOLOGRAM] update_speaking({is_speaking}) — available={_available}")
    if not _available:
        return
    try:
        from .state_emitter import update_speaking as _update
        _update(is_speaking)
    except Exception as e:
        print(f"[HOLOGRAM] Erreur update_speaking: {e}")


def get_ui_components() -> dict:
    if not _available:
        return {}
    try:
        from .hologram_ui import create_header_button_inline
        btn = create_header_button_inline()
        return {'header_button': btn} if btn else {}
    except Exception as e:
        print(f"[HOLOGRAM] Erreur get_ui_components: {e}")
        return {}


def cleanup():
    global _initialized, _available
    _initialized = False
    _available   = False
    print("[HologramProjector] Nettoyage effectue")