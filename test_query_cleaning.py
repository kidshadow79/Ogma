#!/usr/bin/env python3
"""
Test de la correction du nettoyage des requêtes
"""

import asyncio
import sys
sys.path.append('.')

from extensions.web_navigator.config import WebNavigatorConfig
from extensions.web_navigator.serper_client import SerperClient
from extensions.web_navigator.commands import WebNavigatorCommands

async def test_query_cleaning():
    """Test du nettoyage des requêtes"""
    
    print("🧹 Test du nettoyage des requêtes")
    print("="*60)
    
    # Configuration
    config = WebNavigatorConfig()
    client = SerperClient(config)
    commands = WebNavigatorCommands(config, client)
    
    # Test des requêtes problématiques
    test_queries = [
        '"avancées ia relations émotionnelles authentiques 2024-2025".',
        'sur intelligence artificielle tendances, svp',
        '"recherche exacte avec guillemets"',
        'actualités technologie merci',
        'intelligence artificielle relations émotionnelles authentiques 2024-2025 s\'il vous plaît',
        'des nouvelles tendances en IA pour 2024!?'
    ]
    
    print("🔧 TEST DU NETTOYAGE:")
    for query in test_queries:
        cleaned = commands.clean_search_query(query)
        print(f"   Original: '{query}'")
        print(f"   Nettoyée: '{cleaned}'")
        print()
    
    # Test avec la requête problématique originale
    problematic_query = '"avancées ia relations émotionnelles authentiques 2024-2025".'
    cleaned_query = commands.clean_search_query(problematic_query)
    
    print("-" * 60)
    print("🔍 TEST RECHERCHE AVEC NETTOYAGE:")
    print(f"Requête originale: {problematic_query}")
    print(f"Requête nettoyée: {cleaned_query}")
    print()
    
    # Test recherche avec requête nettoyée
    try:
        enriched_content, error = await client.search_with_intelligent_scraping(
            cleaned_query, top_pages=3
        )
        
        if error:
            print(f"❌ Erreur: {error}")
        elif enriched_content:
            print(f"✅ Contenu enrichi généré: {len(enriched_content)} caractères")
            print(f"📊 Aperçu: {enriched_content[:200]}...")
        else:
            print("⚠️ Pas de contenu enrichi généré")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_query_cleaning())