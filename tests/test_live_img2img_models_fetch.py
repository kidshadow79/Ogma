"""
Test du système de récupération dynamique des modèles IMG2IMG depuis les APIs
"""

import asyncio
import sys
from extensions.text2img.image_backend import get_image_backend, reset_backend


class MockSettingsManager:
    """Simulateur de settings manager pour les tests"""
    def __init__(self):
        self.settings = {
            'api_keys_vault': {
                'GROK': '',
                'OpenAI': '',
                'Google': '',
                'Kie': '',  # Remplacer par vraie clé Kie pour tester
                'WaveSpeed': ''  # Remplacer par vraie clé WaveSpeed pour tester
            }
        }


async def test_kie_img2img_models():
    """Test récupération modèles img2img Kie.ai"""
    print("\n" + "="*60)
    print("TEST: Récupération modèles IMG2IMG Kie.ai")
    print("="*60)
    
    # Reset backend
    reset_backend()
    
    # Créer mock settings
    sm = MockSettingsManager()
    
    # Demander la clé API
    kie_key = input("Entrez votre clé API Kie.ai (ou ENTER pour skip): ").strip()
    if not kie_key:
        print("⚠️ Aucune clé Kie - test skippé")
        return
    
    sm.settings['api_keys_vault']['Kie'] = kie_key
    
    # Créer backend
    backend = get_image_backend(sm)
    
    if not backend:
        print("❌ Impossible de créer le backend")
        return
    
    # Tester fetch_live_img2img_models
    print("\n🔄 Appel à fetch_live_img2img_models('Kie')...")
    models, error = await backend.fetch_live_img2img_models('Kie')
    
    if error:
        print(f"❌ Erreur: {error}")
        return
    
    if not models:
        print("⚠️ Aucun modèle img2img récupéré")
        return
    
    print(f"\n✅ {len(models)} modèles img2img Kie récupérés:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")


async def test_wavespeed_img2img_models():
    """Test récupération modèles img2img WaveSpeed.ai"""
    print("\n" + "="*60)
    print("TEST: Récupération modèles IMG2IMG WaveSpeed.ai")
    print("="*60)
    
    # Reset backend
    reset_backend()
    
    # Créer mock settings
    sm = MockSettingsManager()
    
    # Demander la clé API
    ws_key = input("Entrez votre clé API WaveSpeed.ai (ou ENTER pour skip): ").strip()
    if not ws_key:
        print("⚠️ Aucune clé WaveSpeed - test skippé")
        return
    
    sm.settings['api_keys_vault']['WaveSpeed'] = ws_key
    
    # Créer backend
    backend = get_image_backend(sm)
    
    if not backend:
        print("❌ Impossible de créer le backend")
        return
    
    # Tester fetch_live_img2img_models
    print("\n🔄 Appel à fetch_live_img2img_models('WaveSpeed')...")
    models, error = await backend.fetch_live_img2img_models('WaveSpeed')
    
    if error:
        print(f"❌ Erreur: {error}")
        return
    
    if not models:
        print("⚠️ Aucun modèle img2img récupéré")
        return
    
    print(f"\n✅ {len(models)} modèles img2img WaveSpeed récupérés:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")


async def test_comparison_t2i_vs_i2i():
    """Compare les modèles text2img vs img2img pour un provider"""
    print("\n" + "="*60)
    print("TEST: Comparaison T2I vs I2I (Kie)")
    print("="*60)
    
    reset_backend()
    sm = MockSettingsManager()
    
    kie_key = input("Entrez votre clé API Kie.ai pour comparaison (ou ENTER pour skip): ").strip()
    if not kie_key:
        print("⚠️ Test skippé")
        return
    
    sm.settings['api_keys_vault']['Kie'] = kie_key
    backend = get_image_backend(sm)
    
    if not backend:
        print("❌ Backend non disponible")
        return
    
    # Récupérer les deux listes
    print("\n🔄 Récupération modèles TEXT-TO-IMAGE...")
    t2i_models, t2i_error = await backend.fetch_live_models('Kie')
    
    print("🔄 Récupération modèles IMAGE-TO-IMAGE...")
    i2i_models, i2i_error = await backend.fetch_live_img2img_models('Kie')
    
    if t2i_error or i2i_error:
        print(f"❌ Erreurs: T2I={t2i_error}, I2I={i2i_error}")
        return
    
    print(f"\n📊 RÉSULTATS:")
    print(f"  • Text-to-Image: {len(t2i_models) if t2i_models else 0} modèles")
    print(f"  • Image-to-Image: {len(i2i_models) if i2i_models else 0} modèles")
    
    if t2i_models and i2i_models:
        # Modèles communs
        common = set(t2i_models) & set(i2i_models)
        t2i_only = set(t2i_models) - set(i2i_models)
        i2i_only = set(i2i_models) - set(t2i_models)
        
        print(f"\n  • Modèles communs: {len(common)}")
        if common:
            for m in sorted(common):
                print(f"    - {m}")
        
        print(f"\n  • Uniquement T2I: {len(t2i_only)}")
        if t2i_only:
            for m in sorted(t2i_only):
                print(f"    - {m}")
        
        print(f"\n  • Uniquement I2I: {len(i2i_only)}")
        if i2i_only:
            for m in sorted(i2i_only):
                print(f"    - {m}")


async def main():
    """Exécute tous les tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  TEST: Récupération Dynamique Modèles IMG2IMG Providers  ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Test 1: Kie.ai img2img
    await test_kie_img2img_models()
    
    # Test 2: WaveSpeed.ai img2img
    await test_wavespeed_img2img_models()
    
    # Test 3: Comparaison T2I vs I2I
    await test_comparison_t2i_vs_i2i()
    
    print("\n" + "="*60)
    print("✅ Tests terminés")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
