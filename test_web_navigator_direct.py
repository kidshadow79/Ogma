#!/usr/bin/env python3
"""
Test simple de l'extension Web Navigator pour voir si elle est appelée
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

async def test_web_navigator_direct():
    """Test direct de l'extension Web Navigator"""
    print("🔍 Test direct extension Web Navigator...")
    
    try:
        # Import
        from extensions.web_navigator import WebNavigatorConfig, SerperClient, WebNavigatorCommands
        
        # Création des composants
        config = WebNavigatorConfig()
        serper_client = SerperClient(config)
        commands = WebNavigatorCommands(config, serper_client)
        
        # Tests
        test_phrases = ["/web premier ministre francais", "cherche sur internet actualités"]
        
        for phrase in test_phrases:
            print(f"\n--- Test phrase: '{phrase}' ---")
            
            # Test détection
            is_web = commands.is_internet_request(phrase)
            print(f"   Détecté comme web: {is_web}")
            
            if is_web:
                # Test traitement
                try:
                    response, file_path = await commands.process_internet_request(phrase)
                    print(f"   Réponse: {response[:100]}..." if len(response) > 100 else f"   Réponse: {response}")
                    print(f"   Fichier: {file_path}")
                except Exception as e:
                    print(f"   Erreur traitement: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DIRECT WEB NAVIGATOR")
    print("=" * 60)
    
    success = asyncio.run(test_web_navigator_direct())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST RÉUSSI")
        print("Si vous voyez 'clé API manquante', c'est normal.")
        print("Configurez votre clé Serper dans les paramètres OGMA.")
    else:
        print("❌ TEST ÉCHOUÉ")
    print("=" * 60)