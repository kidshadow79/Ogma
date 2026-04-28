# tts_conflict_free.py

"""
Système TTS Sans Conflit - Architecture robuste
Évite tous les conflits connus: OpenCV, NiceGUI, threading, ressources système
"""

import threading
import queue
import time
import subprocess
import tempfile
import os
import platform
import atexit
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import json

# Dossier persistant pour fichiers audio TTS (nettoyé uniquement à la fermeture)
_TTS_AUDIO_TEMP_DIR = None

def _get_tts_audio_temp_dir() -> Path:
    """Retourne le dossier temporaire pour les fichiers audio TTS"""
    global _TTS_AUDIO_TEMP_DIR
    if _TTS_AUDIO_TEMP_DIR is None:
        # Créer dans le dossier du projet
        base_path = Path(__file__).parent / "data" / "audio_temp"
        base_path.mkdir(parents=True, exist_ok=True)
        _TTS_AUDIO_TEMP_DIR = base_path
        print(f"[TTS-TEMP] 📁 Dossier audio temporaire: {base_path}")
    return _TTS_AUDIO_TEMP_DIR

def _cleanup_tts_audio_temp():
    """Nettoie tous les fichiers audio temporaires (appelé à la fermeture et au démarrage)"""
    # Libérer les handles pygame avant de supprimer (Windows garde les fichiers ouverts)
    try:
        import pygame
        if pygame.get_init() and pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            pygame.mixer.quit()
    except Exception:
        pass

    target_dir = _TTS_AUDIO_TEMP_DIR or (Path(__file__).parent / "data" / "audio_temp")
    if target_dir.exists():
        count = 0
        for f in target_dir.glob("ogma_tts_*.mp3"):
            try:
                f.unlink()
                count += 1
            except Exception:
                pass  # Fichier encore verrouillé (rare), ignoré
        if count > 0:
            print(f"[TTS-CLEANUP] {count} fichiers audio temporaires supprimes")

# Nettoyage au démarrage : supprime les restes d'une session précédente
# (utile si la session précédente s'est terminée via os._exit(), bypassing atexit)
_startup_dir = Path(__file__).parent / "data" / "audio_temp"
if _startup_dir.exists():
    _leftover = list(_startup_dir.glob("ogma_tts_*.mp3"))
    if _leftover:
        for _f in _leftover:
            try:
                _f.unlink()
            except Exception:
                pass
        print(f"[TTS-CLEANUP] {len(_leftover)} fichiers residuels session precedente supprimes")

# Enregistrer le nettoyage à la fermeture de l'application
atexit.register(_cleanup_tts_audio_temp)

class ConflictFreeTTSManager:
    """Gestionnaire TTS conçu pour éviter tous les conflits"""
    
    def __init__(self):
        self.is_initialized = False
        self.current_engine = None
        self.speech_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False
        self.lock = threading.Lock()
        
        # États de conflit
        self.perception_active = False
        self.nicegui_active = False
        self.system_busy = False
        
        # Contrôle de lecture
        
        # === TTS Streaming par phrases ===
        self._streaming_buffer = ""
        self._streaming_enabled = True  # Peut être désactivé dans settings
        self._sentence_queue = queue.Queue()  # File pour phrases en streaming
        self.is_playing = False
        self._is_processing = False  # True dès qu'une tâche est prise par le worker
        self.should_stop = False
        self.current_audio_process = None
        self.pygame_mixer = None
        self._pygame_initialized = False  # Tracker l'état du mixer
        
        # Configuration moteurs par priorité (sans conflit)
        # Note: Edge TTS (Microsoft) bloqué depuis 2024 - 403 Forbidden
        # gTTS (Google) est maintenant la priorité recommandée
        self.engine_priority = [
            "gtts_offline",  # Google TTS - stable et gratuit
            "system_safe",   # Subprocess isolé (pyttsx3/SAPI)
            "edge_tts",      # Microsoft Edge TTS (souvent bloqué)
            "fallback"       # Notification visuelle
        ]
        
        self.available_engines = {}
        self._detect_available_engines()
    
    def _detect_available_engines(self):
        """Détecte les moteurs TTS disponibles sans conflits"""
        
        # Note: Edge TTS désactivé - Microsoft a bloqué l'accès (403 Forbidden)
        # depuis 2024. Le service gratuit non-officiel n'est plus fonctionnel.
        
        # gTTS - Cloud avec cache local
        try:
            from gtts import gTTS
            self.available_engines["gtts_offline"] = {
                "module": gTTS,
                "conflict_risk": "none", 
                "description": "Google TTS avec cache local"
            }
            print("[TTS-SAFE] ✅ gTTS disponible (sans conflit)")
        except ImportError:
            pass
        
        # Subprocess système (isolé)
        if platform.system() == "Windows":
            # PowerShell TTS - complètement isolé
            if self._test_powershell_tts():
                self.available_engines["system_safe"] = {
                    "module": None,
                    "conflict_risk": "low",
                    "description": "PowerShell TTS isolé"
                }
                print("[TTS-SAFE] ✅ PowerShell TTS disponible (isolé)")
        
        # Fallback toujours disponible
        self.available_engines["fallback"] = {
            "module": None,
            "conflict_risk": "none",
            "description": "Notification visuelle (sans audio)"
        }
        
        print(f"[TTS-SAFE] 🔍 {len(self.available_engines)} moteurs sans conflit détectés")
    
    def _test_powershell_tts(self) -> bool:
        """Test si PowerShell TTS fonctionne"""
        try:
            cmd = [
                "powershell", "-Command", 
                "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('test')"
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_recommended_engine(self) -> str:
        """Retourne le moteur recommandé selon le contexte"""
        
        # Si Perception active, utiliser seulement Cloud ou Fallback
        if self.perception_active:
            for engine in ["gtts_offline", "system_safe", "fallback"]:
                if engine in self.available_engines:
                    return engine
        
        # Sinon, utiliser le premier disponible par priorité
        for engine in self.engine_priority:
            if engine in self.available_engines:
                return engine
        
        return "fallback"
    
    def initialize(self, preferred_engine: Optional[str] = None) -> bool:
        """Initialise le TTS sans conflit"""
        with self.lock:
            if self.is_initialized:
                return True
            
            # Choisir moteur
            engine = preferred_engine or self.get_recommended_engine()
            
            if engine not in self.available_engines:
                print(f"[TTS-SAFE] ⚠️ Moteur {engine} non disponible, fallback")
                engine = "fallback"
            
            self.current_engine = engine
            print(f"[TTS-SAFE] 🎵 Moteur sélectionné: {engine}")
            print(f"[TTS-SAFE] 📝 {self.available_engines[engine]['description']}")
            
            # Démarrer worker thread isolé
            self.is_running = True
            self.worker_thread = threading.Thread(
                target=self._speech_worker,
                name="TTSSafeWorker",
                daemon=True
            )
            self.worker_thread.start()
            
            self.is_initialized = True
            return True
    
    def _speech_worker(self):
        """Worker thread isolé pour TTS - reste actif en permanence"""
        print("[TTS-WORKER] 🚀 Worker TTS démarré (thread isolé)")
        
        while self.is_running:
            try:
                # Attendre tâche avec timeout plus long
                task = self.speech_queue.get(timeout=5.0)
                
                if task is None:  # Signal d'arrêt
                    print("[TTS-WORKER] 📤 Signal arrêt reçu")
                    break
                
                # Marquer qu'on traite une tâche (AVANT toute opération)
                self._is_processing = True
                
                text = task.get("text", "")
                options = task.get("options", {})
                
                if text.strip():
                    print(f"[TTS-WORKER] 🔊 Traitement: '{text[:50]}...'")
                    self._execute_speech(text, options)
                
                # Marquer fin de traitement (APRÈS lecture terminée)
                self._is_processing = False
                self.speech_queue.task_done()
                
            except queue.Empty:
                # Normal - continue à attendre
                continue
            except Exception as e:
                print(f"[TTS-WORKER] ⚠️ Erreur worker: {e}")
                # Continue même en cas d'erreur
        
        print("[TTS-WORKER] 🛑 Worker TTS arrêté définitivement")
    
    def _execute_speech(self, text: str, options: Dict[str, Any]):
        """Exécute la synthèse vocale selon le moteur avec cascade de fallback"""
        
        engine = self.current_engine
        
        # Liste des moteurs à essayer en cascade
        # Note: Edge TTS retiré (bloqué par Microsoft)
        engines_to_try = [engine]
        
        # Ajouter les fallbacks selon le moteur actuel
        if engine == "gtts_offline":
            engines_to_try.extend(["system_safe", "fallback"])
        elif engine == "system_safe":
            engines_to_try.extend(["gtts_offline", "fallback"])
        else:
            engines_to_try.append("fallback")
        
        # Essayer chaque moteur en cascade
        for try_engine in engines_to_try:
            if try_engine not in self.available_engines and try_engine != "fallback":
                continue
                
            try:
                if try_engine == "gtts_offline":
                    self._speak_gtts_offline(text, options)
                    return  # Succès, on arrête
                elif try_engine == "system_safe":
                    self._speak_system_safe(text, options)
                    return  # Succès, on arrête
                else:  # fallback
                    self._speak_fallback(text, options)
                    return
                    
            except Exception as e:
                print(f"[TTS-SAFE] ⚠️ {try_engine} échec: {e}")
                if try_engine != engine:
                    print(f"[TTS-SAFE] 🔄 Tentative moteur suivant...")
                continue
        
        # Si tout a échoué
        print("[TTS-SAFE] ❌ Tous les moteurs ont échoué")
        self._speak_fallback(text, options)
    
    # Note: _speak_edge_tts() supprimé - Microsoft a bloqué l'accès (403 Forbidden)
    # depuis 2024. Le service gratuit non-officiel n'est plus fonctionnel.
    
    def _speak_gtts_offline(self, text: str, options: Dict[str, Any]):
        """Synthèse avec gTTS - fichiers conservés dans dossier persistant"""
        from gtts import gTTS
        
        lang = options.get("lang", "fr")
        
        # Utiliser le dossier persistant (nettoyé uniquement à la fermeture)
        audio_dir = _get_tts_audio_temp_dir()
        tmp_path = str(audio_dir / f"ogma_tts_{int(time.time()*1000)}.mp3")
        
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(tmp_path)

        # Hologramme : extraire l'enveloppe RMS réelle
        try:
            from extensions.hologram_projector.audio_analyzer import extract_rms_envelope
            from extensions.hologram_projector.state_emitter import send_envelope
            envelope = extract_rms_envelope(tmp_path, interval_ms=50)
            if envelope:
                send_envelope(envelope, interval_ms=50)
        except Exception as _e:
            print(f"[TTS-HOLOGRAM] Analyse audio ignorée : {_e}")

        # Jouer de manière isolée (fichier reste jusqu'à fermeture app)
        self._play_audio_file_safe(tmp_path)
        
        print("[TTS-SAFE] ✅ gTTS synthèse réussie")
    
    def _speak_system_safe(self, text: str, options: Dict[str, Any]):
        """Synthèse système isolée via subprocess"""
        if platform.system() == "Windows":
            # PowerShell TTS complètement isolé
            escaped_text = text.replace("'", "''").replace('"', '""')
            cmd = [
                "powershell", "-WindowStyle", "Hidden", "-Command",
                f"Add-Type -AssemblyName System.Speech; "
                f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$synth.Rate = {options.get('rate', 0)}; "
                f"$synth.Volume = {options.get('volume', 100)}; "
                f"$synth.Speak('{escaped_text}')"
            ]
            
            subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            print("[TTS-SAFE] ✅ PowerShell TTS synthèse réussie")
    
    def _speak_fallback(self, text: str, options: Dict[str, Any]):
        """Fallback : notification visuelle sans audio"""
        print(f"[TTS-FALLBACK] 🔔 '{text[:50]}...'")
        # Ici on pourrait ajouter notification système, popup, etc.
    
    def _play_audio_file_safe(self, file_path: str):
        """Lecture audio sécurisée (évite les applications externes)"""
        # Priorité 1: pygame pour meilleur contrôle
        if self._try_pygame_playback(file_path):
            return
            
        # Priorité 2: winsound (Windows intégré)
        if platform.system() == "Windows":
            try:
                import winsound
                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
                print("[TTS-SAFE] ✅ Lecture winsound réussie")
                return
            except Exception as e:
                print(f"[TTS-SAFE] ⚠️ Erreur winsound: {e}")
        
        # Priorité 3: Système (Linux/Mac)
        try:
            cmd = "afplay" if platform.system() == "Darwin" else "aplay"
            subprocess.run([cmd, file_path], check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[TTS-SAFE] ✅ Lecture système réussie")
        except Exception as e:
            print(f"[TTS-SAFE] ❌ Tous les moyens de lecture ont échoué")
    
    def _try_pygame_playback(self, file_path: str) -> bool:
        """Tentative lecture avec pygame (préférée pour contrôle)"""
        try:
            import pygame
            
            # Toujours réinitialiser le mixer pour éviter les états corrompus
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                    time.sleep(0.05)
            except:
                pass
            
            # Réinitialiser les flags
            self.should_stop = False
            self.is_playing = False
            self.pygame_mixer = None
            self._pygame_initialized = False
            
            # Initialiser mixer avec paramètres conservateurs
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=2048)
            pygame.mixer.init()
            
            # Vérifier que l'init a marché
            if not pygame.mixer.get_init():
                print("[TTS-SAFE] ❌ Échec init pygame mixer")
                return False
            
            self._pygame_initialized = True
            self.pygame_mixer = True
            self.is_playing = True
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play()
            
            print("[TTS-SAFE] 🎵 Lecture pygame démarrée...")
            
            # Attendre fin de lecture avec contrôle d'arrêt
            while pygame.mixer.music.get_busy() and not self.should_stop:
                time.sleep(0.1)
            
            # Arrêter proprement
            try:
                pygame.mixer.music.stop()
            except:
                pass
            
            # Log selon le mode d'arrêt
            if self.should_stop:
                print("[TTS-SAFE] 🛑 Lecture pygame interrompue")
            else:
                print("[TTS-SAFE] ✅ Lecture pygame terminée")
            
            # Cleanup pygame
            try:
                pygame.mixer.quit()
            except:
                pass
            
            self.pygame_mixer = None
            self.is_playing = False
            self._pygame_initialized = False
            self.should_stop = False  # Reset pour les prochaines lectures
            
            return True
            
        except ImportError:
            print("[TTS-SAFE] ⚠️ pygame non disponible")
            return False
        except Exception as e:
            print(f"[TTS-SAFE] ⚠️ Erreur pygame: {e}")
            # Cleanup en cas d'erreur
            self._cleanup_pygame_state()
            return False
    
    def _cleanup_pygame_state(self):
        """Nettoie l'état pygame en cas d'erreur"""
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except:
            pass
        self.pygame_mixer = None
        self.is_playing = False
        self._pygame_initialized = False
        self.should_stop = False
    
    # === TTS STREAMING PAR PHRASES ===
    
    def process_streaming_chunk(self, chunk: str) -> list:
        """
        Traite un chunk de texte en streaming et retourne les phrases complètes.
        Utilisé pour parler en temps réel pendant la génération de réponse.
        
        Args:
            chunk: Morceau de texte reçu du streaming
            
        Returns:
            Liste des phrases complètes détectées (peut être vide)
        """
        import re
        
        self._streaming_buffer += chunk
        completed_sentences = []
        
        # Pattern pour détecter fin de phrase (. ! ? suivi d'espace ou fin)
        # On évite de couper sur les abréviations courantes
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-ZÀ-Ÿa-zà-ÿ])'
        
        parts = re.split(sentence_pattern, self._streaming_buffer)
        
        if len(parts) > 1:
            # On a au moins une phrase complète
            for sentence in parts[:-1]:
                cleaned = sentence.strip()
                if cleaned and len(cleaned) > 3:  # Éviter les fragments trop courts
                    completed_sentences.append(cleaned)
            
            # Garder le reste (phrase incomplète)
            self._streaming_buffer = parts[-1]
        
        return completed_sentences
    
    def speak_streaming_sentence(self, sentence: str):
        """Envoie une phrase au TTS en mode streaming (non-bloquant)"""
        if not self._streaming_enabled:
            return
        
        if not sentence or len(sentence.strip()) < 3:
            return
        
        # Nettoyer le markdown et caractères spéciaux
        clean_sentence = sentence.replace('*', '').replace('**', '').replace('#', '').replace('`', '').strip()
        
        if clean_sentence:
            print(f"[TTS-STREAM] 🎤 Phrase: '{clean_sentence[:40]}...'")
            self.speak(clean_sentence)
    
    def flush_streaming_buffer(self):
        """Vide le buffer de streaming et prononce le reste"""
        if self._streaming_buffer.strip():
            remaining = self._streaming_buffer.strip()
            if len(remaining) > 3:
                self.speak_streaming_sentence(remaining)
        self._streaming_buffer = ""
    
    def reset_streaming(self):
        """Réinitialise le buffer de streaming"""
        self._streaming_buffer = ""
    
    def set_streaming_enabled(self, enabled: bool):
        """Active/désactive le TTS streaming"""
        self._streaming_enabled = enabled
        print(f"[TTS-STREAM] {'✅ Activé' if enabled else '⏸️ Désactivé'}")
    
    def is_fully_finished(self) -> bool:
        """
        Vérifie si le TTS a vraiment terminé TOUTES les phrases.
        Retourne True seulement si:
        - La queue est vide
        - Aucun traitement en cours (worker idle)
        - Aucune lecture en cours
        """
        queue_empty = self.speech_queue.empty()
        not_processing = not self._is_processing
        not_playing = not self.is_playing
        return queue_empty and not_processing and not_playing
    
    def wait_until_finished(self, timeout: float = 60.0) -> bool:
        """
        Attend que le TTS ait terminé toutes les phrases.
        Retourne True si terminé, False si timeout.
        """
        import time
        start_time = time.time()
        check_interval = 0.2  # Vérifier toutes les 200ms
        
        while time.time() - start_time < timeout:
            if self.is_fully_finished():
                return True
            time.sleep(check_interval)
        
        print(f"[TTS-SAFE] ⚠️ Timeout après {timeout}s d'attente")
        return False

    # === FIN TTS STREAMING ===
    
    def _ensure_worker_running(self):
        """S'assure que le worker TTS est actif"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            print("[TTS-WORKER] 🔄 Redémarrage du worker TTS...")
            self.is_running = True
            self.worker_thread = threading.Thread(
                target=self._speech_worker,
                name="TTSSafeWorker",
                daemon=True
            )
            self.worker_thread.start()
    
    def speak(self, text: str, **options) -> bool:
        """Interface publique pour synthèse vocale"""
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        # S'assurer que le worker est actif
        self._ensure_worker_running()
        
        # Vérifier conflits
        if self._should_skip_speech():
            print("[TTS-SAFE] ⏸️ Synthèse ignorée (conflit détecté)")
            return False
        
        # Ajouter à la queue
        task = {"text": text, "options": options}
        
        try:
            self.speech_queue.put(task, timeout=1.0)
            return True
        except queue.Full:
            print("[TTS-SAFE] ⚠️ Queue TTS pleine, synthèse ignorée")
            return False
    
    def stop_speech(self) -> bool:
        """Interface publique pour arrêter la synthèse en cours"""
        self.stop_current_speech()
        return True
    
    def _should_skip_speech(self) -> bool:
        """Détermine si la synthèse doit être ignorée"""
        return (
            self.perception_active and self.current_engine in ["pyttsx3", "sapi"] or
            self.system_busy
        )
    
    def set_perception_state(self, active: bool):
        """Notifie l'état de Perception"""
        self.perception_active = active
        print(f"[TTS-SAFE] 📷 Perception {'activée' if active else 'désactivée'}")
        
        # Changer moteur si nécessaire
        if active and self.current_engine in ["pyttsx3", "sapi"]:
            print("[TTS-SAFE] 🔄 Basculement vers moteur sans conflit...")
            new_engine = self.get_recommended_engine()
            if new_engine != self.current_engine:
                self.current_engine = new_engine
                print(f"[TTS-SAFE] ✅ Moteur changé: {new_engine}")
    
    def stop_current_speech(self):
        """Arrête la lecture audio en cours et vide la queue"""
        print("[TTS-SAFE] 🛑 Demande d'arrêt de lecture...")
        self.should_stop = True
        
        # Vider la queue de parole en attente
        try:
            count = 0
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                    count += 1
                except:
                    break
            if count > 0:
                print(f"[TTS-SAFE] 🗑️ Queue TTS vidée ({count} éléments)")
        except:
            pass
        
        # Reset le buffer de streaming
        self._streaming_buffer = ""
        
        # Arrêter pygame si actif (sans quit, le worker gère le cleanup)
        if self.pygame_mixer or self.is_playing:
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    print("[TTS-SAFE] 🛑 Lecture pygame stoppée")
            except:
                pass
        
        # Arrêter processus audio si actif  
        if self.current_audio_process:
            try:
                self.current_audio_process.terminate()
                self.current_audio_process = None
                print("[TTS-SAFE] 🛑 Processus audio arrêté")
            except:
                pass
        
        # Attendre que le worker finisse son cleanup pygame
        # Le flag should_stop sera remis à False par _try_pygame_playback() après cleanup
        max_wait = 0.5  # Max 500ms d'attente
        waited = 0
        while self.is_playing and waited < max_wait:
            time.sleep(0.05)
            waited += 0.05
        
        # Forcer le reset si pygame est toujours actif (timeout)
        if self.is_playing:
            print("[TTS-SAFE] ⚠️ Timeout cleanup, reset forcé")
            self._cleanup_pygame_state()
        
        print("[TTS-SAFE] ✅ Arrêt complet")
    
    def stop(self):
        """Arrête proprement le TTS"""
        with self.lock:
            # Arrêter lecture en cours
            self.stop_current_speech()
            
            if not self.is_running:
                return
            
            print("[TTS-SAFE] 🛑 Arrêt TTS...")
            self.is_running = False
            
            # Signal d'arrêt au worker
            try:
                self.speech_queue.put(None, timeout=1.0)
            except queue.Full:
                pass
            
            # Attendre worker
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=3.0)
            
            self.is_initialized = False
            print("[TTS-SAFE] ✅ TTS arrêté proprement")

# Instance globale
_conflict_free_tts = None

def get_conflict_free_tts() -> ConflictFreeTTSManager:
    """Récupère l'instance globale TTS sans conflit"""
    global _conflict_free_tts
    if _conflict_free_tts is None:
        _conflict_free_tts = ConflictFreeTTSManager()
    return _conflict_free_tts

# API simplifiée
def speak_safe(text: str, **options) -> bool:
    """API simple pour synthèse vocale sans conflit"""
    return get_conflict_free_tts().speak(text, **options)

def set_perception_active(active: bool):
    """Notifie l'état de Perception au TTS"""
    get_conflict_free_tts().set_perception_state(active)

def play_audio_file(file_path: str):
    """Joue un fichier audio de manière sécurisée"""
    get_conflict_free_tts()._play_audio_file_safe(file_path)

if __name__ == "__main__":
    # Test du système
    import sys
    
    if len(sys.argv) < 2:
        print("🎵 === TTS SANS CONFLIT ===")
        print()
        print("USAGE:")
        print("  python tts_conflict_free.py test       # Test moteurs")
        print("  python tts_conflict_free.py demo       # Démo complète")
        print("  python tts_conflict_free.py perception # Test avec Perception")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    tts = get_conflict_free_tts()
    
    if cmd == "test":
        print("🧪 Test des moteurs TTS...")
        tts.initialize()
        
        if tts.speak("Test du système TTS sans conflit"):
            print("✅ Test réussi")
        else:
            print("❌ Test échoué")
    
    elif cmd == "demo":
        print("🎭 Démo complète...")
        tts.initialize()
        
        # Test normal
        tts.speak("Bonjour, je suis OGMA avec TTS sans conflit")
        time.sleep(3)
        
        # Test avec Perception simulée
        print("\n📷 Simulation Perception active...")
        tts.set_perception_state(True)
        tts.speak("Perception active, TTS adapté automatiquement")
        time.sleep(3)
        
        # Test retour normal
        print("\n🛑 Simulation Perception désactivée...")
        tts.set_perception_state(False) 
        tts.speak("Perception désactivée, TTS normal")
        
        tts.stop()
    
    elif cmd == "perception":
        print("📷 Test compatibilité Perception...")
        
        # Simuler caméra active
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("✅ Caméra ouverte")
            
            # Initialiser TTS avec caméra active
            tts.set_perception_state(True)
            tts.initialize()
            
            # Test synthèse
            tts.speak("TTS fonctionne avec caméra active")
            
            # Test capture simultanée
            for i in range(3):
                ret, frame = cap.read()
                if ret:
                    print(f"   Frame {i+1}: OK")
                time.sleep(1)
            
            cap.release()
            tts.stop()
            
            print("✅ Test Perception/TTS réussi")
        else:
            print("❌ Caméra non disponible")
    
    else:
        print(f"❌ Commande inconnue: {cmd}")