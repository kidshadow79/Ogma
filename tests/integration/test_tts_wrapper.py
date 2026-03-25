"""
Test du wrapper TTS unifié - Tous les moteurs + Cascade Fallback
"""

import asyncio
import time
from tts_conflict_free import get_conflict_free_tts, speak_safe

def test_cascade_fallback():
    """Test la cascade de fallback Edge TTS -> gTTS -> System"""
    print('=' * 60)
    print('=== TEST CASCADE FALLBACK TTS ===')
    print('=' * 60)
    
    tts = get_conflict_free_tts()
    tts.initialize()
    
    print(f"\nMoteur principal: {tts.current_engine}")
    print(f"Moteurs disponibles: {list(tts.available_engines.keys())}")
    
    print("\n[TEST] Envoi texte (Edge TTS va échouer -> doit basculer sur gTTS)...")
    speak_safe("Bonjour, ceci est un test de la cascade de fallback TTS.")
    
    # Attendre que la queue soit traitée
    print("\n[ATTENTE] Traitement en cours...")
    time.sleep(8)
    
    print("\n✅ Test terminé - Vérifiez si vous avez entendu l'audio via gTTS")
    
    # Arrêt propre
    tts.stop()

if __name__ == "__main__":
    test_cascade_fallback()

