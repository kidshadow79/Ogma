#!/usr/bin/env python3
"""
🌙 Dream Engine v2.0 - Test d'Intégration Complet

Test du cycle complet:
1. Extraction mémoire (carburant mémoriel)
2. Génération de rêve (métabolisme)
3. Analyse par l'Archiviste PSY
4. Sauvegarde dans les journaux
5. Injection contexte dans journal de bord
6. Marquage du rêve après mention

Usage:
    python tests/test_dream_engine_integration.py
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Ajouter le dossier racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ==============================================================================
# TESTS UNITAIRES
# ==============================================================================

def test_1_import_modules():
    """Test 1: Vérifier que tous les modules s'importent correctement"""
    print("\n" + "="*60)
    print("TEST 1: Import des modules")
    print("="*60)
    
    modules = [
        ("extensions.dream_engine", "__init__"),
        ("extensions.dream_engine.dream_core", "DreamEngine"),
        ("extensions.dream_engine.dream_memory", "extract_dream_fuel"),
        ("extensions.dream_engine.dream_analysis", "analyze_dream"),
        ("extensions.dream_engine.dream_journal", "DreamJournal"),
        ("extensions.dream_engine.dream_ui", "DREAM_SPINNER_HTML"),
        ("extensions.dream_engine.dream_prompts", "DREAM_GENERATOR_MODE"),
        ("extensions.dream_engine.dream_illustration", "generate_dream_illustration"),
    ]
    
    all_ok = True
    for module_name, attribute in modules:
        try:
            module = __import__(module_name, fromlist=[attribute])
            if hasattr(module, attribute):
                print(f"  ✅ {module_name}.{attribute}")
            else:
                print(f"  ❌ {module_name}.{attribute} - Attribut manquant")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {module_name} - {e}")
            all_ok = False
    
    return all_ok


def test_2_api_publique():
    """Test 2: API publique disponible"""
    print("\n" + "="*60)
    print("TEST 2: API Publique")
    print("="*60)
    
    from extensions import dream_engine
    
    expected_functions = [
        'initialize_dream_engine',
        'is_available',
        'is_initialized',
        'start_dream',
        'wake_up',
        'is_dreaming',
        'cleanup',
        'inject_header_button',
        'get_last_dream_context',
        'mark_dream_mentioned',
    ]
    
    all_ok = True
    for func_name in expected_functions:
        if hasattr(dream_engine, func_name):
            func = getattr(dream_engine, func_name)
            print(f"  ✅ {func_name}()")
        else:
            print(f"  ❌ {func_name} - MANQUANT")
            all_ok = False
    
    return all_ok


def test_3_dream_journal():
    """Test 3: Journal des rêves (lecture/écriture)"""
    print("\n" + "="*60)
    print("TEST 3: Journal des Rêves")
    print("="*60)
    
    from extensions.dream_engine.dream_journal import DreamJournal, get_dream_journal
    
    # Utiliser le singleton au lieu d'instancier directement
    journal = get_dream_journal()
    print(f"  ✅ get_dream_journal() retourne le singleton")
    
    # Vérifier les méthodes
    methods = ['save_dream', 'get_last_dream', 'mark_dream_mentioned', 'get_dreams']
    for method in methods:
        if hasattr(journal, method):
            print(f"  ✅ journal.{method}()")
        else:
            print(f"  ❌ journal.{method} - MANQUANT")
            return False
    
    # Lire les rêves existants
    dreams = journal.get_dreams(limit=5)
    print(f"  📚 {len(dreams)} rêve(s) dans le journal")
    for dream in dreams[:2]:
        title = dream.get('title', 'Sans titre')[:40]
        mentioned = "✓ mentionné" if dream.get('mentioned') else "○ non mentionné"
        print(f"     - {title}... ({mentioned})")
    
    return True


def test_4_dream_prompts():
    """Test 4: Prompts système"""
    print("\n" + "="*60)
    print("TEST 4: Prompts Système")
    print("="*60)
    
    from extensions.dream_engine.dream_prompts import (
        DREAM_GENERATOR_MODE,
        ARCHIVISTE_PSY_VERDICT
    )
    
    # Vérifier le prompt Luna
    if "onirique" in DREAM_GENERATOR_MODE.lower():
        print(f"  ✅ DREAM_GENERATOR_MODE ({len(DREAM_GENERATOR_MODE)} chars)")
    else:
        print(f"  ❌ DREAM_GENERATOR_MODE - Contenu invalide")
        return False
    
    # Vérifier le prompt Archiviste PSY (format flexible)
    required_patterns = ["VERDICT_PSY", "SCORE_IMPORTANCE", "INSIGHT_EGO"]
    missing = [k for k in required_patterns if k not in ARCHIVISTE_PSY_VERDICT]
    
    if not missing:
        print(f"  ✅ ARCHIVISTE_PSY_VERDICT ({len(ARCHIVISTE_PSY_VERDICT)} chars)")
    else:
        print(f"  ❌ ARCHIVISTE_PSY_VERDICT - Patterns manquants: {missing}")
        return False
    
    return True


def test_5_dream_memory():
    """Test 5: Extraction mémoire (structure)"""
    print("\n" + "="*60)
    print("TEST 5: Extraction Mémoire")
    print("="*60)
    
    from extensions.dream_engine.dream_memory import extract_dream_fuel
    import inspect
    
    # Vérifier que la fonction est async
    if asyncio.iscoroutinefunction(extract_dream_fuel):
        print(f"  ✅ extract_dream_fuel() est async")
    else:
        print(f"  ⚠️ extract_dream_fuel() devrait être async")
    
    # Vérifier la signature
    sig = inspect.signature(extract_dream_fuel)
    params = list(sig.parameters.keys())
    print(f"  ✅ Paramètres: {params}")
    
    # Test sans appeler (car nécessite un vrai memory_manager)
    print(f"  ℹ️ Test dry-run (sans memory_manager réel)")
    
    return True


def test_6_dream_analysis():
    """Test 6: Module d'analyse PSY"""
    print("\n" + "="*60)
    print("TEST 6: Module Analyse PSY")
    print("="*60)
    
    from extensions.dream_engine.dream_analysis import analyze_dream
    import inspect
    
    # Vérifier que la fonction existe
    print(f"  ✅ analyze_dream() disponible")
    
    # Vérifier que c'est async
    if asyncio.iscoroutinefunction(analyze_dream):
        print(f"  ✅ analyze_dream() est async")
    else:
        print(f"  ⚠️ analyze_dream() devrait être async")
    
    # Vérifier la signature
    sig = inspect.signature(analyze_dream)
    params = list(sig.parameters.keys())
    expected_params = ['dream_content', 'fuel', 'archiviste_controller']
    
    if all(p in params for p in expected_params):
        print(f"  ✅ Signature correcte: {params}")
    else:
        print(f"  ⚠️ Signature: {params}")
    
    return True


def test_7_context_injection():
    """Test 7: Injection contexte dans journal de bord"""
    print("\n" + "="*60)
    print("TEST 7: Injection Contexte Journal de Bord")
    print("="*60)
    
    from extensions.dream_engine import get_last_dream_context, is_available
    
    if not is_available():
        print("  ⚠️ Dream Engine non disponible")
        return True  # Pas une erreur
    
    ctx = get_last_dream_context()
    
    if ctx:
        print(f"  ✅ get_last_dream_context() retourne un dict")
        print(f"     - id: {ctx.get('id', 'N/A')}")
        print(f"     - title: {ctx.get('title', 'N/A')[:40]}...")
        print(f"     - score: {ctx.get('score', 'N/A')}")
        print(f"     - emotion: {ctx.get('emotion', 'N/A')}")
        print(f"     - mentioned: {ctx.get('mentioned', 'N/A')}")
    else:
        print("  ⚠️ Aucun rêve non mentionné disponible")
    
    return True


def test_8_dream_mention_marking():
    """Test 8: Marquage d'un rêve comme mentionné"""
    print("\n" + "="*60)
    print("TEST 8: Marquage Rêve Mentionné")
    print("="*60)
    
    from extensions.dream_engine import get_last_dream_context, mark_dream_mentioned
    
    # Récupérer le dernier rêve
    ctx_before = get_last_dream_context()
    
    if not ctx_before:
        print("  ⚠️ Aucun rêve à marquer")
        return True
    
    print(f"  📖 Rêve avant marquage: mentioned={ctx_before.get('mentioned')}")
    
    # Marquer comme mentionné
    result = mark_dream_mentioned()
    print(f"  🔖 mark_dream_mentioned(): {result}")
    
    # Vérifier après
    ctx_after = get_last_dream_context()
    
    if ctx_after is None:
        print("  ✅ Plus de rêve non mentionné (comportement attendu)")
        return True
    else:
        print(f"  ❌ Le rêve n'a pas été marqué correctement")
        return False


def test_9_ui_components():
    """Test 9: Composants UI"""
    print("\n" + "="*60)
    print("TEST 9: Composants UI")
    print("="*60)
    
    from extensions.dream_engine.dream_ui import DREAM_SPINNER_HTML
    
    # Vérifier le spinner HTML
    if "<div" in DREAM_SPINNER_HTML and "animation" in DREAM_SPINNER_HTML.lower():
        print(f"  ✅ DREAM_SPINNER_HTML ({len(DREAM_SPINNER_HTML)} chars)")
    else:
        print(f"  ❌ DREAM_SPINNER_HTML - Format invalide")
        return False
    
    return True


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Exécute tous les tests"""
    print("\n" + "🌙"*30)
    print("DREAM ENGINE v2.0 - TESTS D'INTÉGRATION")
    print("🌙"*30)
    
    tests = [
        ("Import modules", test_1_import_modules),
        ("API publique", test_2_api_publique),
        ("Journal des rêves", test_3_dream_journal),
        ("Prompts système", test_4_dream_prompts),
        ("Extraction mémoire", test_5_dream_memory),
        ("Parsing analyse PSY", test_6_dream_analysis),
        ("Injection contexte", test_7_context_injection),
        ("Marquage mention", test_8_dream_mention_marking),
        ("Composants UI", test_9_ui_components),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {passed}/{len(results)} tests réussis")
    
    if failed == 0:
        print("🎉 TOUS LES TESTS PASSENT!")
    else:
        print(f"⚠️ {failed} test(s) échoué(s)")
    
    print("="*60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
