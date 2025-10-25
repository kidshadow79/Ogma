#!/usr/bin/env python3
"""
Debug du nettoyage de requête pour comprendre le problème des guillemets
"""

import sys
sys.path.append('.')

from extensions.web_navigator.config import WebNavigatorConfig
from extensions.web_navigator.serper_client import SerperClient
from extensions.web_navigator.commands import WebNavigatorCommands

def debug_query_cleaning():
    """Debug du nettoyage des requêtes"""
    
    print("🐛 Debug du nettoyage des requêtes")
    print("="*60)
    
    # Configuration
    config = WebNavigatorConfig()
    client = SerperClient(config)
    commands = WebNavigatorCommands(config, client)
    
    # Test de la requête problématique
    test_query = '"avancées ia relations émotionnelles authentiques 2024-2025".'
    
    print(f"📝 Requête test: {repr(test_query)}")
    print(f"📏 Longueur: {len(test_query)}")
    print(f"🔍 Premier char: {repr(test_query[0])}")
    print(f"🔍 Dernier char: {repr(test_query[-1])}")
    print(f"🔍 Avant-dernier char: {repr(test_query[-2])}")
    print()
    
    # Test du nettoyage étape par étape
    cleaned = test_query.strip()
    print(f"1️⃣ Après strip(): {repr(cleaned)}")
    
    # Test condition guillemets
    starts_with_quote = cleaned.startswith('"')
    ends_with_quote = cleaned.endswith('"')
    length_check = len(cleaned) > 2
    
    print(f"2️⃣ Starts with quote: {starts_with_quote}")
    print(f"2️⃣ Ends with quote: {ends_with_quote}")
    print(f"2️⃣ Length > 2: {length_check}")
    print(f"2️⃣ All conditions: {starts_with_quote and ends_with_quote and length_check}")
    
    # Test manuel du nettoyage
    if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) > 2:
        manual_cleaned = cleaned[1:-1]
        print(f"3️⃣ Nettoyage manuel réussi: {repr(manual_cleaned)}")
    else:
        print(f"3️⃣ Conditions non remplies pour nettoyage")
    
    # Test avec fonction complète
    result = commands.clean_search_query(test_query)
    print(f"4️⃣ Résultat fonction complète: {repr(result)}")

if __name__ == "__main__":
    debug_query_cleaning()