# debug_perception_crash.py

"""
Script de debug pour identifier la cause exacte des redémarrages Perception
"""

import sys
import time
import threading
import traceback
from contextlib import contextmanager

class PerceptionCrashDetector:
    """Détecteur de crashes Perception avec stack trace"""
    
    def __init__(self):
        self.perception_ui = None
        self.crash_count = 0
        self.last_crash_trace = None
        
    def initialize(self):
        """Initialise la surveillance"""
        try:
            sys.path.append('.')
            from extensions.perception_ui import get_perception_ui
            from tts_conflict_free import get_conflict_free_tts
            
            self.perception_ui = get_perception_ui()
            self.tts_safe = get_conflict_free_tts()
            
            # Initialiser TTS
            self.tts_safe.initialize()
            print("[DEBUG] ✅ Systèmes initialisés")
            return True
            
        except Exception as e:
            print(f"[DEBUG] ❌ Erreur initialisation: {e}")
            traceback.print_exc()
            return False
    
    @contextmanager
    def crash_detector(self, operation_name):
        """Context manager pour détecter les crashes"""
        print(f"[DEBUG] 🔍 Début: {operation_name}")
        start_time = time.time()
        
        try:
            yield
            duration = time.time() - start_time
            print(f"[DEBUG] ✅ Fin: {operation_name} ({duration:.2f}s)")
            
        except Exception as e:
            self.crash_count += 1
            duration = time.time() - start_time
            
            print(f"[DEBUG] 💥 CRASH #{self.crash_count}: {operation_name} ({duration:.2f}s)")
            print(f"[DEBUG] Erreur: {e}")
            
            # Capturer stack trace
            self.last_crash_trace = traceback.format_exc()
            print("[DEBUG] Stack trace:")
            print(self.last_crash_trace)
            
            raise  # Re-raise pour propagation
    
    def test_perception_lifecycle(self):
        """Test du cycle de vie complet Perception"""
        print("\n🔄 === TEST CYCLE VIE PERCEPTION ===")
        
        try:
            with self.crash_detector("Vérification état initial"):
                initial_active = self.perception_ui.is_enabled
                print(f"[DEBUG] État initial: {'ACTIF' if initial_active else 'INACTIF'}")
            
            with self.crash_detector("Configuration par défaut"):
                config = self.perception_ui.current_config
                print(f"[DEBUG] Webcam index: {config.get('webcam_index', 'N/A')}")
                print(f"[DEBUG] Résolution: {config.get('capture_resolution', 'N/A')}")
                print(f"[DEBUG] FPS limit: {config.get('fps_limit', 'N/A')}")
            
            with self.crash_detector("Démarrage Perception"):
                if not self.perception_ui.is_enabled:
                    success = self.perception_ui.start_perception()
                    print(f"[DEBUG] Démarrage: {'✅ RÉUSSI' if success else '❌ ÉCHOUÉ'}")
                else:
                    print("[DEBUG] Déjà démarrée")
            
            with self.crash_detector("Vérification agent actif"):
                agent = self.perception_ui.perception_agent
                if agent:
                    print(f"[DEBUG] Agent: {type(agent).__name__}")
                    print(f"[DEBUG] Threads actifs: {threading.active_count()}")
                else:
                    print("[DEBUG] ❌ Pas d'agent créé")
            
            with self.crash_detector("Test capture d'image"):
                if self.perception_ui.is_enabled:
                    image_data = self.perception_ui.capture_for_chat()
                    if image_data:
                        print(f"[DEBUG] ✅ Image capturée: {len(image_data)} bytes")
                    else:
                        print("[DEBUG] ❌ Échec capture")
            
            with self.crash_detector("Test TTS avec Perception active"):
                from tts_conflict_free import speak_safe, set_perception_active
                
                set_perception_active(True)
                time.sleep(0.1)
                
                success = speak_safe("Test debug crash perception")
                print(f"[DEBUG] TTS: {'✅ RÉUSSI' if success else '❌ ÉCHOUÉ'}")
                
                set_perception_active(False)
            
            with self.crash_detector("Arrêt Perception"):
                if self.perception_ui.is_enabled:
                    self.perception_ui.stop_perception()
                    print("[DEBUG] ✅ Arrêt demandé")
            
            print("\n✅ CYCLE COMPLET RÉUSSI")
            return True
            
        except Exception as e:
            print(f"\n❌ CYCLE ÉCHOUÉ: {e}")
            return False
    
    def test_continuous_operation(self, duration=30):
        """Test opération continue avec surveillance"""
        print(f"\n⏱️ === TEST CONTINU {duration}s ===")
        
        try:
            # Démarrer Perception
            with self.crash_detector("Démarrage pour test continu"):
                if not self.perception_ui.is_enabled:
                    self.perception_ui.start_perception()
            
            start_time = time.time()
            last_check = time.time()
            
            while (time.time() - start_time) < duration:
                current_time = time.time()
                
                # Vérification toutes les 2 secondes
                if (current_time - last_check) >= 2:
                    with self.crash_detector("Vérification état"):
                        # Vérifier que Perception est toujours active
                        if not self.perception_ui.is_enabled:
                            print("[DEBUG] 💥 PERCEPTION ARRÊTÉE INATTENDU!")
                            return False
                        
                        # Vérifier agent
                        if not self.perception_ui.perception_agent:
                            print("[DEBUG] 💥 AGENT DISPARU!")
                            return False
                        
                        elapsed = int(current_time - start_time)
                        print(f"[DEBUG] ✅ T+{elapsed}s - Perception stable")
                    
                    last_check = current_time
                
                time.sleep(0.1)
            
            # Arrêt propre
            with self.crash_detector("Arrêt après test continu"):
                self.perception_ui.stop_perception()
            
            print(f"\n✅ TEST CONTINU {duration}s RÉUSSI")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST CONTINU ÉCHOUÉ: {e}")
            return False
    
    def generate_report(self):
        """Génère rapport de debug"""
        print("\n" + "="*50)
        print("📋 RAPPORT DEBUG PERCEPTION")
        print("="*50)
        print(f"Crashes détectés: {self.crash_count}")
        
        if self.last_crash_trace:
            print("\nDernière stack trace:")
            print(self.last_crash_trace)
        
        print(f"Threads actifs: {threading.active_count()}")
        
        # État final Perception
        if self.perception_ui:
            print(f"État final Perception: {'ACTIF' if self.perception_ui.is_enabled else 'INACTIF'}")
        
        # Nettoyage
        try:
            if hasattr(self, 'tts_safe'):
                self.tts_safe.stop()
        except:
            pass

def main():
    print("🐛 === DEBUG CRASHES PERCEPTION ===")
    print()
    
    detector = PerceptionCrashDetector()
    
    if not detector.initialize():
        print("❌ Échec initialisation")
        return
    
    try:
        # Test 1: Cycle de vie
        success1 = detector.test_perception_lifecycle()
        
        time.sleep(2)
        
        # Test 2: Opération continue
        success2 = detector.test_continuous_operation(30)
        
        # Rapport
        detector.generate_report()
        
        print(f"\n🎯 RÉSULTAT: {'✅ STABLE' if success1 and success2 else '❌ INSTABLE'}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt manuel")
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")
        traceback.print_exc()
    finally:
        detector.generate_report()

if __name__ == "__main__":
    main()