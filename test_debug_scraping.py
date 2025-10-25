#!/usr/bin/env python3
"""
Test de debug pour analyser le problème de scraping
"""

import asyncio
import sys
sys.path.append('.')

from extensions.web_navigator.config import WebNavigatorConfig
from extensions.web_navigator.serper_client import SerperClient

async def debug_search():
    """Test de debug pour analyser le problème"""
    
    print("🐛 Debug du problème de scraping")
    print("="*60)
    
    # Configuration
    config = WebNavigatorConfig()
    
    # Vérifier que la clé API est disponible
    if not config.has_valid_api_key():
        print("❌ Clé API Serper manquante dans la configuration OGMA")
        return
    
    # Client Serper
    client = SerperClient(config)
    
    # Test avec plusieurs requêtes
    test_queries = [
        "intelligence artificielle tendances 2024",
        "python programming tutorial",
        "actualités technologie"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Test avec: '{query}'")
        print("-" * 40)
        
        try:
            # Test recherche normale d'abord
            print("1️⃣ Test recherche Serper normale...")
            serper_response, error = client.search_web(query)
            
            if error:
                print(f"❌ Erreur Serper: {error}")
                continue
            
            if not serper_response:
                print("❌ Pas de réponse Serper")
                continue
            
            print(f"✅ Réponse Serper reçue")
            print(f"   Clés disponibles: {list(serper_response.keys())}")
            
            if 'organic' in serper_response:
                organic = serper_response['organic']
                print(f"   Résultats organiques: {len(organic)}")
                
                for i, result in enumerate(organic[:3], 1):
                    title = result.get('title', 'Sans titre')
                    link = result.get('link', 'Pas de lien')
                    print(f"   {i}. {title[:50]}...")
                    print(f"      URL: {link}")
            else:
                print("   ❌ Pas de résultats organiques")
            
            # Test recherche intelligente
            print("\n2️⃣ Test recherche intelligente...")
            enriched_content, error = await client.search_with_intelligent_scraping(
                query, top_pages=2
            )
            
            if error:
                print(f"❌ Erreur recherche intelligente: {error}")
            elif enriched_content:
                print(f"✅ Contenu enrichi généré: {len(enriched_content)} caractères")
            else:
                print("⚠️ Pas de contenu enrichi généré")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(debug_search())