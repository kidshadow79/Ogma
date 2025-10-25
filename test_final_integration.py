# test_final_integration.py

"""
Test final d'intégration complète TTS sans conflit dans OGMA
"""

import requests
import time

def test_ogma_interface():
    """Test que l'interface OGMA répond"""
    try:
        response = requests.get("http://127.0.0.1:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Interface OGMA accessible")
            return True
        else:
            print(f"❌ Interface erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Interface inaccessible: {e}")
        return False

def test_tts_systems():
    """Test tous les systèmes TTS"""
    try:
        # Test TTS sans conflit
        from tts_conflict_free import get_conflict_free_tts
        tts_safe = get_conflict_free_tts()
        tts_safe.initialize()
        
        success1 = tts_safe.speak("Test TTS sans conflit fonctionnel", volume=0.3)
        print(f"TTS sans conflit: {'✅ OK' if success1 else '❌ Échec'}")
        
        # Test wrapper
        from audio_manager_wrapper import get_audio_manager
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        success2 = audio_mgr.speak("Test wrapper audio manager", volume=0.3)
        print(f"Wrapper audio: {'✅ OK' if success2 else '❌ Échec'}")
        
        # Test avec Perception
        audio_mgr.set_perception_mode(True)
        success3 = audio_mgr.speak("Test avec mode Perception", volume=0.3)
        audio_mgr.set_perception_mode(False)
        print(f"TTS + Perception: {'✅ OK' if success3 else '❌ Échec'}")
        
        # Nettoyage
        audio_mgr.cleanup()
        tts_safe.stop()
        
        return success1 and success2 and success3
        
    except Exception as e:
        print(f"❌ Erreur test TTS: {e}")
        return False

def test_perception_stability():
    """Test stabilité Perception"""
    try:
        from extensions.perception_ui import get_perception_ui
        
        perception_ui = get_perception_ui()
        
        # Test démarrage
        if not perception_ui.is_enabled:
            success = perception_ui.start_perception()
            if not success:
                print("❌ Échec démarrage Perception")
                return False
            print("✅ Perception démarrée")
        
        # Attendre stabilisation
        time.sleep(5)
        
        # Vérifier état
        if not perception_ui.is_enabled or not perception_ui.perception_agent:
            print("❌ Perception instable")
            return False
        
        print("✅ Perception stable")
        
        # Arrêt propre
        perception_ui.stop_perception()
        print("✅ Perception arrêtée proprement")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test Perception: {e}")
        return False

def main():
    print("🎯 === TEST FINAL INTÉGRATION COMPLÈTE ===")
    print()
    print("Tests de validation finale de l'intégration TTS sans conflit")
    print()
    
    tests = [
        ("Interface OGMA", test_ogma_interface),
        ("Systèmes TTS", test_tts_systems), 
        ("Stabilité Perception", test_perception_stability)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            success = test_func()
            results.append(success)
            print(f"Résultat: {'✅ RÉUSSI' if success else '❌ ÉCHOUÉ'}")
        except Exception as e:
            print(f"❌ Erreur: {e}")
            results.append(False)
        
        print()
        time.sleep(1)
    
    # Résumé
    print("="*50)
    print("📊 RÉSUMÉ FINAL")
    print("="*50)
    
    success_count = sum(results)
    total_tests = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        icon = "✅" if results[i] else "❌"
        print(f"{icon} {test_name}")
    
    print()
    print(f"Tests réussis: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 INTÉGRATION PARFAITEMENT FONCTIONNELLE")
        print("   → OGMA + Perception + TTS sans conflit OPÉRATIONNELS")
        print("   → Système prêt pour utilisation intensive")
    elif success_count >= total_tests - 1:
        print("✅ INTÉGRATION MAJORITAIREMENT FONCTIONNELLE") 
        print("   → Problème mineur détecté")
    else:
        print("⚠️ INTÉGRATION PARTIELLEMENT FONCTIONNELLE")
        print("   → Corrections nécessaires")
    
    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)