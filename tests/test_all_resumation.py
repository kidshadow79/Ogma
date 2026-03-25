"""
Script de test complet pour validation migration résumation v2.2+

Exécute tous les tests liés au système de résumation :
- test_summarizer_persistence.py (nouveau système)
- test_contextual_recall_strict.py (extension)
- test_conversation_manager_strict.py (core)
"""

import subprocess
import sys

def run_tests():
    print("=" * 70)
    print("🧪 TESTS MIGRATION RÉSUMATION v2.2+")
    print("=" * 70)
    print()
    
    tests = [
        ("test_summarizer_persistence.py", "Nouveau système résumation"),
        ("test_contextual_recall_strict.py", "Extension Contextual Recall"),
        ("test_conversation_manager_strict.py", "Core Conversation Manager")
    ]
    
    results = {}
    
    for test_file, description in tests:
        print(f"\n📋 {description}")
        print(f"   Fichier: tests/{test_file if 'summarizer' in test_file else f'unit/{test_file}'}")
        print("-" * 70)
        
        test_path = f"tests/{test_file}" if "summarizer" in test_file else f"tests/unit/{test_file}"
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        results[description] = result.returncode == 0
        
        if result.returncode == 0:
            print(f"✅ TOUS LES TESTS PASSENT")
        else:
            print(f"❌ ERREURS DÉTECTÉES")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ GLOBAL")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ OK" if passed else "❌ ÉCHEC"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅✅✅ MIGRATION RÉSUMATION v2.2+ COMPLÈTE ET VALIDÉE ✅✅✅")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ - VÉRIFIER LES DÉTAILS CI-DESSUS")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_tests())
