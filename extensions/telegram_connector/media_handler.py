"""
OGMA Telegram Connector - Media Handler
Gestion des images et audio entre Telegram et OGMA
"""

import asyncio
import base64
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Callable, Any
from datetime import datetime

# Chemins OGMA
OGMA_ROOT = Path(__file__).parent.parent.parent
UPLOADS_DIR = OGMA_ROOT / "data" / "uploads"
GENERATED_DIR = OGMA_ROOT / "static" / "generated"


class TelegramMediaHandler:
    """Gestionnaire des médias Telegram <-> OGMA"""
    
    def __init__(self):
        self._audio_manager = None
        self._stt_callback: Optional[Callable] = None
        self._tts_callback: Optional[Callable] = None
        
        # Créer les dossiers si nécessaires
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        print("[TELEGRAM-MEDIA] ✅ Gestionnaire médias initialisé")
    
    def set_audio_manager(self, audio_manager) -> None:
        """Configure le gestionnaire audio OGMA"""
        self._audio_manager = audio_manager
        print("[TELEGRAM-MEDIA] ✅ Audio manager connecté")
    
    def set_stt_callback(self, callback: Callable) -> None:
        """Configure le callback de transcription (STT)"""
        self._stt_callback = callback
    
    def set_tts_callback(self, callback: Callable) -> None:
        """Configure le callback de synthèse vocale (TTS)"""
        self._tts_callback = callback
    
    # === IMAGES ===
    
    async def download_telegram_image(self, bot, file_id: str) -> Optional[Tuple[str, bytes]]:
        """
        Télécharge une image depuis Telegram
        
        Returns:
            (file_path, image_bytes) ou None si erreur
        """
        try:
            # Récupérer le fichier via l'API Telegram
            file = await bot.get_file(file_id)
            file_path = file.file_path
            
            # Télécharger les bytes
            file_bytes = await file.download_as_bytearray()
            
            # Sauvegarder localement
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"telegram_{timestamp}.jpg"
            local_path = UPLOADS_DIR / local_filename
            
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            print(f"[TELEGRAM-MEDIA] 📷 Image téléchargée: {local_path}")
            return str(local_path), bytes(file_bytes)
            
        except Exception as e:
            print(f"[TELEGRAM-MEDIA] ❌ Erreur téléchargement image: {e}")
            return None
    
    def image_to_base64(self, image_bytes: bytes) -> str:
        """Convertit des bytes image en base64 pour l'API vision"""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def get_generated_image_path(self, filename: str) -> Optional[Path]:
        """Récupère le chemin d'une image générée par OGMA"""
        image_path = GENERATED_DIR / filename
        if image_path.exists():
            return image_path
        return None
    
    def find_latest_generated_image(self) -> Optional[Path]:
        """Trouve la dernière image générée par OGMA"""
        try:
            if not GENERATED_DIR.exists():
                return None
            
            images = list(GENERATED_DIR.glob("*.png")) + list(GENERATED_DIR.glob("*.jpg"))
            if not images:
                return None
            
            # Trier par date de modification, plus récent en premier
            images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return images[0]
            
        except Exception as e:
            print(f"[TELEGRAM-MEDIA] ⚠️ Erreur recherche image: {e}")
            return None
    
    def extract_image_from_response(self, response: str) -> Optional[str]:
        """
        Extrait le nom de fichier d'une image depuis une réponse OGMA
        Cherche les patterns: <img src="/generated/xxx.png"...>
        """
        import re
        
        # Pattern pour extraire le fichier image
        patterns = [
            r'<img\s+src="[^"]*?/generated/([^"]+)"',
            r'!\[.*?\]\([^)]*?/generated/([^)]+)\)',
            r'/generated/([a-zA-Z0-9_\-]+\.(?:png|jpg|jpeg|webp))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                filename = match.group(1)
                print(f"[TELEGRAM-MEDIA] 🎨 Image détectée dans réponse: {filename}")
                return filename
        
        return None
    
    # === AUDIO ===
    
    async def download_telegram_voice(self, bot, file_id: str) -> Optional[str]:
        """
        Télécharge un message vocal depuis Telegram
        
        Returns:
            Chemin du fichier .ogg local ou None
        """
        try:
            file = await bot.get_file(file_id)
            file_bytes = await file.download_as_bytearray()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"telegram_voice_{timestamp}.ogg"
            local_path = UPLOADS_DIR / local_filename
            
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            print(f"[TELEGRAM-MEDIA] 🎤 Vocal téléchargé: {local_path}")
            return str(local_path)
            
        except Exception as e:
            print(f"[TELEGRAM-MEDIA] ❌ Erreur téléchargement vocal: {e}")
            return None
    
    async def transcribe_voice(self, audio_path: str) -> Optional[str]:
        """
        Transcrit un fichier audio en texte via le STT d'OGMA
        
        Returns:
            Texte transcrit ou None
        """
        try:
            if self._stt_callback:
                # Utiliser le callback STT configuré
                text = await asyncio.to_thread(self._stt_callback, audio_path)
                if text:
                    print(f"[TELEGRAM-MEDIA] 📝 Transcription: {text[:50]}...")
                    return text
            
            # Fallback: essayer d'utiliser audio_manager directement
            if self._audio_manager:
                try:
                    text = self._audio_manager.transcribe(audio_path)
                    if text:
                        print(f"[TELEGRAM-MEDIA] 📝 Transcription (fallback): {text[:50]}...")
                        return text
                except Exception as e:
                    print(f"[TELEGRAM-MEDIA] ⚠️ Fallback STT échoué: {e}")
            
            print("[TELEGRAM-MEDIA] ⚠️ Aucun moteur STT disponible")
            return None
            
        except Exception as e:
            print(f"[TELEGRAM-MEDIA] ❌ Erreur transcription: {e}")
            return None
    
    async def generate_voice_response(self, text: str) -> Optional[str]:
        """
        Génère un fichier audio à partir de texte via le TTS d'OGMA
        
        Returns:
            Chemin du fichier audio ou None
        """
        try:
            if not text or len(text.strip()) < 2:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(UPLOADS_DIR / f"tts_response_{timestamp}.ogg")
            
            if self._tts_callback:
                # Utiliser le callback TTS configuré
                result = await asyncio.to_thread(self._tts_callback, text, output_path)
                if result and Path(output_path).exists():
                    print(f"[TELEGRAM-MEDIA] 🔊 TTS généré: {output_path}")
                    return output_path
            
            # Fallback: utiliser audio_manager
            if self._audio_manager:
                try:
                    # Générer en MP3 puis convertir si nécessaire
                    mp3_path = str(UPLOADS_DIR / f"tts_response_{timestamp}.mp3")
                    self._audio_manager.speak(text, save_path=mp3_path)
                    if Path(mp3_path).exists():
                        # Telegram accepte mp3 et ogg
                        print(f"[TELEGRAM-MEDIA] 🔊 TTS généré (fallback): {mp3_path}")
                        return mp3_path
                except Exception as e:
                    print(f"[TELEGRAM-MEDIA] ⚠️ Fallback TTS échoué: {e}")
            
            print("[TELEGRAM-MEDIA] ⚠️ Aucun moteur TTS disponible")
            return None
            
        except Exception as e:
            print(f"[TELEGRAM-MEDIA] ❌ Erreur génération TTS: {e}")
            return None
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Nettoie les fichiers temporaires anciens
        
        Returns:
            Nombre de fichiers supprimés
        """
        try:
            now = datetime.now()
            deleted = 0
            
            for file_path in UPLOADS_DIR.glob("telegram_*"):
                try:
                    age = now.timestamp() - file_path.stat().st_mtime
                    if age > max_age_hours * 3600:
                        file_path.unlink()
                        deleted += 1
                except:
                    pass
            
            if deleted > 0:
                print(f"[TELEGRAM-MEDIA] 🧹 {deleted} fichiers temporaires nettoyés")
            
            return deleted
            
        except Exception as e:
            print(f"[TELEGRAM-MEDIA] ⚠️ Erreur nettoyage: {e}")
            return 0


# Singleton
_media_handler: Optional[TelegramMediaHandler] = None

def get_media_handler() -> TelegramMediaHandler:
    """Retourne l'instance singleton du gestionnaire média"""
    global _media_handler
    if _media_handler is None:
        _media_handler = TelegramMediaHandler()
    return _media_handler
