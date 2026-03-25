"""
OGMA Telegram Connector - UI Components
Interface utilisateur NiceGUI pour les paramètres
"""

import asyncio
from typing import Optional, Callable
from nicegui import ui

from .config import get_telegram_config
from .bot_handler import get_bot_handler
from . import (
    start_telegram_bot,
    stop_telegram_bot,
    is_telegram_running,
    get_telegram_status,
)


class TelegramConnectorUI:
    """Interface utilisateur pour configurer le connecteur Telegram"""
    
    def __init__(self):
        self.config = get_telegram_config()
        self.bot_handler = get_bot_handler()
        
        # Éléments UI (créés dynamiquement)
        self._enabled_switch = None
        self._token_input = None
        self._status_label = None
        self._start_stop_button = None
        self._auto_start_switch = None
        self._voice_input_switch = None
        self._voice_output_switch = None
        self._image_input_switch = None
        self._image_output_switch = None
        self._allowed_users_input = None
        
        print("[TELEGRAM-UI] ✅ Interface initialisée")
    
    def create_settings_panel(self, container) -> None:
        """
        Crée le panel de paramètres Telegram.
        Appelé depuis ogma_modals.py ou ogma_extensions_ui.py
        """
        with container:
            with ui.card().classes('w-full'):
                # En-tête
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('📱 Telegram Connector').classes('text-lg font-bold')
                    
                    # Indicateur de statut
                    self._status_label = ui.label().classes('text-sm')
                    self._update_status_label()
                
                ui.separator()
                
                # Activation
                with ui.row().classes('w-full items-center gap-4'):
                    self._enabled_switch = ui.switch(
                        'Activer Telegram',
                        value=self.config.enabled,
                        on_change=self._on_enabled_change
                    )
                    
                    self._auto_start_switch = ui.switch(
                        'Démarrage auto',
                        value=self.config.auto_start,
                        on_change=lambda e: self._save_setting('auto_start', e.value)
                    ).tooltip('Démarrer le bot automatiquement au lancement d\'OGMA')
                
                # Token
                with ui.row().classes('w-full items-end gap-2'):
                    self._token_input = ui.input(
                        'Token du Bot',
                        value=self.config.bot_token,
                        password=True,
                        password_toggle_button=True,
                        on_change=lambda e: self._save_setting('bot_token', e.value)
                    ).classes('flex-grow')
                    
                    ui.button(
                        '🔗',
                        on_click=lambda: ui.run_javascript('window.open("https://t.me/BotFather", "_blank")')
                    ).tooltip('Ouvrir @BotFather pour créer un bot')
                
                # Bouton démarrer/arrêter
                with ui.row().classes('w-full justify-center mt-4'):
                    self._start_stop_button = ui.button(
                        '🚀 Démarrer le bot',
                        on_click=self._toggle_bot
                    ).classes('w-48')
                    self._update_button_state()
                
                ui.separator()
                
                # Fonctionnalités
                ui.label('Fonctionnalités').classes('font-semibold mt-2')
                
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    self._voice_input_switch = ui.switch(
                        '🎤 Vocaux entrants',
                        value=self.config.voice_input_enabled,
                        on_change=lambda e: self._save_setting('voice_input_enabled', e.value)
                    ).tooltip('Transcrire les messages vocaux reçus')
                    
                    self._voice_output_switch = ui.switch(
                        '🔊 Vocaux sortants',
                        value=self.config.voice_output_enabled,
                        on_change=lambda e: self._save_setting('voice_output_enabled', e.value)
                    ).tooltip('Répondre par message vocal')
                    
                    self._image_input_switch = ui.switch(
                        '📷 Images entrantes',
                        value=self.config.image_input_enabled,
                        on_change=lambda e: self._save_setting('image_input_enabled', e.value)
                    ).tooltip('Analyser les images reçues')
                    
                    self._image_output_switch = ui.switch(
                        '🎨 Images sortantes',
                        value=self.config.image_output_enabled,
                        on_change=lambda e: self._save_setting('image_output_enabled', e.value)
                    ).tooltip('Envoyer les images générées')
                
                ui.separator()
                
                # Sécurité
                ui.label('Sécurité').classes('font-semibold mt-2')
                
                with ui.row().classes('w-full items-end gap-2'):
                    current_users = ', '.join(map(str, self.config.allowed_user_ids))
                    self._allowed_users_input = ui.input(
                        'User IDs autorisés',
                        value=current_users,
                        on_change=self._on_allowed_users_change
                    ).classes('flex-grow').tooltip(
                        'Liste des IDs Telegram autorisés (séparés par virgule). '
                        'Laisse vide pour autoriser le premier utilisateur.'
                    )
                
                # Instructions
                with ui.expansion('📖 Instructions', value=False).classes('w-full mt-4'):
                    ui.markdown('''
**Configuration:**
1. Ouvre Telegram et cherche `@BotFather`
2. Envoie `/newbot` et suis les instructions
3. Copie le token fourni et colle-le ci-dessus
4. Active l'extension et clique sur "Démarrer"

**Première connexion:**
- Envoie `/start` à ton bot sur Telegram
- Ton ID sera automatiquement enregistré

**Commandes disponibles:**
- `/start` - Démarrer la conversation
- `/help` - Afficher l'aide
- `/status` - Voir l'état d'OGMA
- `/clear` - Effacer l'historique

**Fonctionnalités:**
- 💬 Envoie des messages texte
- 📷 Envoie des photos pour analyse
- 🎤 Envoie des vocaux (transcrits automatiquement)
- 🎨 Reçois les images générées par OGMA
                    ''')
    
    def create_header_button(self) -> Optional[ui.button]:
        """
        Crée un bouton pour le header d'OGMA.
        Retourne le bouton ou None si non configuré.
        """
        if not self.config.is_configured():
            return None
        
        button = ui.button(
            icon='telegram',
            on_click=self._on_header_button_click
        ).props('flat round')
        
        # Mettre à jour l'apparence selon l'état
        if is_telegram_running():
            button.classes('text-green-500')
            button.tooltip('Telegram: Connecté')
        else:
            button.classes('text-gray-400')
            button.tooltip('Telegram: Déconnecté')
        
        return button
    
    # === Callbacks ===
    
    def _on_enabled_change(self, e) -> None:
        """Callback quand on active/désactive l'extension"""
        self.config.enabled = e.value
        self.config.save_config()
        self._update_status_label()
        self._update_button_state()
    
    def _save_setting(self, key: str, value) -> None:
        """Sauvegarde un paramètre"""
        self.config.set(key, value)
        self.config.save_config()
    
    def _on_allowed_users_change(self, e) -> None:
        """Callback pour la liste des utilisateurs autorisés"""
        try:
            # Parser la liste d'IDs
            text = e.value.strip()
            if not text:
                user_ids = []
            else:
                user_ids = [int(x.strip()) for x in text.split(',') if x.strip()]
            
            self.config.allowed_user_ids = user_ids
            self.config.save_config()
        except ValueError:
            ui.notify('Format invalide. Utilise des nombres séparés par des virgules.', type='warning')
    
    async def _toggle_bot(self) -> None:
        """Démarre ou arrête le bot"""
        if is_telegram_running():
            await stop_telegram_bot()
            ui.notify('🛑 Bot Telegram arrêté', type='info')
        else:
            if not self.config.is_configured():
                ui.notify('⚠️ Configure d\'abord le token du bot', type='warning')
                return
            
            success = await start_telegram_bot()
            if success:
                ui.notify('🚀 Bot Telegram démarré !', type='positive')
            else:
                ui.notify('❌ Échec du démarrage du bot', type='negative')
        
        self._update_status_label()
        self._update_button_state()
    
    def _on_header_button_click(self) -> None:
        """Callback du bouton header"""
        status = get_telegram_status()
        
        if status['running']:
            ui.notify(
                f"📱 Telegram actif - {status['allowed_users']} utilisateur(s)",
                type='info'
            )
        else:
            ui.notify('📱 Telegram inactif', type='warning')
    
    # === Mises à jour UI ===
    
    def _update_status_label(self) -> None:
        """Met à jour le label de statut"""
        if not self._status_label:
            return
        
        if not self.bot_handler.is_available():
            self._status_label.text = '⚠️ Bibliothèque manquante'
            self._status_label.classes('text-orange-500', remove='text-green-500 text-red-500 text-gray-500')
        elif not self.config.is_configured():
            self._status_label.text = '⚙️ Non configuré'
            self._status_label.classes('text-gray-500', remove='text-green-500 text-red-500 text-orange-500')
        elif is_telegram_running():
            self._status_label.text = '🟢 Connecté'
            self._status_label.classes('text-green-500', remove='text-gray-500 text-red-500 text-orange-500')
        else:
            self._status_label.text = '🔴 Déconnecté'
            self._status_label.classes('text-red-500', remove='text-green-500 text-gray-500 text-orange-500')
    
    def _update_button_state(self) -> None:
        """Met à jour le bouton démarrer/arrêter"""
        if not self._start_stop_button:
            return
        
        if is_telegram_running():
            self._start_stop_button.text = '🛑 Arrêter le bot'
            self._start_stop_button.classes('bg-red-500', remove='bg-green-500')
        else:
            self._start_stop_button.text = '🚀 Démarrer le bot'
            self._start_stop_button.classes('bg-green-500', remove='bg-red-500')
    
    def refresh(self) -> None:
        """Rafraîchit l'interface avec les valeurs actuelles"""
        self.config.reload()
        
        if self._enabled_switch:
            self._enabled_switch.value = self.config.enabled
        if self._auto_start_switch:
            self._auto_start_switch.value = self.config.auto_start
        if self._token_input:
            self._token_input.value = self.config.bot_token
        if self._voice_input_switch:
            self._voice_input_switch.value = self.config.voice_input_enabled
        if self._voice_output_switch:
            self._voice_output_switch.value = self.config.voice_output_enabled
        if self._image_input_switch:
            self._image_input_switch.value = self.config.image_input_enabled
        if self._image_output_switch:
            self._image_output_switch.value = self.config.image_output_enabled
        if self._allowed_users_input:
            self._allowed_users_input.value = ', '.join(map(str, self.config.allowed_user_ids))
        
        self._update_status_label()
        self._update_button_state()


# Singleton
_ui_instance: Optional[TelegramConnectorUI] = None

def get_telegram_ui() -> TelegramConnectorUI:
    """Retourne l'instance singleton de l'UI"""
    global _ui_instance
    if _ui_instance is None:
        _ui_instance = TelegramConnectorUI()
    return _ui_instance
