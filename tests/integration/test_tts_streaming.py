#!/usr/bin/env python3
"""
Test du système TTS Streaming et Cleanup
=========================================
Vérifie que le système de TTS en streaming fonctionne correctement.
"""

import sys
import time
import os
import tempfile

def test_tts_conflict_free():
    """Test du module ConflictFreeTTS"""
    print("=" * 60)
    print("Test du système TTS Streaming")
    print("=" * 60)
    
    try:
        from tts_conflict_free import get_conflict_free_tts, _get_tts_audio_temp_dir
        print("✅ Import tts_conflict_free OK")
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False
    
    # Test instance
    tts = get_conflict_free_tts()
    print(f"✅ Instance ConflictFreeTTS créée")
    
    # Test dossier temporaire persistant
    temp_dir = _get_tts_audio_temp_dir()
    print(f"✅ Dossier temp persistant: {temp_dir}")
    
    # Vérifier attributs streaming
    streaming_attrs = ['_streaming_buffer', '_streaming_enabled', '_sentence_queue', 
                      'process_streaming_chunk', 'flush_streaming_buffer', 'reset_streaming']
    
    for attr in streaming_attrs:
        if hasattr(tts, attr):
            print(f"  ✅ Attribut {attr} présent")
        else:
            print(f"  ❌ Attribut {attr} MANQUANT")
            return False
    
    # Vérifier attributs pygame
    pygame_attrs = ['_pygame_initialized', '_cleanup_pygame_state']
    
    for attr in pygame_attrs:
        if hasattr(tts, attr):
            print(f"  ✅ Attribut {attr} présent")
        else:
            print(f"  ❌ Attribut {attr} MANQUANT")
            return False
    
    print()
    
    # Test parsing de phrases
    print("Test détection de phrases en streaming:")
    test_chunks = [
        "Bonjour, ",
        "comment allez-vous? ",
        "Je suis ravis. ",
        "Ceci est une phrase plus longue qui continue",
        " encore et encore! ",
        "Et voilà."
    ]
    
    tts.reset_streaming()
    all_sentences = []
    
    for chunk in test_chunks:
        sentences = tts.process_streaming_chunk(chunk)
        if sentences:
            all_sentences.extend(sentences)
            for s in sentences:
                print(f"  📝 Phrase détectée: '{s[:50]}...' " if len(s) > 50 else f"  📝 Phrase détectée: '{s}'")
    
    print(f"\n  Total phrases détectées: {len(all_sentences)}")
    print(f"  Buffer restant: '{tts._streaming_buffer}'")
    
    # Flush remaining
    tts.flush_streaming_buffer()
    print(f"  Après flush, buffer: '{tts._streaming_buffer}'")
    
    print()
    return True


def test_audio_manager_wrapper():
    """Test du wrapper AudioManager"""
    print("=" * 60)
    print("Test AudioManagerWrapper")
    print("=" * 60)
    
    try:
        from audio_manager_wrapper import AudioManagerWrapper, get_audio_manager
        print("✅ Import audio_manager_wrapper OK")
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False
    
    # Test instance
    wrapper = get_audio_manager()
    print(f"✅ Instance AudioManagerWrapper créée")
    
    # Vérifier méthodes streaming
    streaming_methods = ['process_streaming_chunk', 'speak_streaming_sentence', 
                        'flush_streaming_buffer', 'reset_streaming', 'set_streaming_enabled']
    
    for method in streaming_methods:
        if hasattr(wrapper, method):
            print(f"  ✅ Méthode {method} présente")
        else:
            print(f"  ❌ Méthode {method} MANQUANTE")
            return False
    
    print()
    return True


def test_file_cleanup():
    """Test du système de fichiers audio persistants"""
    print("=" * 60)
    print("Test système de fichiers persistants")
    print("=" * 60)
    
    from tts_conflict_free import get_conflict_free_tts, _get_tts_audio_temp_dir
    from pathlib import Path
    
    # Vérifier le dossier persistant
    temp_dir = _get_tts_audio_temp_dir()
    print(f"  Dossier TTS: {temp_dir}")
    print(f"  Existe: {temp_dir.exists()}")
    
    if not temp_dir.exists():
        print(f"  ❌ Dossier non créé")
        return False
    
    # Créer un fichier de test dans le dossier
    test_file = temp_dir / f"ogma_tts_test_{int(time.time()*1000)}.mp3"
    test_file.write_text("test content")
    
    print(f"  Fichier test créé: {test_file.name}")
    print(f"  Existe: {test_file.exists()}")
    
    # Vérifier qu'il reste (pas de suppression automatique)
    time.sleep(0.5)
    if test_file.exists():
        print(f"  ✅ Fichier conservé (suppression uniquement à la fermeture)")
        test_file.unlink()  # Nettoyer le test
        print(f"  ✅ Test réussi")
        return True
    else:
        print(f"  ❌ Fichier supprimé prématurément")
        return False


def main():
    print("\n🔊 TEST TTS STREAMING & CLEANUP\n")
    
    results = []
    
    results.append(("ConflictFreeTTS", test_tts_conflict_free()))
    results.append(("AudioManagerWrapper", test_audio_manager_wrapper()))
    results.append(("File Cleanup", test_file_cleanup()))
    
    print("=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 TOUS LES TESTS PASSÉS!")
        return 0
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        return 1


if __name__ == "__main__":
    sys.exit(main())
