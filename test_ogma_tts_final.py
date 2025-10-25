# test_ogma_tts_final.py

"""
Test final TTS dans OGMA - vérification complète
"""

import sys
import os

def test_ogma_tts_integration():
    """Test complet TTS dans OGMA"""
    print("🖥️ === TEST FINAL OGMA TTS ===")
    
    # Simuler environnement OGMA
    try:
        # Import OGMA modules
        from audio_manager_wrapper import get_audio_manager
        
        print("✅ Import wrapper OGMA réussi")
        
        # Initialiser
        audio_mgr = get_audio_manager()
        success_init = audio_mgr.initialize_tts()
        
        if success_init:
            print("✅ Initialisation TTS réussie")
        else:
            print("❌ Échec initialisation TTS")
            return False
        
        # Test 1: Lecture simple
        print("\n--- Test 1: Lecture simple ---")
        success_speak = audio_mgr.speak("Bonjour, ceci est un test du système TTS dans OGMA.", volume=0.5)
        
        if success_speak:
            print("✅ Speak() fonctionne")
        else:
            print("❌ Speak() échoue")
        
        import time
        time.sleep(3)
        
        # Test 2: Stop pendant lecture
        print("\n--- Test 2: Stop pendant lecture ---")
        audio_mgr.speak("Ceci est un long texte qui va être interrompu avant la fin par la fonction stop.", volume=0.5)
        time.sleep(1)
        
        success_stop = audio_mgr.stop_speaking()
        
        if success_stop:
            print("✅ Stop_speaking() fonctionne")
        else:
            print("❌ Stop_speaking() échoue")
        
        time.sleep(1)
        
        # Test 3: Nouveau speak après stop
        print("\n--- Test 3: Nouveau speak après stop ---")
        success_after_stop = audio_mgr.speak("Nouvelle lecture après arrêt - ceci confirme que le système est stable.", volume=0.5)
        
        if success_after_stop:
            print("✅ Speak après stop fonctionne")
        else:
            print("❌ Speak après stop échoue")
        
        time.sleep(3)
        
        # Cleanup
        audio_mgr.cleanup()
        print("✅ Cleanup terminé")
        
        return success_init and success_speak and success_stop and success_after_stop
        
    except Exception as e:
        print(f"❌ Erreur test OGMA: {e}")
        return False

def verify_ogma_files():
    """Vérifier que les fichiers OGMA sont bien en place"""
    print("📁 === VÉRIFICATION FICHIERS ===")
    
    files_to_check = [
        "tts_conflict_free.py",
        "audio_manager_wrapper.py",
        "ogma_ng.py"
    ]
    
    all_good = True
    
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} MANQUANT")
            all_good = False
    
    return all_good

def main():
    print("🎯 === TEST FINAL TTS OGMA ===")
    print("Validation complète avant utilisation production")
    print()
    
    # Vérifications
    files_ok = verify_ogma_files()
    
    if not files_ok:
        print("❌ Fichiers manquants - arrêt du test")
        return
    
    # Test intégration
    integration_ok = test_ogma_tts_integration()
    
    print("\n" + "="*60)
    print("📊 RAPPORT FINAL")
    print("="*60)
    
    if files_ok and integration_ok:
        print("🎉 TTS OGMA PRÊT POUR PRODUCTION")
        print()
        print("✅ Tous les fichiers présents")
        print("✅ Initialisation TTS fonctionnelle") 
        print("✅ Fonction speak() opérationnelle")
        print("✅ Fonction stop_speaking() opérationnelle")
        print("✅ Stabilité après stop confirmée")
        print()
        print("🚀 INSTRUCTIONS:")
        print("1. Lancez OGMA: python launch_ogma.py")
        print("2. Testez le bouton TTS dans l'interface")
        print("3. Vérifiez que:")
        print("   - L'audio se lit complètement")
        print("   - Le bouton stop interrompt la lecture")
        print("   - Pas de cumul de lectures multiples")
        
    else:
        print("⚠️ PROBLÈMES DÉTECTÉS")
        if not files_ok:
            print("❌ Fichiers manquants")
        if not integration_ok:
            print("❌ Tests d'intégration échoués")
        print()
        print("🔧 Actions requises:")
        print("1. Vérifier les fichiers TTS")
        print("2. Relancer les tests individuels")

if __name__ == "__main__":
    main()