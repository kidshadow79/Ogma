#!/usr/bin/env python3
"""
Test avec le vrai settings_manager d'OGMA
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

async def test_with_real_settings_manager():
    """Test avec le vrai settings_manager d'OGMA"""
    print("🔍 Test avec settings_manager réel...")
    
    try:
        # Import du settings manager d'OGMA
        from core_logic import SettingsManager
        
        # Créer le settings manager réel
        settings_path = Path("data/settings.json")
        settings_manager = SettingsManager(settings_path)
        print(f"   Settings manager créé: {type(settings_manager)}")
        
        # Vérifier si la clé Serper est dans les settings
        web_nav_section = settings_manager.settings.get("web_navigator", {})
        serper_key = web_nav_section.get("serper_api_key", "")
        print(f"   Clé Serper dans settings: {'***' + serper_key[-4:] if serper_key else 'VIDE'}")
        
        # Test avec l'extension
        from extensions.web_navigator import WebNavigatorConfig, SerperClient, WebNavigatorCommands
        
        # Création avec le vrai settings_manager
        config = WebNavigatorConfig(settings_manager)
        print(f"   Config créée avec settings_manager")
        print(f"   Extension activée: {config.is_enabled()}")
        print(f"   Clé API valide: {config.has_valid_api_key()}")
        print(f"   Recherche web activée: {config.is_web_search_enabled()}")
        print(f"   Clé API récupérée: {'***' + config.get_serper_api_key()[-4:] if config.get_serper_api_key() else 'VIDE'}")
        
        # Créer les composants
        serper_client = SerperClient(config)
        commands = WebNavigatorCommands(config, serper_client)
        
        # Test de requête
        print(f"\n--- Test requête '/web premier ministre francais' ---")
        response, file_path = await commands.process_internet_request("/web premier ministre francais")
        print(f"   Réponse: {response[:100]}..." if len(response) > 100 else f"   Réponse: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("TEST AVEC SETTINGS_MANAGER RÉEL")
    print("=" * 70)
    
    success = asyncio.run(test_with_real_settings_manager())
    
    print("\n" + "=" * 70)
    if success:
        print("✅ TEST TERMINÉ - Vérifiez les résultats ci-dessus")
    else:
        print("❌ TEST ÉCHOUÉ")
    print("=" * 70)