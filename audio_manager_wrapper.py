# audio_manager_wrapper.py

"""
Wrapper de compatibilité pour l'ancien audio_manager
Redirige vers le nouveau TTS sans conflit
"""

from tts_conflict_free import get_conflict_free_tts, speak_safe, set_perception_active

class AudioManagerWrapper:
    """Wrapper pour compatibilité avec ancien AudioManager"""
    
    def __init__(self):
        self.tts_safe = get_conflict_free_tts()
        self.initialized = False
    
    def initialize_tts(self):
        """Initialise le TTS (compatibilité)"""
        if not self.initialized:
            self.tts_safe.initialize()
            self.initialized = True
            print("[AUDIO-WRAPPER] ✅ TTS sans conflit initialisé")
        return True
    
    def speak(self, text, voice=None, speed=None, volume=None):
        """Interface speak compatible"""
        if not self.initialized:
            self.initialize_tts()
        
        options = {}
        if voice:
            options["voice"] = voice
        if speed:
            options["rate"] = f"{speed:+d}%"
        if volume:
            options["volume"] = volume
        
        return speak_safe(text, **options)
    
    def set_perception_mode(self, active):
        """Notifie l'état Perception (nouveau)"""
        set_perception_active(active)
    
    def stop_speaking(self):
        """Arrête la synthèse vocale en cours"""
        if not self.initialized:
            return False
        return self.tts_safe.stop_speech()
    
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
