"""
audio_manager.py
----------------
Gestionnaire audio pour OGMA v2.0
Speech-to-Text et Text-to-Speech intégrés
"""

import asyncio
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    PYAUDIO_AVAILABLE = False
    print("[AUDIO] pyaudio non disponible - capture micro desactivee (mode minimal)")

import wave
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    sr = None
    SR_AVAILABLE = False
    print("[AUDIO] speech_recognition non disponible - STT local desactive (mode minimal)")

import os
import tempfile
from typing import Optional, Callable, Dict, List
import threading
import queue
import platform
import requests
import json
import io
import re
import unicodedata
import hashlib
from pathlib import Path

# TTS imports
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("[TTS] pyttsx3 non disponible - installez avec: pip install pyttsx3")

try:
    if platform.system() == "Windows":
        import win32com.client
        SAPI_AVAILABLE = True
    else:
        SAPI_AVAILABLE = False
except ImportError:
    SAPI_AVAILABLE = False
    print("[TTS] win32com non disponible - installez avec: pip install pywin32")

# TTS Cloud imports
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("[TTS] Google Cloud TTS non disponible - installez avec: pip install google-cloud-texttospeech")

try:
    import warnings
    import os
    import sys
    # Silencer le warning pkg_resources de pygame
    warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
    # Silencer le message "Hello from the pygame community"
    _devnull = open(os.devnull, 'w')
    _old_stdout = sys.stdout
    sys.stdout = _devnull
    import pygame
    sys.stdout = _old_stdout
    _devnull.close()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("[TTS] pygame non disponible - installez avec: pip install pygame")

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SPEECH_AVAILABLE = True
except ImportError:
    AZURE_SPEECH_AVAILABLE = False
    print("[TTS] Azure Speech SDK non disponible - installez avec: pip install azure-cognitiveservices-speech")

# Nouveaux moteurs TTS locaux
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("[TTS] gTTS non disponible - installez avec: pip install gtts")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("[TTS] Edge TTS non disponible - installez avec: pip install edge-tts")


def clean_text_for_tts(text: str) -> str:
    """
    Nettoie le texte pour la synthèse vocale en supprimant les balises HTML, émojis et caractères problématiques.
    
    Args:
        text: Texte à nettoyer
        
    Returns:
        Texte nettoyé prêt pour la synthèse vocale
    """
    if not text:
        return text
    
    # 1. Supprimer les balises HTML complètes (ex: <img src="..."/>, <em>, </em>, etc.)
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # 2. Supprimer les balises Markdown courantes
    clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_text)  # **bold** -> bold
    clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)      # *italic* -> italic
    clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)        # `code` -> code
    clean_text = re.sub(r'#{1,6}\s*', '', clean_text)           # # headers
    clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)  # [text](url) -> text
    
    # 3. Pattern pour détecter les émojis (plages Unicode principales)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symboles & pictogrammes  
        "\U0001F680-\U0001F6FF"  # transport & cartes
        "\U0001F1E0-\U0001F1FF"  # drapeaux (iOS)
        "\U00002500-\U00002BEF"  # symboles divers
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # variation selector
        "\u3030"
        "]+", flags=re.UNICODE)
    
    # 4. Supprimer les émojis
    clean_text = emoji_pattern.sub('', clean_text)
    
    # 5. Nettoyer les espaces multiples résultants
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Log pour debugging (optionnel)
    if clean_text != text:
        print(f"[TTS] 🧹 Texte nettoyé: '{text[:50]}...' → '{clean_text[:50]}...'")
    
    return clean_text

class AudioManager:
    """
    Gestionnaire audio central pour OGMA.
    
    Fonctionnalités:
    - Speech-to-Text (Whisper local ou API)
    - Text-to-Speech (à implémenter)
    - Enregistrement/lecture audio
    - Détection activité vocale
    """
    
    def __init__(self, use_whisper_api: bool = False, api_key: Optional[str] = None):
        """
        Initialise le gestionnaire audio.
        
        Args:
            use_whisper_api: Utiliser API OpenAI Whisper (True) ou local (False)
            api_key: Clé API OpenAI si use_whisper_api=True
        """
        self.use_whisper_api = use_whisper_api
        self.api_key = api_key
        
        # Configuration audio optimisée pour stabilité
        self.sample_rate = 16000  # 16kHz recommandé pour Whisper
        self.chunk_size = 512     # Plus petit chunk pour moins de latence
        self.channels = 1
        self.format = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
        self.timeout_recording = 8.0  # Timeout très court pour éviter déconnexions
        self.device_index: Optional[int] = None  # None = micro par défaut, sinon index spécifique
        
        # === TTS Configuration ===
        self.tts_engine = None
        self.sapi_voice = None
        self.available_voices: List[Dict] = []
        self.current_voice_id: str = "auto"  # ID de la voix sélectionnée
        self.tts_speed: int = 150  # Vitesse de parole (mots/minute)
        self.tts_volume: float = 0.8  # Volume (0.0 à 1.0)
        
        # Configuration moteurs TTS externes
        self.tts_engine_type: str = "system"  # "system", "google", "elevenlabs", "azure", "gtts", "edge_tts", "fish_audio", "cartesia", "hume_ai"
        self.google_api_key: Optional[str] = None
        self.google_voice: str = "fr-FR-Standard-A"
        self.elevenlabs_api_key: Optional[str] = None
        self.elevenlabs_voice_id: str = "pNInz6obpgDQGcFmaJgB"
        self.elevenlabs_model: str = "eleven_multilingual_v2"  # eleven_multilingual_v2, eleven_turbo_v2_5, eleven_flash_v2_5
        self.elevenlabs_stability: float = 0.5  # 0.0 - 1.0
        self.elevenlabs_similarity: float = 0.75  # 0.0 - 1.0
        self.elevenlabs_style: float = 0.0  # 0.0 - 1.0 (expressivité)
        self.elevenlabs_speed: float = 1.0  # 0.5 - 2.0
        self.elevenlabs_speaker_boost: bool = True
        self.azure_api_key: Optional[str] = None
        self.azure_region: str = "westeurope"
        self.azure_voice: str = "fr-FR-DeniseNeural"
        self.gtts_lang: str = "fr"
        self.edge_tts_voice: str = "fr-FR-DeniseNeural"
        
        # Fish Audio
        self.fish_audio_api_key: Optional[str] = None
        self.fish_audio_voice_id: str = ""   # reference_id du modèle Fish Audio
        self.fish_audio_model: str = "s2-pro"  # s1, s2-pro
        self.fish_audio_latency: str = "normal"  # normal, balanced (~300ms)
        self.fish_audio_chunk_length: int = 200   # 100-300 caractères par chunk
        self.fish_audio_normalize: bool = True     # normalisation du texte
        self.fish_audio_mp3_bitrate: int = 128     # 64, 128, 192
        self.fish_audio_emotion: str = "none"     # none ou tag émotion (happy, sad, calm...)
        
        # Cartesia AI
        self.cartesia_api_key: Optional[str] = None
        self.cartesia_voice_id: str = ""  # Voice ID Cartesia
        self.cartesia_model: str = "sonic-2"  # sonic-2, sonic-3
        self.cartesia_speed: float = 1.0   # 0.6-1.5, sonic-3 uniquement
        self.cartesia_emotion: str = "neutral"  # sonic-3 uniquement
        
        # Hume AI (Octave TTS)
        self.hume_ai_api_key: Optional[str] = None
        self.hume_ai_voice_name: str = ""  # Nom de la voix Hume (Voice Library)
        self.hume_ai_voice_id: str = ""  # ID de voix personnalisée (Voice Design/Cloning)
        self.hume_ai_description: str = ""  # Description pour génération dynamique de voix
        self.hume_ai_version: int = 2  # Version Octave (1 ou 2)
        
        # États TTS
        self.is_speaking: bool = False
        self.tts_enabled: bool = True
        self._stop_requested: bool = False  # Pour contrôle arrêt
        self._current_synthesizer = None    # Pour Azure Speech
        
        # État
        self.is_recording = False
        self.is_listening = False
        self.manual_recording_active = False  # Pour le contrôle manuel
        self.audio_queue = queue.Queue()
        
        # Callbacks
        self.on_transcription_complete: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Initialisation composants
        self.pyaudio_instance = None
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        # Ajuster le seuil de détection pour meilleure sensibilité
        # Valeur par défaut ~300, on réduit à 200 pour micro plus sensible
        if self.recognizer is not None:
            self.recognizer.energy_threshold = 200
            self.recognizer.dynamic_energy_threshold = True
        self.microphone = None
        self._calibrated = False  # Flag pour calibrage unique au démarrage
        
    async def initialize(self) -> bool:
        """Initialise les composants audio."""
        # Mode minimal : pyaudio/SR absents -> capture micro indisponible
        if not PYAUDIO_AVAILABLE or not SR_AVAILABLE:
            print("[AUDIO] Mode degrade : capture micro indisponible (pyaudio/speech_recognition manquants)")
            return False
        try:
            # Initialiser PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Configurer microphone (avec device_index si configuré)
            if self.device_index is not None:
                print(f"[AUDIO] 🎤 Utilisation micro index {self.device_index}")
                self.microphone = sr.Microphone(device_index=self.device_index, sample_rate=self.sample_rate)
            else:
                self.microphone = sr.Microphone(sample_rate=self.sample_rate)
            
            # Calibrer pour le bruit ambiant (une seule fois au démarrage)
            print("[AUDIO] Calibrage microphone...")
            with self.microphone as source:
                # Calibrage plus long et avec seuil plus bas pour meilleure détection
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                # Réduire le seuil après calibrage pour meilleure sensibilité
                self.recognizer.energy_threshold = max(self.recognizer.energy_threshold * 0.7, 200)
                print(f"[AUDIO] 🎚️ Seuil détection: {self.recognizer.energy_threshold:.0f}")
            self._calibrated = True
            
            # Initialiser TTS
            print("[AUDIO] Initialisation TTS...")
            await self.initialize_tts()
            
            print("[AUDIO] ✅ Système audio complet initialisé")
            return True
            
        except Exception as e:
            print(f"[AUDIO] ❌ Erreur initialisation: {e}")
            if self.on_error:
                self.on_error(f"Initialisation audio échoué: {e}")
            return False
    
    async def start_listening(self) -> None:
        """Démarre l'écoute continue en arrière-plan."""
        if self.is_listening:
            print("[AUDIO] Déjà en écoute")
            return
            
        self.is_listening = True
        print("[AUDIO] 🎤 Démarrage écoute continue...")
        
        # Lancer thread d'écoute
        listen_thread = threading.Thread(target=self._listen_thread, daemon=True)
        listen_thread.start()
    
    async def stop_listening(self) -> None:
        """Arrête l'écoute continue."""
        self.is_listening = False
        print("[AUDIO] 🔇 Arrêt écoute")
    
    async def record_once(
        self, 
        timeout: float = 8.0, 
        phrase_time_limit: float = None,
        pause_threshold: float = None
    ) -> Optional[str]:
        """
        Enregistre un audio et le transcrit (mode push-to-talk).
        Version optimisée pour éviter les déconnexions.
        
        Args:
            timeout: Durée max avant de commencer à parler
            phrase_time_limit: Durée max d'enregistrement par segment
            pause_threshold: Durée de silence avant coupure
            
        Returns:
            Texte transcrit ou None si erreur
        """
        try:
            # Utiliser le timeout de la configuration
            actual_timeout = min(timeout, self.timeout_recording)
            actual_phrase_limit = phrase_time_limit if phrase_time_limit is not None else actual_timeout
            
            print(f"[AUDIO] 🔴 Enregistrement (timeout={actual_timeout}s, phrase={actual_phrase_limit}s, pause={pause_threshold}s)...")
            
            # Configuration plus agressive pour la capture
            with self.microphone as source:
                # NE PAS re-calibrer si déjà calibré (évite seuil trop haut)
                if not self._calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Configurer pause_threshold si fourni
                if pause_threshold is not None:
                    self.recognizer.pause_threshold = pause_threshold
                
                # Enregistrement avec paramètres configurables
                audio_data = self.recognizer.listen(
                    source, 
                    timeout=actual_timeout, 
                    phrase_time_limit=actual_phrase_limit
                )
            
            print("[AUDIO] 🎵 Audio capturé, transcription...")
            
            # Transcrire immédiatement pour éviter les timeouts
            text = await self._transcribe_audio(audio_data)
            
            if text:
                print(f"[AUDIO] ✅ Transcrit: {text[:100]}...")
                if self.on_transcription_complete:
                    self.on_transcription_complete(text)
            
            return text
            
        except sr.WaitTimeoutError:
            print("[AUDIO] ⏱️ Timeout - pas de parole détectée")
            return None
        except Exception as e:
            print(f"[AUDIO] ❌ Erreur enregistrement: {e}")
            if self.on_error:
                self.on_error(f"Erreur enregistrement: {e}")
            return None
    
    async def record_manual_control(self) -> Optional[str]:
        """
        Enregistrement avec contrôle manuel complet.
        Commence l'enregistrement et attend que l'utilisateur arrête manuellement.
        AUCUN timeout automatique.
        """
        try:
            print("[AUDIO] 🎙️ Démarrage enregistrement manuel - AUCUN TIMEOUT")
            
            # Marquer le démarrage
            self.manual_recording_active = True
            frames = []
            
            # Démarrer PyAudio pour capture continue
            if not self.pyaudio_instance:
                self.pyaudio_instance = pyaudio.PyAudio()
            
            stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print("[AUDIO] 🔴 Enregistrement en cours - Contrôle manuel actif")
            
            # Boucle d'enregistrement continue tant que manual_recording_active est True
            while self.manual_recording_active:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    await asyncio.sleep(0.01)  # Petit délai pour éviter surcharge CPU
                except Exception as e:
                    print(f"[AUDIO] Erreur lecture chunk: {e}")
                    break
            
            # Arrêter le stream
            stream.stop_stream()
            stream.close()
            
            print("[AUDIO] 🔴 Enregistrement manuel arrêté - Traitement audio...")
            
            if not frames:
                print("[AUDIO] ⚠️ Aucun audio capturé")
                return None
            
            # Créer AudioData pour transcription
            audio_data = sr.AudioData(
                b''.join(frames), 
                self.sample_rate, 
                self.pyaudio_instance.get_sample_size(self.format)
            )
            
            print("[AUDIO] 🎵 Audio traité, transcription...")
            
            # Transcrire l'audio complet
            text = await self._transcribe_audio(audio_data)
            
            if text:
                print(f"[AUDIO] ✅ Transcrit: {text[:100]}...")
                if self.on_transcription_complete:
                    self.on_transcription_complete(text)
            
            return text
            
        except Exception as e:
            print(f"[AUDIO] ❌ Erreur enregistrement manuel: {e}")
            return None
        finally:
            self.manual_recording_active = False
    
    def stop_manual_recording(self):
        """Arrête l'enregistrement manuel."""
        self.manual_recording_active = False
        print("[AUDIO] 🛑 Arrêt manuel demandé")
    
    def _listen_thread(self) -> None:
        """Thread d'écoute continue (mode ambiant)."""
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Écouter avec timeout court pour vérifier is_listening
                    audio_data = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Mettre en queue pour traitement asynchrone
                self.audio_queue.put(audio_data)
                
            except sr.WaitTimeoutError:
                # Normal - pas de parole détectée
                continue
            except Exception as e:
                print(f"[AUDIO] Erreur écoute continue: {e}")
                break
    
    async def _transcribe_audio(self, audio_data) -> Optional[str]:
        """
        Transcrit un AudioData en texte.
        
        Args:
            audio_data: Données audio de speech_recognition
            
        Returns:
            Texte transcrit ou None
        """
        try:
            if self.use_whisper_api and self.api_key:
                # Utiliser API OpenAI Whisper
                return await self._transcribe_with_whisper_api(audio_data)
            else:
                # Utiliser Whisper local ou Google (fallback)
                return await self._transcribe_with_local(audio_data)
                
        except Exception as e:
            print(f"[AUDIO] Erreur transcription: {e}")
            return None
    
    async def _transcribe_with_whisper_api(self, audio_data) -> Optional[str]:
        """Transcrit avec l'API OpenAI Whisper."""
        try:
            # Sauvegarder audio temporairement
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_data = audio_data.get_wav_data()
                tmp_file.write(wav_data)
                tmp_file_path = tmp_file.name
            
            # Appel API Whisper (nouvelle version)
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            with open(tmp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="fr"  # Français
                )
            
            # Nettoyer fichier temporaire
            os.unlink(tmp_file_path)
            
            result = transcript.text.strip()
            
            # Filtrer les "hallucinations" connues de Whisper
            # Ces textes apparaissent quand l'audio est silencieux ou inaudible
            whisper_hallucinations = [
                "sous-titres réalisés par",
                "sous-titres réalisés para",
                "amara.org",
                "merci d'avoir regardé",
                "thanks for watching",
                "subscribe",
                "abonnez-vous",
                "copyright",
                "♪",
                "...",
            ]
            
            result_lower = result.lower()
            for hallucination in whisper_hallucinations:
                if hallucination in result_lower:
                    print(f"[AUDIO] ⚠️ Hallucination Whisper détectée, ignorée: '{result[:50]}...'")
                    return None
            
            # Rejeter les résultats trop courts (probablement du bruit)
            if len(result) < 3:
                print(f"[AUDIO] ⚠️ Transcription trop courte, ignorée: '{result}'")
                return None
            
            return result
            
        except Exception as e:
            print(f"[AUDIO] Erreur API Whisper: {e}")
            return None
    
    async def _transcribe_with_local(self, audio_data) -> Optional[str]:
        """Transcrit avec reconnaissance locale - optimisé pour fragments courts."""
        try:
            # Google Speech est plus rapide pour les courts segments
            text = self.recognizer.recognize_google(
                audio_data, 
                language="fr-FR",
                show_all=False  # Seulement le meilleur résultat
            )
            return text.strip()
            
        except sr.UnknownValueError:
            print("[AUDIO] Parole non comprise - fragment trop court ou silence")
            return None
        except sr.RequestError as e:
            print(f"[AUDIO] Erreur service reconnaissance: {e}")
            # Fallback silencieux - pas d'erreur bloquante
            return None
    
    async def process_audio_queue(self) -> None:
        """Traite la queue audio en arrière-plan."""
        while True:
            try:
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get_nowait()
                    text = await self._transcribe_audio(audio_data)
                    
                    if text and self.on_transcription_complete:
                        self.on_transcription_complete(text)
                
                await asyncio.sleep(0.1)  # Éviter surcharge CPU
                
            except Exception as e:
                print(f"[AUDIO] Erreur traitement queue: {e}")
                await asyncio.sleep(1)
    
    def cleanup(self) -> None:
        """Nettoie les ressources audio."""
        self.is_listening = False
        self.is_recording = False
        
        # Nettoyage du moteur TTS
        if self.tts_engine:
            try:
                # Arrêter et nettoyer pyttsx3 proprement
                self.tts_engine.stop()
                del self.tts_engine
                self.tts_engine = None
                print("[AUDIO] 🧹 Moteur TTS nettoyé")
            except Exception as e:
                print(f"[AUDIO] Erreur nettoyage TTS: {e}")
        
        # Nettoyage PyAudio
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
                print("[AUDIO] 🧹 PyAudio terminé")
            except Exception as e:
                print(f"[AUDIO] Erreur nettoyage PyAudio: {e}")
            
        print("[AUDIO] 🧹 Ressources nettoyées")
    
    async def transcribe_with_whisper(self, audio_data) -> Optional[str]:
        """Méthode publique pour transcription avec Whisper local."""
        try:
            import whisper
            
            # Sauvegarder audio temporairement
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_data = audio_data.get_wav_data()
                tmp_file.write(wav_data)
                tmp_file_path = tmp_file.name
            
            # Charger modèle Whisper
            model = whisper.load_model("base")
            result = model.transcribe(tmp_file_path, language="French")
            
            # Nettoyer fichier temporaire
            os.unlink(tmp_file_path)
            
            return result["text"].strip()
            
        except Exception as e:
            print(f"[AUDIO] Erreur Whisper local: {e}")
            return None
    
    async def transcribe_with_api(self, audio_data) -> Optional[str]:
        """Méthode publique pour transcription avec API Whisper."""
        return await self._transcribe_with_whisper_api(audio_data)

    # === MÉTHODES TEXT-TO-SPEECH ===
    
    async def initialize_tts(self) -> bool:
        """Initialise le système TTS et scanne les voix disponibles."""
        try:
            self.available_voices = []
            
            # 1. Initialiser pyttsx3 si disponible
            if PYTTSX3_AVAILABLE:
                try:
                    self.tts_engine = pyttsx3.init()
                    voices = self.tts_engine.getProperty('voices')
                    
                    for i, voice in enumerate(voices):
                        if voice and hasattr(voice, 'name'):
                            # Détecter les voix françaises
                            is_french = any(keyword in voice.name.lower() for keyword in 
                                          ['fr', 'french', 'français', 'claire', 'julie', 'hortense'])
                            
                            self.available_voices.append({
                                'id': f'pyttsx3_{i}',
                                'name': voice.name,
                                'gender': 'female' if any(fem in voice.name.lower() 
                                                       for fem in ['female', 'femme', 'claire', 'julie', 'hortense']) else 'male',
                                'language': 'fr' if is_french else 'en',
                                'engine': 'pyttsx3',
                                'voice_object': voice
                            })
                    
                    print(f"[TTS] pyttsx3 initialisé - {len([v for v in self.available_voices if v['engine'] == 'pyttsx3'])} voix trouvées")
                except Exception as e:
                    print(f"[TTS] Erreur pyttsx3: {e}")
            
            # 2. Initialiser SAPI si disponible (Windows)
            if SAPI_AVAILABLE:
                try:
                    self.sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
                    sapi_voices = self.sapi_voice.GetVoices()
                    
                    for i in range(sapi_voices.Count):
                        voice = sapi_voices.Item(i)
                        voice_info = voice.GetDescription()
                        
                        # Détecter les voix françaises
                        is_french = any(keyword in voice_info.lower() for keyword in 
                                      ['fr', 'french', 'français', 'claire', 'julie', 'hortense'])
                        
                        self.available_voices.append({
                            'id': f'sapi_{i}',
                            'name': voice_info,
                            'gender': 'female' if any(fem in voice_info.lower() 
                                                   for fem in ['female', 'femme', 'claire', 'julie', 'hortense']) else 'male',
                            'language': 'fr' if is_french else 'en',
                            'engine': 'sapi',
                            'voice_object': voice
                        })
                    
                    print(f"[TTS] SAPI initialisé - {len([v for v in self.available_voices if v['engine'] == 'sapi'])} voix trouvées")
                except Exception as e:
                    print(f"[TTS] Erreur SAPI: {e}")
            
            # Sélectionner la meilleure voix française par défaut
            french_female_voices = [v for v in self.available_voices 
                                  if v['language'] == 'fr' and v['gender'] == 'female']
            
            if french_female_voices:
                self.current_voice_id = french_female_voices[0]['id']
                print(f"[TTS] Voix par défaut: {french_female_voices[0]['name']}")
            elif self.available_voices:
                self.current_voice_id = self.available_voices[0]['id']
                print(f"[TTS] Voix par défaut: {self.available_voices[0]['name']}")
            
            print(f"[TTS] ✅ {len(self.available_voices)} voix disponibles")
            return True
            
        except Exception as e:
            print(f"[TTS] ❌ Erreur initialisation TTS: {e}")
            return False
    
    def initialize_tts_sync(self) -> bool:
        """Version synchrone de l'initialisation TTS pour l'interface utilisateur."""
        try:
            self.available_voices = []
            
            # 1. Initialiser pyttsx3 si disponible
            if PYTTSX3_AVAILABLE:
                try:
                    self.tts_engine = pyttsx3.init()
                    voices = self.tts_engine.getProperty('voices')
                    
                    for i, voice in enumerate(voices):
                        if voice and hasattr(voice, 'name'):
                            # Détecter les voix françaises
                            is_french = any(keyword in voice.name.lower() for keyword in 
                                          ['fr', 'french', 'français', 'claire', 'julie', 'hortense'])
                            
                            self.available_voices.append({
                                'id': f'pyttsx3_{i}',
                                'name': voice.name,
                                'gender': 'female' if any(fem in voice.name.lower() 
                                                       for fem in ['female', 'femme', 'claire', 'julie', 'hortense']) else 'male',
                                'language': 'fr' if is_french else 'en',
                                'engine': 'pyttsx3',
                                'voice_object': voice
                            })
                    
                    print(f"[TTS] pyttsx3 initialisé - {len([v for v in self.available_voices if v['engine'] == 'pyttsx3'])} voix trouvées")
                except Exception as e:
                    print(f"[TTS] Erreur pyttsx3: {e}")
            
            # 2. Initialiser SAPI si disponible (Windows)
            if SAPI_AVAILABLE:
                try:
                    self.sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
                    sapi_voices = self.sapi_voice.GetVoices()
                    
                    for i in range(sapi_voices.Count):
                        voice = sapi_voices.Item(i)
                        voice_info = voice.GetDescription()
                        
                        # Détecter les voix françaises
                        is_french = any(keyword in voice_info.lower() for keyword in 
                                      ['fr', 'french', 'français', 'claire', 'julie', 'hortense'])
                        
                        self.available_voices.append({
                            'id': f'sapi_{i}',
                            'name': voice_info,
                            'gender': 'female' if any(fem in voice_info.lower() 
                                                   for fem in ['female', 'femme', 'claire', 'julie', 'hortense']) else 'male',
                            'language': 'fr' if is_french else 'en',
                            'engine': 'sapi',
                            'voice_object': voice
                        })
                    
                    print(f"[TTS] SAPI initialisé - {len([v for v in self.available_voices if v['engine'] == 'sapi'])} voix trouvées")
                except Exception as e:
                    print(f"[TTS] Erreur SAPI: {e}")
            
            # Sélectionner la meilleure voix française par défaut
            french_female_voices = [v for v in self.available_voices 
                                  if v['language'] == 'fr' and v['gender'] == 'female']
            
            if french_female_voices:
                self.current_voice_id = french_female_voices[0]['id']
                print(f"[TTS] Voix par défaut: {french_female_voices[0]['name']}")
            elif self.available_voices:
                self.current_voice_id = self.available_voices[0]['id']
                print(f"[TTS] Voix par défaut: {self.available_voices[0]['name']}")
            
            print(f"[TTS] ✅ {len(self.available_voices)} voix disponibles")
            return True
            
        except Exception as e:
            print(f"[TTS] ❌ Erreur initialisation TTS sync: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict]:
        """Retourne la liste des voix disponibles pour l'interface."""
        if not self.available_voices:
            # Essayer d'initialiser les voix si pas encore fait
            self.initialize_tts_sync()
        return self.available_voices
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Sélectionne une voix par son ID.
        
        Args:
            voice_id: ID de la voix à utiliser ou 'auto' pour sélection automatique
            
        Returns:
            True si la voix a été changée avec succès
        """
        try:
            if voice_id == 'auto':
                # Mode automatique - utiliser la voix par défaut (première française si disponible)
                french_voice = next((v for v in self.available_voices if v['language'] == 'fr'), None)
                if french_voice:
                    self.current_voice_id = french_voice['id']
                    print(f"[TTS] Mode auto - Voix française sélectionnée: {french_voice['name']}")
                else:
                    # Fallback sur la première voix disponible
                    self.current_voice_id = self.available_voices[0]['id'] if self.available_voices else None
                    print(f"[TTS] Mode auto - Voix par défaut: {self.available_voices[0]['name'] if self.available_voices else 'Aucune'}")
                return True
            else:
                voice_info = next((v for v in self.available_voices if v['id'] == voice_id), None)
                if voice_info:
                    self.current_voice_id = voice_id
                    print(f"[TTS] Voix changée: {voice_info['name']}")
                    return True
                else:
                    print(f"[TTS] ⚠️ Voix introuvable: {voice_id}")
                    return False
        except Exception as e:
            print(f"[TTS] Erreur changement voix: {e}")
            return False
    
    async def speak(self, text: str) -> bool:
        """
        Synthétise et joue le texte donné selon le moteur configuré.
        
        Args:
            text: Texte à synthétiser
            
        Returns:
            True si la synthèse s'est bien passée
        """
        print(f"[TTS-DEBUG] 🎯 SPEAK() appelée avec: {text[:50]}...")
        print(f"[TTS-DEBUG] 🎯 Moteur TTS actuel: {self.tts_engine_type}")
        print(f"[TTS-DEBUG] 🎯 TTS enabled: {self.tts_enabled}")
        print(f"[TTS-DEBUG] 🎯 État is_speaking: {self.is_speaking}")
        
        if not self.tts_enabled or not text.strip():
            print(f"[TTS-DEBUG] ❌ Conditions non remplies - enabled={self.tts_enabled}, text={'vide' if not text.strip() else 'ok'}")
            return False
        
        if self.is_speaking:
            print("[TTS] 🔇 Arrêt synthèse précédente...")
            self.stop_speaking()
            # Petite pause pour laisser le temps au canal de se libérer
            import asyncio
            await asyncio.sleep(0.2)
        
        try:
            self.is_speaking = True
            self._stop_requested = False  # RESET du flag d'arrêt
            
            # Déterminer le moteur à utiliser
            if self.tts_engine_type == "google":
                if not self.google_api_key:
                    print("[TTS] ❌ Clé API Google manquante")
                    return False
                return await self.speak_google_tts(text, self.google_voice, self.google_api_key)
            elif self.tts_engine_type == "elevenlabs":
                print(f"[DEBUG-ELEVEN] SPEAK - Vérification clé: {self.elevenlabs_api_key[:15] if self.elevenlabs_api_key else 'AUCUNE'}...")
                print(f"[DEBUG-ELEVEN] SPEAK - État bool(clé): {bool(self.elevenlabs_api_key)}")
                if not self.elevenlabs_api_key:
                    print("[TTS] ❌ Clé API ElevenLabs manquante")
                    return False
                return await self.speak_elevenlabs(text, self.elevenlabs_voice_id, self.elevenlabs_api_key)
            elif self.tts_engine_type == "azure":
                if not self.azure_api_key:
                    print("[TTS] ❌ Clé API Azure manquante")
                    return False
                return await self.speak_azure(text, self.azure_voice, self.azure_api_key, self.azure_region)
            elif self.tts_engine_type == "gtts":
                lang = getattr(self, 'gtts_lang', 'fr')
                return await self.speak_gtts(text, lang)
            elif self.tts_engine_type == "edge_tts":
                voice = getattr(self, 'edge_tts_voice', 'fr-FR-DeniseNeural')
                return await self.speak_edge_tts(text, voice)
            elif self.tts_engine_type == "fish_audio":
                if not self.fish_audio_api_key:
                    print("[TTS] ❌ Clé API Fish Audio manquante")
                    return False
                return await self.speak_fish_audio(text, self.fish_audio_voice_id, self.fish_audio_api_key)
            elif self.tts_engine_type == "cartesia":
                if not self.cartesia_api_key:
                    print("[TTS] ❌ Clé API Cartesia manquante")
                    return False
                return await self.speak_cartesia(text, self.cartesia_voice_id, self.cartesia_api_key, self.cartesia_model)
            elif self.tts_engine_type == "hume_ai":
                if not self.hume_ai_api_key:
                    print("[TTS] ❌ Clé API Hume AI manquante")
                    return False
                return await self.speak_hume_ai(
                    text, 
                    self.hume_ai_voice_name, 
                    self.hume_ai_api_key, 
                    self.hume_ai_description,
                    self.hume_ai_voice_id,
                    self.hume_ai_version
                )
            else:
                # Moteur système (SAPI/pyttsx3)
                print(f"[TTS-DEBUG] 🎯 Utilisation moteur système")
                result = await self.speak_system(text)
                print(f"[TTS-DEBUG] 🎯 Résultat moteur système: {result}")
                return result
                
        except Exception as e:
            print(f"[TTS-DEBUG] ❌ Erreur synthèse générale: {e}")
            import traceback
            print(f"[TTS-DEBUG] ❌ Traceback: {traceback.format_exc()}")
            return False
        finally:
            print(f"[TTS-DEBUG] 🎯 Fin SPEAK() - is_speaking reset à False")
            self.is_speaking = False
    
    async def speak_system(self, text: str) -> bool:
        """
        Synthèse avec le moteur système (SAPI ou pyttsx3).
        
        Args:
            text: Texte à synthétiser
            
        Returns:
            True si succès
        """
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)
            
            print(f"[TTS-DEBUG] 🔧 SPEAK_SYSTEM() début avec: {clean_text[:50]}...")
            # Debug: vérifier l'état des voix
            print(f"[TTS-DEBUG] current_voice_id: {self.current_voice_id}")
            print(f"[TTS-DEBUG] available_voices count: {len(self.available_voices)}")
            print(f"[TTS-DEBUG] tts_engine disponible: {self.tts_engine is not None}")
            print(f"[TTS-DEBUG] sapi_voice disponible: {self.sapi_voice is not None}")
            
            # Si aucune voix n'est sélectionnée, essayer d'en choisir une automatiquement
            if not self.current_voice_id and self.available_voices:
                # Choisir la première voix française si disponible
                french_voice = next((v for v in self.available_voices if v['language'] == 'fr'), None)
                if french_voice:
                    self.current_voice_id = french_voice['id']
                    print(f"[TTS] Auto-sélection voix française: {french_voice['name']}")
                else:
                    self.current_voice_id = self.available_voices[0]['id']
                    print(f"[TTS] Auto-sélection première voix: {self.available_voices[0]['name']}")
            
            current_voice = next((v for v in self.available_voices if v['id'] == self.current_voice_id), None)
            
            if not current_voice:
                print(f"[TTS] ❌ Aucune voix système sélectionnée (ID recherché: {self.current_voice_id})")
                # Dernier recours : utiliser la première voix disponible
                if self.available_voices:
                    current_voice = self.available_voices[0]
                    self.current_voice_id = current_voice['id']
                    print(f"[TTS] Utilisation voix de secours: {current_voice['name']}")
                else:
                    print("[TTS] ❌ Aucune voix disponible")
                    return False
            
            print(f"[TTS] 🔊 Synthèse système: {text[:50]}... (voix: {current_voice['name']})")
            
            # Priorité SAPI pour Windows (plus stable et sans conflicts de threading)
            if current_voice['engine'] == 'sapi' and self.sapi_voice:
                try:
                    self.sapi_voice.Voice = current_voice['voice_object']
                    self.sapi_voice.Rate = (self.tts_speed - 150) // 10
                    self.sapi_voice.Volume = int(self.tts_volume * 100)
                    
                    # Vérifier arrêt avant synthèse
                    if getattr(self, '_stop_requested', False):
                        print("[TTS] 🛑 SAPI annulée avant démarrage")
                        return False
                    
                    # Synthèse synchrone pour éviter les conflicts
                    self.sapi_voice.Speak(clean_text)
                    print("[TTS] ✅ Synthèse SAPI terminée")
                    return True
                    
                except Exception as e:
                    print(f"[TTS] Erreur SAPI: {e}")
                    return False
                    
            elif current_voice['engine'] == 'pyttsx3':
                try:
                    # Créer nouvelle instance pour éviter conflicts
                    import pyttsx3
                    engine = pyttsx3.init()
                    
                    # Vérifier que l'instance est valide
                    if not engine:
                        print("[TTS] ❌ Impossible de créer instance pyttsx3")
                        return False
                    
                    engine.setProperty('voice', current_voice['voice_object'].id)
                    engine.setProperty('rate', self.tts_speed)
                    engine.setProperty('volume', self.tts_volume)
                    
                    engine.say(clean_text)
                    engine.runAndWait()
                    
                    # Nettoyer proprement
                    try:
                        engine.stop()
                        del engine
                    except:
                        pass
                    
                    print("[TTS-DEBUG] 🔧 ✅ Synthèse pyttsx3 terminée avec succès")
                    return True
                    
                except Exception as e:
                    print(f"[TTS-DEBUG] 🔧 ❌ Erreur pyttsx3: {e}")
                    import traceback
                    print(f"[TTS-DEBUG] 🔧 ❌ Traceback pyttsx3: {traceback.format_exc()}")
                    return False
            
            print("[TTS-DEBUG] 🔧 ❌ Aucun moteur TTS système disponible")
            return False
            
        except Exception as e:
            print(f"[TTS-DEBUG] 🔧 ❌ Erreur synthèse système générale: {e}")
            import traceback
            print(f"[TTS-DEBUG] 🔧 ❌ Traceback système: {traceback.format_exc()}")
            return False
    
    async def speak_google_tts(self, text: str, voice_name: str, api_key: str) -> bool:
        """
        Synthèse vocale avec Google Cloud TTS.
        
        Args:
            text: Texte à synthétiser
            voice_name: Nom de la voix (ex: 'fr-FR-Standard-A')
            api_key: Clé API Google Cloud
            
        Returns:
            True si succès
        """
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)
            
            if not api_key:
                print("[TTS] ❌ Clé API Google manquante")
                return False
            
            # Construire la requête pour l'API Google TTS
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
            
            # Extraire la langue depuis le nom de la voix
            language_code = voice_name.split('-')[0] + '-' + voice_name.split('-')[1]  # ex: fr-FR
            
            payload = {
                "input": {"text": clean_text},
                "voice": {
                    "languageCode": language_code,
                    "name": voice_name
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": self.tts_speed / 150.0,  # Normaliser à 1.0
                    "volumeGainDb": (self.tts_volume - 0.5) * 20  # Convertir en dB
                }
            }
            
            headers = {"Content-Type": "application/json"}
            
            print(f"[TTS] 🌐 Synthèse Google TTS: {text[:50]}... (voix: {voice_name})")
            
            # Faire la requête
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                audio_content = result.get('audioContent')
                
                if audio_content:
                    # Décoder le contenu audio base64
                    import base64
                    audio_data = base64.b64decode(audio_content)
                    
                    # Sauvegarder temporairement et jouer
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                        tmp_file.write(audio_data)
                        tmp_path = tmp_file.name
                    
                    # Jouer le fichier audio avec pygame
                    if PYGAME_AVAILABLE:
                        import pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load(tmp_path)
                        pygame.mixer.music.play()
                        
                        # Attendre la fin de la lecture
                        while pygame.mixer.music.get_busy():
                            await asyncio.sleep(0.1)
                        
                        pygame.mixer.quit()
                    else:
                        # Fallback - jouer avec le système
                        if platform.system() == "Windows":
                            os.system(f'start /min "" "{tmp_path}"')
                            await asyncio.sleep(2)  # Approximation
                    
                    # Nettoyer le fichier temporaire
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                    
                    print("[TTS] ✅ Synthèse Google TTS terminée")
                    return True
                else:
                    print("[TTS] ❌ Aucun contenu audio reçu de Google")
                    return False
            else:
                print(f"[TTS] ❌ Erreur API Google: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[TTS] ❌ Erreur Google TTS: {e}")
            return False
    
    async def speak_elevenlabs(self, text: str, voice_id: str, api_key: str) -> bool:
        """
        Synthèse vocale avec ElevenLabs.
        
        Args:
            text: Texte à synthétiser
            voice_id: ID de la voix ElevenLabs
            api_key: Clé API ElevenLabs
            
        Returns:
            True si succès
        """
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)
            
            if not api_key:
                print("[TTS] ❌ Clé API ElevenLabs manquante")
                return False
            
            if not voice_id:
                print("[TTS] ❌ Voice ID ElevenLabs manquant")
                return False
            
            # URL de l'API ElevenLabs
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            payload = {
                "text": clean_text,
                "model_id": self.elevenlabs_model,
                "voice_settings": {
                    "stability": self.elevenlabs_stability,
                    "similarity_boost": self.elevenlabs_similarity,
                    "style": self.elevenlabs_style,
                    "use_speaker_boost": self.elevenlabs_speaker_boost,
                    "speed": self.elevenlabs_speed
                }
            }
            
            print(f"[TTS] 🎙️ Synthèse ElevenLabs: {text[:50]}... (voice: {voice_id})")
            
            # Faire la requête
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Sauvegarder temporairement et jouer
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                # Jouer le fichier audio avec pygame
                if PYGAME_AVAILABLE:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    
                    # Attendre la fin de la lecture
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    
                    # Unload AVANT quit pour libérer le handle fichier sur Windows
                    pygame.mixer.music.unload()
                    pygame.mixer.quit()
                else:
                    # Fallback - jouer avec le système
                    if platform.system() == "Windows":
                        os.system(f'start /min "" "{tmp_path}"')
                        await asyncio.sleep(3)  # Approximation
                
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                
                print("[TTS] ✅ Synthèse ElevenLabs terminée")
                return True
            else:
                print(f"[TTS] ❌ Erreur API ElevenLabs: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[TTS] ❌ Erreur ElevenLabs: {e}")
            return False

    async def speak_fish_audio(self, text: str, voice_id: str, api_key: str) -> bool:
        """
        Synthèse vocale avec Fish Audio.
        Cache session : les fichiers sont conservés dans audio_temp/ et supprimés à la fermeture d'OGMA.
        Une même phrase n'est donc synthétisée qu'une seule fois par session.
        """
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)

            if not api_key:
                print("[TTS] Cle API Fish Audio manquante")
                return False

            if not voice_id:
                print("[TTS] Voice ID Fish Audio manquant")
                return False

            # Injection émotion dans le texte
            # S1 : syntaxe (parenthèses) fixe | S2-pro : syntaxe [crochets] langage naturel
            emotion = self.fish_audio_emotion
            if emotion and emotion != 'none':
                if self.fish_audio_model == 's1':
                    text_with_emotion = f"({emotion}) {clean_text}"
                else:  # s2-pro ou futur modèle
                    text_with_emotion = f"[{emotion}] {clean_text}"
            else:
                text_with_emotion = clean_text

            # --- Cache session (même pattern que Cartesia) ---
            cache_dir = Path(__file__).parent / "data" / "audio_temp"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_key = hashlib.md5(
                f"{text_with_emotion}|{voice_id}|{self.fish_audio_model}|{self.fish_audio_latency}|{self.fish_audio_mp3_bitrate}|{self.fish_audio_chunk_length}".encode("utf-8")
            ).hexdigest()
            tmp_path = str(cache_dir / f"ogma_tts_{cache_key}.mp3")

            if Path(tmp_path).exists():
                print(f"[TTS] Cache Fish Audio: {text[:50]}...")
            else:
                # Appel API Fish Audio
                url = "https://api.fish.audio/v1/tts"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "model": self.fish_audio_model
                }
                payload = {
                    "text": text_with_emotion,
                    "reference_id": voice_id,
                    "format": "mp3",
                    "mp3_bitrate": self.fish_audio_mp3_bitrate,
                    "chunk_length": self.fish_audio_chunk_length,
                    "normalize": self.fish_audio_normalize,
                    "latency": self.fish_audio_latency
                }
                print(f"[TTS] Synthese Fish Audio: {text[:50]}... (voice: {voice_id}, model: {self.fish_audio_model}, emotion: {emotion})")
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    print(f"[TTS] Erreur API Fish Audio: {response.status_code} - {response.text}")
                    return False
                # Sauvegarde dans le cache session
                with open(tmp_path, 'wb') as f:
                    f.write(response.content)

            # Lecture du fichier audio
            if PYGAME_AVAILABLE:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                # Unload AVANT quit pour libérer le handle fichier sur Windows
                pygame.mixer.music.unload()
                pygame.mixer.quit()
            else:
                if platform.system() == "Windows":
                    os.system(f'start /min "" "{tmp_path}"')
                    await asyncio.sleep(3)

            # Pas de suppression ici : le fichier reste en cache jusqu'à la fermeture d'OGMA
            print("[TTS] Synthese Fish Audio terminee")
            return True

        except Exception as e:
            print(f"[TTS] Erreur Fish Audio: {e}")
            return False

    async def speak_cartesia(self, text: str, voice_id: str, api_key: str, model: str = "sonic-2") -> bool:
        """
        Synthèse vocale avec Cartesia AI.
        Cache session : les fichiers sont conservés dans audio_temp/ et supprimés à la fermeture d'OGMA.
        Une même phrase n'est donc synthétisée qu'une seule fois par session.
        """
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)

            if not api_key:
                print("[TTS] Cle API Cartesia manquante")
                return False

            if not voice_id:
                print("[TTS] Voice ID Cartesia manquant")
                return False

            # --- Cache session ---
            cache_dir = Path(__file__).parent / "data" / "audio_temp"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_key = hashlib.md5(
                f"{clean_text}|{voice_id}|{model}|{self.cartesia_speed:.2f}|{self.cartesia_emotion}".encode("utf-8")
            ).hexdigest()
            tmp_path = str(cache_dir / f"ogma_tts_{cache_key}.mp3")

            if Path(tmp_path).exists():
                print(f"[TTS] Cache Cartesia: {text[:50]}...")
            else:
                # Appel API Cartesia
                url = "https://api.cartesia.ai/tts/bytes"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Cartesia-Version": "2025-04-16",
                    "Content-Type": "application/json"
                }
                # Construction du dict voice avec experimental_controls pour sonic-3
                voice_dict = {"mode": "id", "id": voice_id}
                if model == "sonic-3":
                    emotion_map = {
                        'neutral': [],
                        'excited': ['positivity:high', 'surprise:medium'],
                        'content': ['positivity:medium'],
                        'sad': ['sadness:high'],
                        'angry': ['anger:high'],
                        'curious': ['curiosity:high'],
                        'affectionate': ['positivity:high'],
                        'calm': ['positivity:low'],
                        'sympathetic': ['sadness:low'],
                        'mysterious': ['curiosity:medium'],
                    }
                    controls = {"speed": self.cartesia_speed}
                    emotions = emotion_map.get(self.cartesia_emotion, [])
                    if emotions:
                        controls["emotion"] = emotions
                    voice_dict["experimental_controls"] = controls

                payload = {
                    "model_id": model,
                    "transcript": clean_text,
                    "voice": voice_dict,
                    "output_format": {"container": "mp3", "bit_rate": 128000, "sample_rate": 44100},
                    "language": "fr"
                }
                print(f"[TTS] Synthese Cartesia: {text[:50]}... (voice: {voice_id}, model: {model}, speed: {self.cartesia_speed}, emotion: {self.cartesia_emotion})")
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code != 200:
                    print(f"[TTS] Erreur API Cartesia: {response.status_code} - {response.text}")
                    return False
                # Sauvegarde dans le cache session
                with open(tmp_path, 'wb') as f:
                    f.write(response.content)

            # Lecture du fichier audio
            if PYGAME_AVAILABLE:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                # Unload AVANT quit pour libérer le handle fichier sur Windows
                pygame.mixer.music.unload()
                pygame.mixer.quit()
            else:
                if platform.system() == "Windows":
                    os.system(f'start /min "" "{tmp_path}"')
                    await asyncio.sleep(3)

            # Pas de suppression ici : le fichier reste en cache jusqu'à la fermeture d'OGMA
            # (atexit + cleanup démarrage dans tts_utils.py supprime tous les ogma_tts_*.mp3)
            print("[TTS] Synthese Cartesia terminee")
            return True

        except Exception as e:
            print(f"[TTS] Erreur Cartesia: {e}")
            return False

    async def speak_hume_ai(self, text: str, voice_name: str, api_key: str, description: str = "", voice_id: str = "", version: int = 2) -> bool:
        """
        Synthèse vocale avec Hume AI (Octave TTS).
        
        Args:
            text: Texte à synthétiser
            voice_name: Nom de la voix Hume (Voice Library)
            api_key: Clé API Hume AI
            description: Description pour génération dynamique de voix (optionnel)
            voice_id: ID de voix personnalisée (prioritaire sur voice_name)
            version: Version Octave (1 ou 2, défaut 2)
            
        Returns:
            True si succès
        """
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)
            
            if not api_key:
                print("[TTS] ❌ Clé API Hume AI manquante")
                return False
            
            # URL de l'API Hume AI TTS
            url = "https://api.hume.ai/v0/tts/file"
            
            headers = {
                "X-Hume-Api-Key": api_key,
                "Content-Type": "application/json"
            }
            
            # Construire l'utterance
            utterance = {
                "text": clean_text
            }
            
            # Priorité: voice_id > voice_name > description (voix dynamique)
            has_voice = False
            if voice_id:
                utterance["voice"] = {"id": voice_id}
                has_voice = True
                print(f"[TTS] 🧠 Hume AI - Utilisation voice_id: {voice_id}")
            elif voice_name:
                utterance["voice"] = {"name": voice_name}
                has_voice = True
                print(f"[TTS] 🧠 Hume AI - Utilisation voice_name: {voice_name}")
            
            # Ajouter la description si fournie (pour voix dynamique ou guidance)
            if description:
                utterance["description"] = description
            
            payload = {
                "utterances": [utterance],
                "format": {"type": "mp3"},
                "num_generations": 1
            }
            
            # Version Octave - API attend une STRING "1" ou "2", pas un int
            if has_voice and version == 2:
                payload["version"] = "2"
            elif version == 1 or not has_voice:
                payload["version"] = "1"  # Version 1 pour voix dynamiques
            
            voice_info = voice_id or voice_name or 'dynamique'
            print(f"[TTS] 🧠 Synthèse Hume AI (Octave {payload.get('version', '1')}): {text[:50]}... (voice: {voice_info})")
            
            # Faire la requête
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Sauvegarder temporairement et jouer
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                # Jouer le fichier audio avec pygame
                if PYGAME_AVAILABLE:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    
                    # Attendre la fin de la lecture
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    
                    pygame.mixer.quit()
                else:
                    # Fallback - jouer avec le système
                    if platform.system() == "Windows":
                        os.system(f'start /min "" "{tmp_path}"')
                        await asyncio.sleep(3)
                
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                
                print("[TTS] ✅ Synthèse Hume AI terminée")
                return True
            else:
                print(f"[TTS] ❌ Erreur API Hume AI: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[TTS] ❌ Erreur Hume AI: {e}")
            return False

    async def speak_azure(self, text: str, voice: str, api_key: str, region: str) -> bool:
        """
        Synthèse vocale avec Azure AI Speech.
        
        Args:
            text: Texte à synthétiser
            voice: Nom de la voix Azure (ex: fr-FR-DeniseNeural)
            api_key: Clé API Azure Speech
            region: Région Azure (ex: westeurope)
            
        Returns:
            True si succès
        """
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)
            
            if not AZURE_SPEECH_AVAILABLE:
                print("[TTS] ❌ Azure Speech SDK non disponible")
                return False
                
            if not api_key:
                print("[TTS] ❌ Clé API Azure manquante")
                return False
            
            if not region:
                print("[TTS] ❌ Région Azure manquante")
                return False
            
            print(f"[TTS] 🔊 Synthèse Azure: {text[:50]}... (voix: {voice})")
            
            # Configuration Azure Speech
            speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
            speech_config.speech_synthesis_voice_name = voice
            speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3)
            
            # Créer le synthétiseur avec sortie par défaut
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            
            # Synthèse synchrone
            result = synthesizer.speak_text_async(clean_text).get()
            
            # Vérifier le résultat
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("[TTS] ✅ Synthèse Azure terminée")
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"[TTS] ❌ Synthèse Azure annulée: {cancellation_details.reason}")
                if cancellation_details.error_details:
                    print(f"[TTS] Détails erreur: {cancellation_details.error_details}")
                return False
            else:
                print(f"[TTS] ❌ Résultat Azure inattendu: {result.reason}")
                return False
                
        except Exception as e:
            print(f"[TTS] ❌ Erreur Azure Speech: {e}")
            return False
    
    def stop_speaking(self):
        """Arrête la synthèse vocale en cours."""
        print("[TTS] � Arrêt de la synthèse vocale demandé")
        
        try:
            # Marquer l'arrêt demandé
            self.is_speaking = False
            self._stop_requested = True
            
            # Arrêt pygame si utilisé
            if PYGAME_AVAILABLE:
                try:
                    import pygame
                    if pygame.mixer.get_init():
                        # CORRECTION CRITIQUE : arrêter la musique ET les effets
                        pygame.mixer.music.stop()  # Arrêt musique (fichiers TTS)
                        pygame.mixer.stop()         # Arrêt autres sons
                        print("[TTS] ✅ Pygame music + mixer arrêtés")
                except Exception as e:
                    print(f"[TTS] ⚠️ Erreur arrêt pygame: {e}")
            
            # Arrêt pyttsx3 si utilisé
            if PYTTSX3_AVAILABLE and hasattr(self, 'tts_engine') and self.tts_engine:
                try:
                    self.tts_engine.stop()
                    print("[TTS] ✅ pyttsx3 engine arrêté")
                except Exception as e:
                    print(f"[TTS] ⚠️ Erreur arrêt pyttsx3: {e}")
            
            # Arrêt SAPI si utilisé
            if SAPI_AVAILABLE and hasattr(self, 'sapi_voice') and self.sapi_voice:
                try:
                    # SAPI interruption avec texte vide
                    self.sapi_voice.Speak("", 3)  # SVSFPurgeBeforeSpeak
                    print("[TTS] ✅ SAPI interrompu")
                except Exception as e:
                    print(f"[TTS] ⚠️ Erreur arrêt SAPI: {e}")
            
            # Arrêt Azure Speech si utilisé
            if AZURE_SPEECH_AVAILABLE and hasattr(self, '_current_synthesizer'):
                try:
                    if self._current_synthesizer:
                        # Azure Speech n'a pas de méthode stop directe
                        # On marque juste qu'il faut arrêter
                        self._stop_requested = True
                        print("[TTS] ✅ Azure Speech arrêt demandé")
                except:
                    pass
            
            print("[TTS] 🔇 Synthèse vocale arrêtée")
            return True
            
        except Exception as e:
            print(f"[TTS] ❌ Erreur lors de l'arrêt: {e}")
            return False
        finally:
            self.is_speaking = False
    
    def set_tts_settings(self, speed: Optional[int] = None, volume: Optional[float] = None, enabled: Optional[bool] = None):
        """
        Configure les paramètres TTS.
        
        Args:
            speed: Vitesse en mots/minute (100-300)
            volume: Volume (0.0 à 1.0)
            enabled: Activer/désactiver le TTS
        """
        if speed is not None:
            self.tts_speed = max(100, min(300, speed))
        if volume is not None:
            self.tts_volume = max(0.0, min(1.0, volume))
        if enabled is not None:
            self.tts_enabled = enabled
        
        print(f"[TTS] Paramètres: vitesse={self.tts_speed}, volume={self.tts_volume:.1f}, activé={self.tts_enabled}")
    
    def configure_tts_engine(self, engine_type: str, **kwargs):
        """
        Configure le moteur de synthèse vocale.
        
        Args:
            engine_type: Type de moteur ("system", "google", "elevenlabs", "azure", "gtts", "edge_tts")
            **kwargs: Paramètres spécifiques au moteur
        """
        self.tts_engine_type = engine_type
        
        if engine_type == "google":
            self.google_api_key = kwargs.get('api_key')
            self.google_voice = kwargs.get('voice', 'fr-FR-Standard-A')
            print(f"[TTS] Moteur Google configuré: voix={self.google_voice}")
            
        elif engine_type == "elevenlabs":
            received_key = kwargs.get('api_key')
            self.elevenlabs_api_key = received_key
            self.elevenlabs_voice_id = kwargs.get('voice_id', 'pNInz6obpgDQGcFmaJgB')
            self.elevenlabs_model = kwargs.get('model', 'eleven_multilingual_v2')
            self.elevenlabs_stability = kwargs.get('stability', 0.5)
            self.elevenlabs_similarity = kwargs.get('similarity', 0.75)
            self.elevenlabs_style = kwargs.get('style', 0.0)
            self.elevenlabs_speed = kwargs.get('speed', 1.0)
            self.elevenlabs_speaker_boost = kwargs.get('speaker_boost', True)
            print(f"[DEBUG-ELEVEN] CONFIGURE - Clé reçue: {received_key[:15] if received_key else 'AUCUNE'}...")
            print(f"[DEBUG-ELEVEN] CONFIGURE - Clé stockée: {self.elevenlabs_api_key[:15] if self.elevenlabs_api_key else 'AUCUNE'}...")
            print(f"[TTS] Moteur ElevenLabs configuré: voice={self.elevenlabs_voice_id}, model={self.elevenlabs_model}")
            print(f"[TTS] ElevenLabs params: stability={self.elevenlabs_stability}, similarity={self.elevenlabs_similarity}, style={self.elevenlabs_style}, speed={self.elevenlabs_speed}")
            
        elif engine_type == "azure":
            self.azure_api_key = kwargs.get('api_key')
            self.azure_region = kwargs.get('region', 'westeurope')
            self.azure_voice = kwargs.get('voice', 'fr-FR-DeniseNeural')
            print(f"[TTS] Moteur Azure configuré: voix={self.azure_voice}, région={self.azure_region}")
            
        elif engine_type == "gtts":
            self.gtts_lang = kwargs.get('lang', 'fr')
            print(f"[TTS] Moteur gTTS configuré: langue={self.gtts_lang}")
            
        elif engine_type == "edge_tts":
            self.edge_tts_voice = kwargs.get('voice', 'fr-FR-DeniseNeural')
            print(f"[TTS] Moteur Edge TTS configuré: voix={self.edge_tts_voice}")
            
        elif engine_type == "fish_audio":
            self.fish_audio_api_key = kwargs.get('api_key')
            self.fish_audio_voice_id = kwargs.get('voice_id', '')
            self.fish_audio_model = kwargs.get('model', 's2-pro')
            self.fish_audio_latency = kwargs.get('latency', 'normal')
            self.fish_audio_chunk_length = int(kwargs.get('chunk_length', 200))
            self.fish_audio_normalize = bool(kwargs.get('normalize', True))
            self.fish_audio_mp3_bitrate = int(kwargs.get('mp3_bitrate', 128))
            self.fish_audio_emotion = kwargs.get('emotion', 'none')
            print(f"[TTS] Moteur Fish Audio configuré: voice_id={self.fish_audio_voice_id}, model={self.fish_audio_model}, latency={self.fish_audio_latency}, emotion={self.fish_audio_emotion}")
            
        elif engine_type == "cartesia":
            self.cartesia_api_key = kwargs.get('api_key')
            self.cartesia_voice_id = kwargs.get('voice_id', '')
            self.cartesia_model = kwargs.get('model', 'sonic-2')
            self.cartesia_speed = float(kwargs.get('speed', 1.0))
            self.cartesia_emotion = kwargs.get('emotion', 'neutral')
            print(f"[TTS] Moteur Cartesia configure: voice_id={self.cartesia_voice_id}, model={self.cartesia_model}, speed={self.cartesia_speed}, emotion={self.cartesia_emotion}")
            
        elif engine_type == "hume_ai":
            self.hume_ai_api_key = kwargs.get('api_key')
            self.hume_ai_voice_name = kwargs.get('voice_name', '')
            self.hume_ai_voice_id = kwargs.get('voice_id', '')
            self.hume_ai_description = kwargs.get('description', '')
            self.hume_ai_version = kwargs.get('version', 2)
            voice_info = self.hume_ai_voice_id or self.hume_ai_voice_name or 'dynamique'
            print(f"[TTS] Moteur Hume AI configuré: voice={voice_info}, version=Octave {self.hume_ai_version}")
            
        elif engine_type == "system":
            print("[TTS] Moteur système configuré")
            
        else:
            print(f"[TTS] ⚠️ Moteur non reconnu: {engine_type}")
    
    def get_engine_info(self) -> Dict:
        """
        Retourne les informations sur le moteur TTS actuel.
        
        Returns:
            Dictionnaire avec les infos du moteur
        """
        return {
            'engine_type': self.tts_engine_type,
            'google_voice': self.google_voice,
            'elevenlabs_voice_id': self.elevenlabs_voice_id,
            'azure_voice': self.azure_voice,
            'azure_region': self.azure_region,
            'system_voice_id': self.current_voice_id,
            'speed': self.tts_speed,
            'volume': self.tts_volume,
            'enabled': self.tts_enabled
        }


    async def speak_gtts(self, text: str, lang: str = 'fr') -> bool:
        """
        Synthèse vocale avec gTTS (Google Text-to-Speech offline)
        
        Args:
            text: Texte à synthétiser
            lang: Langue (fr, en, etc.)
        
        Returns:
            bool: Succès de la synthèse
        """
        if not GTTS_AVAILABLE or not PYGAME_AVAILABLE:
            print("[TTS] ❌ gTTS ou pygame non disponible")
            return False
            
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)
            
            print(f"[TTS] 🔊 Synthèse gTTS: '{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}'")
            self.is_speaking = True
            
            # Créer l'objet gTTS
            tts = gTTS(text=clean_text, lang=lang, slow=False)
            
            # Sauvegarder dans un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                temp_file_path = tmp_file.name

            # Hologramme : extraire l'enveloppe RMS réelle
            try:
                from extensions.hologram_projector.audio_analyzer import extract_rms_envelope
                from extensions.hologram_projector.state_emitter import send_envelope
                envelope = extract_rms_envelope(temp_file_path, interval_ms=50)
                if envelope:
                    send_envelope(envelope, interval_ms=50)
            except Exception as _e:
                print(f"[TTS-HOLOGRAM] Analyse audio ignorée : {_e}")

            # Jouer le fichier avec pygame
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # Attendre la fin de la lecture
            while pygame.mixer.music.get_busy() and self.is_speaking and not self._stop_requested:
                await asyncio.sleep(0.1)
            
            # Nettoyage
            try:
                os.unlink(temp_file_path)
            except:
                pass  # Ignore les erreurs de suppression
            
            print("[TTS] ✅ Synthèse gTTS terminée")
            return True
            
        except Exception as e:
            print(f"[TTS] ❌ Erreur gTTS: {e}")
            return False
        finally:
            self.is_speaking = False
    
    async def speak_edge_tts(self, text: str, voice: str = 'fr-FR-DeniseNeural') -> bool:
        """
        Synthèse vocale avec Microsoft Edge TTS
        
        Args:
            text: Texte à synthétiser  
            voice: Nom de la voix (ex: fr-FR-DeniseNeural)
        
        Returns:
            bool: Succès de la synthèse
        """
        if not EDGE_TTS_AVAILABLE or not PYGAME_AVAILABLE:
            print("[TTS] ❌ Edge TTS ou pygame non disponible")
            return False
            
        try:
            # Nettoyer le texte en supprimant les émojis
            clean_text = clean_text_for_tts(text)
            
            print(f"[TTS] 🔊 Synthèse Edge TTS: '{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}' (voix: {voice})")
            self.is_speaking = True
            
            # Créer la communication Edge TTS
            communicate = edge_tts.Communicate(clean_text, voice)
            
            # Sauvegarder dans un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                temp_file_path = tmp_file.name
            
            # Sauvegarder l'audio
            await communicate.save(temp_file_path)

            # ── Hologramme : extraire l'enveloppe RMS réelle et l'envoyer ──
            try:
                from extensions.hologram_projector.audio_analyzer import extract_rms_envelope
                from extensions.hologram_projector.state_emitter import send_envelope
                envelope = extract_rms_envelope(temp_file_path, interval_ms=50)
                if envelope:
                    send_envelope(envelope, interval_ms=50)
                    print(f"[TTS-HOLOGRAM] Enveloppe envoyée : {len(envelope)} frames")
            except Exception as _e:
                print(f"[TTS-HOLOGRAM] Analyse audio ignorée : {_e}")
            # ─────────────────────────────────────────────────────────────────

            # Jouer le fichier avec pygame
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # Attendre la fin de la lecture
            while pygame.mixer.music.get_busy() and self.is_speaking and not self._stop_requested:
                await asyncio.sleep(0.1)
            
            # Nettoyage (avec délai pour éviter les erreurs de fichier en cours d'utilisation)
            await asyncio.sleep(0.5)
            try:
                os.unlink(temp_file_path)
            except:
                pass  # Ignore les erreurs de suppression
                
            print("[TTS] ✅ Synthèse Edge TTS terminée")
            return True
            
        except Exception as e:
            print(f"[TTS] ❌ Erreur Edge TTS: {e}")
            return False
        finally:
            self.is_speaking = False
    
    async def get_edge_tts_voices(self, locale_filter: str = 'fr-') -> List[Dict]:
        """
        Récupère la liste des voix disponibles pour Edge TTS
        
        Args:
            locale_filter: Filtre par locale (ex: 'fr-' pour français)
        
        Returns:
            List[Dict]: Liste des voix avec leurs métadonnées
        """
        if not EDGE_TTS_AVAILABLE:
            return []
        
        try:
            voices = await edge_tts.list_voices()
            if locale_filter:
                filtered_voices = [v for v in voices if v.get('Locale', '').startswith(locale_filter)]
            else:
                filtered_voices = voices
            
            print(f"[TTS] 📋 {len(filtered_voices)} voix Edge TTS trouvées")
            return filtered_voices
            
        except Exception as e:
            print(f"[TTS] ❌ Erreur listage voix Edge TTS: {e}")
            return []

# === FONCTIONS UTILITAIRES ===

def test_microphone() -> bool:
    """Teste si le microphone fonctionne."""
    if not SR_AVAILABLE or not PYAUDIO_AVAILABLE:
        print("[AUDIO] Test micro indisponible : pyaudio/speech_recognition manquants")
        return False
    try:
        r = sr.Recognizer()
        mic = sr.Microphone()
        
        with mic as source:
            print("Test microphone... parlez maintenant:")
            audio = r.listen(source, timeout=3, phrase_time_limit=5)
        
        print("✅ Microphone fonctionne")
        return True
        
    except Exception as e:
        print(f"❌ Problème microphone: {e}")
        return False


if __name__ == "__main__":
    # Test rapide
    test_microphone()
