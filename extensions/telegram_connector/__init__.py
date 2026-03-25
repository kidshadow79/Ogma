"""
OGMA Telegram Connector Extension
================================

Extension permettant de communiquer avec OGMA via Telegram.
Supporte: texte, images, messages vocaux.

Usage:
------
from extensions.telegram_connector import (
    initialize_telegram_connector,
    start_telegram_bot,
    stop_telegram_bot,
    is_telegram_running,
    send_telegram_notification,
)

# Initialisation avec les contrôleurs OGMA
success = initialize_telegram_connector(
    chat_controller=chat_controller,
    archiviste_controller=archiviste_controller,
    memory_manager=memory_manager,
    settings_manager=settings_manager,
    audio_manager=audio_manager,
)

# Démarrer le bot (mode polling)
await start_telegram_bot()

# Envoyer une notification (ex: quand OGMA rêve)
await send_telegram_notification("🌙 OGMA a fait un rêve...")

# Arrêter le bot
await stop_telegram_bot()
"""

from typing import Optional, Dict, Any

# Imports des composants
from .config import TelegramConfig, get_telegram_config
from .bot_handler import TelegramBotHandler, get_bot_handler
from .message_bridge import TelegramMessageBridge, get_message_bridge
from .media_handler import TelegramMediaHandler, get_media_handler

# État global
_initialized = False
_config: Optional[TelegramConfig] = None
_bot_handler: Optional[TelegramBotHandler] = None
_bridge: Optional[TelegramMessageBridge] = None


def initialize_telegram_connector(
    chat_controller=None,
    archiviste_controller=None,
    memory_manager=None,
    settings_manager=None,
    audio_manager=None,
    text2img_manager=None,
    web_navigator=None,
) -> bool:
    """
    Initialise le connecteur Telegram avec les composants OGMA.
    
    Args:
        chat_controller: Contrôleur de chat OGMA (AIController)
        archiviste_controller: Contrôleur Archiviste (AIController)
        memory_manager: Gestionnaire de mémoire (MemoryManager)
        settings_manager: Gestionnaire de paramètres (SettingsManager)
        audio_manager: Gestionnaire audio (AudioManager)
        text2img_manager: Gestionnaire de génération d'images (Text2ImgManager)
        web_navigator: Instance du Web Navigator pour recherches internet
        
    Returns:
        True si l'initialisation a réussi
    """
    global _initialized, _config, _bot_handler, _bridge
    
    try:
        print("[TELEGRAM-CONNECTOR] 🚀 Initialisation de l'extension...")
        
        # Récupérer les singletons
        _config = get_telegram_config()
        _bot_handler = get_bot_handler()
        _bridge = get_message_bridge()
        media_handler = get_media_handler()
        
        # Vérifier si la bibliothèque est disponible
        if not _bot_handler.is_available():
            print("[TELEGRAM-CONNECTOR] ⚠️ python-telegram-bot non installé")
            print("[TELEGRAM-CONNECTOR] 💡 Exécute: pip install python-telegram-bot")
            return False
        
        # Connecter les contrôleurs OGMA au bridge
        if chat_controller:
            _bridge.set_chat_controller(chat_controller)
        
        if archiviste_controller:
            _bridge.set_archiviste_controller(archiviste_controller)
        
        if memory_manager:
            _bridge.set_memory_manager(memory_manager)
        
        if settings_manager:
            _bridge.set_settings_manager(settings_manager)
        
        if audio_manager:
            _bridge.set_audio_manager(audio_manager)
            media_handler.set_audio_manager(audio_manager)
        
        if text2img_manager:
            _bridge.set_text2img_manager(text2img_manager)
        
        if web_navigator:
            _bridge.set_web_navigator(web_navigator)
        
        _initialized = True
        print("[TELEGRAM-CONNECTOR] ✅ Extension initialisée")
        
        # Démarrage automatique si configuré
        if _config.auto_start and _config.is_configured():
            print("[TELEGRAM-CONNECTOR] 🤖 Démarrage automatique activé")
            # Le démarrage sera fait par l'appelant avec start_telegram_bot()
        
        return True
        
    except Exception as e:
        print(f"[TELEGRAM-CONNECTOR] ❌ Erreur initialisation: {e}")
        return False


async def start_telegram_bot() -> bool:
    """
    Démarre le bot Telegram en mode polling.
    
    Returns:
        True si le bot a démarré avec succès
    """
    global _bot_handler
    
    if not _initialized:
        print("[TELEGRAM-CONNECTOR] ⚠️ Extension non initialisée")
        return False
    
    if not _bot_handler:
        _bot_handler = get_bot_handler()
    
    return await _bot_handler.start()


async def stop_telegram_bot() -> None:
    """Arrête le bot Telegram."""
    global _bot_handler
    
    if _bot_handler:
        await _bot_handler.stop()


def is_telegram_available() -> bool:
    """Vérifie si python-telegram-bot est installé."""
    handler = get_bot_handler()
    return handler.is_available()


def is_telegram_configured() -> bool:
    """Vérifie si le token Telegram est configuré."""
    config = get_telegram_config()
    return config.is_configured()


def is_telegram_running() -> bool:
    """Vérifie si le bot Telegram est en cours d'exécution."""
    handler = get_bot_handler()
    return handler.is_running()


def is_telegram_enabled() -> bool:
    """Vérifie si l'extension est activée dans les paramètres."""
    config = get_telegram_config()
    return config.enabled


async def send_telegram_notification(
    text: str, 
    image_path: Optional[str] = None
) -> bool:
    """
    Envoie une notification à tous les utilisateurs autorisés.
    
    Args:
        text: Le texte de la notification
        image_path: Chemin optionnel vers une image à joindre
        
    Returns:
        True si la notification a été envoyée
    """
    handler = get_bot_handler()
    return await handler.send_notification(text, image_path)


def get_telegram_status() -> Dict[str, Any]:
    """
    Retourne l'état complet du connecteur Telegram.
    
    Returns:
        Dictionnaire avec l'état du bot, bridge, config, etc.
    """
    config = get_telegram_config()
    handler = get_bot_handler()
    bridge = get_message_bridge()
    
    return {
        "initialized": _initialized,
        "available": handler.is_available(),
        "configured": config.is_configured(),
        "enabled": config.enabled,
        "running": handler.is_running(),
        "auto_start": config.auto_start,
        "bridge_status": bridge.get_status(),
        "allowed_users": len(config.allowed_user_ids),
    }


def get_config() -> TelegramConfig:
    """Retourne l'instance de configuration."""
    return get_telegram_config()


def save_config() -> bool:
    """Sauvegarde la configuration actuelle."""
    config = get_telegram_config()
    return config.save_config()


def cleanup():
    """Nettoyage propre de l'extension telegram_connector."""
    global _initialized, _config, _bot_handler, _bridge
    
    # Arreter le bot s'il tourne (appel synchrone safe)
    if _bot_handler:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(stop_telegram_bot())
            else:
                loop.run_until_complete(stop_telegram_bot())
        except Exception as e:
            print(f"[TELEGRAM-CONNECTOR] Erreur arret bot: {e}")
    
    # Reset singletons sous-modules
    try:
        from . import bot_handler as _bh_mod
        from . import message_bridge as _mb_mod
        from . import config as _cfg_mod
        from . import media_handler as _mh_mod
        if hasattr(_bh_mod, '_bot_handler'):
            _bh_mod._bot_handler = None
        if hasattr(_mb_mod, '_bridge_instance'):
            _mb_mod._bridge_instance = None
        if hasattr(_cfg_mod, '_config_instance'):
            _cfg_mod._config_instance = None
        if hasattr(_mh_mod, '_media_handler'):
            _mh_mod._media_handler = None
    except Exception as e:
        print(f"[TELEGRAM-CONNECTOR] Erreur reset sous-modules: {e}")
    
    _config = None
    _bot_handler = None
    _bridge = None
    _initialized = False
    print("[TELEGRAM-CONNECTOR] Cleanup effectue")


# API publique
__all__ = [
    # Fonctions principales
    'initialize_telegram_connector',
    'start_telegram_bot',
    'stop_telegram_bot',
    'send_telegram_notification',
    'cleanup',
    
    # Vérifications d'état
    'is_telegram_available',
    'is_telegram_configured',
    'is_telegram_running',
    'is_telegram_enabled',
    'get_telegram_status',
    
    # Configuration
    'get_config',
    'save_config',
    
    # Classes (pour usage avancé)
    'TelegramConfig',
    'TelegramBotHandler',
    'TelegramMessageBridge',
    'TelegramMediaHandler',
]
