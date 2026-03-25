"""
Test du système de récupération dynamique des modèles depuis les APIs
"""

import asyncio
import sys
from extensions.text2img.image_backend import get_image_backend, reset_backend


class MockSettingsManager:
    """Simulateur de settings manager pour les tests"""
    def __init__(self):
        self.settings = {
            'api_keys_vault': {
                'GROK': '',  # Remplacer par vraie clé pour tester
                'OpenAI': '',
                'Google': '',
                'Kie': '',  # Remplacer par vraie clé Kie pour tester
                'WaveSpeed': ''  # Remplacer par vraie clé WaveSpeed pour tester
            }
        }


async def test_kie_models():
    """Test récupération modèles Kie.ai"""
    print("\n" + "="*60)
    print("TEST: Récupération modèles Kie.ai")
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
    
    # Tester fetch_live_models
    print("\n🔄 Appel à fetch_live_models('Kie')...")
    models, error = await backend.fetch_live_models('Kie')
    
    if error:
        print(f"❌ Erreur: {error}")
        return
    
    if not models:
        print("⚠️ Aucun modèle récupéré")
        return
    
    print(f"\n✅ {len(models)} modèles Kie récupérés:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")


async def test_wavespeed_models():
    """Test récupération modèles WaveSpeed.ai"""
    print("\n" + "="*60)
    print("TEST: Récupération modèles WaveSpeed.ai")
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
    
    # Tester fetch_live_models
    print("\n🔄 Appel à fetch_live_models('WaveSpeed')...")
    models, error = await backend.fetch_live_models('WaveSpeed')
    
    if error:
        print(f"❌ Erreur: {error}")
        return
    
    if not models:
        print("⚠️ Aucun modèle récupéré")
        return
    
    print(f"\n✅ {len(models)} modèles WaveSpeed récupérés:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")


async def test_unsupported_provider():
    """Test d'un provider sans fetch_live_models implémenté"""
    print("\n" + "="*60)
    print("TEST: Provider sans fetch_live_models (GROK)")
    print("="*60)
    
    # Reset backend
    reset_backend()
    
    sm = MockSettingsManager()
    sm.settings['api_keys_vault']['GROK'] = 'xai-fake-key-for-test'
    
    backend = get_image_backend(sm)
    
    print("\n🔄 Appel à fetch_live_models('GROK')...")
    models, error = await backend.fetch_live_models('GROK')
    
    if error:
        print(f"✅ Erreur attendue: {error}")
    else:
        print(f"⚠️ Inattendu - models: {models}")


async def main():
    """Exécute tous les tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  TEST: Récupération Dynamique Modèles Image Providers    ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Test 1: Kie.ai
    await test_kie_models()
    
    # Test 2: WaveSpeed.ai
    await test_wavespeed_models()
    
    # Test 3: Provider non supporté
    await test_unsupported_provider()
    
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
