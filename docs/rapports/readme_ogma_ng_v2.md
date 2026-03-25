# Extension ogma_ng_v2 — Documentation Exhaustive

**Dossier** : `extensions/ogma_ng_v2/`
**Version** : non versionné (coquille extensible)
**Rôle** : Réceptacle modulaire pour toutes les nouvelles fonctionnalités post-refactoring d'OGMA. `ogma_ng.py` étant gelé à 7723 lignes, ce sous-système permet d'ajouter de nouvelles features sans toucher au fichier principal.

---

## Contexte architectural

`ogma_ng.py` est figé à un maximum strict de 7723 lignes (convention projet). Toute nouvelle feature doit passer par :

1. Un module dans `extensions/ogma_ng_v2/features/`
2. Un enregistrement via `register_v2_features()` appelé au démarrage d'OGMA

---

## Architecture — Fichiers

| Fichier | Rôle |
|---------|------|
| `extensions/ogma_ng_v2/__init__.py` | API publique singleton, enregistrement features |
| `extensions/ogma_ng_v2/features/TEMPLATE.py` | Template copier/coller pour nouvelle feature |

---

## `__init__.py` — API Publique

**État interne module :**
```python
_registered_features: list = []     # Noms des features enregistrées
_dependencies: dict = {}            # Dépendances OGMA mémorisées
```

### Fonctions publiques

| Fonction | Paramètres | Retour | Description |
|----------|-----------|--------|-------------|
| `register_v2_features(dependencies)` | `dict` | `dict {feature_name: bool}` | Hook principal — appelé au démarrage OGMA depuis `ogma_ng.py`. Retourne résultat bool par feature. |
| `get_registered_features()` | — | `list` | Copie de `_registered_features` |
| `is_feature_available(feature_name)` | `str` | `bool` | Vérifie présence dans `_registered_features` |
| `get_version_info()` | — | `dict` | `{version, author, features_count, features}` |

### Structure du dictionnaire `dependencies`

```python
{
    "chat_controller": AIController,
    "archiviste_controller": AIController,
    "memory_manager": MemoryManager,
    "settings_manager": SettingsManager,
    "audio_manager": AudioManager
}
```

---

## `features/TEMPLATE.py` — Template Feature V2

Fichier de référence à copier pour implémenter toute nouvelle feature. Il définit le contrat minimal d'une V2 feature.

### Fonctions publiques du template

| Fonction | Retour | Description |
|----------|--------|-------------|
| `initialize_feature(dependencies)` | `bool` | Init singleton, extrait dépendances, valide `chat_controller`, retourne `True/False` |
| `is_available()` | `bool` | Lit `_is_initialized` |
| `get_ui_components()` | `dict` | Retourne composants NiceGUI : `{header_button, modal, sidebar_section}` |
| `get_feature_info()` | `dict` | `{nom, version, auteur, description, initialized, dependencies}` |
| `cleanup()` | — | Remet singleton et flag à `None/False` |
| `votre_fonction_publique()` | — | Placeholder API publique métier |
| `check_magic_phrases(text, source)` | `bool` | Détection phrases magiques pour activer la feature |

### Convention de nommage

Chaque feature doit respecter :
- Singleton global `_instance : Optional[FeatureClass] = None`
- Flag `_is_initialized : bool = False`
- Fonction `initialize_*()` retournant `bool`
- Fonction `cleanup()` remettant tout à zéro

---

## Intégration dans `ogma_ng.py`

Appel unique au démarrage OGMA (dans la fonction d'initialisation) :

```python
from extensions.ogma_ng_v2 import register_v2_features

results = register_v2_features({
    "chat_controller": _chat_controller,
    "archiviste_controller": _archiviste_controller,
    "memory_manager": _memory_manager,
    "settings_manager": _settings_manager,
    "audio_manager": _audio_manager
})
# results = {"feature_a": True, "feature_b": False, ...}
```

---

## Extension avec une nouvelle feature

1. Copier `features/TEMPLATE.py` → `features/ma_feature.py`
2. Implémenter les 6 fonctions publiques
3. Dans `register_v2_features()` de `__init__.py`, ajouter :
   ```python
   from extensions.ogma_ng_v2.features.ma_feature import initialize_feature as init_ma_feature
   results["ma_feature"] = init_ma_feature(dependencies)
   ```

---

## État actuel (v2.2)

Aucune feature V2 concrète enregistrée à ce jour — le système est une **coquille vide extensible**. Toutes les features actuelles d'OGMA sont implémentées dans `extensions/` directement ou dans `ogma_ng.py`.
