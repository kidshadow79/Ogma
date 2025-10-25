#!/usr/bin/env python3
"""
Analyse de la requête problématique de l'IA
"""

import asyncio
import sys
sys.path.append('.')

from extensions.web_navigator.config import WebNavigatorConfig
from extensions.web_navigator.serper_client import SerperClient

async def analyze_problematic_query():
    """Analyse la requête qui a posé problème"""
    
    print("🔍 Analyse de la requête problématique de l'IA")
    print("="*70)
    
    # Configuration
    config = WebNavigatorConfig()
    client = SerperClient(config)
    
    # La requête exacte qui a posé problème (d'après les logs)
    problematic_query = '"avancées ia relations émotionnelles authentiques 2024-2025".'
    
    print(f"📝 Requête problématique: {problematic_query}")
    print(f"📏 Longueur: {len(problematic_query)} caractères")
    print()
    
    # Analyser la requête
    print("🔍 ANALYSE DE LA REQUÊTE:")
    print(f"• Commence par des guillemets: {'✅' if problematic_query.startswith('\"') else '❌'}")
    print(f"• Se termine par un point: {'✅' if problematic_query.endswith('.') else '❌'}")
    print(f"• Contient des guillemets: {'✅' if '\"' in problematic_query else '❌'}")
    print()
    
    # Nettoyer la requête pour voir la différence
    cleaned_query = problematic_query.strip('"').rstrip('.')
    print(f"📝 Requête nettoyée: {cleaned_query}")
    print()
    
    # Test avec la requête originale
    print("1️⃣ TEST AVEC LA REQUÊTE ORIGINALE (problématique):")
    try:
        serper_response, error = client.search_web(problematic_query)
        
        if error:
            print(f"❌ Erreur: {error}")
        elif serper_response and 'organic' in serper_response:
            organic = serper_response['organic']
            print(f"✅ {len(organic)} résultats trouvés")
            
            for i, result in enumerate(organic[:3], 1):
                title = result.get('title', 'Sans titre')
                link = result.get('link', 'Pas de lien')
                print(f"   {i}. {title[:60]}...")
                print(f"      URL: {link}")
                
                # Vérifier si l'URL serait valide pour le scraping
                if link and link.startswith(('http://', 'https://')):
                    blocked_domains = ['youtube.com', 'facebook.com', 'twitter.com', 'linkedin.com']
                    is_blocked = any(domain in link.lower() for domain in blocked_domains)
                    print(f"      Scrapable: {'❌ (domaine bloqué)' if is_blocked else '✅'}")
                else:
                    print(f"      Scrapable: ❌ (URL invalide)")
        else:
            print("❌ Pas de résultats organiques")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-"*70)
    
    # Test avec la requête nettoyée
    print("2️⃣ TEST AVEC LA REQUÊTE NETTOYÉE:")
    try:
        serper_response, error = client.search_web(cleaned_query)
        
        if error:
            print(f"❌ Erreur: {error}")
        elif serper_response and 'organic' in serper_response:
            organic = serper_response['organic']
            print(f"✅ {len(organic)} résultats trouvés")
            
            for i, result in enumerate(organic[:3], 1):
                title = result.get('title', 'Sans titre')
                link = result.get('link', 'Pas de lien')
                print(f"   {i}. {title[:60]}...")
                print(f"      URL: {link}")
                
                # Vérifier si l'URL serait valide pour le scraping
                if link and link.startswith(('http://', 'https://')):
                    blocked_domains = ['youtube.com', 'facebook.com', 'twitter.com', 'linkedin.com']
                    is_blocked = any(domain in link.lower() for domain in blocked_domains)
                    print(f"      Scrapable: {'❌ (domaine bloqué)' if is_blocked else '✅'}")
                else:
                    print(f"      Scrapable: ❌ (URL invalide)")
        else:
            print("❌ Pas de résultats organiques")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-"*70)
    
    # Test avec une requête plus simple
    simple_query = "intelligence artificielle relations émotionnelles"
    print(f"3️⃣ TEST AVEC UNE REQUÊTE SIMPLIFIÉE: '{simple_query}'")
    try:
        serper_response, error = client.search_web(simple_query)
        
        if error:
            print(f"❌ Erreur: {error}")
        elif serper_response and 'organic' in serper_response:
            organic = serper_response['organic']
            print(f"✅ {len(organic)} résultats trouvés")
            
            scrapable_count = 0
            for i, result in enumerate(organic[:5], 1):
                title = result.get('title', 'Sans titre')
                link = result.get('link', 'Pas de lien')
                print(f"   {i}. {title[:60]}...")
                print(f"      URL: {link}")
                
                # Vérifier si l'URL serait valide pour le scraping
                if link and link.startswith(('http://', 'https://')):
                    blocked_domains = ['youtube.com', 'facebook.com', 'twitter.com', 'linkedin.com']
                    is_blocked = any(domain in link.lower() for domain in blocked_domains)
                    if not is_blocked:
                        scrapable_count += 1
                        print(f"      Scrapable: ✅")
                    else:
                        print(f"      Scrapable: ❌ (domaine bloqué)")
                else:
                    print(f"      Scrapable: ❌ (URL invalide)")
            
            print(f"\n📊 BILAN: {scrapable_count}/5 URLs scrapables")
        else:
            print("❌ Pas de résultats organiques")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_problematic_query())