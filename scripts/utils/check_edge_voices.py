#!/usr/bin/env python3
"""
Vérifier toutes les voix disponibles sur Edge TTS
"""
import asyncio
import edge_tts

async def list_all_edge_voices():
    """Liste toutes les voix Edge TTS disponibles"""
    try:
        voices = await edge_tts.list_voices()
        
        print("VOIX EDGE TTS DISPONIBLES")
        print("=" * 50)
        
        # Filtrer par régions
        spanish_voices = [v for v in voices if v['Locale'].startswith('es-')]
        french_voices = [v for v in voices if v['Locale'].startswith('fr-')]
        
        print("\n=== VOIX ESPAGNOLES (Sud-Amérique) ===")
        for voice in spanish_voices:
            gender = voice.get('Gender', 'Unknown')
            gender_icon = "♀️" if gender == "Female" else "♂️" if gender == "Male" else "⚪"
            
            locale = voice['Locale']
            name = voice['DisplayName']
            short_name = voice['ShortName']
            
            print(f"{gender_icon} {locale} - {name} ({short_name})")
        
        print(f"\nTotal voix espagnoles: {len(spanish_voices)}")
        
        print("\n=== VOIX FRANÇAISES (toutes régions) ===")
        for voice in french_voices:
            gender = voice.get('Gender', 'Unknown')
            gender_icon = "♀️" if gender == "Female" else "♂️" if gender == "Male" else "⚪"
            
            locale = voice['Locale']
            name = voice['DisplayName']
            short_name = voice['ShortName']
            
            print(f"{gender_icon} {locale} - {name} ({short_name})")
            
        print(f"\nTotal voix françaises: {len(french_voices)}")
        
        # Voix féminines sud-américaines spécifiquement
        print("\n=== VOIX FÉMININES SUD-AMÉRICAINES ===")
        south_american_locales = ['es-AR', 'es-CL', 'es-CO', 'es-PE', 'es-VE', 'es-UY', 'es-EC', 'es-BO']
        
        for voice in spanish_voices:
            if voice.get('Gender') == 'Female' and any(voice['Locale'].startswith(loc) for loc in south_american_locales):
                locale = voice['Locale']
                name = voice['DisplayName']
                short_name = voice['ShortName']
                print(f"♀️ {locale} - {name} ({short_name})")
        
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(list_all_edge_voices())