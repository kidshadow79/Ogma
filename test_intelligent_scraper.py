#!/usr/bin/env python3
"""
Test du scraper intelligent pour validation
"""

import asyncio
import sys
sys.path.append('.')

from extensions.web_navigator.web_scraper import WebContentScraper

async def test_scraper():
    """Test du scraper avec une page simple"""
    
    print("🧪 Test du scraper intelligent")
    print("="*50)
    
    async with WebContentScraper() as scraper:
        # Test avec Wikipedia
        print("\n📄 Test avec Wikipedia...")
        result = await scraper.scrape_page('https://fr.wikipedia.org/wiki/Intelligence_artificielle')
        
        print(f"✅ URL: {result.url}")
        print(f"📝 Titre: {result.title[:100]}...")
        print(f"📄 Contenu: {len(result.content)} caractères, {result.word_count} mots")
        print(f"⏱️ Temps: {result.scrape_time:.1f}s")
        print(f"🎯 Succès: {result.success}")
        
        if result.error:
            print(f"❌ Erreur: {result.error}")
        else:
            print("✅ Pas d'erreur")
            
        if result.success and len(result.content) > 100:
            print(f"\n📖 Aperçu du contenu:")
            print(result.content[:300] + "...")
        
        print("\n" + "="*50)
        
        # Test multiple
        print("\n🔄 Test scraping multiple...")
        urls = [
            'https://fr.wikipedia.org/wiki/Intelligence_artificielle',
            'https://www.lemonde.fr/'
        ]
        
        results = await scraper.scrape_multiple(urls, max_concurrent=2)
        
        for i, result in enumerate(results, 1):
            print(f"\n📄 Résultat {i}: {'✅' if result.success else '❌'}")
            print(f"   URL: {result.url}")
            print(f"   Titre: {result.title[:50]}...")
            print(f"   Contenu: {len(result.content)} chars")
            if result.error:
                print(f"   Erreur: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_scraper())