# OGMA NG V2 — Architecture extensible post-refactoring

**Source vérifiée** : `extensions/ogma_ng_v2/__init__.py`

---

## Concept

`ogma_ng.py` est le fichier orchestrateur principal d'OGMA. Avec la croissance organique du projet, ce fichier a atteint une taille limite (`7723 lignes max`). Toute nouvelle fonctionnalité ajoutée directement à `ogma_ng.py` rendrait le fichier ingérable.

L'extension `ogma_ng_v2/` est la réponse architecturale : un espace isolé pour toutes les nouvelles fonctionnalités post-refactoring, sans toucher au fichier principal.

---

## Structure

```
extensions/ogma_ng_v2/
├── features/     → Fonctionnalités complètes, isolées
├── shared/       → Code partagé entre features
└── templates/    → Templates pour nouvelles features
```

Chaque feature dans `features/` est un module autonome qui :
1. Importe ce dont il a besoin depuis `ogma_ng` via `sys.modules`
2. Ne modifie pas directement `ogma_ng.py`
3. Suit le pattern singleton standard des extensions OGMA

---

## Règle d'or

> "ogma_ng.py est GELÉ. Toute nouvelle feature → extensions/ogma_ng_v2/features/"

Cette contrainte volontaire garantit que le fichier orchestrateur reste stable et lisible, tandis que les nouvelles fonctionnalités peuvent être développées, testées et supprimées sans risque de régression.
