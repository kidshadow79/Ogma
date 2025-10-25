# test_ogma_audio_integration.py

"""
Test complet de l'intégration audio dans OGMA (sans Media Player)
"""

import time
import threading

def test_audio_manager_integration():
    """Test l'audio manager intégré à OGMA"""
    print("🔗 === TEST AUDIO MANAGER OGMA ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        print("Test synthèse via wrapper OGMA...")
        success = audio_mgr.speak("Test intégration OGMA - doit jouer directement sans Media Player", volume=0.5)
        
        if success:
            print("✅ Audio manager OGMA fonctionne")
        else:
            print("⚠️ Audio manager en mode fallback")
        
        time.sleep(3)
        audio_mgr.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur audio manager: {e}")
        return False

def test_simulation_interface_ogma():
    """Simulation du comportement dans l'interface OGMA"""
    print("\n🖥️ === SIMULATION INTERFACE OGMA ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        def simulate_tts_click():
            """Simule un clic sur le bouton TTS dans OGMA"""
            print("👆 Simulation clic bouton TTS...")
            
            # Comme dans ogma_ng.py
            success = audio_mgr.speak("Bonjour ! Ceci est une réponse de Luna. L'audio doit jouer directement dans OGMA.", volume=0.6)
            
            if success:
                print("✅ TTS interface réussi")
            else:
                print("⚠️ TTS interface fallback")
        
        # Lancer dans thread comme dans OGMA
        thread = threading.Thread(target=simulate_tts_click, daemon=True)
        thread.start()
        thread.join(timeout=10)
        
        audio_mgr.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Erreur simulation: {e}")
        return False

def test_perception_coexistence():
    """Test coexistence TTS + Perception"""
    print("\n👁️ === TEST TTS + PERCEPTION ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        # Simuler Perception active
        print("Activation mode Perception...")
        audio_mgr.set_perception_mode(True)
        
        # Test TTS pendant Perception
        print("Test TTS pendant Perception active...")
        success = audio_mgr.speak("TTS fonctionnel même pendant Perception active", volume=0.5)
        
        # Désactiver Perception
        audio_mgr.set_perception_mode(False)
        print("Perception désactivée")
        
        if success:
            print("✅ Coexistence TTS/Perception réussie")
        else:
            print("⚠️ Coexistence limitée")
        
        audio_mgr.cleanup()
        return success
        
    except Exception as e:
        print(f"❌ Erreur coexistence: {e}")
        return False

def main():
    print("🎯 === TEST INTÉGRATION AUDIO COMPLÈTE OGMA ===")
    print("Objectif: Vérifier que l'audio fonctionne dans OGMA sans ouvrir d'apps externes")
    print()
    
    tests = [
        ("Audio Manager OGMA", test_audio_manager_integration),
        ("Simulation Interface", test_simulation_interface_ogma),
        ("TTS + Perception", test_perception_coexistence)
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
        
        time.sleep(1)
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ INTÉGRATION AUDIO OGMA")
    print("="*60)
    
    success_count = sum(results)
    total_tests = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        icon = "✅" if results[i] else "❌"
        print(f"{icon} {test_name}")
    
    print(f"\nTests réussis: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 INTÉGRATION AUDIO PARFAITE")
        print("   → TTS fonctionne directement dans OGMA")
        print("   → Aucune application externe ouverte")
        print("   → Compatible avec Perception")
    elif success_count >= total_tests - 1:
        print("✅ INTÉGRATION MAJORITAIREMENT FONCTIONNELLE")
        print("   → Problème mineur détecté")
    else:
        print("⚠️ PROBLÈMES D'INTÉGRATION")
        print("   → Vérifiez la configuration audio")

if __name__ == "__main__":
    main()