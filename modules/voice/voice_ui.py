"""
modules/voice/voice_ui.py
=========================
Composants UI pour le système vocal OGMA

Indicateur visuel animé avec spinner NiceGUI intégré dans le header :
- STANDBY : dots orange  
- LISTENING : dots vert
- SPEAKING : dots violet

Auteur: Yohan BROCARD
Date: Janvier 2026
"""

from typing import Optional, Callable
from nicegui import ui

from .voice_manager import VoiceState


class VoiceIndicator:
    """
    Indicateur visuel de l'état vocal.
    
    Affiche un badge animé dans le header de l'application.
    Style compact pour s'intégrer avec les autres boutons.
    """
    
    # Configuration des états
    STATE_CONFIG = {
        VoiceState.INACTIVE: {
            'visible': False,
            'color': 'grey',
            'text': 'Micro inactif',
            'icon': '🔇',
            'tooltip': 'Mode vocal désactivé - Cliquez sur la zone de message'
        },
        VoiceState.STANDBY: {
            'visible': True,
            'color': 'orange',
            'text': 'En veille',
            'icon': '💤',
            'tooltip': 'En attente du trigger - Dites le mot d\'activation'
        },
        VoiceState.LISTENING: {
            'visible': True,
            'color': 'green',
            'text': 'Écoute...',
            'icon': '🎤',
            'tooltip': 'Transcription en cours - Parlez maintenant'
        },
        VoiceState.SPEAKING: {
            'visible': True,
            'color': 'purple',
            'text': 'L\'IA parle',
            'icon': '🌸',
            'tooltip': 'L\'IA répond - Dites le trigger pour interrompre'
        }
    }
    
    def __init__(self):
        """Initialise l'indicateur vocal"""
        self._container: Optional[ui.element] = None
        self._spinner: Optional[ui.spinner] = None
        self._label: Optional[ui.label] = None
        self._current_state = VoiceState.INACTIVE
        self._status_text = ""
        self._is_created = False
    
    def create(self, parent_container=None):
        """
        Crée l'indicateur visuel.
        
        Args:
            parent_container: Container parent NiceGUI (optionnel).
                              Si None, crée un container autonome.
        """
        if self._is_created:
            return
        
        # Contexte parent ou création d'un container autonome
        def build_indicator():
            with ui.element('div').classes(
                'flex items-center gap-2 px-3 py-1.5 rounded-lg '
                'bg-zinc-700/80 border border-zinc-600'
            ).style(
                'min-width: 110px; height: 36px;'
            ) as container:
                # Spinner animé
                spinner = ui.spinner(
                    'dots',
                    size='sm',
                    color='orange'
                ).classes('flex-shrink-0')
                
                # Texte de statut compact
                label = ui.label('💤 En veille').classes(
                    'text-xs font-medium text-white whitespace-nowrap'
                )
                
                # Tooltip
                container.props('title="En attente du trigger vocal"')
            
            return container, spinner, label
        
        if parent_container:
            with parent_container:
                self._container, self._spinner, self._label = build_indicator()
        else:
            self._container, self._spinner, self._label = build_indicator()
        
        # Masquer par défaut (INACTIVE)
        if self._container:
            self._container.style('display: none;')
        
        self._is_created = True
        print("[VOICE-UI] ✅ Indicateur créé")
    
    def update_state(self, state: VoiceState):
        """
        Met à jour l'indicateur selon l'état.
        
        Args:
            state: Nouvel état vocal
        """
        if not self._is_created:
            return
        
        self._current_state = state
        config = self.STATE_CONFIG.get(state, self.STATE_CONFIG[VoiceState.INACTIVE])
        
        # Visibilité via display style (plus fiable que set_visibility)
        if self._container:
            if config['visible']:
                self._container.style('display: flex;')
            else:
                self._container.style('display: none;')
            
            # Tooltip
            self._container.props(f'title="{config["tooltip"]}"')
            
            try:
                self._container.update()
            except Exception:
                pass
        
        # Couleur du spinner
        if self._spinner and config['visible']:
            self._spinner.props(f'color="{config["color"]}"')
            try:
                self._spinner.update()
            except Exception:
                pass
        
        # Texte principal
        if self._label:
            self._label.text = f"{config['icon']} {config['text']}"
            try:
                self._label.update()
            except Exception:
                pass
        
        print(f"[VOICE-UI] 🎨 État: {state.name} -> {config['color']}")
    
    def update_status_text(self, text: str):
        """
        Met à jour le texte de statut (transcription preview).
        
        Args:
            text: Texte à afficher
        """
        self._status_text = text
        
        # En mode LISTENING, afficher un aperçu de la transcription
        if self._label and self._is_created and self._current_state == VoiceState.LISTENING:
            if text:
                # Tronquer si trop long
                preview = text[:20] + "..." if len(text) > 20 else text
                self._label.text = f"🎤 {preview}"
            else:
                self._label.text = "🎤 Parlez..."
            
            try:
                self._label.update()
            except Exception:
                pass
    
    def show(self):
        """Affiche l'indicateur"""
        if self._container:
            self._container.style('display: flex;')
    
    def hide(self):
        """Masque l'indicateur"""
        if self._container:
            self._container.style('display: none;')
    
    def cleanup(self):
        """Nettoyage propre"""
        if self._container:
            try:
                self._container.delete()
            except Exception:
                pass
        self._is_created = False


# Singleton
_voice_indicator: Optional[VoiceIndicator] = None


def create_voice_indicator(parent_container=None, force_recreate: bool = False) -> VoiceIndicator:
    """
    Crée et retourne l'indicateur vocal singleton.
    Doit être appelé dans le contexte de la page NiceGUI.
    
    Args:
        parent_container: Container parent où injecter l'indicateur
        force_recreate: Force la recréation (pour rechargement de page)
    """
    global _voice_indicator
    
    # Si force_recreate ou pas d'instance, créer une nouvelle
    if force_recreate or _voice_indicator is None:
        # Cleanup ancien indicateur si existe
        if _voice_indicator is not None:
            _voice_indicator.cleanup()
        _voice_indicator = VoiceIndicator()
    
    # Toujours recréer les éléments UI (peuvent être orphelins après rechargement)
    if _voice_indicator._is_created:
        # Reset le flag pour permettre recréation
        _voice_indicator._is_created = False
    
    _voice_indicator.create(parent_container)
    return _voice_indicator


def get_voice_indicator() -> Optional[VoiceIndicator]:
    """Retourne l'indicateur existant ou None"""
    return _voice_indicator
