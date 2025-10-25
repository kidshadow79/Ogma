# test_tts_audio_fix.py

"""
Test audio TTS avec fallbacks améliorés
"""

import time

def test_audio_playback():
    """Test lecture audio avec différents moteurs"""
    print("🎵 === TEST LECTURE AUDIO AMÉLIORÉE ===")
    
    try:
        from tts_conflict_free import get_conflict_free_tts
        
        tts_safe = get_conflict_free_tts()
        tts_safe.initialize()
        
        test_text = "Test de lecture audio avec système amélioré. Si vous entendez ce message, l'audio fonctionne parfaitement."
        
        print("🎵 Test lecture courte...")
        success = tts_safe.speak(test_text, volume=0.6)
        
        # Attendre fin
        time.sleep(3)
        
        print(f"Résultat: {'✅ RÉUSSI' if success else '❌ ÉCHOUÉ'}")
        
        tts_safe.stop()
        return success
        
    except Exception as e:
        print(f"❌ Erreur test audio: {e}")
        return False

def test_ogma_integration():
    """Test intégration OGMA avec nouveau système"""
    print("\n🖥️ === TEST INTÉGRATION OGMA ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        print("🎵 Test via wrapper OGMA...")
        success = audio_mgr.speak("Test d'intégration OGMA avec système audio amélioré", volume=0.5)
        
        time.sleep(3)
        
        print(f"Résultat: {'✅ RÉUSSI' if success else '❌ ÉCHOUÉ'}")
        
        audio_mgr.cleanup()
        return success
        
    except Exception as e:
        print(f"❌ Erreur test OGMA: {e}")
        return False

def main():
    print("🔊 === TEST AUDIO TTS AMÉLIORÉ ===")
    print("Objectif: Lecture audio sans erreurs pygame")
    print()
    
    tests = [
        ("Audio direct", test_audio_playback),
        ("Intégration OGMA", test_ogma_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            print(f"❌ Erreur: {e}")
            results.append(False)
        
        time.sleep(1)
    
    print("\n" + "="*50)
    print("📊 RÉSUMÉ AUDIO")
    print("="*50)
    
    success_count = sum(results)
    total_tests = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        icon = "✅" if results[i] else "❌"
        print(f"{icon} {test_name}")
    
    if success_count == total_tests:
        print("🎉 AUDIO PARFAIT")
        print("   → Prêt pour production OGMA")
    else:
        print("⚠️ PROBLÈMES AUDIO")
        print("   → Vérifier configuration")

if __name__ == "__main__":
    main()