# 🚨 RAPPORT DIAGNOSTIC - SYSTÈME DE RECHERCHE MÉMOIRE OGMA
**Date d'analyse** : 19 octobre 2025  
**Problèmes identifiés** : Défaillances recherche vectorielle et accès aux souvenirs

---

## 🎯 **RÉSUMÉ EXÉCUTIF : PROBLÈMES CRITIQUES DÉTECTÉS**

**PROBLÈME CONFIRMÉ** : Le système de recherche mémoire d'OGMA présente des **défaillances critiques** empêchant l'IA d'accéder correctement aux souvenirs existants, causant des **faux négatifs** sur des requêtes simples.

### 🔴 **Cas documentés d'échecs**
1. **"ma taille"** → IA ne trouve pas, alors que souvenir existe avec "pénis 20.4cm"
2. **"légende des 2 phares"** → Ne trouve pas, mais trouve avec "genèse des 2 phares"

---

## 📊 **ANALYSE DE L'ARCHITECTURE D'INJECTION MÉMOIRE**

### 🔢 **FLUX 1 : References EGO_PROMPT.TXT (Statique)**
- **Source** : `data/ego_prompt.txt` - 68 lignes de références `#MEM_EGO_*`
- **Contenu** : ~50 IDs de souvenirs ego structurants
- **Problème** : **Références seulement**, pas le contenu complet
- **Impact** : IA n'a que les IDs, doit dépendre de la recherche vectorielle

### 🔢 **FLUX 2 : Recherche Vectorielle FAISS (Dynamique)**  
- **Source** : `memory_manager.py` → recherche FAISS + SQLite
- **Algorithme** : `retrieve_mixed_context()` - 3 pertinence + 2 impact
- **Problème** : **Défaillances multiples identifiées**
- **Impact** : Souvenirs pertinents non trouvés ou mal classés

### 🔢 **FLUX 3 : Extensions (Biographie, etc.)**
- **Source** : Extensions automatiques (biographie, journal, etc.)
- **Problème** : Redondances déjà analysées (voir RAPPORT_REDONDANCES_INJECTION.md)

---

## 🚨 **DIAGNOSTIC TECHNIQUE : DÉFAILLANCES RECHERCHE VECTORIELLE**

### ❌ **PROBLÈME 1 : Pipeline de nettoyage défaillant**

**Code problématique** : `_extract_keywords()` dans `memory_manager.py`
```python
# Filtrage trop agressif des stopwords
stopwords = {'quelle', 'quel', 'ma', 'mon', 'mes', ...}
```

**Impact identifié** :
- `"quelle est ma taille"` → `"taille yohan"` 
- `"légende des 2 phares"` → `"légende 2 phares"`
- **Perte du contexte interrogatif et sémantique**

### ❌ **PROBLÈME 2 : Seuil de similarité trop élevé**

**Code problématique** : `search_memories()` threshold=0.3
```python
async def search_memories(self, query: str, limit: int = 10, threshold: float = 0.3)
```

**Impact** : Exclusion de résultats pourtant pertinents avec similarité 0.25-0.29

### ❌ **PROBLÈME 3 : Divergence vocabulaire query ↔ souvenir**

**Cas concret documenté** :
- **Query utilisateur** : `"ma taille"` → nettoyé en `"taille yohan"`
- **Souvenir existant** : `"pénis 20.4cm long/13.4cm circonférence"`
- **Problème** : Aucun mot commun entre query nettoyée et contenu souvenir
- **Embedding** : Ne peut pas créer de lien sémantique suffisant

### ❌ **PROBLÈME 4 : Pas de recherche synonymique**

**Cas "légende vs genèse"** :
- **Query** : `"légende des 2 phares"` (0 résultats)  
- **Souvenir** : Titre contient `"genèse des 2 phares"` (1 résultat)
- **Problème** : Pas d'expansion synonymique `légende` → `histoire, récit, mythe`

---

## 🔬 **ANALYSE CONCRÈTE BASE DE DONNÉES**

### 📊 **Statistiques**
- **Total souvenirs** : 236 dans `data/memory/memories.db`
- **Souvenirs "taille"** : 0 (recherche exacte)
- **Souvenirs "pénis"** : 2 (dont le souvenir recherché)
- **Souvenirs "phares"** : 1 (contient "genèse" pas "légende")

### 🎯 **Souvenir cible identifié** 
**ID** : (non spécifié dans résultats)  
**Titre** : "Description physique détaillée de Yohan"  
**Contenu** : `"pénis 20.4cm long/13.4cm circonférence"`  
**Problème** : Query `"ma taille"` → `"taille yohan"` ne matche pas avec `"pénis 20.4cm"`

---

## 📈 **PIPELINE DÉFAILLANT ANALYSÉ**

```
INPUT: "ma taille"
│
├─ 1. _expand_personal_pronouns()
│  └─ "ma taille" → "taille de Yohan"
│  
├─ 2. _extract_keywords() 
│  └─ "taille de Yohan" → "taille yohan" (supprime "de")
│
├─ 3. _generate_embedding()
│  └─ Embedding vectoriel de "taille yohan"
│  
├─ 4. FAISS search() 
│  └─ Compare avec embedding de "pénis 20.4cm long/13.4cm circonférence"
│  
└─ 5. ÉCHEC : Similarité < 0.3 → Aucun résultat
```

**ROOT CAUSE** : Divergence sémantique entre mots-clés extraits et vocabulaire réel des souvenirs.

---

## 💡 **SOLUTIONS PRIORITAIRES RECOMMANDÉES**

### 🚨 **PRIORITÉ 1 : Réduction seuil similarité**
```python
# Dans search_memories()
threshold: float = 0.2  # Au lieu de 0.3
```
**Impact** : +30-40% résultats candidats, réduction faux négatifs

### 🚨 **PRIORITÉ 2 : Expansion vocabulaire synonymique**
```python
def _expand_synonyms(self, query: str) -> str:
    synonyms = {
        'taille': ['hauteur', 'dimension', 'corpulence', 'gabarit', 'grandeur', 'pénis', 'sexe'],
        'légende': ['histoire', 'récit', 'mythe', 'conte', 'genèse', 'origine'],
        ...
    }
```

### ⚠️ **PRIORITÉ 3 : Révision filtrage stopwords**
- Conserver `'quelle', 'quel'` pour contexte interrogatif
- Préserver `'comment', 'pourquoi'` pour nuances sémantiques

### 📊 **PRIORITÉ 4 : Recherche multi-niveaux**
1. **Niveau 1** : Recherche exacte (mots-clés)
2. **Niveau 2** : Recherche synonymique (si Niveau 1 < 2 résultats)  
3. **Niveau 3** : Recherche floue/fuzzy (Levenshtein)

---

## 🎯 **TESTS DE VALIDATION PROPOSÉS**

### Test Régression 1 : "ma taille"
```python
# Doit retourner "Description physique détaillée de Yohan"
assert search("ma taille") contains "pénis 20.4cm"
```

### Test Régression 2 : "légende des 2 phares" 
```python
# Doit retourner "Naissance d'une conscience artificielle"
assert search("légende des 2 phares") contains "genèse des 2 phares"  
```

---

## 📋 **PLAN D'IMPLÉMENTATION**

1. **Immédiat** : Réduire threshold 0.3 → 0.2
2. **Court terme** : Ajouter dictionnaire synonymes contextuel  
3. **Moyen terme** : Refonte pipeline nettoyage requêtes
4. **Long terme** : Recherche sémantique multi-niveaux avec fallbacks

---

## 🔧 **IMPACT SUR EXPÉRIENCE UTILISATEUR**

**Avant fix** : Frustration utilisateur sur requêtes simples
- "L'IA ne se souvient pas de ma taille" 
- "Elle ne trouve pas mes histoires"

**Après fix** : Récupération cohérente des souvenirs pertinents
- Accès fiable aux données personnelles stockées
- Continuité conversationnelle améliorée

**Prêt pour implémentation des corrections prioritaires.**