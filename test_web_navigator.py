#!/usr/bin/env python3
"""
Test simple de l'extension Web Navigator avec Serper

Vérifie si l'extension se charge correctement et peut détecter les phrases magiques
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

def test_web_navigator_extension():
    """Test de l'extension Web Navigator"""
    print("🧪 Test de l'extension Web Navigator...")
    
    try:
        # Test 1: Import des modules
        print("\n1. Test import des modules...")
        from extensions.web_navigator import WebNavigatorConfig, SerperClient, WebNavigatorCommands
        print("✅ Import des modules réussi")
        
        # Test 2: Configuration
        print("\n2. Test configuration...")
        config = WebNavigatorConfig()
        print(f"✅ Configuration créée - Extension activée: {config.is_enabled()}")
        print(f"   - Clé API configurée: {'Oui' if config.has_valid_api_key() else 'Non'}")
        print(f"   - Recherche web: {config.is_web_search_enabled()}")
        print(f"   - Recherche images: {config.is_image_search_enabled()}")
        
        # Test 3: Client Serper
        print("\n3. Test client Serper...")
        serper_client = SerperClient(config)
        print("✅ Client Serper créé")
        
        # Test 4: Commandes
        print("\n4. Test système de commandes...")
        commands = WebNavigatorCommands(config, serper_client)
        print("✅ Système de commandes créé")
        
        # Test 5: Détection phrases magiques
        print("\n5. Test détection phrases magiques...")
        test_phrases = [
            "cherche sur internet intelligence artificielle",
            "/web python programming",
            "actualités sur technologie",
            "/image chat mignon",
            "bonjour comment allez-vous?",  # phrase normale
        ]
        
        for phrase in test_phrases:
            is_web = commands.is_internet_request(phrase)
            status = "🌐 WEB" if is_web else "💬 NORMAL"
            print(f"   {status}: {phrase}")
        
        print("\n✅ Tests de l'extension Web Navigator terminés avec succès!")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_components():
    """Test des composants UI"""
    print("\n🎨 Test des composants UI...")
    
    try:
        from extensions.web_navigator.ui_components import WebNavigatorUI
        print("✅ Import UI components réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur UI: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST EXTENSION WEB NAVIGATOR")
    print("=" * 60)
    
    success1 = test_web_navigator_extension()
    success2 = test_ui_components()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("L'extension Web Navigator est prête à utiliser.")
        print("\nPour utiliser l'extension:")
        print("1. Configurez votre clé API Serper dans les paramètres")
        print("2. Utilisez les phrases magiques comme 'cherche sur internet IA'")
        print("3. Ou les commandes directes comme '/web intelligence artificielle'")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Vérifiez les erreurs ci-dessus")
    print("=" * 60)