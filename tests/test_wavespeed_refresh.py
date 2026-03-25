"""
Test de la fonctionnalité de refresh dynamique des modèles WaveSpeed
"""
import asyncio
import json

async def test_wavespeed_refresh():
    print("=== TEST REFRESH MODÈLES WAVESPEED ===")
    print()
    
    # 1. Charger les settings
    print("1. Chargement des settings...")
    with open('data/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    api_key = settings.get('api_keys_vault', {}).get('WaveSpeed', '')
    if not api_key:
        print("   ❌ Aucune clé API WaveSpeed configurée")
        return
    print(f"   ✅ Clé API: {api_key[:15]}...")
    
    # 2. Créer le provider WaveSpeed
    print()
    print("2. Création du provider WaveSpeed...")
    from extensions.text2img.image_backend import WaveSpeedImageProvider
    
    provider = WaveSpeedImageProvider(api_key)
    print(f"   ✅ Provider créé: {provider.name}")
    print(f"   ✅ Disponible: {provider.is_available}")
    
    # 3. Test fetch_live_models (Text-to-Image)
    print()
    print("3. Test fetch_live_models (T2I)...")
    models_t2i, error_t2i = await provider.fetch_live_models()
    
    if error_t2i:
        print(f"   ❌ Erreur: {error_t2i}")
    elif models_t2i:
        print(f"   ✅ {len(models_t2i)} modèles T2I récupérés")
        print(f"   📋 Premiers modèles:")
        for model in models_t2i[:5]:
            print(f"      - {model}")
        if len(models_t2i) > 5:
            print(f"      ... et {len(models_t2i) - 5} autres")
    else:
        print("   ⚠️ Aucun modèle récupéré")
    
    # 4. Test fetch_live_img2img_models (Image-to-Image)
    print()
    print("4. Test fetch_live_img2img_models (I2I)...")
    models_i2i, error_i2i = await provider.fetch_live_img2img_models()
    
    if error_i2i:
        print(f"   ❌ Erreur: {error_i2i}")
    elif models_i2i:
        print(f"   ✅ {len(models_i2i)} modèles I2I récupérés")
        print(f"   📋 Premiers modèles:")
        for model in models_i2i[:5]:
            print(f"      - {model}")
        if len(models_i2i) > 5:
            print(f"      ... et {len(models_i2i) - 5} autres")
    else:
        print("   ⚠️ Aucun modèle récupéré")
    
    # 5. Comparaison avec modèles hardcodés
    print()
    print("5. Comparaison avec modèles hardcodés...")
    hardcoded_t2i = provider.get_available_models()
    hardcoded_i2i = provider.get_img2img_models()
    
    print(f"   📦 Hardcodés T2I: {len(hardcoded_t2i)} modèles")
    print(f"   📦 Hardcodés I2I: {len(hardcoded_i2i)} modèles")
    
    if models_t2i:
        nouveaux_t2i = set(models_t2i) - set(hardcoded_t2i)
        if nouveaux_t2i:
            print(f"   🆕 {len(nouveaux_t2i)} nouveaux modèles T2I découverts:")
            for model in list(nouveaux_t2i)[:3]:
                print(f"      - {model}")
    
    if models_i2i:
        nouveaux_i2i = set(models_i2i) - set(hardcoded_i2i)
        if nouveaux_i2i:
            print(f"   🆕 {len(nouveaux_i2i)} nouveaux modèles I2I découverts:")
            for model in list(nouveaux_i2i)[:3]:
                print(f"      - {model}")
    
    print()
    print("=== ✅ TEST TERMINÉ ===")

if __name__ == "__main__":
    asyncio.run(test_wavespeed_refresh())
