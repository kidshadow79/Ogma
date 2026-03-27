# audio_manager_wrapper.py

"""
OGMA Audio Manager Wrapper - Interface TTS/STT Unifiée
======================================================
Refonte v2.0 - Architecture unifiée pour tous les moteurs TTS

MOTEURS SUPPORTÉS:
- Edge TTS (Microsoft, gratuit, haute qualité)
- gTTS (Google Text-to-Speech, gratuit)
- Google Cloud TTS (API payante)
- ElevenLabs (API payante, voix IA)
- Azure Speech (API payante)
- Système (pyttsx3/SAPI Windows)

ARCHITECTURE:
- Délégation vers AudioManager pour méthodes TTS spécifiques
- ConflictFreeTTS pour synthèse générale sans conflits
- STT via AudioManager (Whisper API ou Google Speech)
"""

from .tts_utils import get_conflict_free_tts, speak_safe, set_perception_active
from typing import Optional, List, Dict

# Import du vrai AudioManager pour TTS avancé + STT
_real_audio_manager = None


def reload_stt_config():
    """Recharge la configuration STT depuis settings.json.
    Utile après modification des paramètres dans le profil."""
    global _real_audio_manager
    
    if _real_audio_manager is None:
        return
    
    try:
        from pathlib import Path
        import json
        settings_path = Path('data/settings.json')
        
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            stt_settings = settings.get('stt', {})
            
            # Chercher la clé API OpenAI
            openai_key = stt_settings.get('api_key') or stt_settings.get('openai_api_key')
            
            if not openai_key:
                for provider_key in ['openai_api', 'OpenAI']:
                    if settings.get(provider_key, {}).get('api_key'):
                        openai_key = settings[provider_key]['api_key']
                        break
            
            if not openai_key:
                chat_provider = settings.get('chat_api', {}).get('provider', '').lower()
                if chat_provider == 'openai':
                    openai_key = settings.get('chat_api', {}).get('api_key')
            
            # Mettre à jour l'AudioManager
            use_whisper = stt_settings.get('use_whisper_api', False) and bool(openai_key)
            _real_audio_manager.use_whisper_api = use_whisper
            _real_audio_manager.api_key = openai_key if use_whisper else None
            
            engine = "Whisper API" if use_whisper else "Google Speech"
            print(f"[AUDIO-WRAPPER] 🔄 Config STT rechargée: {engine}")
            
    except Exception as e:
        print(f"[AUDIO-WRAPPER] ⚠️ Erreur reload config STT: {e}")


def _get_real_audio_manager():
    """Récupère le vrai AudioManager avec configuration depuis settings."""
    global _real_audio_manager
    if _real_audio_manager is None:
        try:
            from .manager import AudioManager
            
            # Charger la configuration depuis settings
            use_whisper_api = False
            api_key = None
            device_index = None
            
            try:
                from pathlib import Path
                import json
                settings_path = Path('data/settings.json')
                if settings_path.exists():
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    
                    # Vérifier si on utilise l'API Whisper (OpenAI)
                    stt_settings = settings.get('stt', {})
                    
                    # 1. Chercher clé STT dédiée dans settings.stt
                    openai_key = stt_settings.get('api_key') or stt_settings.get('openai_api_key')
                    
                    # 2. Chercher dans openai_api ou OpenAI sections
                    if not openai_key:
                        for provider_key in ['openai_api', 'OpenAI']:
                            if settings.get(provider_key, {}).get('api_key'):
                                openai_key = settings[provider_key]['api_key']
                                break
                    
                    # 3. En dernier recours, chat_api SEULEMENT si c'est OpenAI
                    if not openai_key:
                        chat_provider = settings.get('chat_api', {}).get('provider', '').lower()
                        if chat_provider == 'openai':
                            openai_key = settings.get('chat_api', {}).get('api_key')
                    
                    # Configuration STT
                    use_whisper_api = stt_settings.get('use_whisper_api', True) and bool(openai_key)
                    api_key = openai_key
                    
                    # Récupérer le device_index du microphone si configuré
                    device_index = stt_settings.get('device_index', None)
                    
                    if use_whisper_api and api_key:
                        print(f"[AUDIO-WRAPPER] 🎤 Mode Whisper API activé")
                    else:
                        print(f"[AUDIO-WRAPPER] 🎤 Mode Google Speech (fallback - pas de clé OpenAI)")
                        use_whisper_api = False
                        
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ⚠️ Config STT par défaut: {e}")
                device_index = None
            
            _real_audio_manager = AudioManager(use_whisper_api=use_whisper_api, api_key=api_key)
            
            # Configurer le device_index si spécifié
            if device_index is not None:
                _real_audio_manager.device_index = device_index
                print(f"[AUDIO-WRAPPER] 🎤 Microphone configuré: index {device_index}")
            
            # Initialiser TTS système pour voix système disponibles
            try:
                _real_audio_manager.initialize_tts_sync()
                print(f"[AUDIO-WRAPPER] ✅ AudioManager chargé + {len(_real_audio_manager.available_voices)} voix système")
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ⚠️ Voix système non chargées: {e}")
                print("[AUDIO-WRAPPER] ✅ AudioManager chargé (TTS + STT)")
                
        except Exception as e:
            print(f"[AUDIO-WRAPPER] ❌ Erreur chargement AudioManager: {e}")
    return _real_audio_manager


class AudioManagerWrapper:
    """Wrapper pour compatibilité avec ancien AudioManager - TTS + STT"""
    
    def __init__(self):
        self.tts_safe = get_conflict_free_tts()
        self.initialized = False
        self._stt_initialized = False
        
        # Queue pour le streaming TTS cloud (Hume AI, ElevenLabs, etc.)
        import queue as queue_module
        import threading
        self._queue_module = queue_module  # Garder référence pour accès dans méthodes
        self._cloud_tts_queue = queue_module.Queue()
        self._cloud_tts_worker_running = False
        self._cloud_tts_worker_thread = None
    
    def initialize_tts(self):
        """Initialise le TTS (compatibilité)"""
        if not self.initialized:
            self.tts_safe.initialize()
            self.initialized = True
            print("[AUDIO-WRAPPER] ✅ TTS sans conflit initialisé")
        return True
    
    def _start_cloud_tts_worker(self):
        """Démarre le worker de queue TTS cloud si pas déjà actif"""
        import threading
        if self._cloud_tts_worker_running and self._cloud_tts_worker_thread and self._cloud_tts_worker_thread.is_alive():
            return
        
        self._cloud_tts_worker_running = True
        self._cloud_tts_worker_thread = threading.Thread(target=self._cloud_tts_worker, daemon=True)
        self._cloud_tts_worker_thread.start()
        print("[TTS-CLOUD-QUEUE] 🚀 Worker TTS cloud démarré")
    
    def _cloud_tts_worker(self):
        """Worker thread pour lire les phrases cloud TTS en séquence"""
        import asyncio
        import time
        import traceback
        
        print("[TTS-CLOUD-QUEUE] 🚀 Worker thread démarré")
        
        while self._cloud_tts_worker_running:
            try:
                # Attendre une phrase avec timeout
                sentence = self._cloud_tts_queue.get(timeout=10.0)
                
                if sentence is None:  # Signal d'arrêt
                    print("[TTS-CLOUD-QUEUE] 📤 Signal arrêt reçu")
                    break
                
                # Synthétiser la phrase avec le moteur cloud configuré
                print(f"[TTS-CLOUD-QUEUE] 🔊 Lecture: '{sentence[:40]}...'")
                
                # Exécuter la méthode speak() synchrone (qui gère l'async internement)
                try:
                    self.speak(sentence)
                except Exception as e:
                    print(f"[TTS-CLOUD-QUEUE] ⚠️ Erreur synthèse: {e}")
                    traceback.print_exc()
                
                self._cloud_tts_queue.task_done()
                
            except self._queue_module.Empty:
                # Timeout normal, continue à attendre
                continue
            except Exception as e:
                print(f"[TTS-CLOUD-QUEUE] ❌ Erreur worker: {e}")
                traceback.print_exc()
                continue
        
        self._cloud_tts_worker_running = False
        print("[TTS-CLOUD-QUEUE] 🛑 Worker TTS cloud arrêté")
    
    def _queue_cloud_tts(self, sentence: str):
        """Ajoute une phrase à la queue TTS cloud"""
        self._start_cloud_tts_worker()
        self._cloud_tts_queue.put(sentence)
    
    def _clear_cloud_tts_queue(self):
        """Vide la queue TTS cloud"""
        try:
            while True:
                self._cloud_tts_queue.get_nowait()
        except self._queue_module.Empty:
            pass
        print("[TTS-CLOUD-QUEUE] 🗑️ Queue vidée")
    
    async def initialize(self):
        """Initialise TTS + STT (pour compatibilité avec record_manual_control)"""
        # Initialiser TTS
        self.initialize_tts()
        
        # Initialiser STT via le vrai AudioManager
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.initialize()
                self._stt_initialized = result
                if result:
                    print("[AUDIO-WRAPPER] ✅ STT initialisé via AudioManager")
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur init STT: {e}")
                return False
        return False
    
    async def record_manual_control(self):
        """Enregistrement manuel - délègue au vrai AudioManager"""
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                if not self._stt_initialized:
                    await self.initialize()
                return await real_am.record_manual_control()
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur record_manual_control: {e}")
                return None
        else:
            print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour STT")
            return None
    
    async def record_once(
        self, 
        timeout: float = 8.0,
        phrase_time_limit: float = None,
        pause_threshold: float = None
    ):
        """Enregistrement une fois - délègue au vrai AudioManager"""
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                if not self._stt_initialized:
                    await self.initialize()
                return await real_am.record_once(timeout, phrase_time_limit, pause_threshold)
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur record_once: {e}")
                return None
        return None
    
    def stop_manual_recording(self):
        """Arrête l'enregistrement manuel"""
        real_am = _get_real_audio_manager()
        if real_am:
            real_am.stop_manual_recording()
    
    def speak(self, text, voice=None, speed=None, volume=None):
        """Interface speak compatible (synchrone) - utilise le moteur configuré"""
        if not self.initialized:
            self.initialize_tts()
        
        # Vérifier si un moteur spécifique est configuré
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'tts_engine_type'):
            engine = real_am.tts_engine_type
            if engine in ('elevenlabs', 'google', 'azure', 'gtts', 'edge_tts', 'fish_audio', 'cartesia', 'hume_ai'):
                print(f"[AUDIO-WRAPPER] 🎤 speak() → moteur configuré: {engine}")
                # Exécuter la méthode async speak() du vrai AudioManager de manière synchrone
                import asyncio
                try:
                    # Créer une nouvelle boucle pour ce thread (nécessaire car appelé depuis un thread séparé)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(real_am.speak(text))
                        return result
                    finally:
                        loop.close()
                except Exception as e:
                    print(f"[AUDIO-WRAPPER] ⚠️ Erreur {engine} dans speak(), fallback speak_safe: {e}")
        
        # Fallback sur speak_safe (conflict_free/gtts)
        options = {}
        if voice:
            options["voice"] = voice
        if speed:
            options["rate"] = f"{speed:+d}%"
        if volume:
            options["volume"] = volume
        
        return speak_safe(text, **options)
    
    async def speak_async(self, text, voice=None, speed=None, volume=None):
        """Interface speak async - utilise le moteur configuré dans settings"""
        real_am = _get_real_audio_manager()
        
        # Debug: afficher l'état du moteur
        if real_am:
            engine = getattr(real_am, 'tts_engine_type', 'N/A')
            voice_id = getattr(real_am, 'elevenlabs_voice_id', 'N/A')
            print(f"[AUDIO-WRAPPER] 🔍 DEBUG speak_async: engine={engine}, elevenlabs_voice_id={voice_id}")
        
        # Si le vrai AudioManager a un moteur spécifique configuré (pas system/conflict_free)
        # utiliser sa méthode speak() qui gère elevenlabs, google, azure, fish_audio, cartesia, hume_ai, etc.
        if real_am and hasattr(real_am, 'tts_engine_type'):
            engine = real_am.tts_engine_type
            if engine in ('elevenlabs', 'google', 'azure', 'gtts', 'edge_tts', 'fish_audio', 'cartesia', 'hume_ai'):
                print(f"[AUDIO-WRAPPER] 🎤 Utilisation moteur configuré: {engine}")
                try:
                    # real_am.speak() est async, on l'attend directement
                    return await real_am.speak(text)
                except Exception as e:
                    print(f"[AUDIO-WRAPPER] ⚠️ Erreur {engine}, fallback speak_safe: {e}")
        
        # Fallback sur speak_safe (conflict_free/gtts)
        result = self.speak(text, voice, speed, volume)
        return result
    
    def configure_tts_engine(self, engine_type: str, **kwargs):
        """Configure le moteur TTS - délègue au vrai AudioManager"""
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'configure_tts_engine'):
            print(f"[AUDIO-WRAPPER] ⚙️ Configuration TTS: engine={engine_type}, kwargs={list(kwargs.keys())}")
            if 'voice_id' in kwargs:
                print(f"[AUDIO-WRAPPER] ⚙️ voice_id reçu: {kwargs['voice_id']}")
            real_am.configure_tts_engine(engine_type, **kwargs)
            # Vérifier que la config a bien été appliquée
            if engine_type == 'elevenlabs':
                print(f"[AUDIO-WRAPPER] ✅ Après config: elevenlabs_voice_id={real_am.elevenlabs_voice_id}")
            print(f"[AUDIO-WRAPPER] ⚙️ Moteur TTS configuré: {engine_type}")
        else:
            print(f"[AUDIO-WRAPPER] ⚠️ AudioManager non disponible pour configure_tts_engine")
    
    def set_tts_settings(self, **kwargs):
        """Configure les paramètres TTS - délègue au vrai AudioManager"""
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'set_tts_settings'):
            real_am.set_tts_settings(**kwargs)
    
    def set_perception_mode(self, active):
        """Notifie l'état Perception (nouveau)"""
        set_perception_active(active)
    
    def stop_speaking(self):
        """Arrête la synthèse vocale en cours et vide la queue cloud"""
        # Vider la queue cloud TTS en premier
        self._clear_cloud_tts_queue()
        
        # Arrêter le vrai AudioManager (pour les moteurs cloud)
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'stop_speaking'):
            real_am.stop_speaking()
        
        # Arrêter tts_safe (pour les moteurs locaux)
        if not self.initialized:
            return False
        return self.tts_safe.stop_speech()
    
    # =========================================================================
    # MÉTHODES TTS SPÉCIFIQUES - Délégation vers AudioManager
    # =========================================================================
    
    async def speak_gtts(self, text: str, lang: str = 'fr') -> bool:
        """
        Synthèse vocale avec gTTS (Google Text-to-Speech offline)
        
        Args:
            text: Texte à synthétiser
            lang: Langue (fr, en, etc.)
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_gtts(text, lang)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_gtts: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour gTTS")
        return False
    
    async def speak_edge_tts(self, text: str, voice: str = 'fr-FR-DeniseNeural') -> bool:
        """
        Synthèse vocale avec Microsoft Edge TTS
        
        Args:
            text: Texte à synthétiser  
            voice: Nom de la voix (ex: fr-FR-DeniseNeural)
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_edge_tts(text, voice)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_edge_tts: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour Edge TTS")
        return False
    
    async def speak_google_tts(self, text: str, voice_name: str, api_key: str) -> bool:
        """
        Synthèse vocale avec Google Cloud TTS (API payante)
        
        Args:
            text: Texte à synthétiser
            voice_name: Nom de la voix Google Cloud
            api_key: Clé API Google Cloud
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_google_tts(text, voice_name, api_key)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_google_tts: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour Google Cloud TTS")
        return False
    
    async def speak_elevenlabs(self, text: str, voice_id: str, api_key: str) -> bool:
        """
        Synthèse vocale avec ElevenLabs
        
        Args:
            text: Texte à synthétiser
            voice_id: ID de la voix ElevenLabs
            api_key: Clé API ElevenLabs
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_elevenlabs(text, voice_id, api_key)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_elevenlabs: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour ElevenLabs")
        return False
    
    async def speak_azure(self, text: str, voice: str = None, api_key: str = None, region: str = None) -> bool:
        """
        Synthèse vocale avec Azure Speech
        
        Args:
            text: Texte à synthétiser
            voice: Nom de la voix Azure (optionnel, utilise settings)
            api_key: Clé API Azure (optionnel, utilise settings)
            region: Région Azure (optionnel, utilise settings)
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                # Charger config depuis settings si non fourni
                if voice is None or api_key is None or region is None:
                    try:
                        from pathlib import Path
                        import json
                        settings_path = Path('data/settings.json')
                        if settings_path.exists():
                            with open(settings_path, 'r', encoding='utf-8') as f:
                                settings = json.load(f)
                            tts_settings = settings.get('tts', {})
                            if voice is None:
                                voice = tts_settings.get('azure_voice', 'fr-FR-DeniseNeural')
                            if api_key is None:
                                api_key = tts_settings.get('azure_api_key', '')
                            if region is None:
                                region = tts_settings.get('azure_region', 'eastus')
                    except Exception:
                        pass
                
                result = await real_am.speak_azure(text, voice, api_key, region)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_azure: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour Azure Speech")
        return False
    
    async def speak_system(self, text: str) -> bool:
        """
        Synthèse vocale avec le moteur système (pyttsx3/SAPI)
        
        Args:
            text: Texte à synthétiser
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_system(text)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_system: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour System TTS")
        return False
    
    async def speak_fish_audio(self, text: str, voice_id: str, api_key: str) -> bool:
        """
        Synthèse vocale avec Fish Audio
        
        Args:
            text: Texte à synthétiser
            voice_id: Reference ID de la voix Fish Audio
            api_key: Clé API Fish Audio
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_fish_audio(text, voice_id, api_key)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_fish_audio: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour Fish Audio")
        return False
    
    async def speak_cartesia(self, text: str, voice_id: str, api_key: str, model: str = "sonic-2") -> bool:
        """
        Synthèse vocale avec Cartesia AI
        
        Args:
            text: Texte à synthétiser
            voice_id: ID de la voix Cartesia
            api_key: Clé API Cartesia
            model: Modèle à utiliser (sonic-2 ou sonic-3)
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_cartesia(text, voice_id, api_key, model)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_cartesia: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour Cartesia")
        return False
    
    async def speak_hume_ai(self, text: str, voice_name: str, api_key: str, description: str = "", voice_id: str = "", version: int = 2) -> bool:
        """
        Synthèse vocale avec Hume AI (Octave TTS)
        
        Args:
            text: Texte à synthétiser
            voice_name: Nom de la voix Hume (Voice Library)
            api_key: Clé API Hume AI
            description: Description pour génération dynamique de voix
            voice_id: ID de voix personnalisée (prioritaire sur voice_name)
            version: Version Octave (1 ou 2)
        
        Returns:
            bool: Succès de la synthèse
        """
        real_am = _get_real_audio_manager()
        if real_am:
            try:
                result = await real_am.speak_hume_ai(text, voice_name, api_key, description, voice_id, version)
                return result
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur speak_hume_ai: {e}")
                return False
        print("[AUDIO-WRAPPER] ❌ AudioManager non disponible pour Hume AI")
        return False
    
    # =========================================================================
    # MÉTHODES CONFIGURATION - Délégation vers AudioManager
    # =========================================================================
    
    def get_available_voices(self) -> List[Dict]:
        """
        Récupère la liste des voix système disponibles
        
        Returns:
            List[Dict]: Liste des voix avec id, name, language, gender
        """
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'get_available_voices'):
            try:
                return real_am.get_available_voices()
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur get_available_voices: {e}")
        return []
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Définit la voix système à utiliser
        
        Args:
            voice_id: ID de la voix
        
        Returns:
            bool: Succès
        """
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'set_voice'):
            try:
                return real_am.set_voice(voice_id)
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur set_voice: {e}")
        return False
    
    def set_tts_settings(self, speed: Optional[int] = None, volume: Optional[float] = None, enabled: Optional[bool] = None):
        """
        Configure les paramètres TTS
        
        Args:
            speed: Vitesse de parole (mots/min)
            volume: Volume (0.0 à 1.0)
            enabled: TTS activé/désactivé
        """
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'set_tts_settings'):
            try:
                real_am.set_tts_settings(speed=speed, volume=volume, enabled=enabled)
            except Exception as e:
                print(f"[AUDIO-WRAPPER] ❌ Erreur set_tts_settings: {e}")
    
    def is_speaking(self) -> bool:
        """Vérifie si une synthèse vocale est en cours"""
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'is_speaking'):
            return real_am.is_speaking
        return self.tts_safe.is_playing if self.tts_safe else False
    
    # =========================================================================
    # MÉTHODES TTS STREAMING - Pour lecture pendant le streaming
    # =========================================================================
    
    def process_streaming_chunk(self, chunk: str) -> list:
        """
        Traite un chunk de texte streaming et retourne les phrases complètes.
        
        Args:
            chunk: Morceau de texte reçu du streaming
            
        Returns:
            Liste des phrases complètes à lire
        """
        if self.tts_safe and hasattr(self.tts_safe, 'process_streaming_chunk'):
            return self.tts_safe.process_streaming_chunk(chunk)
        return []
    
    def speak_streaming_sentence(self, sentence: str):
        """
        Lit une phrase complète de manière non-bloquante.
        Utilise le moteur TTS configuré (Hume AI, ElevenLabs, etc.) via une queue.
        
        Args:
            sentence: Phrase complète à lire
        """
        if not sentence or len(sentence.strip()) < 3:
            return
            
        # Nettoyer le markdown/caractères spéciaux
        clean_sentence = sentence.replace('*', '').replace('**', '').replace('#', '').replace('`', '').strip()
        if not clean_sentence:
            return
        
        # Vérifier si un moteur cloud est configuré (Hume AI, ElevenLabs, etc.)
        real_am = _get_real_audio_manager()
        if real_am and hasattr(real_am, 'tts_engine_type'):
            engine = real_am.tts_engine_type
            if engine in ('elevenlabs', 'google', 'azure', 'fish_audio', 'cartesia', 'hume_ai'):
                # Utiliser la queue TTS cloud pour enchaîner les phrases sans interruption
                print(f"[TTS-STREAM] 🎤 Queue ({engine}): '{clean_sentence[:40]}...'")
                self._queue_cloud_tts(clean_sentence)
                return
        
        # Fallback sur tts_safe (gTTS) pour les moteurs locaux
        if self.tts_safe and hasattr(self.tts_safe, 'speak_streaming_sentence'):
            self.tts_safe.speak_streaming_sentence(sentence)
    
    def flush_streaming_buffer(self):
        """
        Vide le buffer streaming et lit le texte restant via le moteur configuré.
        À appeler à la fin du streaming.
        """
        # Récupérer le buffer restant de tts_safe
        if self.tts_safe and hasattr(self.tts_safe, '_streaming_buffer'):
            remaining = self.tts_safe._streaming_buffer.strip() if self.tts_safe._streaming_buffer else ""
            self.tts_safe._streaming_buffer = ""  # Vider le buffer
            
            if remaining and len(remaining) > 3:
                # Utiliser speak_streaming_sentence (qui route vers cloud ou fallback)
                self.speak_streaming_sentence(remaining)
    
    def reset_streaming(self):
        """
        Réinitialise le buffer de streaming et vide la queue cloud.
        À appeler avant de commencer un nouveau streaming.
        """
        # Vider la queue cloud TTS
        self._clear_cloud_tts_queue()
        
        if self.tts_safe and hasattr(self.tts_safe, 'reset_streaming'):
            self.tts_safe.reset_streaming()
    
    def set_streaming_enabled(self, enabled: bool):
        """
        Active/désactive le mode TTS streaming.
        
        Args:
            enabled: True pour activer, False pour désactiver
        """
        if self.tts_safe and hasattr(self.tts_safe, 'set_streaming_enabled'):
            self.tts_safe.set_streaming_enabled(enabled)
    
    def cleanup(self):
        """Nettoyage"""
        if self.initialized:
            self.tts_safe.stop()
            self.initialized = False

# Instance globale pour compatibilité
_audio_manager = None

def get_audio_manager():
    """Récupère instance compatible AudioManager"""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManagerWrapper()
    return _audio_manager

# Fonctions legacy pour compatibilité
def speak_text(text, **kwargs):
    """Fonction legacy speak_text"""
    return get_audio_manager().speak(text, **kwargs)

def initialize_audio():
    """Fonction legacy initialize_audio"""
    return get_audio_manager().initialize_tts()
