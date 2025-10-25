# 🛡️ PLAN DE REFACTORING SÉCURISÉ OGMA

**Principe fondamental** : "Jamais casser l'existant - Créer le nouveau à côté"

---

## 🎯 MÉTHODOLOGIE : Refactoring Progressif Non-Destructif

### ⚠️ RÈGLES D'OR

1. **JAMAIS toucher à `ogma_ng.py` directement**
2. **TOUJOURS dupliquer avant de modifier**
3. **TESTER chaque fonction isolément AVANT intégration**
4. **VALIDER fonctionnellement après chaque micro-étape**
5. **COMMIT Git à chaque étape validée**

---

## 📊 PHASES DE REFACTORING

### PHASE 0 : PRÉPARATION (30 min)

#### 0.1 - Créer branche Git dédiée
```bash
git checkout -b refactoring-phase1-message-handler
git commit -m "BACKUP: État stable avant refactoring"
```

#### 0.2 - Créer fichier de tests de régression
**Fichier** : `test_regression_refactoring.py`

```python
"""
Tests de non-régression pour refactoring OGMA
À exécuter AVANT et APRÈS chaque extraction de module
"""
import pytest
from unittest.mock import Mock, patch

def test_message_rendering_basic():
    """Vérifie rendu message basique (user/assistant)"""
    # Test que _message() fonctionne
    pass

def test_send_message_flow():
    """Vérifie flow complet envoi message"""
    # Test que _send_chat_message() fonctionne
    pass

def test_magic_phrases_detection():
    """Vérifie détection phrases magiques"""
    # Test toutes les phrases (Perception, Cognitive, Bio, etc.)
    pass

def test_memory_injection():
    """Vérifie injection souvenirs FAISS"""
    pass

def test_conversation_persistence():
    """Vérifie save/load conversations"""
    pass

# TODO: 20+ tests à compléter
```

#### 0.3 - Créer structure modules cibles
```bash
mkdir modules
mkdir modules/message
mkdir modules/ui
mkdir modules/conversation
mkdir modules/managers
mkdir modules/extension_hooks
mkdir modules/utils
```

#### 0.4 - Baseline de performance
**Fichier** : `benchmark_baseline.py`

```python
"""Mesure temps exécution fonctions critiques AVANT refactoring"""
import time
from ogma_ng import _send_chat_message, _message, _sidebar

def benchmark_send_message():
    start = time.time()
    # Mock call _send_chat_message
    duration = time.time() - start
    print(f"_send_chat_message: {duration:.3f}s")

# Sauvegarder résultats dans baseline.json
```

---

### PHASE 1 : EXTRACTION UTILITAIRES (2h - Faible risque)

**Objectif** : Extraire fonctions pures sans dépendances complexes

#### 1.1 - Créer `modules/utils/formatters.py`

**Fonctions à extraire** :
- `format_size()` (ligne 82)
- `_format_datetime()` (ligne 2821)
- `_truncate_filename()` (ligne 1071)
- `_get_file_icon()` (ligne 1077)

**Process** :
```bash
1. Créer modules/utils/formatters.py
2. COPIER (pas déplacer) les 4 fonctions
3. Ajouter tests unitaires → test_formatters.py
4. ✅ Valider tests (100% pass)
5. Importer dans ogma_ng.py: from modules.utils.formatters import *
6. Commenter anciennes fonctions (ne pas supprimer)
7. ✅ Lancer OGMA → tester manuellement
8. ✅ Tests régression → Tout vert
9. Git commit "feat: Extract formatters to modules/utils"
10. Supprimer anciennes fonctions commentées
11. Git commit "refactor: Clean old formatters"
```

#### 1.2 - Créer `modules/utils/parsers.py`

**Fonctions à extraire** :
- `_parse_thinking_format()` (ligne 2835)
- `_parse_introspection_format()` (ligne 2917)
- `_strip_magic_phrases()` (ligne ~5500)
- `_extract_magic_memories()` (ligne ~5450)

**Process** : Identique 1.1

#### 1.3 - Créer `modules/utils/notifications.py`

**Fonction à extraire** :
- `_notify_safe()` (ligne 1057)

#### ✅ VALIDATION PHASE 1
- [ ] Tous les tests unitaires passent (utils isolés)
- [ ] Tests régression passent (100%)
- [ ] OGMA démarre sans erreur
- [ ] Test manuel : Envoi message → rendu correct
- [ ] Test manuel : Thinking format affiché
- [ ] Git : 3 commits propres

---

### PHASE 2 : EXTRACTION MANAGERS (4h - Risque moyen)

**Objectif** : Isoler initialisations lazy dans module dédié

#### 2.1 - Créer `modules/managers/lazy_initializers.py`

**Fonctions à extraire** :
- `_ensure_settings_manager()` (239)
- `_ensure_audio_manager()` (247)
- `_ensure_backends()` (268)
- `_ensure_memory_manager()` (322)
- `_ensure_temporal_guardian()` (480)
- `_ensure_cognitive_mirror()` (840)
- `_ensure_chat_controller()` (931)
- `_ensure_archiviste_controller()` (1025)

**ATTENTION** : Ces fonctions manipulent variables globales !

**Process sécurisé** :
```python
# modules/managers/lazy_initializers.py
"""
Managers lazy initialization
Utilise les MÊMES variables globales que ogma_ng.py
"""
import sys
import ogma_ng  # Import module parent pour accès globals

def ensure_settings_manager():
    """Wrapper qui manipule ogma_ng._settings_manager"""
    if ogma_ng._settings_manager is None:
        # Code original copié
        ogma_ng._settings_manager = SettingsManager(...)
    return ogma_ng._settings_manager

# Répéter pour tous les _ensure_*
```

**Tests critiques** :
```python
def test_lazy_init_idempotent():
    """Vérifie qu'appeler 2× retourne même instance"""
    m1 = ensure_settings_manager()
    m2 = ensure_settings_manager()
    assert m1 is m2  # Même objet en mémoire
```

#### 2.2 - Créer `modules/managers/memory_integration.py`

**Responsabilité** : Injection souvenirs dans prompt système

**Fonction à extraire** :
- Bloc injection FAISS dans `_send_chat_message()` (lignes ~5900-6000)

**Signature** :
```python
async def inject_memories_to_prompt(
    user_message: str,
    memory_manager,
    settings_manager
) -> list[dict]:
    """
    Retourne liste de dicts à injecter dans prompt système
    [
        {"role": "system", "content": "[MÉMOIRE] ..."},
        ...
    ]
    """
```

#### ✅ VALIDATION PHASE 2
- [ ] Tests unitaires managers (init, idempotence)
- [ ] Tests régression (100%)
- [ ] OGMA démarre
- [ ] Test manuel : Mémorisation fonctionne
- [ ] Test manuel : Injection mémoire visible (via thinking)
- [ ] Git : 2 commits

---

### PHASE 3 : EXTRACTION MESSAGE RENDERING (5h - Risque ÉLEVÉ)

**⚠️ ZONE CRITIQUE** : `_message()` 554 lignes avec hooks extensions

#### 3.1 - Créer `modules/extension_hooks/hook_manager.py`

**Objectif** : Centraliser toutes les détections magic phrases IA

**Architecture** :
```python
from typing import Callable, Dict
import asyncio

class ExtensionHook:
    """Représente un hook d'extension"""
    def __init__(
        self, 
        name: str,
        patterns: list[str],
        action: Callable,
        delay: float = 0.3
    ):
        self.name = name
        self.patterns = patterns
        self.action = action
        self.delay = delay

class HookManager:
    """Gestionnaire centralisé des hooks extensions"""
    def __init__(self):
        self._hooks: Dict[str, ExtensionHook] = {}
    
    def register_hook(self, hook: ExtensionHook):
        """Enregistre un hook"""
        self._hooks[hook.name] = hook
    
    async def process_message(
        self, 
        message_content: str, 
        role: str,
        metadata: dict
    ):
        """
        Analyse message et déclenche hooks si patterns détectés
        Retourne: (processed_content, triggered_hooks)
        """
        if role != 'assistant':
            return message_content, []
        
        triggered = []
        for hook in self._hooks.values():
            if self._match_patterns(message_content, hook.patterns):
                # Protection historique
                if not should_process_magic_phrase(metadata, hook.name):
                    continue
                
                # Trigger async avec delay
                asyncio.create_task(self._trigger_hook(hook))
                triggered.append(hook.name)
        
        return message_content, triggered
    
    async def _trigger_hook(self, hook: ExtensionHook):
        await asyncio.sleep(hook.delay)
        await hook.action()

# Instance globale
hook_manager = HookManager()
```

#### 3.2 - Migrer hooks extensions vers HookManager

**Dans ogma_ng.py (fonction d'init, pas dans _message)** :
```python
from modules.extension_hooks.hook_manager import hook_manager, ExtensionHook

# Enregistrer Perception hook
perception_hook = ExtensionHook(
    name="perception",
    patterns=["il faut que je te vois", "je veux te voir"],
    action=lambda: perception_ui.start_perception()
)
hook_manager.register_hook(perception_hook)

# Enregistrer Cognitive Mirror
cognitive_hook = ExtensionHook(
    name="cognitive_mirror",
    patterns=["il faut que je réfléchisse"],
    action=lambda: _cognitive_mirror.trigger_introspection()
)
hook_manager.register_hook(cognitive_hook)

# Biography, etc.
```

#### 3.3 - Simplifier `_message()` avec HookManager

**AVANT** (ligne 1708-1777 - 70 lignes pour Perception) :
```python
# Détection Perception
if role == 'assistant':
    content_lower = main_content.lower()
    if any(phrase in content_lower for phrase in [...]):
        # 60 lignes de logique
```

**APRÈS** (5 lignes) :
```python
# Process extension hooks
processed_content, triggered = await hook_manager.process_message(
    main_content, role, msg
)
main_content = processed_content
```

#### 3.4 - Créer `modules/ui/message_renderer.py`

**Extraire** :
- Rendu badges
- Rendu thinking
- Rendu introspection
- Mode édition

**Signature** :
```python
def render_message(
    msg: dict,
    on_edit_callback: Callable = None
) -> NiceGUIComponent:
    """
    Retourne composant NiceGUI pour un message
    """
```

#### ✅ VALIDATION PHASE 3
- [ ] Tests hooks (registration, triggering, delay)
- [ ] Tests régression (CRITIQUE)
- [ ] Test manuel : Magic phrases Perception IA → Activation
- [ ] Test manuel : Magic phrases Cognitive Mirror → Introspection
- [ ] Test manuel : Biography injection
- [ ] Test manuel : Thinking format affiché
- [ ] OGMA démarre et fonctionne normalement
- [ ] Git : 3 commits

---

### PHASE 4 : EXTRACTION MESSAGE HANDLER (8h - Risque TRÈS ÉLEVÉ)

**⚠️ ZONE ULTRA-CRITIQUE** : `_send_chat_message()` 1576 lignes

#### 4.1 - Analyser dépendances exactes

**Créer** : `analyse_send_chat_message_dependencies.py`

```python
"""
Analyse statique de _send_chat_message
Liste TOUS les appels de fonctions, variables globales utilisées
"""
import ast

# Parser ogma_ng.py
# Extraire fonction _send_chat_message (lignes 4981-6557)
# Lister:
# - Variables globales lues/modifiées
# - Fonctions appelées
# - Imports nécessaires
# - Managers utilisés
```

#### 4.2 - Découper en sous-fonctions (DANS ogma_ng.py d'abord)

**Créer fonctions internes** :
```python
async def _send_chat_message(...):
    # 1. Validation & préparation
    validated_data = await _validate_and_prepare_message(message_text)
    
    # 2. Détection magic phrases USER
    magic_actions = await _detect_user_magic_phrases(message_text)
    
    # 3. Construction prompt système
    system_prompt = await _build_system_prompt(message_text)
    
    # 4. Injection Perception capture
    if perception_enabled:
        system_prompt = await _inject_perception_capture(system_prompt)
    
    # 5. Appel IA streaming
    async for chunk in _stream_ai_response(system_prompt, history):
        yield chunk
    
    # 6. Post-processing (mémorisation auto, etc.)
    await _post_process_message(response)
```

**Tester SANS bouger** : OGMA doit fonctionner identique

#### 4.3 - Extraire vers modules (1 par 1)

**Module 1** : `modules/message/validator.py`
- Fonction : `_validate_and_prepare_message`
- Tests unitaires
- Import dans ogma_ng.py
- Validation

**Module 2** : `modules/message/magic_phrase_detector.py`
- Fonction : `_detect_user_magic_phrases`
- Tests avec TOUS les patterns
- Validation

**Module 3** : `modules/message/prompt_builder.py`
- Fonction : `_build_system_prompt`
- Tests injection (Temporal, Ego, Memory)
- Validation

**Module 4** : `modules/message/perception_injector.py`
- Fonction : `_inject_perception_capture`
- Tests base64 encoding
- Validation

**Module 5** : `modules/message/ai_streamer.py`
- Fonction : `_stream_ai_response`
- Tests streaming (mock API)
- Validation

**Module 6** : `modules/message/post_processor.py`
- Fonction : `_post_process_message`
- Tests mémorisation auto
- Validation

#### 4.4 - Refactorer `_send_chat_message` final

**Résultat** : ~100 lignes (orchestration uniquement)

```python
async def _send_chat_message(message_text: str):
    """Handler principal - Orchestration uniquement"""
    from modules.message import (
        validate_and_prepare,
        detect_user_magic_phrases,
        build_system_prompt,
        inject_perception,
        stream_ai_response,
        post_process_message
    )
    
    # 1. Validation
    data = await validate_and_prepare(message_text)
    
    # 2. Magic phrases
    actions = await detect_user_magic_phrases(message_text)
    for action in actions:
        await action.execute()
    
    # 3. Prompt
    prompt = await build_system_prompt(message_text, _chat_history)
    
    # 4. Perception
    if perception_ui.is_enabled:
        prompt = await inject_perception(prompt)
    
    # 5. Stream
    response = ""
    async for chunk in stream_ai_response(prompt, _chat_controller):
        response += chunk
        yield chunk
    
    # 6. Post-process
    await post_process_message(response, _chat_history)
```

#### ✅ VALIDATION PHASE 4
- [ ] Tests unitaires (6 modules)
- [ ] Tests intégration (flow complet)
- [ ] Tests régression (100%)
- [ ] Test manuel : Envoi message simple
- [ ] Test manuel : Message avec thinking
- [ ] Test manuel : Message avec image Perception
- [ ] Test manuel : Magic phrases (toutes)
- [ ] Test manuel : Mémorisation auto
- [ ] Benchmark performance (≤ baseline +10%)
- [ ] Git : 7 commits (1 par module + final)

---

## 🎯 CHECKPOINTS DE VALIDATION

### Après chaque phase :

#### 1. Tests Automatiques
```bash
pytest test_regression_refactoring.py -v
pytest modules/ -v  # Tests unitaires nouveaux modules
```

#### 2. Tests Manuels (Checklist)
- [ ] OGMA démarre sans erreur
- [ ] Envoi message simple → Réponse IA
- [ ] Upload fichier → Contexte injecté
- [ ] Nouvelle conversation → Titre auto
- [ ] Load conversation → Historique correct
- [ ] Magic phrase Perception IA → Activation webcam
- [ ] Magic phrase Cognitive Mirror → Introspection
- [ ] Magic phrase mémorisation → Sauvegarde FAISS
- [ ] Audio STT → Transcription
- [ ] Audio TTS → Lecture réponse
- [ ] Perception capture → Image dans prompt
- [ ] Settings modal → Sauvegarde config

#### 3. Benchmark Performance
```bash
python benchmark_baseline.py  # Avant
python benchmark_current.py   # Après
# Comparer: Δ < +10% acceptable
```

#### 4. Git Status
```bash
git status  # Doit être clean
git log --oneline -10  # Vérifier commits propres
```

---

## 📊 ESTIMATION TEMPS TOTAL

| Phase | Durée | Risque | Validation |
|-------|-------|--------|------------|
| Phase 0 - Préparation | 30 min | ✅ Nul | Setup tests |
| Phase 1 - Utilitaires | 2h | ✅ Faible | Tests isolés |
| Phase 2 - Managers | 4h | ⚠️ Moyen | Lazy init OK |
| Phase 3 - Message Rendering | 5h | 🔥 Élevé | Hooks fonctionnent |
| Phase 4 - Message Handler | 8h | 🔥🔥 Très élevé | Flow complet OK |
| **TOTAL** | **~20h** | | **100% validé** |

---

## 🛡️ STRATÉGIE ROLLBACK

### Si problème détecté :

#### 1. Rollback Git (recommandé)
```bash
git log --oneline  # Identifier commit stable
git reset --hard <commit_stable>
```

#### 2. Désactivation module (temporaire)
```python
# Dans ogma_ng.py
USE_REFACTORED_MODULES = False  # Flag global

if USE_REFACTORED_MODULES:
    from modules.message import send_chat_message
else:
    # Utiliser fonction originale (commentée, pas supprimée)
```

#### 3. Debugging ciblé
```python
# Ajouter logs détaillés
import logging
logging.basicConfig(level=logging.DEBUG)

logger.debug(f"Module: {module_name}, Function: {func_name}, Args: {args}")
```

---

## ✅ CRITÈRES DE SUCCÈS FINAL

### Fonctionnalité (100% identique)
- [ ] Tous les tests régression passent
- [ ] Checklist manuelle 100% validée
- [ ] Aucune régression utilisateur visible

### Architecture (amélioration)
- [ ] ogma_ng.py < 3000 lignes (vs 7724 actuellement)
- [ ] Aucune fonction > 200 lignes
- [ ] Modules découplés (imports unidirectionnels)
- [ ] 80%+ code coverage tests

### Performance (acceptable)
- [ ] Temps démarrage ≤ baseline +5%
- [ ] Temps envoi message ≤ baseline +10%
- [ ] Mémoire utilisée ≤ baseline +15%

### Maintenabilité (objectif)
- [ ] Documentation modules (docstrings)
- [ ] Type hints Python 3.10+
- [ ] Linting (pylint score > 8/10)
- [ ] Architecture documentée (ce fichier + cartographie)

---

## 🚨 SIGNAUX D'ALERTE - STOP IMMÉDIAT

### ❌ Arrêter le refactoring si :

1. **Tests régression < 90%** après 2 tentatives fix
2. **Temps debug > 2× temps planifié** pour une phase
3. **Bugs bloquants** utilisateur (crash, perte données)
4. **Performance dégradée > +25%** vs baseline
5. **Complexité accidentelle** (code plus compliqué qu'avant)

### 🔄 Action si signal alerte :

1. **STOP** - Ne pas continuer
2. **ROLLBACK** - Git reset au dernier commit stable
3. **ANALYSE** - Post-mortem : Qu'est-ce qui a échoué ?
4. **REPLANNING** - Ajuster approche/découpage
5. **VALIDATION** - Obtenir feu vert architecte avant reprise

---

## 📝 DOCUMENTATION CONTINUE

### Pendant le refactoring :

#### 1. Journal de bord (JOURNAL_REFACTORING.md)
```markdown
## 2025-10-25 14:30 - Phase 1.1 - Extract formatters

**Objectif** : Isoler format_size, format_datetime, etc.

**Actions** :
- ✅ Créé modules/utils/formatters.py
- ✅ Copié 4 fonctions
- ✅ Tests unitaires (12/12 pass)
- ✅ Import dans ogma_ng.py
- ⚠️ Problème : format_size() manquait import math
- ✅ Fix : Ajouté import
- ✅ Validation : OGMA fonctionne

**Durée** : 25 min (estimation: 30 min) ✅

**Commit** : a3f892b "feat: Extract formatters to modules/utils"
```

#### 2. Décisions architecturales (ADR - Architecture Decision Records)
```markdown
# ADR-001: Utilisation HookManager pour extensions

**Date** : 2025-10-25
**Statut** : Accepté

**Contexte** : 
Actuellement 70 lignes par extension dans _message()
Detection phrases magiques dupliquée 4 fois

**Décision** :
Créer HookManager centralisé avec pattern Observer

**Conséquences** :
+ Ajout extension = 5 lignes (vs 70)
+ Tests isolés par hook
- Complexité abstraite (pattern observer)
- Overhead léger (loop hooks)

**Alternatives rejetées** :
- Décorateurs Python (difficile async)
- Système événements (trop complexe)
```

---

## 🎓 LEÇONS APPRISES (Post-mortem anticipé)

### Risques identifiés :

1. **Variables globales** → Solution: Encapsulation progressive
2. **Couplage fort** → Solution: Interfaces/protocols
3. **Tests manquants** → Solution: TDD sur nouveaux modules
4. **Async complexity** → Solution: Documenter async boundaries

### Si échec (contingence) :

**Plan B** : Refactoring "en place" (sans extraction)
- Reorganiser ogma_ng.py avec sections claires
- Ajouter commentaires structurels
- Créer index fonction (CTRL+F friendly)
- Accepter monolithe mais organisé

---

**FIN DU PLAN**

*Prochaine étape* : Validation plan par Architecte → Feu vert Phase 0
