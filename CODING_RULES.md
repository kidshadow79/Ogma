# 📜 RÈGLES DE DÉVELOPPEMENT OGMA

**Date de création** : 25 octobre 2025  
**Statut** : ACTIF - Application stricte obligatoire  
**Objectif** : Geler la croissance du monolithe ogma_ng.py

---

## 🚫 INTERDICTIONS STRICTES

### 1. Modification ogma_ng.py
**INTERDIT** :
- ❌ Ajouter de nouvelles fonctions dans ogma_ng.py
- ❌ Ajouter de nouvelles classes dans ogma_ng.py
- ❌ Augmenter la taille du fichier (sauf bugs critiques)

**AUTORISÉ UNIQUEMENT** :
- ✅ Correction de bugs critiques
- ✅ Ajout de hooks (1-2 lignes max) pour extensions V2
- ✅ Mise à jour commentaires/documentation

### 2. Fonctions Trop Longues
**LIMITE HARD** : Aucune fonction > 200 lignes

**Si dépassé** :
- Découper en plusieurs fonctions
- OU créer extension dédiée

### 3. Code Dupliqué
**INTERDIT** :
- ❌ Copy-paste code existant
- ❌ Dupliquer logique entre extensions

**SOLUTION** :
- ✅ Créer helper partagé dans `extensions/ogma_ng_v2/shared/`

---

## ✅ RÈGLES OBLIGATOIRES

### 1. Nouvelle Feature = Extension V2

**Toute nouvelle fonctionnalité DOIT être créée dans** :
```
extensions/ogma_ng_v2/features/[nom_feature]/
```

**Jamais directement dans ogma_ng.py !**

### 2. Structure Standard Extension

Chaque feature suit ce pattern :
```
extensions/ogma_ng_v2/features/ma_feature/
├── __init__.py              # API publique
├── core.py                  # Logique métier
├── ui_components.py         # Interface (optionnel)
├── config.py                # Configuration (optionnel)
└── README.md                # Documentation
```

### 3. Tests Obligatoires

Chaque feature DOIT avoir :
- ✅ Tests unitaires (`test_[feature].py`)
- ✅ Tests d'intégration avec OGMA
- ✅ Validation manuelle documentée

### 4. Documentation Inline

**Obligatoire** :
- Docstrings pour toutes les fonctions publiques
- Commentaires pour logique complexe
- README.md pour chaque feature

---

## 📏 LIMITES TECHNIQUES

### Taille Fichiers

| Fichier | Limite Actuelle | Limite Max | Action si Dépassé |
|---------|-----------------|------------|-------------------|
| `ogma_ng.py` | 7723 lignes | **8000 lignes** | ⛔ CLEANUP OBLIGATOIRE |
| Feature V2 | N/A | 500 lignes | Découper en modules |
| Fonction | N/A | 200 lignes | Refactoring obligatoire |

### Complexité

**Indicateurs surveillance** :
- Nombre de fonctions dans ogma_ng.py : **Ne pas augmenter**
- Nombre de variables globales : **Ne pas augmenter**
- Profondeur imbrication : Max 4 niveaux

---

## 🎯 WORKFLOW DÉVELOPPEMENT

### Créer Nouvelle Feature

**ÉTAPES** :

1. **Créer dossier feature** :
   ```bash
   mkdir extensions/ogma_ng_v2/features/ma_feature
   ```

2. **Copier template** :
   ```bash
   cp extensions/ogma_ng_v2/features/TEMPLATE.py extensions/ogma_ng_v2/features/ma_feature/__init__.py
   ```

3. **Coder dans l'extension** (PAS dans ogma_ng.py)

4. **Ajouter hook** dans `extensions/ogma_ng_v2/__init__.py` :
   ```python
   from .features.ma_feature import initialize_feature
   
   def register_v2_features():
       # ... autres features
       initialize_feature(dependencies)
   ```

5. **Tester** :
   ```bash
   python test_ma_feature.py
   python launch_ogma.py  # Vérifier intégration
   ```

6. **Commit Git** :
   ```bash
   git add extensions/ogma_ng_v2/features/ma_feature/
   git commit -m "feat(v2): Add ma_feature"
   ```

### Modifier Feature Existante

**SI la feature est dans ogma_ng.py** :
- ❌ Ne PAS modifier directement
- ✅ Créer version V2 dans extension
- ✅ Garder ancienne version (compatibilité)

**SI la feature est dans extension V2** :
- ✅ Modifier librement
- ✅ Tester après modification
- ✅ Commit avec message clair

### Corriger Bug

**SI bug dans ogma_ng.py** :
- ✅ Correction autorisée (minimal)
- ✅ Ajouter test régression
- ✅ Documenter le fix

**SI bug dans extension V2** :
- ✅ Corriger dans extension
- ✅ Tester
- ✅ Commit

---

## 🔍 REVIEWS MENSUELS

### Checklist Mensuelle

**À vérifier chaque mois** :

- [ ] ogma_ng.py < 8000 lignes ?
- [ ] Aucune fonction > 200 lignes ajoutée ?
- [ ] Toutes features récentes dans V2 ?
- [ ] Tests passent (100%) ?
- [ ] Documentation à jour ?

### Actions si Dépassement

**SI ogma_ng.py > 8000 lignes** :
1. ⛔ STOP développement features
2. 🧹 Cleanup obligatoire :
   - Supprimer code mort
   - Extraire fonctions vers V2
   - Simplifier logique
3. ✅ Retour sous 7800 lignes
4. 🚀 Reprendre développement

---

## 📚 RESSOURCES

### Templates
- `extensions/ogma_ng_v2/features/TEMPLATE.py` - Template feature standard

### Documentation
- `CARTOGRAPHIE_OGMA_COMPLETE.md` - Architecture OGMA complète
- `REFACTORING_LESSONS_LEARNED.md` - Leçons refactoring échec

### Guides
- `extensions/ogma_ng_v2/README.md` - Guide OGMA V2

---

## 🎓 PHILOSOPHIE

### Principes Fondamentaux

**1. Gel du Monolithe**
> "ogma_ng.py est COMPLET. Toute évolution = Extension V2."

**2. Modularité Progressive**
> "Nouvelles features isolées, testables, désactivables."

**3. Pragmatisme**
> "Code qui marche > Code parfait. Mais code organisé > Code spaghetti."

**4. Documentation > Perfection**
> "Un monolithe documenté vaut mieux qu'une architecture propre incompréhensible."

### Citations Inspirantes

> "Perfection is the enemy of good" - Voltaire

> "Make it work, make it right, make it fast" - Kent Beck

> "The best code is no code at all" - Jeff Atwood

---

## ⚠️ EXCEPTIONS

### Quand Modifier ogma_ng.py ?

**CAS AUTORISÉS** :
1. **Bug critique** bloquant utilisation OGMA
2. **Sécurité** (faille critique)
3. **Performance** (optimisation critique <5% fichier)
4. **Hook V2** (1-2 lignes pour nouvelle extension)

**PROCÉDURE** :
1. Créer issue/note décrivant modification
2. Estimer impact (lignes ajoutées/modifiées)
3. Valider nécessité (vraiment critique ?)
4. Modifier MINIMALEMENT
5. Tester exhaustivement
6. Documenter changement
7. Commit avec justification détaillée

---

## 📊 MÉTRIQUES DE SUCCÈS

### Objectifs 6 Mois (Octobre 2025 → Avril 2026)

| Métrique | Actuel | Objectif 6 mois |
|----------|--------|-----------------|
| **ogma_ng.py** | 7723 lignes | ≤ 7723 lignes (GEL) |
| **Extensions V2** | 0 lignes | 2000-3000 lignes |
| **Features V2** | 0 | 5-10 features |
| **Coverage tests V2** | N/A | > 80% |

### KPIs

**Indicateurs surveillance** :
- ✅ `ogma_ng.py` : Aucune augmentation taille
- ✅ Nouvelles features : 100% dans V2
- ✅ Tests : Couverture > 80% V2
- ✅ Bugs : < 5% viennent d'extensions V2

---

## 🚀 CONCLUSION

**CES RÈGLES SONT NON-NÉGOCIABLES**

Pourquoi ?
- ✅ Garantir stabilité ogma_ng.py (FONCTIONNE)
- ✅ Permettre innovation (V2 sans limite)
- ✅ Faciliter maintenance (code isolé)
- ✅ Éviter répétition échec refactoring

**OGMA V2 = L'avenir. ogma_ng.py = Le passé stable.**

---

**Auteur** : Tytan  
**Dernière mise à jour** : 25 octobre 2025  
**Version** : 1.0  
**Status** : ACTIF ✅
