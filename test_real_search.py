#!/usr/bin/env python3
"""
Test d'une vraie recherche avec l'API Serper
"""
import asyncio
import sys
import os

# Ajouter le dossier OGMA au path
sys.path.insert(0, os.path.dirname(__file__))

async def test_real_search():
    print("=== TEST RECHERCHE RÉELLE SERPER ===")
    
    try:
        # Import de l'extension
        from extensions.web_navigator import WebNavigatorExtension
        print("✅ Extension importée")
        
        # Initialisation
        web_nav = WebNavigatorExtension()
        print("✅ Extension initialisée")
        
        # Vérifier la configuration
        api_key = web_nav.config.get_serper_api_key()
        if not api_key:
            print("❌ Clé API Serper non configurée")
            return
        print(f"✅ Clé API configurée: {api_key[:10]}...")
        
        # Test de différentes requêtes
        test_queries = [
            "cherche sur internet actualités intelligence artificielle",
            "/web nouvelles technologie 2024",
            "recherche web framework python fastapi"
        ]
        
        for query in test_queries:
            print(f"\n--- TEST: {query} ---")
            
            if web_nav.commands.is_internet_request(query):
                try:
                    print("🔍 Requête détectée comme recherche internet")
                    result, file_path = await web_nav.commands.process_internet_request(query)
                    
                    if result:
                        print(f"✅ Recherche réussie!")
                        print(f"📄 Longueur réponse: {len(result)} caractères")
                        print(f"📂 Fichier sauvé: {file_path}")
                        print(f"🔍 Aperçu:\n{result[:300]}...")
                    else:
                        print("❌ Aucun résultat retourné")
                        
                except Exception as e:
                    print(f"❌ Erreur lors de la recherche: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Requête non détectée comme recherche internet")
        
        print("\n=== TEST TERMINÉ ===")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_search())