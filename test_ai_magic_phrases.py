#!/usr/bin/env python3
"""
Test de la détection des phrases magiques Web Navigator dans les réponses IA
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions.web_navigator import WebNavigatorExtension

def test_ai_magic_phrase_detection():
    """Test détection phrases magiques IA"""
    
    print("🧪 TEST: Détection phrases magiques Web Navigator dans réponses IA")
    print("=" * 70)
    
    # Initialiser l'extension
    try:
        web_ext = WebNavigatorExtension()
        print("✅ Extension Web Navigator initialisée")
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return
    
    # Exemples de réponses IA avec phrases magiques
    test_responses = [
        # Phrase magique exacte du log
        'Ah, Yohan, parfait timing pour plonger dans le futur ! Je vais lancer la phrase magique direct : "il faut que je recherche sur internet : les tendances et artistes reggaeton latina pour 2025".',
        
        # Autres variantes 
        "Je vais faire une recherche : il faut que je cherche sur internet des informations récentes.",
        "Laisse-moi vérifier ça en ligne : je dois rechercher sur internet les dernières actualités.",
        "Pour répondre à ta question, il faut que je recherche sur le net les données les plus récentes.",
        "Je vais googler ça pour toi : cherche sur internet Python 3.12 nouveautés",
        
        # Phrases non-magiques (contrôle)
        "Je pense que tu peux chercher sur internet si tu veux plus d'infos.",
        "Il serait bien de faire une recherche pour vérifier.",
    ]
    
    print(f"\n🔍 Test de détection sur {len(test_responses)} réponses IA:")
    print("-" * 50)
    
    detected = 0
    for i, response in enumerate(test_responses, 1):
        is_detected = web_ext.commands.is_internet_request(response)
        status = "✅ DÉTECTÉE" if is_detected else "⚪ Non détectée"
        
        print(f"\n{i}. {status}")
        print(f"   Texte: \"{response[:80]}...\"")
        
        if is_detected:
            detected += 1
    
    print(f"\n" + "=" * 70)
    print(f"🎯 RÉSULTAT: {detected}/{len(test_responses)} phrases magiques détectées")
    
    expected_detected = 5  # Les 5 premières devraient être détectées
    if detected >= expected_detected:
        print(f"✅ Test RÉUSSI - Détection fonctionne pour les phrases IA")
    else:
        print(f"❌ Test ÉCHOUÉ - Détection insuffisante (attendu >= {expected_detected})")

if __name__ == "__main__":
    test_ai_magic_phrase_detection()