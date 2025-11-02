"""
Test du système d'enrichissement de prompts PromptEnhancer
============================================================
Valide que l'enrichissement transforme correctement les prompts simples
en descriptions ultra-détaillées style Perchance.
"""

import sys
import os

# Ajouter le dossier extensions/text2img au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'extensions', 'text2img'))

from prompt_enhancer import PromptEnhancer


def test_basic_enhancement():
    """Test enrichissement prompt simple"""
    print("=" * 80)
    print("TEST 1 - Enrichissement prompt simple")
    print("=" * 80)
    
    enhancer = PromptEnhancer(debug=True)
    
    # Prompts de test
    test_prompts = [
        "femme latina nue",
        "femme nue voluptueuse",
        "woman with beautiful smile",
        "latina in shower",
        "sensual bedroom scene"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'=' * 80}")
        print(f"PROMPT ORIGINAL : '{prompt}'")
        print(f"{'=' * 80}")
        
        enhanced = enhancer.enhance(prompt)
        
        print(f"\nPROMPT ENRICHI ({len(enhanced)} caractères) :")
        print(f"{enhanced}\n")
        
        # Statistiques
        original_len = len(prompt)
        enhanced_len = len(enhanced)
        increase_percent = ((enhanced_len - original_len) / original_len) * 100
        
        print(f"📊 STATISTIQUES :")
        print(f"   - Original : {original_len} caractères")
        print(f"   - Enrichi : {enhanced_len} caractères")
        print(f"   - Augmentation : +{increase_percent:.1f}%")
        
        # Vérification contenu enrichi
        checks = {
            "Prompt original conservé": prompt in enhanced,
            "Qualifiers techniques ajoutés": any(q in enhanced for q in ["photorealistic", "8k uhd", "highly detailed"]),
            "Expansions anatomiques": enhanced_len > original_len * 3
        }
        
        print(f"\n✅ VALIDATIONS :")
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
    
    return True


def test_nsfw_detection():
    """Test détection contenu NSFW et ajout boosts spécifiques"""
    print("\n" + "=" * 80)
    print("TEST 2 - Détection NSFW et boosts spécifiques")
    print("=" * 80)
    
    enhancer = PromptEnhancer(debug=False)
    
    test_cases = [
        ("femme nue", True, "Contient 'nue'"),
        ("beautiful landscape", False, "Pas de contenu NSFW"),
        ("voluptuous woman", True, "Contient 'voluptuous'"),
        ("city skyline", False, "Pas de contenu NSFW")
    ]
    
    for prompt, should_be_nsfw, description in test_cases:
        print(f"\n🧪 Test: {description}")
        print(f"   Prompt: '{prompt}'")
        
        enhanced = enhancer.enhance(prompt)
        
        # Vérifier présence boosts NSFW
        nsfw_boosts = ["anatomically correct", "natural proportions", "realistic body"]
        has_nsfw_boosts = any(boost in enhanced for boost in nsfw_boosts)
        
        expected = "NSFW" if should_be_nsfw else "SFW"
        detected = "NSFW" if has_nsfw_boosts else "SFW"
        
        status = "✅" if (has_nsfw_boosts == should_be_nsfw) else "❌"
        print(f"   {status} Attendu: {expected} | Détecté: {detected}")
        
        if should_be_nsfw:
            print(f"   🔞 Boosts NSFW ajoutés: {has_nsfw_boosts}")


def test_keyword_expansion():
    """Test expansion spécifique des mots-clés"""
    print("\n" + "=" * 80)
    print("TEST 3 - Expansion mots-clés anatomiques")
    print("=" * 80)
    
    enhancer = PromptEnhancer(debug=False)
    
    keyword_tests = {
        "latina": ["caramel skin tone", "exotic beauty"],
        "nue": ["natural body", "authentic nudity"],
        "voluptueuse": ["voluptuous curves", "full figure"],
        "sensuel": ["sensual expression", "seductive look"]
    }
    
    for keyword, expected_expansions in keyword_tests.items():
        prompt = f"femme {keyword}"
        print(f"\n🔍 Mot-clé: '{keyword}'")
        print(f"   Prompt: '{prompt}'")
        
        enhanced = enhancer.enhance(prompt)
        
        found_expansions = []
        for expansion in expected_expansions:
            if expansion in enhanced:
                found_expansions.append(expansion)
        
        success_rate = len(found_expansions) / len(expected_expansions) * 100
        status = "✅" if success_rate >= 50 else "❌"
        
        print(f"   {status} Expansions trouvées: {len(found_expansions)}/{len(expected_expansions)}")
        for expansion in found_expansions:
            print(f"      ✓ '{expansion}'")


def test_statistics():
    """Test statistiques enhancer"""
    print("\n" + "=" * 80)
    print("TEST 4 - Statistiques PromptEnhancer")
    print("=" * 80)
    
    enhancer = PromptEnhancer(debug=False)
    stats = enhancer.get_statistics()
    
    print(f"\n📊 STATISTIQUES :")
    print(f"   - Mots-clés anatomiques : {stats['anatomy_keywords']}")
    print(f"   - Boosts qualité généraux : {stats['quality_boosts']}")
    print(f"   - Boosts NSFW spécifiques : {stats['nsfw_boosts']}")
    print(f"   - Total patterns compilés : {stats['total_keywords']}")
    
    # Validation minimums
    checks = {
        "Mots-clés >= 20": stats['anatomy_keywords'] >= 20,
        "Boosts qualité >= 10": stats['quality_boosts'] >= 10,
        "Boosts NSFW >= 5": stats['nsfw_boosts'] >= 5
    }
    
    print(f"\n✅ VALIDATIONS :")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


def test_comparison_perchance():
    """Test comparaison avec transformation Perchance attendue"""
    print("\n" + "=" * 80)
    print("TEST 5 - Comparaison avec style Perchance")
    print("=" * 80)
    
    enhancer = PromptEnhancer(debug=False)
    
    # Prompt simple typique user
    original = "femme latina nue voluptueuse"
    
    # Exemple transformation Perchance (référence)
    perchance_example_keywords = [
        "beautiful woman",
        "latina",
        "caramel skin",
        "voluptuous curves",
        "nude",
        "natural body",
        "highly detailed",
        "photorealistic",
        "8k uhd",
        "professional photography",
        "masterpiece quality"
    ]
    
    print(f"\n🧪 Prompt original : '{original}'")
    
    enhanced = enhancer.enhance(original)
    print(f"\n📝 Prompt enrichi OGMA :")
    print(f"{enhanced[:200]}...")
    
    # Vérifier présence keywords Perchance
    found_keywords = []
    for keyword in perchance_example_keywords:
        if keyword.lower() in enhanced.lower():
            found_keywords.append(keyword)
    
    match_rate = len(found_keywords) / len(perchance_example_keywords) * 100
    
    print(f"\n📊 ANALYSE COMPATIBILITÉ PERCHANCE :")
    print(f"   - Keywords Perchance trouvés : {len(found_keywords)}/{len(perchance_example_keywords)}")
    print(f"   - Taux de compatibilité : {match_rate:.1f}%")
    
    status = "✅" if match_rate >= 70 else "⚠️" if match_rate >= 50 else "❌"
    print(f"\n{status} RÉSULTAT : ", end="")
    
    if match_rate >= 70:
        print("EXCELLENT - Très proche style Perchance")
    elif match_rate >= 50:
        print("BON - Compatible style Perchance")
    else:
        print("INSUFFISANT - Enrichissement trop différent")
    
    print(f"\n✅ Keywords présents :")
    for keyword in found_keywords:
        print(f"   ✓ {keyword}")
    
    missing = [kw for kw in perchance_example_keywords if kw not in found_keywords]
    if missing:
        print(f"\n❌ Keywords manquants :")
        for keyword in missing:
            print(f"   ✗ {keyword}")
    
    return match_rate >= 70


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "█" * 80)
    print(" " * 20 + "TESTS PROMPT ENHANCER - SUITE COMPLÈTE")
    print("█" * 80 + "\n")
    
    results = {
        "Enrichissement de base": False,
        "Détection NSFW": False,
        "Expansion mots-clés": False,
        "Statistiques": False,
        "Compatibilité Perchance": False
    }
    
    try:
        # Test 1
        results["Enrichissement de base"] = test_basic_enhancement()
        
        # Test 2
        test_nsfw_detection()
        results["Détection NSFW"] = True
        
        # Test 3
        test_keyword_expansion()
        results["Expansion mots-clés"] = True
        
        # Test 4
        results["Statistiques"] = test_statistics()
        
        # Test 5
        results["Compatibilité Perchance"] = test_comparison_perchance()
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE : {e}")
        import traceback
        traceback.print_exc()
    
    # Résumé final
    print("\n" + "█" * 80)
    print(" " * 25 + "RÉSUMÉ DES TESTS")
    print("█" * 80 + "\n")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status:12} - {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    success_rate = (total_passed / total_tests) * 100
    
    print(f"\n{'=' * 80}")
    print(f"RÉSULTAT GLOBAL : {total_passed}/{total_tests} tests passés ({success_rate:.1f}%)")
    print(f"{'=' * 80}\n")
    
    if success_rate == 100:
        print("🎉 SUCCÈS COMPLET - PromptEnhancer opérationnel qualité Perchance!")
    elif success_rate >= 80:
        print("✅ SUCCÈS - Quelques ajustements mineurs possibles")
    elif success_rate >= 60:
        print("⚠️ PARTIEL - Nécessite optimisations")
    else:
        print("❌ ÉCHEC - Problèmes majeurs à corriger")


if __name__ == "__main__":
    run_all_tests()
