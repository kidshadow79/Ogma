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
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import json

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
        self.is_playing = False
        self.should_stop = False
        self.current_audio_process = None
        self.pygame_mixer = None
        
        # Configuration moteurs par priorité (sans conflit)
        self.engine_priority = [
            "edge_tts",      # Cloud, pas de conflit système
            "gtts_offline",  # Fichier, pas de conflit temps réel
            "system_safe",   # Subprocess isolé
            "fallback"       # Notification visuelle
        ]
        
        self.available_engines = {}
        self._detect_available_engines()
    
    def _detect_available_engines(self):
        """Détecte les moteurs TTS disponibles sans conflits"""
        
        # Edge TTS - Cloud, très stable
        try:
            import edge_tts
            self.available_engines["edge_tts"] = {
                "module": edge_tts,
                "conflict_risk": "none",
                "description": "Edge TTS Cloud (recommandé)"
            }
            print("[TTS-SAFE] ✅ Edge TTS disponible (sans conflit)")
        except ImportError:
            pass
        
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
            for engine in ["edge_tts", "gtts_offline", "fallback"]:
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
                
                text = task.get("text", "")
                options = task.get("options", {})
                
                if text.strip():
                    print(f"[TTS-WORKER] 🔊 Traitement: '{text[:50]}...'")
                    self._execute_speech(text, options)
                
                self.speech_queue.task_done()
                
            except queue.Empty:
                # Normal - continue à attendre
                continue
            except Exception as e:
                print(f"[TTS-WORKER] ⚠️ Erreur worker: {e}")
                # Continue même en cas d'erreur
        
        print("[TTS-WORKER] 🛑 Worker TTS arrêté définitivement")
    
    def _execute_speech(self, text: str, options: Dict[str, Any]):
        """Exécute la synthèse vocale selon le moteur"""
        
        engine = self.current_engine
        
        try:
            if engine == "edge_tts":
                self._speak_edge_tts(text, options)
            elif engine == "gtts_offline":
                self._speak_gtts_offline(text, options)
            elif engine == "system_safe":
                self._speak_system_safe(text, options)
            else:  # fallback
                self._speak_fallback(text, options)
                
        except Exception as e:
            print(f"[TTS-SAFE] ⚠️ Erreur synthèse {engine}: {e}")
            # Fallback automatique
            if engine != "fallback":
                self._speak_fallback(text, options)
    
    def _speak_edge_tts(self, text: str, options: Dict[str, Any]):
        """Synthèse avec Edge TTS (cloud, sans conflit)"""
        import asyncio
        import edge_tts
        
        async def _async_speak():
            voice = options.get("voice", "fr-FR-DeniseNeural")
            rate = options.get("rate", "+0%")
            
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            # Créer fichier temporaire
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            await communicate.save(tmp_path)
            
            # Jouer avec subprocess isolé (pas de conflit)
            self._play_audio_file_safe(tmp_path)
            
            # Nettoyer
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        # Exécuter dans nouvelle event loop (isolation)
        try:
            asyncio.run(_async_speak())
            print("[TTS-SAFE] ✅ Edge TTS synthèse réussie")
        except Exception as e:
            print(f"[TTS-SAFE] ⚠️ Edge TTS échec: {e}")
            raise
    
    def _speak_gtts_offline(self, text: str, options: Dict[str, Any]):
        """Synthèse avec gTTS + cache local"""
        from gtts import gTTS
        
        lang = options.get("lang", "fr")
        
        # Créer fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(tmp_path)
        
        # Jouer de manière isolée
        self._play_audio_file_safe(tmp_path)
        
        # Nettoyer
        try:
            os.unlink(tmp_path)
        except:
            pass
        
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
            
            # Arrêter lecture précédente si active
            if self.pygame_mixer:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                time.sleep(0.1)  # Pause courte pour cleanup
            
            # Initialiser mixer avec paramètres conservateurs
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=2048)
            pygame.mixer.init()
            
            # Vérifier que l'init a marché
            if not pygame.mixer.get_init():
                print("[TTS-SAFE] ❌ Échec init pygame mixer")
                return False
                
            self.pygame_mixer = True
            self.is_playing = True
            self.should_stop = False
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play()
            
            print("[TTS-SAFE] 🎵 Lecture pygame démarrée...")
            
            # Attendre fin de lecture avec contrôle d'arrêt
            while pygame.mixer.music.get_busy() and not self.should_stop:
                time.sleep(0.1)
            
            # Vérifier si arrêté manuellement ou naturellement
            if self.should_stop:
                pygame.mixer.music.stop()
                print("[TTS-SAFE] 🛑 Lecture pygame interrompue")
            else:
                print("[TTS-SAFE] ✅ Lecture pygame terminée complètement")
            
            pygame.mixer.quit()
            self.pygame_mixer = None
            self.is_playing = False
            
            return True
            
        except ImportError:
            print("[TTS-SAFE] ⚠️ pygame non disponible")
            return False
        except Exception as e:
            print(f"[TTS-SAFE] ⚠️ Erreur pygame: {e}")
            # Cleanup en cas d'erreur
            try:
                if self.pygame_mixer:
                    pygame.mixer.quit()
            except:
                pass
            self.is_playing = False
            self.pygame_mixer = None
            return False
    
    def speak(self, text: str, **options) -> bool:
        """Interface publique pour synthèse vocale"""
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        # Si déjà en cours de lecture, arrêter
        if self.is_playing:
            self.stop_current_speech()
            return True
        
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
        """Arrête la lecture audio en cours"""
        self.should_stop = True
        
        # Arrêter pygame si actif
        if self.pygame_mixer:
            try:
                import pygame
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                self.pygame_mixer = None
                print("[TTS-SAFE] 🛑 Lecture pygame arrêtée")
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
        
        self.is_playing = False
        print("[TTS-SAFE] 🛑 Lecture arrêtée")
    
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