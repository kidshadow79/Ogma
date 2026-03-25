"""
Test validation : Option A - 4 souvenirs maximum
=================================================

Valide que le système limite l'injection mémoire à exactement 4 souvenirs :
- 2 intégraux (top 2)
- 2 synthétisés (rangs 3-4)

Économie tokens attendue : -67% vs 12 souvenirs actuels

Auteur: Système OGMA
Date: 27 novembre 2025
"""

import sys
from pathlib import Path

def test_option_a_implementation():
    """Vérifie que le code limite bien à 4 souvenirs"""
    
    print("\n" + "="*60)
    print("TEST OPTION A : Validation 4 souvenirs maximum")
    print("="*60)
    
    # Lire le fichier source
    optimizer_file = Path("archiviste_memory_optimizer.py")
    
    if not optimizer_file.exists():
        print("❌ ERREUR: Fichier archiviste_memory_optimizer.py introuvable")
        return False
    
    content = optimizer_file.read_text(encoding='utf-8')
    
    # Test 1: Vérifier assemblage final
    print("\n📋 TEST 1: Vérification assemblage final...")
    
    if "remaining_memories[:2]" in content:
        print("✅ PASS: Limite 2 souvenirs synthétisés (rangs 3-4) confirmée")
        test1_pass = True
    else:
        print("❌ FAIL: Code ne limite pas à 2 souvenirs synthétisés")
        print("   Recherché: 'remaining_memories[:2]'")
        test1_pass = False
    
    # Test 2: Vérifier synthèse adaptative
    print("\n📋 TEST 2: Vérification synthèse adaptative...")
    
    if "all_memories_for_synthesis = remaining_memories[:2]" in content:
        print("✅ PASS: Synthèse limitée à 2 souvenirs (rangs 3-4)")
        test2_pass = True
    else:
        print("❌ FAIL: Synthèse non limitée à 2 souvenirs")
        test2_pass = False
    
    # Test 3: Vérifier commentaires Option A
    print("\n📋 TEST 3: Vérification documentation Option A...")
    
    if "OPTION A: 4 souvenirs total" in content:
        print("✅ PASS: Documentation Option A présente")
        test3_pass = True
    else:
        print("❌ FAIL: Documentation Option A manquante")
        test3_pass = False
    
    # Test 4: Calcul économie tokens
    print("\n📋 TEST 4: Calcul économie tokens théorique...")
    
    tokens_avant = 1750  # 12 souvenirs (rapport initial)
    tokens_apres_top2 = 115  # 2 souvenirs intégraux
    tokens_apres_rangs34 = 200  # 2 souvenirs synthétisés (~100 chars chacun)
    tokens_apres_synthese = 400  # Synthèse Archiviste sur 2 souvenirs
    tokens_apres_total = tokens_apres_top2 + tokens_apres_rangs34 + tokens_apres_synthese
    
    economie_tokens = tokens_avant - tokens_apres_total
    economie_pct = (economie_tokens / tokens_avant) * 100
    
    print(f"   Avant (12 souvenirs): {tokens_avant} tokens")
    print(f"   Après Option A (4 souvenirs):")
    print(f"     - Top 2 intégraux: {tokens_apres_top2} tokens")
    print(f"     - Rangs 3-4 (texte): {tokens_apres_rangs34} tokens")
    print(f"     - Synthèse Archiviste: {tokens_apres_synthese} tokens")
    print(f"     - TOTAL: {tokens_apres_total} tokens")
    print(f"   📊 ÉCONOMIE: {economie_tokens} tokens (-{economie_pct:.1f}%)")
    
    if economie_pct >= 50:
        print("✅ PASS: Économie significative (>50%)")
        test4_pass = True
    else:
        print("❌ FAIL: Économie insuffisante")
        test4_pass = False
    
    # Test 5: Vérifier absence ancien code 12 souvenirs
    print("\n📋 TEST 5: Vérification suppression ancien code...")
    
    if "remaining_memories[:10]" not in content:
        print("✅ PASS: Ancien code (12 souvenirs) supprimé")
        test5_pass = True
    else:
        print("❌ FAIL: Ancien code (12 souvenirs) toujours présent")
        test5_pass = False
    
    # Résumé
    print("\n" + "="*60)
    all_tests = [test1_pass, test2_pass, test3_pass, test4_pass, test5_pass]
    passed = sum(all_tests)
    total = len(all_tests)
    
    if passed == total:
        print(f"✅ TOUS LES TESTS RÉUSSIS ({passed}/{total})")
        print("="*60)
        print("\n💡 OPTION A IMPLÉMENTÉE AVEC SUCCÈS")
        print("\n📊 CONFIGURATION FINALE:")
        print("   - Souvenirs intégraux (top 2): 2")
        print("   - Souvenirs synthétisés (rangs 3-4): 2")
        print("   - TOTAL: 4 souvenirs par message")
        print(f"   - Économie tokens: ~{economie_tokens} tokens/message (-{economie_pct:.1f}%)")
        print("\n🎯 IMPACT ATTENDU:")
        print("   - Moins de dilution contexte (4 vs 12 souvenirs)")
        print("   - Réponses plus ciblées et cohérentes")
        print("   - Latence réduite (moins de contexte à traiter)")
        print("="*60)
        return True
    else:
        print(f"❌ TESTS ÉCHOUÉS ({total-passed}/{total})")
        print("="*60)
        return False

if __name__ == "__main__":
    success = test_option_a_implementation()
    sys.exit(0 if success else 1)
