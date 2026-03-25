"""
OGMA Telegram Connector - Configuration
Gestion des paramètres de l'extension Telegram
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Chemin vers settings.json
SETTINGS_PATH = Path(__file__).parent.parent.parent / "data" / "settings.json"


class TelegramConfig:
    """Gestionnaire de configuration pour le connecteur Telegram"""
    
    DEFAULT_CONFIG = {
        "enabled": False,
        "bot_token": "",
        "allowed_user_ids": [],  # Liste des user IDs Telegram autorisés (sécurité)
        "auto_start": False,  # Démarrer le bot avec OGMA
        "polling_interval": 1.0,  # Secondes entre chaque poll
        "max_message_length": 4000,  # Limite Telegram = 4096
        "send_typing_indicator": True,  # Afficher "en train d'écrire..."
        "voice_input_enabled": True,  # Transcrire les vocaux reçus
        "voice_output_enabled": True,  # Envoyer des vocaux en réponse
        "image_input_enabled": True,  # Recevoir des images
        "image_output_enabled": True,  # Envoyer des images générées
        "streaming_edit": False,  # Éditer le message pendant la génération
        "streaming_edit_interval": 500,  # ms entre chaque mise à jour
        "notification_on_dream": True,  # Notifier quand OGMA rêve
        "log_conversations": True,  # Enregistrer dans l'historique OGMA
    }
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Charge la configuration depuis settings.json"""
        try:
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    telegram_settings = settings.get('telegram_connector', {})
                    # Fusionner avec les valeurs par défaut
                    self._config = {**self.DEFAULT_CONFIG, **telegram_settings}
            else:
                self._config = self.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"[TELEGRAM-CONFIG] ⚠️ Erreur chargement config: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """Sauvegarde la configuration dans settings.json"""
        try:
            settings = {}
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            settings['telegram_connector'] = self._config
            
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            print("[TELEGRAM-CONFIG] ✅ Configuration sauvegardée")
            return True
        except Exception as e:
            print(f"[TELEGRAM-CONFIG] ❌ Erreur sauvegarde: {e}")
            return False
    
    def reload(self) -> None:
        """Recharge la configuration depuis le fichier"""
        self._load_config()
    
    # === Propriétés d'accès ===
    
    @property
    def enabled(self) -> bool:
        return self._config.get('enabled', False)
    
    @enabled.setter
    def enabled(self, value: bool):
        self._config['enabled'] = value
    
    @property
    def bot_token(self) -> str:
        return self._config.get('bot_token', '')
    
    @bot_token.setter
    def bot_token(self, value: str):
        self._config['bot_token'] = value
    
    @property
    def allowed_user_ids(self) -> list:
        return self._config.get('allowed_user_ids', [])
    
    @allowed_user_ids.setter
    def allowed_user_ids(self, value: list):
        self._config['allowed_user_ids'] = value
    
    @property
    def auto_start(self) -> bool:
        return self._config.get('auto_start', False)
    
    @property
    def polling_interval(self) -> float:
        return self._config.get('polling_interval', 1.0)
    
    @property
    def max_message_length(self) -> int:
        return self._config.get('max_message_length', 4000)
    
    @property
    def send_typing_indicator(self) -> bool:
        return self._config.get('send_typing_indicator', True)
    
    @property
    def voice_input_enabled(self) -> bool:
        return self._config.get('voice_input_enabled', True)
    
    @property
    def voice_output_enabled(self) -> bool:
        return self._config.get('voice_output_enabled', True)
    
    @property
    def image_input_enabled(self) -> bool:
        return self._config.get('image_input_enabled', True)
    
    @property
    def image_output_enabled(self) -> bool:
        return self._config.get('image_output_enabled', True)
    
    @property
    def streaming_edit(self) -> bool:
        return self._config.get('streaming_edit', False)
    
    @property
    def streaming_edit_interval(self) -> int:
        return self._config.get('streaming_edit_interval', 500)
    
    @property
    def notification_on_dream(self) -> bool:
        return self._config.get('notification_on_dream', True)
    
    @property
    def log_conversations(self) -> bool:
        return self._config.get('log_conversations', True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Accès générique à une clé de configuration"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration"""
        self._config[key] = value
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Vérifie si un utilisateur Telegram est autorisé"""
        # Si liste vide, tout le monde est autorisé (premier usage)
        if not self.allowed_user_ids:
            return True
        return user_id in self.allowed_user_ids
    
    def add_allowed_user(self, user_id: int) -> None:
        """Ajoute un utilisateur à la liste autorisée"""
        if user_id not in self._config['allowed_user_ids']:
            self._config['allowed_user_ids'].append(user_id)
            self.save_config()
            print(f"[TELEGRAM-CONFIG] ✅ User {user_id} ajouté aux autorisés")
    
    def is_configured(self) -> bool:
        """Vérifie si le token est configuré"""
        return bool(self.bot_token and len(self.bot_token) > 20)


# Singleton
_config_instance: Optional[TelegramConfig] = None

def get_telegram_config() -> TelegramConfig:
    """Retourne l'instance singleton de la configuration"""
    global _config_instance
    if _config_instance is None:
        _config_instance = TelegramConfig()
    return _config_instance
