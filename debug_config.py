#!/usr/bin/env python3
"""
Test de debug de la configuration
"""
import sys
import os

# Ajouter le dossier OGMA au path
sys.path.insert(0, os.path.dirname(__file__))

def test_config():
    print("=== DEBUG CONFIGURATION ===")
    
    try:
        # Test direct de la configuration
        from extensions.web_navigator.config import WebNavigatorConfig
        print("✅ Import config réussi")
        
        # Créer la config sans settings manager
        config = WebNavigatorConfig()
        print("✅ Config créée sans settings manager")
        
        # Tester les méthodes
        print(f"Extension activée: {config.is_enabled()}")
        print(f"Recherche web activée: {config.is_web_search_enabled()}")
        api_key = config.get_serper_api_key()
        print(f"Clé API: {'Définie' if api_key else 'Non définie'}")
        if api_key:
            print(f"Clé API (10 premiers chars): {api_key[:10]}...")
        
        # Test avec settings.json direct
        print("\n--- TEST LECTURE DIRECTE settings.json ---")
        import json
        
        try:
            with open('data/settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            web_nav_section = settings.get('web_navigator', {})
            print(f"Section web_navigator trouvée: {bool(web_nav_section)}")
            print(f"Keys dans web_navigator: {list(web_nav_section.keys())}")
            
            serper_key = web_nav_section.get('serper_api_key')
            print(f"serper_api_key: {'Définie' if serper_key else 'Non définie'}")
            if serper_key:
                print(f"serper_api_key (10 premiers): {serper_key[:10]}...")
                
        except Exception as e:
            print(f"Erreur lecture settings.json: {e}")
        
        print("\n=== DEBUG TERMINÉ ===")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config()