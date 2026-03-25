"""
Dream Engine - Interface Utilisateur
=====================================

Composants UI pour l'intégration dans OGMA :
- Bouton header 🌙 pour activer le mode veille
- Spinner conversation pendant le rêve
- Timer d'inactivité
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import asyncio


def _get_ia_name() -> str:
    """Récupère le nom de l'IA depuis le profil."""
    try:
        from identity_manager import IdentityManager
        manager = IdentityManager()
        name = manager.get_ai_name()
        return name if name else "L'IA"
    except Exception:
        return "L'IA"


# ========== SPINNER HTML (dynamique via fonction) ==========
def _get_spinner_html() -> str:
    """Génère le HTML du spinner avec le nom de l'IA."""
    ia_name = _get_ia_name()
    return f'''
<div style="display:flex;flex-direction:column;align-items:center;margin:16px 0;">
<div style="width:28px;height:28px;border:3px solid #1a1a2e;border-top:3px solid #9b59b6;border-radius:50%;animation:dream-spin 1.5s linear infinite;"></div>
<span style="font-size:11px;color:#9b59b6;margin-top:6px;font-style:italic;">💭 {ia_name} rêve...</span>
</div>
<style>@keyframes dream-spin{{0%{{transform:rotate(0deg)}}100%{{transform:rotate(360deg)}}}}</style>
'''


# Alias pour compatibilité (sera généré dynamiquement)
DREAM_SPINNER_HTML = _get_spinner_html()

# ========== CONFIGURATION UI ==========
_inactivity_timer: Optional[asyncio.Task] = None
_last_activity: Optional[datetime] = None
_inactivity_timeout_minutes: int = 10  # Stocké pour redémarrage après cycle complet
_on_dream_start_callback: Optional[Callable] = None
_on_dream_end_callback: Optional[Callable] = None
_dream_chat_container: Optional[Any] = None  # Widget NiceGUI du spinner
_dream_header_btn_ref: Optional[Any] = None  # Référence au bouton header (pour sync visuelle)


def register_dream_header_btn(btn) -> None:
    """Enregistre la référence au bouton header pour sync visuelle."""
    global _dream_header_btn_ref
    _dream_header_btn_ref = btn


def update_dream_header_btn(is_dreaming_state: bool) -> None:
    """Met à jour l’apparence du bouton header selon l’état du rêve."""
    global _dream_header_btn_ref
    if not _dream_header_btn_ref:
        return
    try:
        _ = _dream_header_btn_ref.client  # Test connexion
        if is_dreaming_state:
            _dream_header_btn_ref.classes(add='dream-btn-active')
            _dream_header_btn_ref.props(add='color=deep-purple')
        else:
            _dream_header_btn_ref.classes(remove='dream-btn-active')
            _dream_header_btn_ref.props(remove='color=deep-purple')
    except RuntimeError:
        _dream_header_btn_ref = None  # Client déconnecté
    except Exception as e:
        print(f"[DREAM-UI] ⚠️ Erreur sync bouton header: {e}")


# ========== SPINNER DANS LE CHAT ==========
def show_dream_spinner_in_chat():
    """Affiche le spinner de rêve dans la zone de chat OGMA."""
    global _dream_chat_container
    try:
        from nicegui import ui
        import sys
        
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng:
            chat_inner = getattr(ogma_ng, '_chat_inner', None)
            if chat_inner:
                with chat_inner:
                    # Créer un conteneur pour le spinner
                    _dream_chat_container = ui.element('div').classes('dream-spinner-container').style('''
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                        margin: 16px auto;
                        max-width: 400px;
                        background: rgba(147, 112, 219, 0.1);
                        border: 1px solid rgba(147, 112, 219, 0.3);
                        border-radius: 16px;
                        animation: dream-pulse 2s ease-in-out infinite;
                    ''')
                    with _dream_chat_container:
                        # Spinner animé avec nom dynamique
                        ia_name = _get_ia_name()
                        ui.html(f'''
                            <div style="display:flex;flex-direction:column;align-items:center;">
                                <div style="width:40px;height:40px;border:3px solid #1a1a2e;border-top:3px solid #9b59b6;border-radius:50%;animation:dream-spin 1.5s linear infinite;"></div>
                                <span style="font-size:14px;color:#9b59b6;margin-top:10px;font-style:italic;">🌙 {ia_name} rêve...</span>
                                <span style="font-size:11px;color:#666;margin-top:4px;">Le rêve apparaîtra dans le journal</span>
                            </div>
                            <style>
                                @keyframes dream-spin{{0%{{transform:rotate(0deg)}}100%{{transform:rotate(360deg)}}}}
                                @keyframes dream-pulse{{0%,100%{{opacity:0.8}}50%{{opacity:1}}}}
                            </style>
                        ''')
                print("[DREAM-UI] ✅ Spinner affiché dans le chat")
    except Exception as e:
        print(f"[DREAM-UI] ⚠️ Erreur affichage spinner: {e}")


def hide_dream_spinner_in_chat():
    """Cache le spinner de rêve dans le chat."""
    global _dream_chat_container
    try:
        if _dream_chat_container:
            # 🛡️ PROTECTION CLIENT DÉCONNECTÉ
            try:
                _ = _dream_chat_container.client
                _dream_chat_container.delete()
            except RuntimeError:
                # Client déconnecté - élément déjà supprimé automatiquement
                print(f"[DREAM-UI] ℹ️ Spinner déjà supprimé (client déconnecté)")
            _dream_chat_container = None
            print("[DREAM-UI] ✅ Spinner retiré du chat")
    except Exception as e:
        print(f"[DREAM-UI] ⚠️ Erreur suppression spinner: {e}")


def update_dream_spinner_phase(phase: str, ia_name: str = None):
    """
    Met à jour le spinner selon la phase du rêve.
    
    Args:
        phase: "dreaming" | "sleeping" | "waking"
        ia_name: Nom de l'IA (optionnel, récupéré automatiquement sinon)
    """
    global _dream_chat_container
    
    if ia_name is None:
        ia_name = _get_ia_name()
    
    # Configuration selon la phase
    phase_configs = {
        "dreaming": {
            "icon": "🌙",
            "text": f"{ia_name} rêve...",
            "subtext": "Le rêve apparaîtra dans le journal",
            "color": "#9b59b6",  # Violet
            "border_color": "rgba(147, 112, 219, 0.3)",
            "bg_color": "rgba(147, 112, 219, 0.1)",
        },
        "sleeping": {
            "icon": "💤",
            "text": f"{ia_name} s'est endormi(e)",
            "subtext": "En sommeil paisible jusqu'au réveil",
            "color": "#3498db",  # Bleu calme
            "border_color": "rgba(52, 152, 219, 0.3)",
            "bg_color": "rgba(52, 152, 219, 0.1)",
        },
        "waking": {
            "icon": "☀️",
            "text": f"Éveil en cours...",
            "subtext": f"{ia_name} se réveille et prépare son récit",
            "color": "#f39c12",  # Orange soleil
            "border_color": "rgba(243, 156, 18, 0.3)",
            "bg_color": "rgba(243, 156, 18, 0.1)",
        }
    }
    
    config = phase_configs.get(phase, phase_configs["dreaming"])
    
    try:
        from nicegui import ui
        import sys
        
        # Si pas de spinner existant, ne rien faire
        if not _dream_chat_container:
            print(f"[DREAM-UI] ⚠️ Pas de spinner à mettre à jour (phase: {phase})")
            return
        
        # 🛡️ PROTECTION CLIENT DÉCONNECTÉ
        try:
            # Tester si le client est toujours connecté
            _ = _dream_chat_container.client
        except RuntimeError as e:
            print(f"[DREAM-UI] ℹ️ Client déconnecté - skip update spinner (phase: {phase})")
            return
        
        # Supprimer l'ancien contenu et recréer
        try:
            _dream_chat_container.clear()
        except RuntimeError:
            print(f"[DREAM-UI] ℹ️ Client déconnecté pendant clear() - skip")
            return
        
        with _dream_chat_container:
            # Animation différente selon phase
            if phase == "sleeping":
                # Animation de respiration lente pour le sommeil
                spinner_animation = "animation: dream-breathe 3s ease-in-out infinite;"
            elif phase == "waking":
                # Animation rapide pour le réveil
                spinner_animation = "animation: dream-spin 0.5s linear infinite;"
            else:
                # Animation standard pour le rêve
                spinner_animation = "animation: dream-spin 1.5s linear infinite;"
            
            ui.html(f'''
                <div style="display:flex;flex-direction:column;align-items:center;">
                    <div style="width:40px;height:40px;border:3px solid #1a1a2e;border-top:3px solid {config['color']};border-radius:50%;{spinner_animation}"></div>
                    <span style="font-size:14px;color:{config['color']};margin-top:10px;font-style:italic;">{config['icon']} {config['text']}</span>
                    <span style="font-size:11px;color:#666;margin-top:4px;">{config['subtext']}</span>
                </div>
                <style>
                    @keyframes dream-spin{{0%{{transform:rotate(0deg)}}100%{{transform:rotate(360deg)}}}}
                    @keyframes dream-pulse{{0%,100%{{opacity:0.8}}50%{{opacity:1}}}}
                    @keyframes dream-breathe{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.1)}}}}
                </style>
            ''')
        
        # Mettre à jour le style du container
        _dream_chat_container.style(f'''
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            margin: 16px auto;
            max-width: 400px;
            background: {config['bg_color']};
            border: 1px solid {config['border_color']};
            border-radius: 16px;
            animation: dream-pulse 2s ease-in-out infinite;
        ''')
        
        print(f"[DREAM-UI] ✅ Spinner mis à jour (phase: {phase})")
        
    except Exception as e:
        print(f"[DREAM-UI] ⚠️ Erreur mise à jour spinner phase: {e}")
        import traceback
        traceback.print_exc()


def get_header_button_config() -> Dict[str, Any]:
    """
    Retourne la configuration du bouton header pour intégration OGMA.
    
    Returns:
        Dict avec 'icon', 'tooltip', 'onclick', etc.
    """
    return {
        'id': 'dream-engine-btn',
        'icon': '🌙',
        'tooltip': 'Mode Rêve',
        'onclick': _on_dream_button_click,
        'is_visible': _is_button_visible,
        'get_state': _get_button_state,
    }


def _is_button_visible() -> bool:
    """Le bouton est toujours visible."""
    return True


def _get_button_state() -> Dict[str, Any]:
    """Retourne l'état actuel du bouton."""
    try:
        from . import is_dreaming
        dreaming = is_dreaming()
    except:
        dreaming = False
    
    return {
        'is_dreaming': dreaming,
        'icon': '☀️' if dreaming else '🌙',
        'tooltip': f'Réveiller {_get_ia_name()}' if dreaming else 'Mode Rêve',
        'class': 'dream-active' if dreaming else ''
    }


async def _on_dream_button_click():
    """Callback quand le bouton est cliqué."""
    try:
        from . import is_dreaming, start_dream, wake_up
        
        if is_dreaming():
            # Réveiller l'IA principale
            result = await wake_up("button_click")
            print(f"[DREAM-UI] ☀️ Réveil par bouton: {result.get('sleep_duration_formatted', 'N/A')}")
            
            if _on_dream_end_callback:
                await _on_dream_end_callback(result)
        else:
            # Endormir l'IA principale
            success = await start_dream()
            print(f"[DREAM-UI] 🌙 Entrée en veille: {success}")
            
            if success and _on_dream_start_callback:
                await _on_dream_start_callback()
                
    except Exception as e:
        print(f"[DREAM-UI] ❌ Erreur bouton: {e}")
        import traceback
        traceback.print_exc()


def set_callbacks(on_start: Callable = None, on_end: Callable = None):
    """Configure les callbacks de début/fin de rêve."""
    global _on_dream_start_callback, _on_dream_end_callback
    _on_dream_start_callback = on_start
    _on_dream_end_callback = on_end


def get_dream_spinner() -> str:
    """Retourne le HTML du spinner de rêve."""
    return DREAM_SPINNER_HTML


# ========== TIMER INACTIVITÉ ==========
async def start_inactivity_timer(timeout_minutes: int = 10, on_timeout: Callable = None):
    """
    Démarre le timer d'inactivité.
    
    Args:
        timeout_minutes: Minutes avant déclenchement auto
        on_timeout: Callback à appeler après timeout
    """
    global _inactivity_timer, _last_activity, _inactivity_timeout_minutes
    _inactivity_timeout_minutes = timeout_minutes  # Mémoriser pour redémarrage
    
    # Annuler le timer précédent
    if _inactivity_timer and not _inactivity_timer.done():
        _inactivity_timer.cancel()
    
    _last_activity = datetime.now()
    timeout_seconds = timeout_minutes * 60

    async def _timer_loop():
        global _last_activity
        print(f"[DREAM-UI] Timer: objectif {timeout_minutes} min ({timeout_seconds}s)")
        while True:
            # Calculer précisément le temps restant
            if _last_activity:
                elapsed = (datetime.now() - _last_activity).total_seconds()
                remaining = timeout_seconds - elapsed
            else:
                # Timer annulé (réveil)
                return

            if remaining <= 0:
                elapsed_min = round((datetime.now() - _last_activity).total_seconds() / 60, 1)
                print(f"[DREAM-UI] ⏰ Inactivité détectée ({elapsed_min} min / {timeout_minutes} min configurés)")
                if on_timeout:
                    await on_timeout()
                else:
                    try:
                        from . import start_dream, is_dreaming
                        if not is_dreaming():
                            await start_dream()
                            update_dream_header_btn(True)  # Bouton visuel état actif
                    except Exception as e:
                        print(f"[DREAM-UI] ❌ Erreur auto-veille: {e}")
                _last_activity = None
                return

            # Dormir par tranches de 30s max pour réagir rapidement aux resets d'activité
            await asyncio.sleep(min(30.0, max(1.0, remaining)))
    
    _inactivity_timer = asyncio.create_task(_timer_loop())
    print(f"[DREAM-UI] ⏱️ Timer inactivité démarré ({timeout_minutes} min)")


def reset_inactivity_timer():
    """Réinitialise le timer d'inactivité. Redémarre la tâche si elle s'est terminée (après cycle complet)."""
    global _last_activity, _inactivity_timer, _inactivity_timeout_minutes
    _last_activity = datetime.now()
    # Si la tâche timer est terminée (cycle complet), la redémarrer
    if _inactivity_timer is None or _inactivity_timer.done():
        # Verifier si le Dream Engine est active avant de relancer le timer
        try:
            from . import get_config
            if not get_config().get('enabled', True):
                return  # Desactive dans les settings - ne pas relancer
        except Exception:
            pass
        print(f"[DREAM-UI] Timer termine - redemarrage ({_inactivity_timeout_minutes} min)")
        _inactivity_timer = asyncio.create_task(
            start_inactivity_timer(timeout_minutes=_inactivity_timeout_minutes)
        )


def stop_inactivity_timer():
    """Arrête le timer d'inactivité."""
    global _inactivity_timer
    if _inactivity_timer and not _inactivity_timer.done():
        _inactivity_timer.cancel()
    _inactivity_timer = None
    print("[DREAM-UI] ⏱️ Timer inactivité arrêté")


# ========== INTÉGRATION NICEGUI ==========
def create_dream_button():
    """
    Crée le bouton NiceGUI pour le header.
    À appeler depuis ogma_ng.py ou ogma_headers.py.
    """
    try:
        from nicegui import ui
        
        async def on_click():
            await _on_dream_button_click()
            # Rafraîchir l'UI
            button.refresh()
        
        @ui.refreshable
        def button():
            state = _get_button_state()
            with ui.button(
                on_click=on_click
            ).props('flat dense').classes('dream-button ' + state.get('class', '')):
                ui.html(f'<span style="font-size: 18px;">{state["icon"]}</span>')
            
            # Tooltip
            ui.tooltip(state['tooltip'])
        
        button()
        return button
        
    except ImportError:
        print("[DREAM-UI] ⚠️ NiceGUI non disponible")
        return None


def inject_dream_styles():
    """Injecte les styles CSS pour le Dream Engine."""
    css = """
    <style>
    .dream-button {
        transition: all 0.3s ease;
    }
    .dream-button:hover {
        transform: scale(1.1);
    }
    .dream-button.dream-active {
        animation: dream-pulse 2s ease-in-out infinite;
    }
    @keyframes dream-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    </style>
    """
    try:
        from nicegui import ui
        ui.html(css)
    except:
        pass


# ========== EXPORT ==========
__all__ = [
    'get_header_button_config',
    'get_dream_spinner',
    'DREAM_SPINNER_HTML',
    'set_callbacks',
    'start_inactivity_timer',
    'reset_inactivity_timer',
    'stop_inactivity_timer',
    'create_dream_button',
    'inject_dream_styles',
    'show_dream_spinner_in_chat',
    'hide_dream_spinner_in_chat',
    'update_dream_spinner_phase',
    'register_dream_header_btn',
    'update_dream_header_btn',
]

