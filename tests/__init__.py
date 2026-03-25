"""
OGMA Testing Suite - Option 2 (Standard Coverage)
===================================================

Structure:
- unit/         : Tests unitaires (fonctions isolées)
- integration/  : Tests d'intégration (composants multiples)
- e2e/          : Tests end-to-end (scénarios complets)
- fixtures/     : Données de test réutilisables

Couverture cible: 50-65% du code
Total estimé: 110-150 tests

Frameworks:
- pytest: Framework de test principal
- pytest-asyncio: Support tests asynchrones
- pytest-cov: Couverture de code
- pytest-mock: Mocking avancé

Exécution:
```bash
# Tous les tests
pytest tests/

# Tests unitaires uniquement
pytest tests/unit/

# Avec couverture
pytest --cov=. --cov-report=html tests/

# Tests spécifiques
pytest tests/unit/test_memory_manager.py -v
```

Conventions:
- Fichiers: test_*.py
- Classes: Test*
- Fonctions: test_*
- Fixtures: conftest.py
"""
