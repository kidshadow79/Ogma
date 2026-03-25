"""
Script de Validation Installation Testing OGMA
==============================================

Vérifie que tous les composants de testing sont correctement installés.

Usage:
    python validate_testing_setup.py
"""

import sys
import importlib
from pathlib import Path


def check_python_version():
    """Vérifie version Python >= 3.10."""
    version = sys.version_info
    print(f"🐍 Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("   ❌ Python 3.10+ requis")
        return False
    
    print("   ✅ Version OK")
    return True


def check_package(package_name, friendly_name=None):
    """Vérifie qu'un package est installé."""
    if friendly_name is None:
        friendly_name = package_name
    
    try:
        importlib.import_module(package_name)
        print(f"   ✅ {friendly_name}")
        return True
    except ImportError:
        print(f"   ❌ {friendly_name} manquant")
        return False


def check_testing_packages():
    """Vérifie packages de testing."""
    print("\n📦 Packages Testing:")
    
    packages = {
        'pytest': 'pytest',
        'pytest_asyncio': 'pytest-asyncio',
        'pytest_cov': 'pytest-cov',
        'pytest_mock': 'pytest-mock',
        'pytest_timeout': 'pytest-timeout',
        'responses': 'responses',
        'faker': 'faker',
    }
    
    results = []
    for module, name in packages.items():
        results.append(check_package(module, name))
    
    return all(results)


def check_ogma_core():
    """Vérifie modules OGMA core."""
    print("\n🧠 OGMA Core Modules:")
    
    modules = [
        'memory_manager',
        'core_logic',
        'utils',
    ]
    
    results = []
    for module in modules:
        results.append(check_package(module))
    
    return all(results)


def check_test_structure():
    """Vérifie structure dossiers tests."""
    print("\n📁 Structure Tests:")
    
    base_dir = Path(__file__).parent
    
    required_paths = [
        base_dir / 'unit',
        base_dir / 'integration',
        base_dir / 'e2e',
        base_dir / 'fixtures',
        base_dir / 'conftest.py',
        base_dir / 'pytest.ini' if (base_dir.parent / 'pytest.ini').exists() else base_dir / '../pytest.ini',
        base_dir / 'requirements-testing.txt',
    ]
    
    results = []
    for path in required_paths:
        path_resolved = path.resolve() if not path.is_absolute() else path
        exists = path_resolved.exists()
        
        status = "✅" if exists else "❌"
        print(f"   {status} {path.name}")
        results.append(exists)
    
    return all(results)


def check_test_files():
    """Vérifie fichiers de test critiques."""
    print("\n🧪 Tests Critiques:")
    
    base_dir = Path(__file__).parent
    
    critical_tests = [
        base_dir / 'unit' / 'test_memory_manager.py',
        base_dir / 'unit' / 'test_core_logic.py',
        base_dir / 'unit' / 'test_cognitive_mirror.py',
    ]
    
    results = []
    for test_file in critical_tests:
        exists = test_file.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {test_file.name}")
        results.append(exists)
    
    return all(results)


def run_quick_test():
    """Exécute un test rapide pytest."""
    print("\n⚡ Test Rapide pytest:")
    
    try:
        import subprocess
        result = subprocess.run(
            ['pytest', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✅ {version}")
            return True
        else:
            print(f"   ❌ Échec exécution pytest")
            return False
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def print_summary(results):
    """Affiche résumé final."""
    print("\n" + "="*60)
    print("📊 RÉSUMÉ VALIDATION")
    print("="*60)
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"\n✅ Réussi: {passed}/{total}")
    print(f"❌ Échoué: {failed}/{total}")
    
    if failed == 0:
        print("\n🎉 INSTALLATION TESTING COMPLÈTE ET FONCTIONNELLE !")
        print("\nProchaines étapes:")
        print("  1. Exécuter tests: pytest tests/unit/test_memory_manager.py -v")
        print("  2. Vérifier couverture: pytest --cov=. --cov-report=html tests/")
        print("  3. Consulter README: tests/README.md")
        return True
    else:
        print("\n⚠️ INSTALLATION INCOMPLÈTE")
        print("\nActions correctives:")
        
        if not results['packages']:
            print("  • Installer dépendances: pip install -r tests/requirements-testing.txt")
        
        if not results['structure']:
            print("  • Vérifier structure dossiers tests/")
        
        if not results['ogma']:
            print("  • Vérifier PYTHONPATH inclut racine OGMA")
        
        print("\nConsulter: tests/README.md section Troubleshooting")
        return False


def main():
    """Fonction principale validation."""
    print("="*60)
    print("🔍 VALIDATION INSTALLATION TESTING OGMA")
    print("="*60)
    
    results = {}
    
    # Vérifications
    results['python'] = check_python_version()
    results['packages'] = check_testing_packages()
    results['ogma'] = check_ogma_core()
    results['structure'] = check_test_structure()
    results['tests'] = check_test_files()
    results['pytest'] = run_quick_test()
    
    # Résumé
    success = print_summary(results)
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
