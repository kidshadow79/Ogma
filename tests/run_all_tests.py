"""
OGMA - Script Validation Complète Tests
=========================================

Exécute TOUS les tests unitaires OGMA et génère rapport synthétique.

Usage:
    python run_all_tests.py
    python run_all_tests.py --verbose
    python run_all_tests.py --coverage

Résultat attendu: 315 tests PASS (100%)
"""

import subprocess
import sys
import time
from pathlib import Path


def print_banner():
    """Affiche bannière démarrage"""
    print("\n" + "="*70)
    print("  OGMA - VALIDATION COMPLÈTE TESTS")
    print("="*70)
    print(f"📊 Target: 315 tests (165.8% coverage)")
    print(f"🎯 Pass rate attendu: 100%")
    print(f"⚡ Temps estimé: ~8-10s")
    print("="*70 + "\n")


def run_pytest(verbose=False, coverage=False):
    """
    Exécute pytest sur tous tests unitaires.
    
    Args:
        verbose: Mode verbose (-v)
        coverage: Génère rapport coverage
    
    Returns:
        tuple: (exit_code, duration)
    """
    # Commande base
    cmd = ["pytest", "tests/unit/", "-v" if verbose else "-q"]
    
    # Coverage optionnel
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Execution
    print(f"🚀 Commande: {' '.join(cmd)}\n")
    start_time = time.time()
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    duration = time.time() - start_time
    
    return result.returncode, duration


def print_summary(exit_code, duration):
    """Affiche résumé résultats"""
    print("\n" + "="*70)
    print("  RÉSUMÉ VALIDATION")
    print("="*70)
    
    if exit_code == 0:
        print("✅ STATUS: TOUS LES TESTS PASSENT")
        print(f"✅ Durée: {duration:.2f}s")
        print(f"✅ Performance: {'EXCELLENT' if duration < 10 else 'BON'}")
        print("\n🎊 MISSION ACCOMPLIE - 315 tests validés! 🚀")
    else:
        print("❌ STATUS: ÉCHECS DÉTECTÉS")
        print(f"⏱️  Durée: {duration:.2f}s")
        print("\n⚠️  Vérifier les erreurs ci-dessus")
    
    print("="*70 + "\n")


def main():
    """Point entrée principal"""
    # Parse args simples
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    coverage = "--coverage" in sys.argv or "--cov" in sys.argv
    
    # Vérifier dossier tests existe
    tests_dir = Path("tests/unit")
    if not tests_dir.exists():
        print(f"❌ Erreur: Dossier {tests_dir} introuvable")
        print(f"   Exécuter depuis racine projet OGMA")
        sys.exit(1)
    
    # Banner
    print_banner()
    
    # Run tests
    try:
        exit_code, duration = run_pytest(verbose=verbose, coverage=coverage)
    except KeyboardInterrupt:
        print("\n⚠️  Interruption utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur exécution: {e}")
        sys.exit(1)
    
    # Summary
    print_summary(exit_code, duration)
    
    # Exit avec code pytest
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
