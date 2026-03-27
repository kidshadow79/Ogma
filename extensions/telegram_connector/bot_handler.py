"""
OGMA Telegram Connector - Bot Handler
Gestion du bot Telegram avec polling
"""
from __future__ import annotations

import asyncio
from typing import Optional, Callable
from pathlib import Path
import traceback

# Import conditionnel de python-telegram-bot
try:
    from telegram import Update, Bot
    from telegram.ext import (
        Application, 
        CommandHandler, 
        MessageHandler, 
        filters,
        ContextTypes
    )
    from telegram.constants import ChatAction, ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("[TELEGRAM-BOT] ⚠️ python-telegram-bot non installé. Exécute: pip install python-telegram-bot")

from .config import get_telegram_config
from .message_bridge import get_message_bridge
from .media_handler import get_media_handler


class TelegramBotHandler:
    """
    Gestionnaire du bot Telegram utilisant le mode polling.
    Pas besoin de webhook ni de tunnel - fonctionne derrière un NAT.
    """
    
    def __init__(self):
        self.config = get_telegram_config()
        self.bridge = get_message_bridge()
        self.media_handler = get_media_handler()
        
        self._application: Optional[Application] = None
        self._bot: Optional[Bot] = None
        self._is_running = False
        self._is_starting = False  # Verrou pour éviter démarrages concurrents
        self._polling_task: Optional[asyncio.Task] = None
        
        # Callbacks pour notifications
        self._on_start_callback: Optional[Callable] = None
        self._on_stop_callback: Optional[Callable] = None
        self._on_error_callback: Optional[Callable] = None
        
        print("[TELEGRAM-BOT] ✅ Handler initialisé")
    
    def is_available(self) -> bool:
        """Vérifie si la bibliothèque Telegram est disponible"""
        return TELEGRAM_AVAILABLE
    
    def is_configured(self) -> bool:
        """Vérifie si le bot est configuré (token présent)"""
        return self.config.is_configured()
    
    def is_running(self) -> bool:
        """Vérifie si le bot est en cours d'exécution"""
        return self._is_running
    
    async def start(self) -> bool:
        """
        Démarre le bot Telegram en mode polling.
        
        Returns:
            True si démarré avec succès
        """
        if not TELEGRAM_AVAILABLE:
            print("[TELEGRAM-BOT] ❌ python-telegram-bot non disponible")
            return False
        
        if not self.config.is_configured():
            print("[TELEGRAM-BOT] ❌ Token non configuré")
            return False
        
        if self._is_running:
            print("[TELEGRAM-BOT] ⚠️ Déjà en cours d'exécution")
            return True
        
        if self._is_starting:
            print("[TELEGRAM-BOT] ⚠️ Démarrage déjà en cours...")
            return False
        
        self._is_starting = True
        
        try:
            print("[TELEGRAM-BOT] 🚀 Démarrage du bot...")
            
            # Créer l'application Telegram
            self._application = (
                Application.builder()
                .token(self.config.bot_token)
                .build()
            )
            
            # Enregistrer les handlers AVANT initialize
            self._register_handlers()
            
            # Initialiser l'application (requis par v20+)
            await self._application.initialize()
            
            # Récupérer le bot après initialisation
            self._bot = self._application.bot
            
            # Récupérer les infos du bot
            bot_info = await self._bot.get_me()
            print(f"[TELEGRAM-BOT] ✅ Bot connecté: @{bot_info.username}")
            
            # Démarrer l'application
            await self._application.start()
            
            # Démarrer le polling en arrière-plan
            self._polling_task = asyncio.create_task(self._run_polling())
            
            self._is_running = True
            self._is_starting = False
            
            print(f"[TELEGRAM-BOT] ✅ Bot démarré: @{bot_info.username}")
            
            if self._on_start_callback:
                self._on_start_callback()
            
            return True
            
        except Exception as e:
            print(f"[TELEGRAM-BOT] ❌ Erreur démarrage: {e}")
            traceback.print_exc()
            self._is_running = False
            self._is_starting = False
            self._application = None
            self._bot = None
            
            if self._on_error_callback:
                self._on_error_callback(str(e))
            
            return False
    
    async def stop(self) -> None:
        """Arrête le bot Telegram"""
        if not self._is_running:
            return
        
        self._is_running = False  # Marquer comme arrêté immédiatement
        
        try:
            print("[TELEGRAM-BOT] 🛑 Arrêt du bot...")
            
            # Annuler la tâche de polling d'abord
            if self._polling_task:
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass
            
            if self._application:
                # Arrêter le updater d'abord
                if self._application.updater and self._application.updater.running:
                    await self._application.updater.stop()
                
                # Puis l'application
                if self._application.running:
                    await self._application.stop()
                
                # Enfin shutdown
                await self._application.shutdown()
            
            self._application = None
            self._bot = None
            self._polling_task = None
            
            print("[TELEGRAM-BOT] ✅ Bot arrêté")
            
            if self._on_stop_callback:
                self._on_stop_callback()
                
        except Exception as e:
            print(f"[TELEGRAM-BOT] ⚠️ Erreur arrêt: {e}")
            # Nettoyer quand même
            self._application = None
            self._bot = None
            self._polling_task = None
    
    async def _run_polling(self) -> None:
        """Exécute le polling en continu"""
        try:
            # Lancer le polling (non-bloquant)
            await self._application.updater.start_polling(
                poll_interval=self.config.polling_interval,
                drop_pending_updates=True  # Ignorer les messages en attente au démarrage
            )
            
            # Garder le polling actif jusqu'à annulation
            while self._is_running:
                await asyncio.sleep(1)
            
            # Arrêter le polling proprement
            if self._application and self._application.updater and self._application.updater.running:
                await self._application.updater.stop()
                
        except asyncio.CancelledError:
            print("[TELEGRAM-BOT] 🛑 Polling annulé")
            # Arrêter proprement si annulé
            if self._application and self._application.updater and self._application.updater.running:
                try:
                    await self._application.updater.stop()
                except:
                    pass
        except Exception as e:
            print(f"[TELEGRAM-BOT] ❌ Erreur polling: {e}")
            self._is_running = False
    
    def _register_handlers(self) -> None:
        """Enregistre les handlers de messages"""
        if not self._application:
            return
        
        # Commandes
        self._application.add_handler(CommandHandler("start", self._handle_start))
        self._application.add_handler(CommandHandler("help", self._handle_help))
        self._application.add_handler(CommandHandler("status", self._handle_status))
        self._application.add_handler(CommandHandler("clear", self._handle_clear))
        self._application.add_handler(CommandHandler("memory", self._handle_memory))
        
        # Messages texte
        self._application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_text_message
        ))
        
        # Photos
        self._application.add_handler(MessageHandler(
            filters.PHOTO,
            self._handle_photo_message
        ))
        
        # Messages vocaux
        self._application.add_handler(MessageHandler(
            filters.VOICE | filters.AUDIO,
            self._handle_voice_message
        ))
        
        # Documents (fichiers)
        self._application.add_handler(MessageHandler(
            filters.Document.ALL,
            self._handle_document
        ))
        
        print("[TELEGRAM-BOT] ✅ Handlers enregistrés")
    
    # === Handlers de commandes ===
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /start"""
        user = update.effective_user
        user_id = user.id
        
        # Ajouter l'utilisateur aux autorisés si c'est le premier
        if not self.config.allowed_user_ids:
            self.config.add_allowed_user(user_id)
            await update.message.reply_text(
                f"🌟 Bienvenue {user.first_name} !\n\n"
                f"Tu es maintenant connecté(e) à OGMA via Telegram.\n"
                f"Ton ID ({user_id}) a été enregistré comme utilisateur autorisé.\n\n"
                f"Tu peux me parler normalement, m'envoyer des images ou des vocaux !\n\n"
                f"Tape /help pour voir les commandes disponibles."
            )
        elif not self.config.is_user_allowed(user_id):
            await update.message.reply_text(
                "⛔ Désolé, tu n'es pas autorisé(e) à utiliser ce bot.\n"
                "Contacte l'administrateur pour être ajouté(e)."
            )
        else:
            await update.message.reply_text(
                f"👋 Re-bonjour {user.first_name} !\n\n"
                f"OGMA est prêt à discuter. Envoie-moi un message !"
            )
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /help"""
        if not self._check_user_allowed(update):
            return
        
        help_text = """🤖 *OGMA Telegram Connector*

*Commandes disponibles:*
/start - Démarrer la conversation
/help - Afficher cette aide
/status - Voir l'état d'OGMA
/clear - Effacer l'historique de conversation
/memory - Voir les souvenirs récents

*Fonctionnalités:*
📝 Envoie un message texte pour discuter
📷 Envoie une photo pour que je l'analyse
🎤 Envoie un vocal pour parler
📎 Envoie un fichier pour le traiter

*Notes:*
- Les images que je génère sont envoyées automatiquement
- Je peux répondre par vocal si tu m'envoies un vocal
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /status"""
        if not self._check_user_allowed(update):
            return
        
        status = self.bridge.get_status()
        
        status_text = f"""📊 *État OGMA*

🟢 Bot Telegram: Actif
{"🟢" if status["chat_controller_ready"] else "🔴"} Chat Controller: {"Prêt" if status["chat_controller_ready"] else "Non connecté"}
{"🟢" if status["memory_manager_ready"] else "🔴"} Memory Manager: {"Prêt" if status["memory_manager_ready"] else "Non connecté"}
💬 Historique: {status["history_length"]} messages
{"⏳" if status["is_processing"] else "✅"} État: {"En traitement..." if status["is_processing"] else "Disponible"}
"""
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /clear"""
        if not self._check_user_allowed(update):
            return
        
        self.bridge.clear_history()
        await update.message.reply_text("🧹 Historique de conversation effacé !")
    
    async def _handle_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /memory"""
        if not self._check_user_allowed(update):
            return
        
        # TODO: Implémenter l'affichage des souvenirs récents
        await update.message.reply_text(
            "🧠 Fonctionnalité en cours de développement.\n"
            "Tu peux me demander de me souvenir de quelque chose dans la conversation !"
        )
    
    # === Handlers de messages ===
    
    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour les messages texte"""
        if not self._check_user_allowed(update):
            return
        
        user = update.effective_user
        text = update.message.text
        
        # Indicateur de frappe
        if self.config.send_typing_indicator:
            await update.message.chat.send_action(ChatAction.TYPING)
        
        # Traiter le message
        response, image_path = await self.bridge.process_text_message(
            text=text,
            user_id=user.id,
            username=user.first_name or user.username or "User"
        )
        
        # Envoyer la réponse
        await self._send_response(update, response, image_path)
    
    async def _handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour les photos"""
        if not self._check_user_allowed(update):
            return
        
        if not self.config.image_input_enabled:
            await update.message.reply_text("📷 La réception d'images est désactivée.")
            return
        
        user = update.effective_user
        photo = update.message.photo[-1]  # Prendre la meilleure résolution
        caption = update.message.caption
        
        # Indicateur de traitement
        await update.message.chat.send_action(ChatAction.TYPING)
        
        # Télécharger l'image
        result = await self.media_handler.download_telegram_image(self._bot, photo.file_id)
        
        if not result:
            await update.message.reply_text("❌ Impossible de télécharger l'image.")
            return
        
        file_path, image_bytes = result
        
        # Traiter l'image
        response, response_image_path = await self.bridge.process_image_message(
            image_bytes=image_bytes,
            caption=caption,
            user_id=user.id,
            username=user.first_name or "User"
        )
        
        # Envoyer la réponse
        await self._send_response(update, response, response_image_path)
    
    async def _handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour les messages vocaux"""
        if not self._check_user_allowed(update):
            return
        
        if not self.config.voice_input_enabled:
            await update.message.reply_text("🎤 La réception de vocaux est désactivée.")
            return
        
        user = update.effective_user
        voice = update.message.voice or update.message.audio
        
        # Indicateur d'enregistrement vocal
        await update.message.chat.send_action(ChatAction.RECORD_VOICE)
        
        # Télécharger le vocal
        audio_path = await self.media_handler.download_telegram_voice(self._bot, voice.file_id)
        
        if not audio_path:
            await update.message.reply_text("❌ Impossible de télécharger le message vocal.")
            return
        
        # Traiter le vocal
        response, image_path, voice_path = await self.bridge.process_voice_message(
            audio_path=audio_path,
            user_id=user.id,
            username=user.first_name or "User"
        )
        
        # Envoyer la réponse (texte + éventuellement vocal)
        await self._send_response(update, response, image_path, voice_path)
    
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour les documents/fichiers"""
        if not self._check_user_allowed(update):
            return
        
        document = update.message.document
        filename = document.file_name or "fichier"
        
        # TODO: Implémenter le traitement des fichiers via file_processor
        await update.message.reply_text(
            f"📎 J'ai reçu le fichier *{filename}*.\n"
            f"Le traitement des fichiers via Telegram sera bientôt disponible !",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # === Méthodes utilitaires ===
    
    def _check_user_allowed(self, update: Update) -> bool:
        """Vérifie si l'utilisateur est autorisé"""
        user_id = update.effective_user.id
        
        if not self.config.is_user_allowed(user_id):
            asyncio.create_task(update.message.reply_text(
                "⛔ Tu n'es pas autorisé(e) à utiliser ce bot."
            ))
            return False
        return True
    
    async def _send_response(
        self, 
        update: Update, 
        text: str, 
        image_path: Optional[str] = None,
        voice_path: Optional[str] = None
    ) -> None:
        """Envoie une réponse (texte + optionnellement image/vocal)"""
        try:
            # Envoyer le texte
            if text:
                # Découper si trop long
                max_len = self.config.max_message_length
                if len(text) <= max_len:
                    await update.message.reply_text(text)
                else:
                    # Découper en plusieurs messages
                    for i in range(0, len(text), max_len):
                        chunk = text[i:i+max_len]
                        await update.message.reply_text(chunk)
                        await asyncio.sleep(0.2)  # Éviter le rate limit
            
            # Envoyer l'image si présente
            if image_path and self.config.image_output_enabled:
                image_file = Path(image_path)
                if image_file.exists():
                    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
                    with open(image_file, 'rb') as f:
                        await update.message.reply_photo(f, caption="🎨 Image générée par OGMA")
            
            # Envoyer le vocal si présent
            if voice_path and self.config.voice_output_enabled:
                voice_file = Path(voice_path)
                if voice_file.exists():
                    await update.message.chat.send_action(ChatAction.RECORD_VOICE)
                    with open(voice_file, 'rb') as f:
                        await update.message.reply_voice(f)
                        
        except Exception as e:
            print(f"[TELEGRAM-BOT] ❌ Erreur envoi réponse: {e}")
            try:
                await update.message.reply_text(f"⚠️ Erreur d'envoi: {str(e)[:100]}")
            except:
                pass
    
    async def send_notification(self, text: str, image_path: Optional[str] = None) -> bool:
        """
        Envoie une notification à tous les utilisateurs autorisés.
        Utilisé pour les événements comme les rêves d'OGMA.
        """
        if not self._is_running or not self._bot:
            return False
        
        try:
            for user_id in self.config.allowed_user_ids:
                try:
                    await self._bot.send_message(chat_id=user_id, text=text)
                    
                    if image_path:
                        image_file = Path(image_path)
                        if image_file.exists():
                            with open(image_file, 'rb') as f:
                                await self._bot.send_photo(chat_id=user_id, photo=f)
                                
                except Exception as e:
                    print(f"[TELEGRAM-BOT] ⚠️ Échec notification user {user_id}: {e}")
            
            return True
            
        except Exception as e:
            print(f"[TELEGRAM-BOT] ❌ Erreur notification: {e}")
            return False
    
    def set_callbacks(
        self,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> None:
        """Configure les callbacks d'événements"""
        self._on_start_callback = on_start
        self._on_stop_callback = on_stop
        self._on_error_callback = on_error


# Singleton
_bot_handler: Optional[TelegramBotHandler] = None

def get_bot_handler() -> TelegramBotHandler:
    """Retourne l'instance singleton du bot handler"""
    global _bot_handler
    if _bot_handler is None:
        _bot_handler = TelegramBotHandler()
    return _bot_handler
