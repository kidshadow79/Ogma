"""Test direct d'Edge TTS pour diagnostiquer le problème"""
import asyncio
import edge_tts
import os

async def test_edge_tts():
    print("[TEST] Démarrage test Edge TTS...")
    
    voice = "fr-FR-DeniseNeural"
    text = "Bonjour, ceci est un test de synthèse vocale Edge TTS."
    
    print(f"[TEST] Voix: {voice}")
    print(f"[TEST] Texte: {text}")
    
    try:
        # Méthode 1: Communicate.save()
        print("\n[TEST] Méthode 1: Communicate.save()")
        communicate = edge_tts.Communicate(text, voice)
        output_file = "test_edge_output.mp3"
        
        await communicate.save(output_file)
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"[TEST] ✅ Fichier créé: {size} bytes")
            if size > 0:
                print("[TEST] ✅ Edge TTS fonctionne correctement!")
            else:
                print("[TEST] ⚠️ Fichier vide!")
            os.unlink(output_file)
        else:
            print("[TEST] ❌ Fichier non créé")
            
    except Exception as e:
        print(f"[TEST] ❌ Erreur: {type(e).__name__}: {e}")
        
    # Test avec stream pour plus de détails
    print("\n[TEST] Méthode 2: Communicate.stream()")
    try:
        communicate = edge_tts.Communicate(text, voice)
        audio_chunks = []
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
                
        total_size = sum(len(c) for c in audio_chunks)
        print(f"[TEST] Audio reçu: {total_size} bytes en {len(audio_chunks)} chunks")
        
        if total_size > 0:
            print("[TEST] ✅ Stream Edge TTS fonctionne!")
        else:
            print("[TEST] ⚠️ Aucune donnée audio reçue via stream")
            
    except Exception as e:
        print(f"[TEST] ❌ Erreur stream: {type(e).__name__}: {e}")

    # Lister les voix disponibles
    print("\n[TEST] Voix françaises disponibles:")
    try:
        voices = await edge_tts.list_voices()
        french_voices = [v for v in voices if v["Locale"].startswith("fr-")]
        for v in french_voices[:5]:
            print(f"  - {v['ShortName']}: {v['FriendlyName']}")
    except Exception as e:
        print(f"[TEST] ❌ Erreur liste voix: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge_tts())
