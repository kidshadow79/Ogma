#!/usr/bin/env python3
"""
Test de la logique de sélection intelligente pour l'extension biographie
========================================================================

Valide que le système sélectionne correctement les utilisateurs selon :
- IA : Seulement sur mention explicite
- Utilisateur : Sur mots-clés personnels OU mention explicite
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent pour les imports
sys.path.append(str(Path(__file__).parent))

def test_biography_intelligent_selection():
    """Test la logique de sélection intelligente"""
    print("🧪 TEST SÉLECTION INTELLIGENTE BIOGRAPHIE")
    print("=" * 50)
    
    try:
        # Import des modules nécessaires
        from extensions.biographie_profil.magic_phrases import BiographyMagicPhrases
        from identity_manager import get_identity_manager
        
        # Créer une instance avec manager minimal
        magic_phrases = BiographyMagicPhrases(None)  # Manager minimal pour test
        
        # Récupérer les identités du profil actuel
        identity_manager = get_identity_manager()
        current_identity = identity_manager.get_current_identity()
        print(f"📋 Profil actuel:")
        print(f"   👤 Utilisateur: {current_identity['user_name']}")
        print(f"   🤖 IA: {current_identity['ai_name']}")
        print()
        
        # Simuler les utilisateurs disponibles
        available_users = ["Luna", "Yohan"]  # Basé sur les biographies existantes
        print(f"📁 Utilisateurs simulés: {available_users}")
        print()
        
        # Scénarios de test
        test_cases = [
            {
                "message": "salut ma Luna comment tu vas?",
                "expected": "Luna",
                "reason": "Mention explicite de l'IA + mot-clé 'ma'"
            },
            {
                "message": "je vais bien",
                "expected": "Yohan", 
                "reason": "Mot-clé personnel 'je' → utilisateur"
            },
            {
                "message": "comment va Yohan aujourd'hui?",
                "expected": "Yohan",
                "reason": "Mention explicite de l'utilisateur"
            },
            {
                "message": "bonjour comment ça va?",
                "expected": None,
                "reason": "Aucun déclencheur → pas d'injection"
            },
            {
                "message": "Luna est une IA",
                "expected": "Luna",
                "reason": "Mention explicite de l'IA sans mots-clés"
            },
            {
                "message": "notre conversation",
                "expected": "Yohan",
                "reason": "Mot-clé personnel 'notre' → utilisateur"
            }
        ]
        
        # Exécuter les tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔍 Test {i}: '{test_case['message']}'")
            print(f"   Attendu: {test_case['expected']} ({test_case['reason']})")
            
            try:
                # Simuler la détection de noms (logique simplifiée)
                import re
                detected_names = []
                for user in available_users:
                    if re.search(rf"\b{re.escape(user)}\b", test_case['message'], re.IGNORECASE):
                        detected_names.append(user)
                
                # Mots-clés personnels
                personal_keywords = [
                    r"\bmoi\b", r"\bje\b", r"\bj'\b",
                    r"\bmon\b", r"\bma\b", r"\bmes\b",
                    r"\bnotre\b", r"\bnos\b"
                ]
                
                has_personal_keywords = any(
                    __import__('re').search(pattern, test_case['message'], __import__('re').IGNORECASE) 
                    for pattern in personal_keywords
                )
                
                # Utiliser la logique de sélection intelligente
                result = magic_phrases._select_target_user_intelligent(
                    test_case['message'], available_users, detected_names, has_personal_keywords
                )
                
                # Vérifier le résultat
                if result == test_case['expected']:
                    print(f"   ✅ RÉUSSI: {result}")
                else:
                    print(f"   ❌ ÉCHEC: attendu {test_case['expected']}, obtenu {result}")
                
                print(f"   📊 Détails:")
                print(f"      - Noms détectés: {detected_names}")
                print(f"      - Mots-clés personnels: {has_personal_keywords}")
                print()
                
            except Exception as e:
                print(f"   ❌ ERREUR: {e}")
                print()
        
        print("🎯 Test terminé!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_biography_intelligent_selection()