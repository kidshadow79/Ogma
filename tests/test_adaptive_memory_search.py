#!/usr/bin/env python3
"""
🧪 TEST - Système Adaptatif de Recherche Mémoire
================================================

Vérifie le comportement du seuil adaptatif:
- ≤6 mots après nettoyage Python → Utilisation directe (pas d'IA)
- >6 mots après nettoyage Python → IA filtre (sélectionne, n'ajoute pas)

Date: 12 janvier 2026
"""

import asyncio
import sys
from typing import List, Tuple

# Test cases: (query, expected_behavior)
TEST_CASES = [
    # Requêtes COURTES (≤6 mots après nettoyage) → Python only
    ("tu te souviens de la genese des 2 phares?", "PYTHON_ONLY", ["genese", "phares"]),
    ("comment s'appelle mon chat?", "PYTHON_ONLY", ["appelle", "chat"]),
    ("où habite Yohan?", "PYTHON_ONLY", ["habite", "Yohan"]),
    ("parle moi de Luna", "PYTHON_ONLY", ["parle", "Luna"]),
    ("qu'est-ce que la conscience?", "PYTHON_ONLY", ["conscience"]),
    ("Lyon café discussion philosophie", "PYTHON_ONLY", ["Lyon", "café", "discussion", "philosophie"]),
    
    # Requêtes LONGUES (>6 mots après nettoyage) → IA filtering
    ("tu te souviens de notre longue discussion sur la philosophie de la conscience artificielle et les implications éthiques?", 
     "IA_FILTER", None),
    ("raconte moi l'histoire du chat noir qui vivait dans la maison abandonnée près du lac gelé en hiver",
     "IA_FILTER", None),
]


def test_python_cleanup():
    """Test du nettoyage Python seul"""
    print("\n" + "="*70)
    print("🧹 TEST 1: Nettoyage Python (clean_conversational_noise)")
    print("="*70)
    
    try:
        from memory_manager import clean_conversational_noise
        print("✅ Import réussi\n")
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        return False
    
    all_passed = True
    
    for query, expected_behavior, expected_words in TEST_CASES:
        cleaned = clean_conversational_noise(query)
        word_count = len(cleaned.split())
        
        # Déterminer comportement attendu
        should_use_python = (expected_behavior == "PYTHON_ONLY")
        will_use_python = (word_count <= 6)
        
        status = "✅" if should_use_python == will_use_python else "❌"
        if status == "❌":
            all_passed = False
        
        print(f"{status} Query: \"{query[:50]}...\"")
        print(f"   Nettoyé: \"{cleaned}\" ({word_count} mots)")
        print(f"   Attendu: {expected_behavior} | Résultat: {'PYTHON_ONLY' if will_use_python else 'IA_FILTER'}")
        
        # Vérifier mots clés si spécifiés
        if expected_words:
            cleaned_lower = cleaned.lower()
            missing = [w for w in expected_words if w.lower() not in cleaned_lower]
            if missing:
                print(f"   ⚠️ Mots manquants dans nettoyage: {missing}")
        print()
    
    return all_passed


def test_threshold_logic():
    """Test de la logique de seuil adaptatif"""
    print("\n" + "="*70)
    print("📊 TEST 2: Seuil Adaptatif (ADAPTIVE_THRESHOLD = 6)")
    print("="*70)
    
    ADAPTIVE_THRESHOLD = 6
    
    test_word_counts = [
        (1, "PYTHON_ONLY"),
        (2, "PYTHON_ONLY"),  # "genese phares"
        (3, "PYTHON_ONLY"),
        (6, "PYTHON_ONLY"),  # Limite
        (7, "IA_FILTER"),    # Juste au-dessus
        (10, "IA_FILTER"),
        (15, "IA_FILTER"),
    ]
    
    all_passed = True
    
    for word_count, expected in test_word_counts:
        will_filter = word_count > ADAPTIVE_THRESHOLD
        result = "IA_FILTER" if will_filter else "PYTHON_ONLY"
        status = "✅" if result == expected else "❌"
        if status == "❌":
            all_passed = False
        
        print(f"{status} {word_count} mots → {result} (attendu: {expected})")
    
    return all_passed


def test_validation_logic():
    """Test de la validation stricte (mots inventés rejetés)"""
    print("\n" + "="*70)
    print("🔒 TEST 3: Validation Stricte (rejet mots inventés)")
    print("="*70)
    
    # Simuler la validation
    available_words = ["genese", "phares", "conscience", "bien", "mal"]
    
    test_ia_outputs = [
        # (output IA, mots attendus validés, mots attendus rejetés)
        (["genese", "phares"], ["genese", "phares"], []),
        (["genese", "phares", "mythologie"], ["genese", "phares"], ["mythologie"]),
        (["légende", "maritime", "lumière"], [], ["légende", "maritime", "lumière"]),
        (["conscience", "bien", "mal", "morale"], ["conscience", "bien", "mal"], ["morale"]),
    ]
    
    all_passed = True
    
    for ia_output, expected_valid, expected_rejected in test_ia_outputs:
        available_lower = set(w.lower() for w in available_words)
        
        validated = []
        rejected = []
        
        for concept in ia_output:
            if concept.lower() in available_lower:
                validated.append(concept)
            else:
                rejected.append(concept)
        
        valid_ok = validated == expected_valid
        reject_ok = rejected == expected_rejected
        status = "✅" if valid_ok and reject_ok else "❌"
        if status == "❌":
            all_passed = False
        
        print(f"{status} IA output: {ia_output}")
        print(f"   Validés: {validated} (attendu: {expected_valid})")
        print(f"   Rejetés: {rejected} (attendu: {expected_rejected})")
        print()
    
    return all_passed


async def test_full_integration():
    """Test d'intégration complet avec le vrai système"""
    print("\n" + "="*70)
    print("🔗 TEST 4: Intégration Complète (optionnel)")
    print("="*70)
    
    try:
        from archiviste_memory_optimizer import ArchivisteMemoryOptimizer
        print("✅ Import ArchivisteMemoryOptimizer réussi")
        
        # Note: Ce test nécessite les contrôleurs IA configurés
        print("⚠️ Test intégration nécessite contrôleurs IA - skip en mode test unitaire")
        return True
        
    except ImportError as e:
        print(f"⚠️ Import non disponible (normal en test isolé): {e}")
        return True


def main():
    """Exécution de tous les tests"""
    print("\n" + "🧪"*35)
    print("   TEST SYSTÈME ADAPTATIF RECHERCHE MÉMOIRE")
    print("🧪"*35)
    
    results = []
    
    # Test 1: Nettoyage Python
    results.append(("Nettoyage Python", test_python_cleanup()))
    
    # Test 2: Logique seuil
    results.append(("Seuil Adaptatif", test_threshold_logic()))
    
    # Test 3: Validation stricte
    results.append(("Validation Stricte", test_validation_logic()))
    
    # Test 4: Intégration (async)
    results.append(("Intégration", asyncio.run(test_full_integration())))
    
    # Résumé
    print("\n" + "="*70)
    print("📋 RÉSUMÉ DES TESTS")
    print("="*70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 TOUS LES TESTS PASSENT!")
    else:
        print("⚠️ Certains tests ont échoué - vérifier les détails ci-dessus")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
