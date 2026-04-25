"""
Hologram Projector — Interface Utilisateur
==========================================

Bouton toggle dans le header OGMA pour activer/désactiver l'extension.
Suit le pattern des autres extensions (dream_engine, cognitive_mirror).
"""

from typing import Optional

_header_btn_ref: Optional[object] = None


def create_header_button_inline() -> Optional[object]:
    """
    Crée le bouton toggle hologramme pour le header OGMA.
    Retourne le bouton NiceGUI créé, ou None si NiceGUI non disponible.
    """
    try:
        from nicegui import ui
        from .state_emitter import is_enabled, set_enabled

        enabled = is_enabled()

        btn = ui.button(
            icon='wb_incandescent',
            on_click=_toggle_hologram,
        ).props(
            f'flat round color={"amber" if enabled else "grey"}'
        ).tooltip('Hologramme actif' if enabled else 'Hologramme désactivé')

        _register_header_btn(btn)
        return btn

    except Exception as e:
        print(f"[HOLOGRAM-UI] Erreur création bouton: {e}")
        return None


def _register_header_btn(btn) -> None:
    global _header_btn_ref
    _header_btn_ref = btn


def _toggle_hologram():
    """Active ou désactive l'extension hologramme."""
    from .state_emitter import is_enabled, set_enabled
    new_state = not is_enabled()
    set_enabled(new_state)
    _sync_header_btn(new_state)
    state_label = "activé" if new_state else "désactivé"
    print(f"[HOLOGRAM-UI] Hologramme {state_label}")

    # Notifier proprement via NiceGUI
    try:
        from nicegui import ui
        ui.notify(
            f"Hologramme {state_label}",
            type='positive' if new_state else 'warning',
            timeout=2000
        )
    except Exception:
        pass


def _sync_header_btn(enabled: bool) -> None:
    """Met à jour l'apparence du bouton selon l'état."""
    global _header_btn_ref
    if not _header_btn_ref:
        return
    try:
        _ = _header_btn_ref.client  # test connexion
        if enabled:
            _header_btn_ref.props('flat round color=amber')
            _header_btn_ref.tooltip('Hologramme actif')
        else:
            _header_btn_ref.props('flat round color=grey')
            _header_btn_ref.tooltip('Hologramme désactivé')
    except RuntimeError:
        _header_btn_ref = None
    except Exception as e:
        print(f"[HOLOGRAM-UI] Erreur sync bouton: {e}")
