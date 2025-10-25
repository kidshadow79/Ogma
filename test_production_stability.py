# test_production_stability.py

"""
Test de stabilité en production avec OGMA complet
"""

import time
import requests
import threading
from datetime import datetime

class ProductionStabilityTest:
    """Test stabilité en production OGMA"""
    
    def __init__(self):
        self.ogma_url = "http://127.0.0.1:8080"
        self.test_results = {
            'ui_responsive': False,
            'perception_available': False,
            'tts_functional': False,
            'stability_30s': False,
            'no_crashes': False
        }
    
    def test_ui_responsive(self):
        """Test que l'UI répond"""
        print("🌐 Test réactivité interface...")
        
        try:
            response = requests.get(self.ogma_url, timeout=5)
            
            if response.status_code == 200:
                print("✅ Interface OGMA accessible")
                self.test_results['ui_responsive'] = True
                return True
            else:
                print(f"❌ Interface erreur: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Interface inaccessible: {e}")
            return False
    
    def test_perception_integration(self):
        """Test intégration Perception via imports directs"""
        print("👁️ Test intégration Perception...")
        
        try:
            import sys
            sys.path.append('.')
            
            from extensions.perception_ui import get_perception_ui
            from tts_conflict_free import get_conflict_free_tts
            
            perception_ui = get_perception_ui()
            tts_safe = get_conflict_free_tts()
            
            print(f"   Perception disponible: {perception_ui is not None}")
            print(f"   TTS sans conflit: {tts_safe is not None}")
            
            if perception_ui and tts_safe:
                self.test_results['perception_available'] = True
                print("✅ Systèmes Perception + TTS disponibles")
                return True
            else:
                print("❌ Systèmes non disponibles")
                return False
                
        except Exception as e:
            print(f"❌ Erreur intégration: {e}")
            return False
    
    def test_tts_functionality(self):
        """Test fonctionnalité TTS"""
        print("🔊 Test fonctionnalité TTS...")
        
        try:
            from tts_conflict_free import speak_safe, set_perception_active
            
            # Test TTS normal
            success1 = speak_safe("Test TTS production", volume=0.3)
            
            # Test TTS avec Perception active
            set_perception_active(True)
            time.sleep(0.1)
            success2 = speak_safe("Test TTS avec Perception", volume=0.3)
            set_perception_active(False)
            
            if success1 and success2:
                print("✅ TTS fonctionnel (normal + avec Perception)")
                self.test_results['tts_functional'] = True
                return True
            else:
                print(f"❌ TTS échecs: normal={success1}, perception={success2}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur TTS: {e}")
            return False
    
    def test_stability_continuous(self):
        """Test stabilité continue 30s"""
        print("⏱️ Test stabilité continue 30s...")
        
        try:
            from extensions.perception_ui import get_perception_ui
            
            perception_ui = get_perception_ui()
            
            # Démarrer Perception
            if not perception_ui.is_enabled:
                success = perception_ui.start_perception()
                if not success:
                    print("❌ Échec démarrage Perception")
                    return False
                
                print("✅ Perception démarrée pour test")
            
            # Test stabilité 30s
            start_time = time.time()
            stable = True
            
            for i in range(30):
                # Vérifier état
                if not perception_ui.is_enabled or not perception_ui.perception_agent:
                    print(f"❌ Perception arrêtée à T+{i}s")
                    stable = False
                    break
                
                # Affichage toutes les 10s
                if i % 10 == 0:
                    print(f"   T+{i}s - Perception stable")
                
                time.sleep(1)
            
            # Arrêter proprement
            if perception_ui.is_enabled:
                perception_ui.stop_perception()
                print("✅ Perception arrêtée proprement")
            
            if stable:
                print("✅ Stabilité 30s confirmée")
                self.test_results['stability_30s'] = True
                self.test_results['no_crashes'] = True
                return True
            else:
                print("❌ Instabilité détectée")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test stabilité: {e}")
            return False
    
    def generate_report(self):
        """Génère rapport final"""
        print("\n" + "="*60)
        print("📊 RAPPORT TEST PRODUCTION OGMA")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            icon = "✅" if result else "❌"
            print(f"{icon} {test_name.replace('_', ' ').title()}")
        
        print()
        print(f"Tests réussis: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 SYSTÈME PRODUCTION ENTIÈREMENT FONCTIONNEL")
            print("   → OGMA + Perception + TTS sans conflit OPÉRATIONNELS")
        elif passed_tests >= total_tests - 1:
            print("✅ SYSTÈME PRODUCTION MAJORITAIREMENT FONCTIONNEL")
            print("   → Problème mineur détecté")
        else:
            print("⚠️ SYSTÈME PRODUCTION PARTIELLEMENT FONCTIONNEL")
            print("   → Plusieurs problèmes détectés")
        
        return passed_tests == total_tests

def main():
    print("🚀 === TEST STABILITÉ PRODUCTION OGMA ===")
    print()
    print("Ce test vérifie le bon fonctionnement d'OGMA")
    print("avec Perception + TTS sans conflit en production.")
    print()
    
    tester = ProductionStabilityTest()
    
    # Tests séquentiels
    tests = [
        ("Interface responsive", tester.test_ui_responsive),
        ("Intégration Perception", tester.test_perception_integration),
        ("Fonctionnalité TTS", tester.test_tts_functionality),
        ("Stabilité continue", tester.test_stability_continuous)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append(result)
            print(f"Résultat: {'✅ RÉUSSI' if result else '❌ ÉCHOUÉ'}")
        except Exception as e:
            print(f"❌ Erreur test: {e}")
            results.append(False)
        
        time.sleep(1)  # Pause entre tests
    
    # Rapport final
    success = tester.generate_report()
    
    print(f"\n🎯 CONCLUSION: {'PRODUCTION PRÊTE' if success else 'CORRECTIONS NÉCESSAIRES'}")

if __name__ == "__main__":
    main()