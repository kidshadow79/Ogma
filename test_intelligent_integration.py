#!/usr/bin/env python3
"""
Test de l'intégration complète scraping intelligent + Serper
"""

import asyncio
import sys
sys.path.append('.')

from extensions.web_navigator.config import WebNavigatorConfig
from extensions.web_navigator.serper_client import SerperClient

async def test_intelligent_search():
    """Test de la recherche intelligente avec scraping"""
    
    print("🧠 Test de la recherche intelligente")
    print("="*60)
    
    # Configuration
    config = WebNavigatorConfig()
    
    # Vérifier que la clé API est disponible
    if not config.has_valid_api_key():
        print("❌ Clé API Serper manquante dans la configuration OGMA")
        print("   Vérifiez les settings dans l'interface OGMA")
        return
    
    # Client Serper
    client = SerperClient(config)
    
    # Test recherche intelligente
    query = "intelligence artificielle nouvelles tendances 2024"
    print(f"\n🔍 Recherche: '{query}'")
    print("⏳ Recherche Serper + scraping Top 5 pages...")
    
    try:
        enriched_content, error = await client.search_with_intelligent_scraping(
            query, top_pages=3  # Limité à 3 pour le test
        )
        
        if error:
            print(f"❌ Erreur: {error}")
        elif enriched_content:
            print(f"✅ Contenu enrichi généré:")
            print(f"📊 Taille: {len(enriched_content)} caractères")
            print(f"\n📖 Aperçu du contenu enrichi:")
            print("-" * 60)
            print(enriched_content[:1000] + "...")
            print("-" * 60)
        else:
            print("⚠️ Aucun contenu généré")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_intelligent_search())