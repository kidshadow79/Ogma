# 🧪 OGMA Testing Suite - Documentation Complète

**Version**: 1.0.0  
**Date**: 4 novembre 2025  
**Coverage Target**: 50-65% (Option 2 - Standard Coverage)  
**Framework**: pytest + fixtures industriels

---

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Installation](#installation)
- [Structure des Tests](#structure-des-tests)
- [Exécution des Tests](#exécution-des-tests)
- [Couverture de Code](#couverture-de-code)
- [Écriture de Tests](#écriture-de-tests)
- [Fixtures Disponibles](#fixtures-disponibles)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Vue d'Ensemble

### Objectif

Fournir une **suite de tests industriels** pour OGMA garantissant:
- ✅ Fiabilité du code (détection bugs précoce)
- ✅ Non-régression (éviter casser features existantes)
- ✅ Documentation vivante (tests = spécifications)
- ✅ Confiance refactoring (modification sans peur)

### Statistiques

| Catégorie | Tests Estimés | Couverture |
|-----------|---------------|------------|
| **Unit** | 121-160 | ~60% |
| **Integration** | 45-70 | ~25% |
| **E2E** | 5-10 | ~15% |
| **TOTAL** | **110-150** | **50-65%** |

### Composants Testés (Priorité)

**🔴 CRITIQUE** (60-80 tests):
1. Memory Manager (25-35 tests) - Système mémoire hybride
2. Core Logic (20-25 tests) - Contrôleurs IA multi-providers
3. Cognitive Mirror (15-20 tests) - Extension introspection

**🟠 HAUTE** (50-70 tests):
4. Audio Manager (20-25 tests) - STT/TTS multi-moteurs
5. Conversations (15-20 tests) - Gestion conversations
6. Extensions (15-25 tests) - Autres extensions

---

## 🚀 Installation

### 1. Installer Dépendances Testing

```bash
# Depuis la racine d'OGMA
pip install -r tests/requirements-testing.txt
```

**Contenu `requirements-testing.txt`**:
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-timeout>=2.1.0
pytest-xdist>=3.3.0
responses>=0.23.0
freezegun>=1.2.0
faker>=19.0.0
```

### 2. Vérifier Installation

```bash
pytest --version
# Output: pytest 7.4.0
```

### 3. Configuration pytest

Le fichier `pytest.ini` est déjà configuré:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short
```

---

## 📁 Structure des Tests

```
tests/
├── __init__.py                  # Documentation suite
├── conftest.py                  # Fixtures globales pytest
├── pytest.ini                   # Configuration pytest
├── requirements-testing.txt     # Dépendances
│
├── unit/                        # Tests unitaires (121-160)
│   ├── __init__.py
│   ├── test_memory_manager.py   # 25-35 tests (CRITIQUE)
│   ├── test_core_logic.py       # 20-25 tests (CRITIQUE)
│   ├── test_cognitive_mirror.py # 15-20 tests (CRITIQUE)
│   ├── test_audio_manager.py    # 20-25 tests
│   ├── test_conversations.py    # 15-20 tests
│   ├── test_utils.py            # 15-20 tests
│   ├── test_settings.py         # 10-15 tests
│   └── test_identity_manager.py # 8-12 tests
│
├── integration/                 # Tests intégration (45-70)
│   ├── __init__.py
│   ├── test_memory_search.py    # Search hybride FAISS+FTS5
│   ├── test_ia_pipeline.py      # Pipeline complet IA
│   ├── test_extensions.py       # Extensions + Core
│   └── test_audio_tts_stt.py    # Audio complet
│
├── e2e/                         # Tests end-to-end (5-10)
│   ├── __init__.py
│   ├── test_conversation_flow.py # Scénario conversation complète
│   ├── test_memory_lifecycle.py  # Cycle vie souvenir
│   └── test_introspection_flow.py # Introspection complète
│
└── fixtures/                    # Données test réutilisables
    ├── sample_conversations.json
    ├── sample_memories.json
    └── mock_responses.json
```

---

## ▶️ Exécution des Tests

### Commandes de Base

```bash
# Tous les tests
pytest tests/

# Tests unitaires uniquement
pytest tests/unit/

# Tests d'intégration uniquement
pytest tests/integration/

# Tests E2E uniquement
pytest tests/e2e/

# Test spécifique
pytest tests/unit/test_memory_manager.py

# Test avec verbose
pytest tests/unit/test_memory_manager.py -v

# Test avec output détaillé
pytest tests/unit/test_memory_manager.py -vv
```

### Tests par Markers

```bash
# Tests lents (>1s)
pytest -m slow

# Tests nécessitant API
pytest -m requires_api

# Tests nécessitant GPU
pytest -m requires_gpu

# Exclure tests lents
pytest -m "not slow"
```

### Exécution Parallèle

```bash
# Exécuter sur 4 workers (4× plus rapide)
pytest -n 4 tests/

# Auto-détection nombre CPU
pytest -n auto tests/
```

### Tests Spécifiques

```bash
# Tester une classe
pytest tests/unit/test_memory_manager.py::TestMemoryCreation

# Tester une fonction
pytest tests/unit/test_memory_manager.py::TestMemoryCreation::test_add_memory_simple

# Pattern de nom
pytest tests/ -k "memory"  # Tous tests contenant "memory"
```

---

## 📊 Couverture de Code

### Générer Rapport Couverture

```bash
# Avec rapport terminal
pytest --cov=. --cov-report=term tests/

# Avec rapport HTML
pytest --cov=. --cov-report=html tests/

# Ouvrir rapport HTML
start htmlcov/index.html  # Windows
```

### Rapport Détaillé

```bash
# Afficher lignes manquantes
pytest --cov=. --cov-report=term-missing tests/

# Générer rapport XML (pour CI/CD)
pytest --cov=. --cov-report=xml tests/
```

### Exemple Output

```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
memory_manager.py          2757    800   71%    45-67, 123-145
core_logic.py              1706    600   65%    234-456
cognitive_mirror.py         456    150   67%    89-123
-------------------------------------------------------
TOTAL                     10000   3000   70%
```

### Objectif Couverture

| Fichier | Couverture Cible | Priorité |
|---------|------------------|----------|
| `memory_manager.py` | 70-80% | 🔴 CRITIQUE |
| `core_logic.py` | 60-70% | 🔴 CRITIQUE |
| `cognitive_mirror/` | 60-70% | 🔴 CRITIQUE |
| `audio_manager.py` | 50-60% | 🟠 HAUTE |
| `ogma_ng.py` | 30-40% | 🟡 MOYENNE |

---

## ✍️ Écriture de Tests

### Structure Test Type

```python
"""
tests/unit/test_example.py
"""

import pytest
from unittest.mock import Mock, patch


class TestExampleFeature:
    """Tests d'une feature spécifique."""
    
    def test_basic_functionality(self):
        """Test cas nominal."""
        # Arrange
        input_data = "test"
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == "expected_output"
    
    def test_error_handling(self):
        """Test gestion d'erreur."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test fonction asynchrone."""
        result = await async_function()
        assert result is not None
```

### Conventions

1. **Nommage**:
   - Fichiers: `test_*.py`
   - Classes: `Test*`
   - Fonctions: `test_*`

2. **Organisation**:
   - 1 classe par feature/composant
   - Grouper tests similaires
   - Docstrings explicites

3. **Assertions**:
   ```python
   # ✅ BON
   assert result == expected
   assert result is not None
   assert len(results) > 0
   
   # ❌ MAUVAIS
   assert result  # Pas clair
   ```

4. **Mocking**:
   ```python
   # Mock simple
   @patch('module.function')
   def test_with_mock(mock_func):
       mock_func.return_value = "mocked"
       result = call_function()
       assert result == "mocked"
   ```

---

## 🎁 Fixtures Disponibles

### Fixtures Temporaires

```python
def test_with_temp_dir(temp_dir):
    """temp_dir: Répertoire temporaire auto-nettoyé."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test")
    assert file_path.exists()
    # Auto-supprimé après test
```

### Fixtures Mock IA

```python
def test_with_mock_controllers(mock_chat_controller, mock_archiviste_controller):
    """Mock contrôleurs IA pré-configurés."""
    response = mock_chat_controller.send_message([{"role": "user", "content": "test"}])
    assert "test" in response or response is not None
```

### Fixtures Memory

```python
def test_with_memory_manager(mock_memory_manager):
    """MemoryManager avec SQLite temporaire."""
    memory_id = mock_memory_manager.add_memory(
        text="Test",
        metadata={}
    )
    assert memory_id is not None
```

### Fixtures Settings

```python
def test_with_settings(mock_settings_manager):
    """SettingsManager avec config temporaire."""
    provider = mock_settings_manager.settings["chat_api"]["provider"]
    assert provider == "OpenAI"
```

### Liste Complète

| Fixture | Description | Scope |
|---------|-------------|-------|
| `temp_dir` | Répertoire temporaire | function |
| `test_data_dir` | Dossier fixtures | session |
| `mock_chat_controller` | Mock Chat IA | function |
| `mock_archiviste_controller` | Mock Archiviste | function |
| `mock_embedding_controller` | Mock Embedding | function |
| `mock_memory_manager` | MemoryManager test | function |
| `mock_settings_manager` | SettingsManager test | function |
| `mock_audio_manager` | AudioManager mock | function |
| `status_queue` | Queue statut UI | function |
| `sample_conversation` | Conversation exemple | session |
| `sample_memory_data` | Données mémoire | session |

---

## 🤖 CI/CD Integration

### GitHub Actions (Recommandé)

Créer `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-testing.txt
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hook (Local)

Créer `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Exécuter tests avant chaque commit

echo "Running tests..."
pytest tests/unit/ -x

if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Commit aborted."
    exit 1
fi

echo "✅ Tests passed!"
```

Rendre exécutable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 🔧 Troubleshooting

### Problème: Tests Échouent Localement

```bash
# 1. Vérifier dépendances à jour
pip install -r tests/requirements-testing.txt --upgrade

# 2. Nettoyer cache pytest
pytest --cache-clear

# 3. Exécuter avec verbose
pytest -vv tests/unit/test_failing.py
```

### Problème: Import Errors

```bash
# Ajouter PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows

# Ou installer OGMA en mode dev
pip install -e .
```

### Problème: Tests Lents

```bash
# Identifier tests lents
pytest --durations=10 tests/

# Exécuter en parallèle
pytest -n auto tests/

# Skip tests lents
pytest -m "not slow" tests/
```

### Problème: Couverture Faible

```bash
# Identifier fichiers non testés
pytest --cov=. --cov-report=term-missing tests/

# Générer rapport HTML pour analyse
pytest --cov=. --cov-report=html tests/
start htmlcov/index.html
```

---

## 📈 Métriques de Succès

### Objectifs Testing (Option 2)

| Métrique | Cible | Actuel | Status |
|----------|-------|--------|--------|
| **Tests Unitaires** | 121-160 | 60+ | 🟡 En cours |
| **Tests Intégration** | 45-70 | 0 | 🔴 À faire |
| **Tests E2E** | 5-10 | 0 | 🔴 À faire |
| **Couverture Code** | 50-65% | ~20% | 🟡 En cours |
| **Temps Exécution** | <2 min | N/A | ⚪ À mesurer |

### Prochaines Étapes

**Phase 1** (Actuelle):
- ✅ Structure testing créée
- ✅ Fixtures globales configurées
- ✅ Tests critiques Memory Manager (25-35)
- ✅ Tests critiques Core Logic (20-25)
- ✅ Tests critiques Cognitive Mirror (15-20)

**Phase 2** (Prochaine semaine):
- ⏳ Tests Audio Manager (20-25)
- ⏳ Tests Conversations (15-20)
- ⏳ Tests Extensions (15-25)

**Phase 3** (2 semaines):
- ⏳ Tests Intégration (45-70)
- ⏳ Tests E2E (5-10)
- ⏳ CI/CD GitHub Actions

**Phase 4** (1 mois):
- ⏳ Atteindre 50-65% couverture
- ⏳ Documentation tests complète
- ⏳ Formation équipe (si applicable)

---

## 🎓 Ressources Apprentissage

### Documentation Pytest

- **Guide officiel**: https://docs.pytest.org/
- **Fixtures**: https://docs.pytest.org/en/stable/fixture.html
- **Parametrize**: https://docs.pytest.org/en/stable/parametrize.html
- **Asyncio**: https://pytest-asyncio.readthedocs.io/

### Bonnes Pratiques

1. **Test Pyramid**:
   - 70% Unit (rapides, isolés)
   - 20% Integration (composants multiples)
   - 10% E2E (scénarios complets)

2. **F.I.R.S.T Principles**:
   - **F**ast: Tests rapides (<1s unitaires)
   - **I**solated: Indépendants les uns des autres
   - **R**epeatable: Résultats identiques à chaque run
   - **S**elf-validating: Pass/Fail automatique
   - **T**imely: Écrits avant/pendant développement

3. **AAA Pattern** (Arrange-Act-Assert):
   ```python
   def test_example():
       # Arrange: Préparer données
       input_data = "test"
       
       # Act: Exécuter fonction
       result = function(input_data)
       
       # Assert: Vérifier résultat
       assert result == "expected"
   ```

---

## 📞 Support

### Questions / Issues

- **GitHub Issues**: Pour bugs/features tests
- **Documentation**: Ce README + docstrings tests
- **Contact**: Architecte OGMA

### Contribution

Pour ajouter de nouveaux tests:

1. Suivre structure existante (`tests/unit/`, `tests/integration/`, `tests/e2e/`)
2. Utiliser fixtures disponibles (`conftest.py`)
3. Respecter conventions nommage
4. Ajouter docstrings explicites
5. Vérifier couverture augmente:
   ```bash
   pytest --cov=. --cov-report=term tests/
   ```

---

## 🏆 Conclusion

Cette suite de tests industriels transforme OGMA d'un **projet fonctionnel** en **projet professionnel** avec:

- ✅ **Confiance refactoring** (modification sans peur casser)
- ✅ **Détection bugs précoce** (avant production)
- ✅ **Documentation vivante** (tests = spécifications)
- ✅ **Qualité professionnelle** (standard industrie)

**Prochaine action**: Exécuter `pytest tests/unit/test_memory_manager.py -v` pour vérifier les 25-35 tests critiques du Memory Manager ! 🚀

---

**Version**: 1.0.0  
**Dernière mise à jour**: 4 novembre 2025  
**Auteur**: Équipe OGMA Testing  
**Licence**: Même que projet OGMA
