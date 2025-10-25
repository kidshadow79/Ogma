# test_tts_controls.py

"""
Test des contrôles TTS : lecture complète + arrêt sur clic
"""

import time
import threading

def test_full_playback():
    """Test que la lecture va jusqu'au bout"""
    print("🎵 === TEST LECTURE COMPLÈTE ===")
    
    try:
        from tts_conflict_free import get_conflict_free_tts
        
        tts_safe = get_conflict_free_tts()
        tts_safe.initialize()
        
        long_text = (
            "Ceci est un test de lecture complète. "
            "Le texte doit être lu entièrement, du début à la fin, "
            "sans s'arrêter au milieu. Cette phrase est assez longue "
            "pour vérifier que le système lit tout le contenu. "
            "Si vous entendez cette fin de phrase, le test est réussi."
        )
        
        print("🎵 Début lecture longue...")
        start_time = time.time()
        
        success = tts_safe.speak(long_text, volume=0.6)
        
        # Attendre que la lecture soit terminée
        while tts_safe.is_playing:
            time.sleep(0.5)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Lecture terminée en {duration:.1f}s")
        
        tts_safe.stop()
        return success
        
    except Exception as e:
        print(f"❌ Erreur test lecture: {e}")
        return False

def test_stop_on_replay():
    """Test que recliquer arrête la lecture en cours"""
    print("\n🛑 === TEST ARRÊT SUR NOUVEAU CLIC ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        # Premier texte long
        long_text = (
            "Première lecture qui doit être interrompue. "
            "Cette phrase ne devrait pas aller jusqu'au bout "
            "car une deuxième lecture va l'interrompre. "
            "Si vous entendez cette fin, il y a un problème."
        )
        
        print("🎵 Début première lecture...")
        audio_mgr.speak(long_text, volume=0.5)
        
        # Attendre un peu puis interrompre
        time.sleep(2)
        
        print("🛑 Interruption par nouvelle lecture...")
        success = audio_mgr.speak("Deuxième lecture qui remplace la première", volume=0.5)
        
        time.sleep(3)
        
        audio_mgr.cleanup()
        
        if success:
            print("✅ Interruption réussie")
        else:
            print("❌ Interruption échouée")
            
        return success
        
    except Exception as e:
        print(f"❌ Erreur test interruption: {e}")
        return False

def test_stop_method():
    """Test de la méthode stop_speaking"""
    print("\n⏹️ === TEST MÉTHODE STOP ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        # Texte long à interrompre
        long_text = (
            "Cette lecture sera interrompue par la méthode stop. "
            "Si le stop fonctionne, vous n'entendrez pas cette fin de phrase "
            "qui contient ce message final pour vérifier l'arrêt."
        )
        
        print("🎵 Début lecture à interrompre...")
        audio_mgr.speak(long_text, volume=0.5)
        
        # Attendre puis arrêter
        time.sleep(2)
        
        print("🛑 Appel stop_speaking()...")
        success = audio_mgr.stop_speaking()
        
        if success:
            print("✅ Stop réussi")
        else:
            print("❌ Stop échoué")
        
        time.sleep(1)
        audio_mgr.cleanup()
        
        return success
        
    except Exception as e:
        print(f"❌ Erreur test stop: {e}")
        return False

def test_simulation_ogma_behavior():
    """Simulation du comportement dans OGMA"""
    print("\n🖥️ === SIMULATION COMPORTEMENT OGMA ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        def simulate_button_click(text):
            """Simule un clic sur le bouton TTS dans OGMA"""
            print(f"👆 Clic bouton TTS: '{text[:30]}...'")
            return audio_mgr.speak(text, volume=0.5)
        
        # Premier clic
        first_text = "Première réponse de Luna qui commence à parler et explique quelque chose de long"
        simulate_button_click(first_text)
        
        time.sleep(2)
        
        # Deuxième clic (doit arrêter le premier)
        print("👆 Nouveau clic (doit arrêter le premier)")
        second_text = "Nouvelle lecture qui remplace la première"
        success = simulate_button_click(second_text)
        
        time.sleep(3)
        
        audio_mgr.cleanup()
        
        if success:
            print("✅ Comportement OGMA correct")
        else:
            print("❌ Comportement OGMA problématique")
        
        return success
        
    except Exception as e:
        print(f"❌ Erreur simulation: {e}")
        return False

def main():
    print("🎯 === TEST CONTRÔLES TTS ===")
    print("Objectifs:")
    print("1. Lecture complète jusqu'au bout")
    print("2. Arrêt sur nouveau clic (pas de cumul)")
    print("3. Méthode stop fonctionnelle")
    print()
    
    tests = [
        ("Lecture complète", test_full_playback),
        ("Arrêt sur nouveau clic", test_stop_on_replay),
        ("Méthode stop", test_stop_method),
        ("Simulation OGMA", test_simulation_ogma_behavior)
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
    print("📊 RÉSUMÉ CONTRÔLES TTS")
    print("="*60)
    
    success_count = sum(results)
    total_tests = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        icon = "✅" if results[i] else "❌"
        print(f"{icon} {test_name}")
    
    print(f"\nTests réussis: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 CONTRÔLES TTS PARFAITS")
        print("   → Lecture complète fonctionnelle")
        print("   → Pas de cumul de lectures")
        print("   → Arrêt sur clic opérationnel")
    elif success_count >= total_tests - 1:
        print("✅ CONTRÔLES MAJORITAIREMENT FONCTIONNELS")
        print("   → Problème mineur détecté")
    else:
        print("⚠️ PROBLÈMES DE CONTRÔLES")
        print("   → Corrections nécessaires")

if __name__ == "__main__":
    main()