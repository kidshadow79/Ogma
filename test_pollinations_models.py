"""
Test des modèles Pollinations.AI disponibles
"""
import asyncio
import aiohttp

async def test_pollinations_models():
    """Teste les différents modèles Pollinations"""
    
    # Modèles connus de Pollinations
    models = [
        "flux",           # Flux (défaut)
        "flux-pro",       # Flux Pro (haute qualité, CENSURE NSFW)
        "flux-realism",   # Flux Realism
        "turbo",          # Turbo (rapide)
        "flux-anime",     # Flux Anime
        "flux-3d",        # Flux 3D
        "any-dark",       # Any Dark (NSFW possible?)
    ]
    
    test_prompt = "beautiful woman portrait"
    
    print("🔍 Test des modèles Pollinations.AI disponibles\n")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        for model in models:
            url = f"https://image.pollinations.ai/prompt/{test_prompt}?model={model}&width=512&height=512&nologo=true"
            
            try:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    status = response.status
                    if status == 200:
                        print(f"✅ {model:20s} - Disponible")
                    else:
                        print(f"❌ {model:20s} - HTTP {status}")
            except Exception as e:
                print(f"⚠️ {model:20s} - Erreur: {str(e)[:50]}")
            
            await asyncio.sleep(0.5)  # Rate limiting

    print("\n" + "="*80)
    print("💡 INFORMATIONS SUR LES MODÈLES:")
    print("="*80)
    print("""
    flux          - Modèle de base, NSFW PERMIS ✅
    flux-pro      - Haute qualité, NSFW BLOQUÉ ❌
    flux-realism  - Réalisme poussé, NSFW ?
    turbo         - Rapide, qualité moindre, NSFW PERMIS ✅
    flux-anime    - Style anime, NSFW ?
    flux-3d       - Style 3D, NSFW ?
    any-dark      - Modèle alternatif, NSFW ?
    
    ⚠️ IMPORTANT:
    - flux-pro = MEILLEURE QUALITÉ mais CENSURE NSFW
    - flux/turbo = NSFW OK mais qualité moyenne
    - La clé est l'ENRICHISSEMENT DU PROMPT, pas le modèle!
    """)

if __name__ == "__main__":
    asyncio.run(test_pollinations_models())
