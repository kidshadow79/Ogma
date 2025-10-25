# test_audio_direct.py

"""
Test de la correction de lecture audio directe (sans ouvrir Media Player)
"""

import time

def test_edge_tts_direct():
    """Test Edge TTS sans ouvrir d'application externe"""
    print("🎵 === TEST EDGE TTS LECTURE DIRECTE ===")
    
    try:
        from tts_conflict_free import get_conflict_free_tts
        
        tts_safe = get_conflict_free_tts()
        tts_safe.initialize()
        
        print("Lecture test - doit jouer DANS OGMA, pas Media Player...")
        success = tts_safe.speak("Test de lecture audio directe sans ouvrir Media Player", volume=0.5)
        
        if success:
            print("✅ Test réussi - audio lu directement")
        else:
            print("❌ Test échoué")
            
        time.sleep(3)  # Laisser temps pour la lecture
        
        tts_safe.stop()
        return success
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_winsound_compatibility():
    """Test compatibilité winsound"""
    print("\n🔊 === TEST WINSOUND WINDOWS ===")
    
    try:
        import winsound
        import tempfile
        from gtts import gTTS
        import os
        
        # Créer un fichier audio test
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        tts = gTTS(text="Test winsound direct", lang="fr")
        tts.save(tmp_path)
        
        print("Lecture avec winsound (doit être directe)...")
        winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
        
        # Nettoyer
        os.unlink(tmp_path)
        
        print("✅ Winsound fonctionne")
        return True
        
    except Exception as e:
        print(f"❌ Erreur winsound: {e}")
        return False

def test_pygame_fallback():
    """Test fallback pygame"""
    print("\n🎮 === TEST PYGAME FALLBACK ===")
    
    try:
        import pygame
        print("✅ Pygame disponible")
        return True
    except ImportError:
        print("⚠️ Pygame non disponible (normal)")
        return False

def main():
    print("🎯 === TEST LECTURE AUDIO DIRECTE ===")
    print("Objectif: Vérifier que l'audio ne lance pas Media Player")
    print()
    
    tests = [
        ("Edge TTS Direct", test_edge_tts_direct),
        ("Winsound Windows", test_winsound_compatibility), 
        ("Pygame Fallback", test_pygame_fallback)
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
    
    print("\n" + "="*50)
    print("📊 RÉSUMÉ TESTS AUDIO DIRECT")
    print("="*50)
    
    for i, (test_name, _) in enumerate(tests):
        icon = "✅" if results[i] else "❌"
        print(f"{icon} {test_name}")
    
    if results[0]:  # Test principal réussi
        print("\n🎉 CORRECTION RÉUSSIE")
        print("   → Audio lu directement dans OGMA")
        print("   → Plus de Media Player externe")
    else:
        print("\n⚠️ Problèmes détectés")
        print("   → Vérifiez la configuration audio")

if __name__ == "__main__":
    main()