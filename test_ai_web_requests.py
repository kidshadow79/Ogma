#!/usr/bin/env python3
"""
Test des patterns de recherche web pour l'IA elle-même
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions.web_navigator import WebNavigatorExtension

def test_ai_web_patterns():
    """Test des patterns pour l'IA"""
    
    print("🧪 Test des patterns de recherche web pour l'IA")
    print("=" * 50)
    
    # Initialiser l'extension
    ext = WebNavigatorExtension()
    
    # Messages de test pour l'IA
    test_messages = [
        # Patterns basiques pour l'IA
        "il faut que je recherche sur le net",
        "il faut que je recherche sur internet",
        "il faut que je cherche sur internet",
        "je dois rechercher sur internet",
        "je dois chercher sur le web",
        "je vais faire une recherche web",
        "laissez-moi rechercher sur internet",
        "permettez-moi de faire une recherche",
        
        # Patterns avec requête spécifique
        "il faut que je recherche sur le net les dernières nouvelles",
        "il faut que je recherche sur internet des informations sur Python",
        "je dois rechercher sur internet l'actualité politique",
        "je vais faire une recherche web sur les technologies IA",
        "il faut que je vérifie sur internet les horaires du train",
        "je dois vérifier en ligne la météo de demain",
        
        # Messages qui ne devraient PAS déclencher
        "il faut que je réfléchisse",
        "je peux vous aider",
        "voici ma réponse",
    ]
    
    print("\n📝 Test de détection des patterns:")
    print("-" * 30)
    
    for msg in test_messages:
        is_detected = ext.commands.is_internet_request(msg)
        intent, query = ext.commands.extract_search_intent_and_query(msg)
        
        status = "✅ DETECTÉ" if is_detected else "❌ NON DETECTÉ"
        print(f"{status:12} | '{msg}'")
        
        if is_detected and intent:
            print(f"{'':12} | → Type: {intent}, Requête: '{query or 'N/A'}'")
        
        print()

if __name__ == "__main__":
    test_ai_web_patterns()