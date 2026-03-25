"""
modules/voice/voice_manager.py
==============================
Gestionnaire principal de conversation vocale pour OGMA

Machine à états :
- INACTIVE : Micro complètement off
- STANDBY : Écoute trigger d'activation ("Louna Louna")
- LISTENING : Transcription live dans zone de message
- SPEAKING : Luna répond, écoute trigger interruption

Auteur: Yohan BROCARD
Date: Janvier 2026
"""

import asyncio
import threading
import time
from enum import Enum, auto
from typing import Optional, Callable, Any
from pathlib import Path
import json


class VoiceState(Enum):
    """États de la machine vocale"""
    INACTIVE = auto()   # Micro off
    STANDBY = auto()    # Écoute trigger activation
    LISTENING = auto()  # Transcription live
    SPEAKING = auto()   # Luna parle (TTS)


class VoiceManager:
    """
    Gestionnaire de conversation vocale avec machine à états.
    
    Usage:
        voice_manager = VoiceManager(settings_manager, audio_manager)
        voice_manager.set_callbacks(
            on_state_change=update_ui,
            on_transcription=update_input,
            on_message_ready=send_message
        )
        
        # Activation via focus zone message
        voice_manager.activate()    # INACTIVE -> STANDBY
        voice_manager.deactivate()  # -> INACTIVE
    """
    
    def __init__(self, settings_manager=None, audio_manager=None):
        """
        Initialise le gestionnaire vocal.
        
        Args:
            settings_manager: Gestionnaire de settings OGMA
            audio_manager: Gestionnaire audio pour STT/TTS
        """
        self.settings_manager = settings_manager
        self.audio_manager = audio_manager
        
        # État machine
        self._state = VoiceState.INACTIVE
        self._state_lock = threading.Lock()
        
        # Thread d'écoute
        self._listening_thread: Optional[threading.Thread] = None
        self._stop_requested = False
        
        # Texte accumulé
        self._accumulated_text = ""
        
        # Triggers (chargés depuis settings)
        self._trigger_activation = "louna louna"
        self._trigger_send = "point final"
        
        # Paramètres d'écoute (configurables depuis frontend)
        self._listening_timeout = 1.0      # Timeout pour commencer à parler
        self._phrase_time_limit = 15.0     # Durée max par segment
        self._pause_threshold = 3.0        # Silence avant coupure
        self._continuous_mode = False      # Mode conversation continue (pas de trigger d'activation)
        self._auto_send_delay = 5.0        # Délai de silence avant envoi automatique (0 = désactivé)
        
        # Timer pour silence intelligent
        self._last_speech_time: Optional[float] = None
        
        # Callbacks
        self._on_state_change: Optional[Callable[[VoiceState], None]] = None
        self._on_transcription: Optional[Callable[[str], None]] = None
        self._on_message_ready: Optional[Callable[[str], None]] = None
        self._on_status_text: Optional[Callable[[str], None]] = None
        self._get_current_text: Optional[Callable[[], str]] = None  # Callback pour lire le texte du frontend
        
        # Event loop principal pour callbacks thread-safe
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Charger la config
        self._load_config()
        
        print("[VOICE] 🎙️ VoiceManager initialisé")
    
    def _load_config(self):
        """Charge la configuration depuis settings"""
        try:
            if self.settings_manager:
                voice_config = self.settings_manager.settings.get('voice', {})
                self._trigger_activation = voice_config.get('trigger_activation', 'louna louna').lower()
                self._trigger_send = voice_config.get('trigger_send', 'point final').lower()
                
                # Paramètres d'écoute
                self._listening_timeout = float(voice_config.get('listening_timeout', 1.0))
                self._phrase_time_limit = float(voice_config.get('phrase_time_limit', 15.0))
                self._pause_threshold = float(voice_config.get('pause_threshold', 3.0))
                self._continuous_mode = voice_config.get('continuous_mode', False)
                self._auto_send_delay = float(voice_config.get('auto_send_delay', 5.0))
            else:
                # Fallback: charger depuis fichier
                settings_path = Path('data/settings.json')
                if settings_path.exists():
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    voice_config = settings.get('voice', {})
                    self._trigger_activation = voice_config.get('trigger_activation', 'louna louna').lower()
                    self._trigger_send = voice_config.get('trigger_send', 'point final').lower()
                    
                    # Paramètres d'écoute
                    self._listening_timeout = float(voice_config.get('listening_timeout', 1.0))
                    self._phrase_time_limit = float(voice_config.get('phrase_time_limit', 15.0))
                    self._pause_threshold = float(voice_config.get('pause_threshold', 3.0))
                    self._continuous_mode = voice_config.get('continuous_mode', False)
                    self._auto_send_delay = float(voice_config.get('auto_send_delay', 5.0))
            
            print(f"[VOICE] 📋 Config: activation='{self._trigger_activation}', envoi='{self._trigger_send}', continu={self._continuous_mode}, auto_send={self._auto_send_delay}s")
            print(f"[VOICE] 🎙️ Audio: timeout={self._listening_timeout}s, phrase={self._phrase_time_limit}s, pause={self._pause_threshold}s")
        except Exception as e:
            print(f"[VOICE] ⚠️ Erreur chargement config: {e}")
    
    def reload_config(self):
        """Recharge la configuration (appelé après changement dans UI)"""
        self._load_config()
    
    # ==================== CALLBACKS ====================
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable[[VoiceState], None]] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_message_ready: Optional[Callable[[str], None]] = None,
        on_status_text: Optional[Callable[[str], None]] = None,
        get_current_text: Optional[Callable[[], str]] = None
    ):
        """
        Définit les callbacks pour la communication avec l'UI.
        
        Args:
            get_current_text: Callback pour lire le texte actuel du frontend (source unique de vérité)
        """
        self._on_state_change = on_state_change
        self._on_transcription = on_transcription
        self._on_message_ready = on_message_ready
        self._on_status_text = on_status_text
        self._get_current_text = get_current_text
    
    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """Définit l'event loop principal pour callbacks thread-safe"""
        self._main_loop = loop
        print(f"[VOICE] ✅ Event loop configuré")
    
    def _notify_state_change(self, new_state: VoiceState):
        """Notifie le changement d'état (thread-safe via queue dans ogma_ng)"""
        if self._on_state_change:
            try:
                # Les callbacks utilisent maintenant un système de queue
                # qui sera traité par le timer NiceGUI
                self._on_state_change(new_state)
            except Exception as e:
                print(f"[VOICE] ⚠️ Erreur notification état: {e}")
    
    def _notify_transcription(self, text: str):
        """Notifie la transcription (thread-safe via queue dans ogma_ng)"""
        if self._on_transcription:
            try:
                self._on_transcription(text)
            except Exception as e:
                print(f"[VOICE] ⚠️ Erreur notification transcription: {e}")
    
    def _notify_message_ready(self, message: str):
        """Notifie qu'un message est prêt à envoyer (thread-safe via queue)"""
        if self._on_message_ready:
            try:
                self._on_message_ready(message)
            except Exception as e:
                print(f"[VOICE] ⚠️ Erreur notification message: {e}")
    
    def _notify_status(self, status: str):
        """Notifie le texte de statut (thread-safe via queue)"""
        if self._on_status_text:
            try:
                self._on_status_text(status)
            except Exception as e:
                print(f"[VOICE] ⚠️ Erreur notification status: {e}")
    
    # ==================== PROPRIÉTÉS ====================
    
    @property
    def state(self) -> VoiceState:
        """État actuel de la machine vocale"""
        with self._state_lock:
            return self._state
    
    @property
    def is_active(self) -> bool:
        """Retourne True si le système vocal est actif (pas INACTIVE)"""
        return self.state != VoiceState.INACTIVE
    
    @property
    def is_listening(self) -> bool:
        """Retourne True si en mode transcription"""
        return self.state == VoiceState.LISTENING
    
    @property
    def is_speaking(self) -> bool:
        """Retourne True si Luna parle"""
        return self.state == VoiceState.SPEAKING
    
    @property
    def accumulated_text(self) -> str:
        """Texte accumulé en cours de dictée"""
        return self._accumulated_text
    
    def sync_accumulated_text(self, current_field_value: str):
        """
        Synchronise le texte accumulé avec la valeur actuelle du champ.
        Appelé quand l'utilisateur modifie manuellement le champ.
        OPTIMISATION: Appelé uniquement si mode vocal actif.
        
        Args:
            current_field_value: Valeur actuelle du champ de saisie
        """
        if current_field_value != self._accumulated_text:
            self._accumulated_text = current_field_value
            # Log désactivé par défaut pour éviter spam (réactiver si debug nécessaire)
            # print(f"[VOICE] 🔄 Sync texte: {len(current_field_value)} chars")
    
    def clear_accumulated_text(self):
        """Efface le texte accumulé (appelé quand l'utilisateur efface le champ)"""
        if self._accumulated_text:
            print("[VOICE] 🗑️ Texte accumulé effacé")
            self._accumulated_text = ""
    
    # ==================== TRANSITIONS D'ÉTAT ====================
    
    def _set_state(self, new_state: VoiceState):
        """Change l'état interne et notifie"""
        with self._state_lock:
            old_state = self._state
            if old_state == new_state:
                return
            
            self._state = new_state
            print(f"[VOICE] 🔄 État: {old_state.name} → {new_state.name}")
        
        self._notify_state_change(new_state)
    
    def activate(self):
        """
        Active le système vocal (appelé au focus sur zone message).
        Transition: INACTIVE -> STANDBY (normal) ou INACTIVE -> LISTENING (mode continu)
        """
        if self.state != VoiceState.INACTIVE:
            print("[VOICE] ⚠️ Déjà actif, ignoré")
            return
        
        # Recharger config pour capter les changements depuis le frontend
        self.reload_config()
        
        self._stop_requested = False
        self._accumulated_text = ""
        self._last_speech_time = None  # Reset timer silence intelligent
        
        # Mode conversation continue: passer directement en LISTENING
        if self._continuous_mode:
            print("[VOICE] 🔥 Mode continu: activation directe en LISTENING")
            self._set_state(VoiceState.LISTENING)
            self._notify_status("🎤 Parlez...")
        else:
            # Mode normal: attendre le trigger d'activation
            self._set_state(VoiceState.STANDBY)
            self._notify_status(f"💤 Dites \"{self._trigger_activation}\"...")
        
        # Démarrer l'écoute en arrière-plan
        self._start_listening_thread()
    
    def deactivate(self):
        """
        Désactive le système vocal (appelé au blur de zone message).
        Transition: * -> INACTIVE
        """
        if self.state == VoiceState.INACTIVE:
            return
        
        print("[VOICE] ⏹️ Désactivation...")
        self._stop_requested = True
        self._accumulated_text = ""
        
        # Stopper le TTS si en cours
        self._stop_tts()
        
        self._set_state(VoiceState.INACTIVE)
        self._notify_status("")
    
    def notify_tts_started(self):
        """
        Appelé quand le TTS commence à parler.
        Transition: LISTENING -> SPEAKING
        """
        if self.state == VoiceState.INACTIVE:
            return
        
        print("[VOICE] 🔊 TTS démarré")
        self._accumulated_text = ""  # Reset pour ne pas capturer Luna
        self._set_state(VoiceState.SPEAKING)
        self._notify_status("🌸 Luna répond...")
    
    def notify_tts_finished(self):
        """
        Appelé quand le TTS a fini de parler.
        Transition: SPEAKING -> STANDBY (normal) ou SPEAKING -> LISTENING (mode continu)
        """
        if self.state != VoiceState.SPEAKING:
            return
        
        print("[VOICE] ✅ TTS terminé")
        
        # Délai anti-écho
        time.sleep(0.5)
        
        # Mode conversation continue: passer directement en LISTENING
        if self._continuous_mode:
            print("[VOICE] 🔄 Mode continu: passage direct en LISTENING")
            self._accumulated_text = ""
            self._set_state(VoiceState.LISTENING)
            self._notify_status("🎤 Parlez...")
        else:
            # Mode normal: retour en STANDBY, attente trigger d'activation
            self._set_state(VoiceState.STANDBY)
            self._notify_status(f"💤 Dites \"{self._trigger_activation}\"...")
    
    # ==================== LOGIQUE D'ÉCOUTE ====================
    
    def _start_listening_thread(self):
        """Démarre le thread d'écoute en arrière-plan"""
        if self._listening_thread and self._listening_thread.is_alive():
            return
        
        self._listening_thread = threading.Thread(
            target=self._listening_loop,
            daemon=True,
            name="VoiceListeningThread"
        )
        self._listening_thread.start()
    
    def _listening_loop(self):
        """
        Boucle principale d'écoute.
        Comportement différent selon l'état :
        - STANDBY: Écoute trigger d'activation uniquement
        - LISTENING: Transcription complète
        - SPEAKING: Écoute trigger d'interruption
        """
        print("[VOICE] 🎤 Thread d'écoute démarré")
        
        try:
            # Importer le trigger detector
            from .voice_triggers import TriggerDetector
            
            # On stocke les triggers actuels pour détecter les changements
            last_activation = self._trigger_activation
            last_send = self._trigger_send
            
            trigger_detector = TriggerDetector(
                self._trigger_activation,
                self._trigger_send
            )
            
            # Obtenir l'audio manager
            from audio_manager_wrapper import get_audio_manager
            audio_mgr = get_audio_manager()
            
            if not audio_mgr:
                print("[VOICE] ❌ Audio manager non disponible")
                self._set_state(VoiceState.INACTIVE)
                return
            
            # Créer un event loop pour ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                while not self._stop_requested and self.state != VoiceState.INACTIVE:
                    current_state = self.state
                    
                    # Vérifier si les triggers ont changé (modifiés via UI)
                    if self._trigger_activation != last_activation or self._trigger_send != last_send:
                        print(f"[VOICE] 🔄 Triggers mis à jour: '{self._trigger_activation}' / '{self._trigger_send}'")
                        last_activation = self._trigger_activation
                        last_send = self._trigger_send
                        trigger_detector = TriggerDetector(last_activation, last_send)
                    
                    # === ÉTAT STANDBY : Écoute trigger activation ===
                    if current_state == VoiceState.STANDBY:
                        try:
                            # Enregistrer un segment court pour détection trigger
                            if hasattr(audio_mgr, 'record_once'):
                                result = loop.run_until_complete(
                                    audio_mgr.record_once(timeout=3.0)
                                )
                            else:
                                time.sleep(0.5)
                                continue
                            
                            if result and result.strip():
                                result = result.strip()
                                print(f"[VOICE] 👂 STANDBY entendu: '{result}'")
                                
                                # Vérifier trigger d'activation
                                if trigger_detector.check_activation(result):
                                    print(f"[VOICE] 🎯 TRIGGER ACTIVATION détecté!")
                                    self._accumulated_text = ""
                                    self._set_state(VoiceState.LISTENING)
                                    self._notify_status("🎤 Parlez...")
                        
                        except Exception as e:
                            print(f"[VOICE] ⚠️ Erreur STANDBY: {e}")
                            time.sleep(0.3)
                    
                    # === ÉTAT LISTENING : Transcription live ===
                    elif current_state == VoiceState.LISTENING:
                        try:
                            # Enregistrer pour transcription avec paramètres configurables
                            if hasattr(audio_mgr, 'record_once'):
                                result = loop.run_until_complete(
                                    audio_mgr.record_once(
                                        timeout=self._listening_timeout,
                                        phrase_time_limit=self._phrase_time_limit,
                                        pause_threshold=self._pause_threshold
                                    )
                                )
                            else:
                                time.sleep(0.5)
                                continue
                            
                            # === SILENCE INTELLIGENT ===
                            # Si pas de parole détectée mais du texte accumulé, vérifier le timer
                            if not result or not result.strip():
                                if self._accumulated_text and self._last_speech_time and self._auto_send_delay > 0:
                                    silence_duration = time.time() - self._last_speech_time
                                    
                                    if silence_duration >= self._auto_send_delay:
                                        print(f"[VOICE] ⏱️ Silence intelligent: {silence_duration:.1f}s >= {self._auto_send_delay}s → ENVOI AUTO")
                                        
                                        # Lire le texte du frontend
                                        message = ""
                                        if self._get_current_text:
                                            try:
                                                message = self._get_current_text().strip()
                                            except:
                                                message = self._accumulated_text.strip()
                                        else:
                                            message = self._accumulated_text.strip()
                                        
                                        if message:
                                            print(f"[VOICE] 🚀 ENVOI AUTO: '{message}'")
                                            self._accumulated_text = ""
                                            self._last_speech_time = None
                                            self._notify_transcription("")  # Effacer le champ
                                            self._notify_message_ready(message)
                                            
                                            # Transition selon le mode
                                            if self._continuous_mode:
                                                self._set_state(VoiceState.SPEAKING)  # Sera confirmé par notify_tts_started
                                            else:
                                                self._set_state(VoiceState.STANDBY)
                                continue  # Pas de parole, passer au tour suivant
                            
                            if result and result.strip():
                                result = result.strip()
                                print(f"[VOICE] 📝 LISTENING transcrit: '{result}'")
                                
                                # Reset timer silence intelligent (on a reçu de la parole)
                                self._last_speech_time = time.time()
                                
                                # D'ABORD: Vérifier le trigger d'envoi sur le FRAGMENT SEUL
                                # Cela détecte "go go" immédiatement sans attendre le frontend
                                if trigger_detector.check_send(result):
                                    print(f"[VOICE] 🎯 TRIGGER ENVOI détecté dans fragment: '{result}'")
                                    
                                    # Lire le texte actuel du frontend AVANT d'ajouter le fragment
                                    current_full_text = ""
                                    if self._get_current_text:
                                        try:
                                            current_full_text = self._get_current_text()
                                        except Exception as e:
                                            print(f"[VOICE] ⚠️ Erreur lecture frontend: {e}")
                                            current_full_text = self._accumulated_text
                                    
                                    # Le message final = texte actuel (SANS le trigger)
                                    # Le trigger est dans le fragment, pas encore ajouté au frontend
                                    message = current_full_text.strip() if current_full_text else ""
                                    
                                    # Si le texte contient aussi le trigger (doublé), le nettoyer
                                    if message:
                                        message = trigger_detector.remove_send_trigger(message)
                                    
                                    print(f"[VOICE] 🚀 ENVOI: '{message}'")
                                    
                                    # Reset et envoyer
                                    self._accumulated_text = ""
                                    self._last_speech_time = None  # Reset timer silence intelligent
                                    self._notify_transcription("")  # Effacer le champ
                                    if message:  # N'envoyer que si message non vide
                                        self._notify_message_ready(message)
                                    
                                    self._set_state(VoiceState.STANDBY)
                                else:
                                    # Pas de trigger - ajouter le fragment au frontend
                                    self._notify_transcription(result)
                                    
                                    # Mettre à jour le cache local pour le preview
                                    if self._accumulated_text:
                                        self._accumulated_text += " " + result
                                    else:
                                        self._accumulated_text = result
                                    
                                    # Afficher le preview
                                    preview = self._accumulated_text[:40]
                                    if len(self._accumulated_text) > 40:
                                        preview += "..."
                                    self._notify_status(f"🎤 {preview}")
                        
                        except Exception as e:
                            print(f"[VOICE] ⚠️ Erreur LISTENING: {e}")
                            time.sleep(0.3)
                    
                    # === ÉTAT SPEAKING : Écoute trigger interruption ===
                    elif current_state == VoiceState.SPEAKING:
                        try:
                            # Enregistrer pour détecter interruption
                            if hasattr(audio_mgr, 'record_once'):
                                result = loop.run_until_complete(
                                    audio_mgr.record_once(timeout=2.0)
                                )
                            else:
                                time.sleep(0.5)
                                continue
                            
                            if result and result.strip():
                                result = result.strip()
                                print(f"[VOICE] 👂 SPEAKING entendu: '{result}'")
                                
                                # Vérifier trigger d'activation (pour interrompre)
                                if trigger_detector.check_activation(result):
                                    print(f"[VOICE] ⏹️ INTERRUPTION détectée!")
                                    
                                    # Stopper le TTS
                                    self._stop_tts()
                                    
                                    # Passer directement en LISTENING
                                    self._accumulated_text = ""
                                    self._set_state(VoiceState.LISTENING)
                                    self._notify_status("🎤 Parlez...")
                        
                        except Exception as e:
                            print(f"[VOICE] ⚠️ Erreur SPEAKING: {e}")
                            time.sleep(0.3)
                    
                    # Petit délai pour éviter surcharge CPU
                    time.sleep(0.1)
            
            finally:
                loop.close()
        
        except Exception as e:
            print(f"[VOICE] ❌ Erreur boucle: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("[VOICE] 🎤 Thread d'écoute terminé")
    
    def _stop_tts(self):
        """Stoppe le TTS ET le streaming en cours pour interruption immédiate"""
        try:
            # 1. PRIORITÉ: Stopper le streaming IA immédiatement
            from stop_signal import request_stop
            request_stop()
            print("[VOICE] 🛑 Signal d'arrêt streaming envoyé")
            
            # 2. Stopper le TTS audio (essayer plusieurs méthodes)
            tts_stopped = False
            
            # Méthode 1: Via audio_manager.stop_tts()
            if self.audio_manager and hasattr(self.audio_manager, 'stop_tts'):
                self.audio_manager.stop_tts()
                tts_stopped = True
                print("[VOICE] ⏹️ TTS stoppé (stop_tts)")
            
            # Méthode 2: Via audio_manager.stop_speaking() 
            elif self.audio_manager and hasattr(self.audio_manager, 'stop_speaking'):
                self.audio_manager.stop_speaking()
                tts_stopped = True
                print("[VOICE] ⏹️ TTS stoppé (stop_speaking)")
            
            # Méthode 3: Fallback via wrapper
            if not tts_stopped:
                from audio_manager_wrapper import get_audio_manager
                audio_mgr = get_audio_manager()
                if audio_mgr:
                    if hasattr(audio_mgr, 'stop_speaking'):
                        audio_mgr.stop_speaking()
                        print("[VOICE] ⏹️ TTS stoppé (wrapper.stop_speaking)")
                    elif hasattr(audio_mgr, 'stop_tts'):
                        audio_mgr.stop_tts()
                        print("[VOICE] ⏹️ TTS stoppé (wrapper.stop_tts)")
                    elif hasattr(audio_mgr, 'tts_safe') and audio_mgr.tts_safe:
                        audio_mgr.tts_safe.stop_current_speech()
                        print("[VOICE] ⏹️ TTS stoppé (tts_safe.stop_current_speech)")
        except Exception as e:
            print(f"[VOICE] ⚠️ Erreur stop: {e}")
    
    # ==================== CLEANUP ====================
    
    def cleanup(self):
        """Nettoyage propre"""
        print("[VOICE] 🧹 Cleanup...")
        self.deactivate()


# Singleton global
_voice_manager: Optional[VoiceManager] = None


def get_voice_manager() -> Optional[VoiceManager]:
    """Retourne l'instance singleton du VoiceManager"""
    return _voice_manager


def initialize_voice_manager(
    settings_manager=None,
    audio_manager=None
) -> VoiceManager:
    """Initialise le singleton VoiceManager"""
    global _voice_manager
    
    if _voice_manager is None:
        _voice_manager = VoiceManager(settings_manager, audio_manager)
    else:
        # Singleton existe déjà, recharger la config pour capter les changements
        _voice_manager.reload_config()
    
    return _voice_manager
