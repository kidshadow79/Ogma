# 🚀 OGMA V2 - Extension Architecture

**Version** : 2.0.0  
**Date** : 25 octobre 2025  
**Auteur** : Tytan

---

## 📖 Vue d'Ensemble

OGMA V2 est l'architecture d'extension pour toutes les **nouvelles fonctionnalités** OGMA.

**Principe fondamental** :
> ogma_ng.py est GELÉ (7723 lignes). Toute évolution future = Extension V2.

---

## 🏗️ Structure

```
extensions/ogma_ng_v2/
├── __init__.py              # Hook principal (register_v2_features)
├── README.md                # Ce fichier
├── features/                # Toutes les features V2
│   ├── TEMPLATE.py          # Template pour nouvelle feature
│   └── [votre_feature]/     # Vos features ici
│       ├── __init__.py      # API publique feature
│       ├── core.py          # Logique métier
│       ├── ui_components.py # Interface UI (optionnel)
│       └── README.md        # Doc feature
└── shared/                  # Code partagé entre features
    └── helpers.py           # Helpers communs
```

---

## ✨ Créer Nouvelle Feature

### Méthode Rapide (Copier Template)

```bash
# 1. Créer dossier feature
mkdir extensions/ogma_ng_v2/features/ma_feature

# 2. Copier template
cp extensions/ogma_ng_v2/features/TEMPLATE.py extensions/ogma_ng_v2/features/ma_feature/__init__.py

# 3. Éditer __init__.py
# - Renommer "template_feature" → "ma_feature"
# - Implémenter initialize_feature()
# - Ajouter votre logique
```

### Enregistrement Feature

**Éditer** `extensions/ogma_ng_v2/__init__.py` :

```python
def register_v2_features(dependencies=None):
    print("[OGMA-V2] 🚀 Initialisation...")
    
    status = {}
    
    # Ajouter votre feature ici
    from .features.ma_feature import initialize_feature
    status['ma_feature'] = initialize_feature(dependencies)
    
    return status
```

### Test Feature

```bash
# Test unitaire
python test_ma_feature.py

# Test intégration OGMA
python launch_ogma.py
# Vérifier logs: [MA-FEATURE] ✅ Initialisé
```

---

## 📚 API Feature Standard

Chaque feature DOIT implémenter :

### Fonction `initialize_feature(dependencies)`

**Signature** :
```python
def initialize_feature(dependencies=None):
    """
    Initialise feature avec dépendances OGMA.
    
    Args:
        dependencies (dict): {
            'chat_controller': AIController,
            'archiviste_controller': AIController,
            'memory_manager': MemoryManager,
            'settings_manager': SettingsManager,
            'audio_manager': AudioManager
        }
    
    Returns:
        bool: True si succès
    """
    # Votre code
    return True
```

### Fonction `is_available()`

```python
def is_available():
    """Vérifie si feature disponible."""
    return True/False
```

### Fonction `cleanup()` (Optionnel)

```python
def cleanup():
    """Nettoyage propre (arrêt OGMA)."""
    pass
```

### Fonction `get_ui_components()` (Optionnel)

```python
def get_ui_components():
    """
    Retourne composants UI pour intégration.
    
    Returns:
        dict: {
            'header_button': callable,
            'modal': callable,
            'sidebar_section': callable
        }
    """
    return {}
```

---

## 🎯 Exemples Features

### Feature Simple (Sans UI)

```python
# extensions/ogma_ng_v2/features/auto_save/__init__.py

_timer = None

def initialize_feature(dependencies=None):
    global _timer
    print("[AUTO-SAVE] Initialisation...")
    
    # Démarrer timer auto-save toutes les 5min
    import threading
    _timer = threading.Timer(300, _auto_save)
    _timer.start()
    
    return True

def _auto_save():
    """Sauvegarde automatique."""
    print("[AUTO-SAVE] Sauvegarde...")
    # Logique sauvegarde

def cleanup():
    global _timer
    if _timer:
        _timer.cancel()
```

### Feature Avec UI

```python
# extensions/ogma_ng_v2/features/statistics/__init__.py

def initialize_feature(dependencies=None):
    print("[STATS] Initialisation...")
    # Setup
    return True

def get_ui_components():
    """Ajoute bouton dans header."""
    return {
        'header_button': _create_stats_button
    }

def _create_stats_button():
    """Crée bouton statistiques."""
    from nicegui import ui
    
    def show_stats():
        # Afficher modal stats
        pass
    
    with ui.button(icon='bar_chart', on_click=show_stats):
        ui.tooltip('Statistiques OGMA')
```

### Feature Avec Magic Phrases

```python
# extensions/ogma_ng_v2/features/summarizer/__init__.py

def initialize_feature(dependencies=None):
    print("[SUMMARIZER] Initialisation...")
    return True

def check_magic_phrases(text, source="user"):
    """Détecte 'résume la conversation'."""
    import re
    patterns = [
        r"résume la conversation",
        r"fais un résumé"
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def on_magic_phrase_detected(message_data):
    """Génère résumé."""
    print("[SUMMARIZER] Génération résumé...")
    # Logique résumé
```

---

## 🔗 Intégration OGMA Core

### Hook dans ogma_ng.py

**Ajouter UNE SEULE FOIS** (déjà fait normalement) :

```python
# Dans ogma_ng.py, ligne ~100 (après imports)

# OGMA V2 Extensions (ne pas modifier sauf bugs)
try:
    from extensions.ogma_ng_v2 import register_v2_features
    
    # Préparer dépendances (après initialisation managers)
    _v2_dependencies = {
        'chat_controller': _chat_controller,
        'archiviste_controller': _archiviste_controller,
        'memory_manager': _memory_manager,
        'settings_manager': _settings_manager,
        'audio_manager': _audio_manager
    }
    
    # Enregistrer features V2
    _v2_status = register_v2_features(_v2_dependencies)
    
except ImportError:
    print("[OGMA] ℹ️  Extensions V2 non disponibles")
except Exception as e:
    print(f"[OGMA] ⚠️  Erreur chargement V2: {e}")
```

---

## 📋 Checklist Nouvelle Feature

Avant de commencer :
- [ ] Lire `CODING_RULES.md`
- [ ] Copier template TEMPLATE.py
- [ ] Choisir nom feature (snake_case)

Développement :
- [ ] Implémenter `initialize_feature()`
- [ ] Ajouter tests unitaires
- [ ] Documenter fonction publiques (docstrings)
- [ ] Créer README feature

Intégration :
- [ ] Enregistrer dans `__init__.py`
- [ ] Tester avec `python launch_ogma.py`
- [ ] Vérifier logs initialisation
- [ ] Tester fonctionnalité manuellement

Finalisation :
- [ ] Commit Git avec message clair
- [ ] Mettre à jour cette doc (si nécessaire)

---

## 🐛 Debugging

### Feature Ne Charge Pas

**Vérifier** :
1. Import correct dans `ogma_ng_v2/__init__.py` ?
2. Fonction `initialize_feature()` existe ?
3. Pas d'erreur syntax Python ?
4. Logs OGMA : `[OGMA-V2]` et `[VOTRE-FEATURE]`

**Commandes debug** :
```bash
# Vérifier imports Python
python -c "from extensions.ogma_ng_v2.features.ma_feature import initialize_feature; print('OK')"

# Lancer OGMA en mode verbose
python launch_ogma.py
```

### Feature Initialisée Mais Ne Fonctionne Pas

**Vérifier** :
1. `is_available()` retourne True ?
2. Dépendances correctement passées ?
3. Hooks UI correctement enregistrés ?
4. Logs erreurs dans console ?

---

## 📊 Métriques

**Objectifs 6 mois (Oct 2025 → Avril 2026)** :

| Métrique | Actuel | Objectif |
|----------|--------|----------|
| Features V2 | 0 | 5-10 |
| Lignes code V2 | 0 | 2000-3000 |
| Coverage tests | N/A | > 80% |
| ogma_ng.py | 7723 | ≤ 7723 (GEL) |

---

## 🎓 Bonnes Pratiques

### DO ✅

- **Isoler** : Chaque feature indépendante
- **Tester** : Tests unitaires systématiques
- **Documenter** : Docstrings + README
- **Logger** : `print("[FEATURE] message")` pour debug
- **Cleanup** : Implémenter `cleanup()` si ressources

### DON'T ❌

- **Modifier ogma_ng.py** (sauf hook 1 ligne)
- **Dépendances circulaires** entre features
- **Code spaghetti** (> 200 lignes/fonction)
- **Dupliquer code** (utiliser shared/)
- **Commit sans tests**

---

## 🆘 Support

**Questions** : Consulter documentation OGMA
**Bugs** : Vérifier logs + debugger Python
**Amélioration** : Créer issue/note

---

## 📜 Licence

Même licence que OGMA principal.

---

**Bonne création de features ! 🚀**
