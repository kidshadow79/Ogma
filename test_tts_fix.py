# test_tts_fix.py

"""
Test rapide de la correction TTS
"""

import sys
sys.path.append('.')

def test_tts_wrapper():
    """Test le wrapper TTS"""
    try:
        from audio_manager_wrapper import get_audio_manager
        
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        # Test synthèse (doit retourner bool, pas async)
        result = audio_mgr.speak("Test correction TTS", volume=0.3)
        print(f"Résultat synthèse: {result} (type: {type(result)})")
        
        if isinstance(result, bool):
            print("✅ Wrapper fonctionne correctement (retourne bool)")
            return True
        else:
            print(f"❌ Wrapper problématique (retourne {type(result)})")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test wrapper: {e}")
        return False

def test_threading_call():
    """Test appel dans thread"""
    try:
        import threading
        
        from audio_manager_wrapper import get_audio_manager
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        def audio_task():
            try:
                success = audio_mgr.speak("Test thread TTS", volume=0.3)
                print(f"Thread result: {success}")
            except Exception as e:
                print(f"Thread error: {e}")
        
        # Lancer dans thread
        thread = threading.Thread(target=audio_task, daemon=True)
        thread.start()
        thread.join(timeout=5)
        
        print("✅ Thread TTS fonctionne")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test thread: {e}")
        return False

def main():
    print("🔧 === TEST CORRECTION TTS ===")
    
    tests = [
        ("Wrapper TTS", test_tts_wrapper),
        ("Threading TTS", test_threading_call)
    ]
    
    success_count = 0
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            success_count += 1
    
    print(f"\n📊 Résultat: {success_count}/{len(tests)} tests réussis")
    
    if success_count == len(tests):
        print("🎉 CORRECTION TTS FONCTIONNELLE")
    else:
        print("⚠️ Problèmes détectés")

if __name__ == "__main__":
    main()