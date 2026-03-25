# Tests d'Intégration - Cognitive Mirror

## 🎯 Objectif

Valider que le dialogue **RÉEL** Luna ↔ Archiviste fonctionne avec de vraies API IA (pas de mocks).

**Différence avec tests unitaires:**
- ❌ **Unit tests** : Utilisent `AsyncMock`, réponses hardcodées → Valident structure code
- ✅ **Integration tests** : Utilisent vraies APIs (OpenAI/Mistral) → Valident fonctionnalité réelle

## 📋 Tests Disponibles

| Test | Description | Durée | Coût API |
|------|-------------|-------|----------|
| `test_luna_archiviste_single_turn_dialogue` | Dialogue 1 tour | ~15s | ~$0.002 |
| `test_luna_archiviste_multi_turn_conversation` | Conversation 3 tours | ~45s | ~$0.008 |
| `test_magic_phrase_end_to_end` | Workflow complet | ~30s | ~$0.004 |
| `test_dialogue_persistence_to_memory` | Persistence mémoire | ~20s | ~$0.003 |
| `test_api_connectivity` (bonus) | Test connexion rapide | ~3s | ~$0.001 |

**Total:** ~2min, ~$0.02 par run complet

## 🔧 Configuration

### 1. API Keys

Créer fichier `.env` à la racine du projet:

```env
# Au moins UNE de ces clés requis
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
MISTRAL_API_KEY=xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

**Recommandé:** OpenAI (gpt-4o-mini) - Rapide et économique

### 2. Dépendances

```bash
pip install pytest pytest-asyncio
```

## 🚀 Exécution

### Tous les tests d'intégration

```bash
pytest tests/integration/ -v -s
```

### Tests spécifiques

```bash
# Seulement tests lents (tous les integration)
pytest tests/integration/ -v -m slow

# Seulement tests integration (exclut bonus)
pytest tests/integration/ -v -m integration

# Un seul test
pytest tests/integration/test_cognitive_mirror_real_dialogue.py::test_luna_archiviste_single_turn_dialogue -v -s
```

### Skip si pas d'API key

Les tests se skipperont automatiquement si aucune API key n'est configurée:

```
SKIPPED [1] ... : Aucune API key configurée (OPENAI/MISTRAL/ANTHROPIC requis)
```

## 📊 Output Attendu

### Succès (4/4 PASS)

```
🔬 TESTS D'INTÉGRATION COGNITIVE MIRROR
==================================================
⚠️  ATTENTION: Ces tests font des VRAIS appels API
⚠️  Coût estimé: ~0.01-0.05$ (selon provider)
⚠️  Durée totale: ~2-3 minutes
==================================================

test_cognitive_mirror_real_dialogue.py::test_luna_archiviste_single_turn_dialogue 
==================================================
🔬 TEST 1: DIALOGUE 1 TOUR - LUNA ↔ ARCHIVISTE
==================================================

[ÉTAPE 1] Luna génère question initiale...
✅ Luna question (127 chars):
   Comment l'apprentissage continu influence-t-il ma capacité à comprendre...

[ÉTAPE 2] Archiviste analyse et répond...
✅ Archiviste réponse (342 chars):
   L'apprentissage continu renforce ta capacité à identifier des patterns...

[ÉTAPE 3] Vérifications qualité dialogue...
✅ Qualité dialogue validée:
   - Luna: 127 chars
   - Archiviste: 342 chars
   - Mots-clés pertinents: Oui
   - Pas d'erreurs: Oui

[ÉTAPE 4] Test sauvegarde dialogue en mémoire...
✅ Dialogue sauvegardé en mémoire (ID: 1)
✅ Mémoire count: 1

==================================================
✅ TEST 1 RÉUSSI - Dialogue 1 tour validé
==================================================
PASSED

[... autres tests ...]

✅ TESTS D'INTÉGRATION TERMINÉS
==================================================

=========== 4 passed in 110.23s (1m 50s) ===========
```

### Échec (erreurs API)

Si erreur de connexion/authentification:

```
AssertionError: Erreur Luna: Authentication failed
```

→ Vérifier API key dans `.env`

## 🔍 Validation

### Ce que les tests confirment

✅ **Luna génère vraies questions** (via API)  
✅ **Archiviste répond vraiment** (via API)  
✅ **Dialogue cohérent** (mots-clés, longueur, pas d'erreurs)  
✅ **Context preservation** (multi-tour référence tours précédents)  
✅ **Persistence mémoire** (SQLite + FAISS)  
✅ **Workflow end-to-end** (phrase magique → dialogue → sauvegarde)

### Niveaux de confiance

| Aspect | Avant (mocks) | Après (4/4 PASS) |
|--------|---------------|-------------------|
| Code structure | 95% ✅ | 95% ✅ |
| Dialogue Luna réel | 10% ❌ | **95% ✅** |
| Dialogue Archiviste réel | 10% ❌ | **95% ✅** |
| Orchestration multi-tour | 15% ❌ | **90% ✅** |
| Workflow end-to-end | 5% ❌ | **85% ✅** |

**Impact:** Confiance fonctionnalité réelle passe de ~10% à ~95% 🎯

## 🐛 Debugging

### Tests skipés

```bash
# Vérifier .env chargé
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

### Tests échouent

```bash
# Verbose output
pytest tests/integration/ -vv -s --tb=long

# Logs détaillés
pytest tests/integration/ -v -s --log-cli-level=DEBUG
```

### Timeout API

Augmenter timeout dans `core_logic.py`:

```python
controller = AIController(
    timeout=60  # Au lieu de 30
)
```

## 📁 Structure

```
tests/integration/
├── README.md (ce fichier)
├── __init__.py
├── test_cognitive_mirror_real_dialogue.py (4 tests)
└── conftest.py (fixtures partagées - optionnel)
```

## 🚦 CI/CD

**Recommandation:** Ne pas exécuter en CI automatique (coûts API)

**Alternative:**
- CI: Tests unitaires seulement (fast, gratuit)
- Nightly: Tests d'intégration (1x/jour, budgeté)
- Manual: Tests intégration avant releases

```yaml
# .github/workflows/tests.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit/ -v
  
  integration-tests:
    if: github.event_name == 'schedule'  # Nightly only
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/integration/ -v
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## 💡 Best Practices

1. **API Keys:** Jamais commit dans Git → Utiliser `.env` + `.gitignore`
2. **Coûts:** Monitorer usage API (OpenAI dashboard)
3. **Rate limits:** Espacer tests si rate limit atteint
4. **Isolation:** Tests utilisent DB temporaire (pas pollution mémoire prod)
5. **Nettoyage:** Fixtures auto-cleanup après tests

## 📞 Support

Si tests échouent de manière inexpliquée:

1. Vérifier solde API provider
2. Vérifier rate limits
3. Tester connexion avec test bonus: `pytest tests/integration/ -k connectivity -v`
4. Consulter logs détaillés: `-vv -s --tb=long`
