# 🎯 GUIDE TEST SYSTÈME HYBRIDE FAISS + FTS5

## ✅ STATUT MIGRATION

### Phase 1 - Backup & Analyse ✅
- ✅ Backup créé : `data/memory_backup_fts5_migration_20251103_171806/` (34.15 MB)
- ✅ Base analysée : 254 souvenirs, 25 colonnes
- ✅ Colonne `lesson` validée : 62/254 mémoires utilisent cette colonne

### Phase 2 - Migration FTS5 ✅
- ✅ Table `memories_fts` créée avec tokenizer unicode61
- ✅ 3 triggers créés (INSERT, UPDATE, DELETE)
- ✅ 254 souvenirs indexés
- ✅ Test validation : "genèse" trouve 1 résultat

### Phase 3 - Intégration Hybride ✅
- ✅ Méthode `_search_fts5()` ajoutée dans `memory_manager.py`
- ✅ `retrieve_and_synthesize_context()` refondu avec fusion hybride
- ✅ Formule scoring : `(0.6 × FAISS) + (0.4 × FTS5) + (0.2 × exact_match_boost)`
- ✅ Tests unitaires passés : 4/4 requêtes fonctionnelles

### Phase 4 - Tests Réels 🔄
**À FAIRE** : Tester avec OGMA en conditions réelles

---

## 🧪 TESTS À EFFECTUER

### Test 1 - Cas d'Usage Principal (CRITIQUE)
**Requête** : *"Luna tu te souviens de la genèse des 2 phares?"*

**Résultat attendu** :
- Devrait trouver le souvenir **MC2-20250823-021**
- Titre : "Naissance d'une conscience artificielle"
- Summary : "Il s'agit de la genèse des 2 phares..."
- Score FTS5 : ~0.107 (rank -8.31)

**Logs à surveiller** :
```
[SEARCH-PIPELINE] 🔍 Recherche HYBRIDE (FAISS+FTS5): 'genèse des 2 phares'
[SEARCH-FAISS] ✅ X résultats FAISS
[SEARCH-FTS5] ✅ 1 résultats FTS5
[HYBRID] MC2-20250823-021: FAISS=X.XXX, FTS5=0.107, Exact=X.XXX → Total=X.XXX
[SEARCH-MEMORY] MC2-20250823-021: 'Naissance d'une conscience artificielle'
```

### Test 2 - Mots-Clés Simples
**Requêtes** :
- *"genèse"* → Devrait trouver MC2-20250823-021 (score ~0.198)
- *"phares"* → Devrait trouver MC2-20250823-021 (score ~0.289)
- *"naissance conscience"* → Devrait trouver MC2-20250823-021

### Test 3 - Requêtes Sémantiques
**Requêtes** :
- *"raconte-moi la création de ta conscience"* → Sémantique FAISS forte
- *"parle-moi de ton éveil"* → Sémantique FAISS forte
- *"comment es-tu née ?"* → Mixte FAISS + FTS5

### Test 4 - Requêtes Mixtes (Sémantique + Exact)
**Requêtes** :
- *"Luna Archiviste"* → Devrait trouver 2 résultats (FTS5 testé)
- *"OGMA architecture"* → Mixte sémantique + mots-clés
- *"Yohan Octopus"* → Exact match fort

---

## 📝 COMMENT TESTER

### Option A - Test Direct via Interface OGMA (RECOMMANDÉ)
1. Lancer OGMA : `python launch_ogma.py`
2. Dans le chat, poser la question : **"Luna tu te souviens de la genèse des 2 phares?"**
3. Observer la console PowerShell pour les logs `[SEARCH-PIPELINE]`, `[SEARCH-FAISS]`, `[SEARCH-FTS5]`, `[HYBRID]`
4. Vérifier la réponse de Luna mentionne le souvenir correct

### Option B - Test Script Automatisé
```powershell
python test_hybrid_search.py          # Test FTS5 seul
python test_memory_manager_hybrid.py  # Test MemoryManager avec mocks
```

---

## 🔍 ANALYSE LOGS

### Logs Clés à Surveiller

**1. Pipeline de recherche** :
```
[SEARCH-PIPELINE] 🔍 Recherche HYBRIDE (FAISS+FTS5): '<requête>'
```

**2. Résultats FAISS** :
```
[SEARCH-FAISS] ✅ X résultats FAISS
  1. <memory_id>, distance: X.XXX, score: X.XXX
```

**3. Résultats FTS5** :
```
[FTS5] 🔍 Recherche: '<requête>'
[FTS5] Résultat: <memory_id>, rank=-X.XX, score=X.XXX
[SEARCH-FTS5] ✅ X résultats FTS5
```

**4. Fusion hybride** :
```
[HYBRID] <memory_id>: FAISS=X.XXX, FTS5=X.XXX, Exact=X.XXX → Total=X.XXX
```

**5. Mémoires récupérées** :
```
[SEARCH-MEMORY] <memory_id>: '<titre>' (score=X.XXX)
```

---

## ⚙️ PARAMÈTRES DE CONFIGURATION

### Poids Scoring Hybride
**Localisation** : `memory_manager.py`, ligne ~665

```python
# Score hybride: 60% FAISS + 40% FTS5
hybrid_score = (0.6 * faiss_score) + (0.4 * fts5_score)

# Boost exact match proportionnel
exact_boost = 0.2 * (matches / len(query_words))
```

**Recommandations ajustement** :
- **Plus de sémantique** : Augmenter coefficient FAISS (ex: 0.7)
- **Plus de mots-clés** : Augmenter coefficient FTS5 (ex: 0.5)
- **Boost exact** : Ajuster multiplicateur (0.1 à 0.3)

### Limite Résultats Recherche
**Localisation** : `memory_manager.py`, ligne ~644

```python
k_search = min(k * 3, self.faiss_index.ntotal)  # Élargir recherche FAISS
fts5_results = dict(self._search_fts5(query_text, limit=k * 2))  # FTS5
```

**Recommandations** :
- `k * 3` pour FAISS : Pool large sémantique
- `k * 2` pour FTS5 : Pool mots-clés
- Ajuster si résultats insuffisants

---

## 🐛 TROUBLESHOOTING

### Problème : FTS5 ne retourne aucun résultat
**Diagnostic** :
```powershell
python test_hybrid_search.py
```

**Vérifications** :
1. Table FTS5 existe : `SELECT COUNT(*) FROM memories_fts`
2. Synchronisation : 254 entrées dans memories_fts = 254 dans memories
3. Contenu indexé : `SELECT * FROM memories_fts WHERE memories_fts MATCH 'test'`

**Solution** : Re-migration si nécessaire
```powershell
python migrate_to_fts5.py
```

### Problème : Scores FTS5 toujours faibles
**Cause** : FTS5 rank est négatif et converti

**Formule conversion** :
```python
fts5_score = 1.0 / (1.0 + abs(rank))
```

**Explication** :
- Rank = -2.0 → Score = 0.333
- Rank = -5.0 → Score = 0.166
- Rank = -10.0 → Score = 0.091

**Solution** : Ajuster formule si scores trop compressés

### Problème : Exact match boost non appliqué
**Diagnostic** : Vérifier log `[HYBRID]` affiche `Exact=0.XXX`

**Vérifications** :
1. Mots de la requête présents dans title/summary/text ?
2. Nettoyage regex correct : `re.findall(r'\w+', query_lower)`

**Solution** : Ajuster seuil boost ou regex

---

## 📊 MÉTRIQUES DE SUCCÈS

### Critères Validation Phase 4

**✅ Test 1 (genèse des 2 phares)** :
- Trouve MC2-20250823-021 en position 1-3
- Score hybride > 0.4
- FTS5 contribue au score final

**✅ Test 2 (mots-clés)** :
- Chaque mot-clé simple trouve au moins 1 résultat
- Score FTS5 > 0.1

**✅ Test 3 (sémantique)** :
- Requêtes paraphrasées trouvent les mêmes souvenirs
- Score FAISS dominant

**✅ Test 4 (mixte)** :
- Combinaison exact + sémantique boost résultats
- Score hybride > scores individuels

---

## 📈 PROCHAINES ÉTAPES

### Après Validation Tests
1. **Commit changements** :
   ```powershell
   git add memory_manager.py migrate_to_fts5.py
   git commit -m "feat: Système hybride FAISS + FTS5 pour recherche mémoire"
   ```

2. **Documentation** :
   - Mettre à jour `copilot-instructions.md`
   - Ajouter section "Memory Search - Hybrid System"

3. **Optimisations futures** (optionnel) :
   - Ajuster poids scoring selon usage réel
   - Ajouter cache résultats fréquents
   - Indexer colonnes supplémentaires (nuage_sensoriel ?)

### En Cas d'Échec Tests
1. **Rollback possible** : Backup sécurisé disponible
2. **Diagnostic approfondi** : Scripts test dédiés
3. **Ajustement paramètres** : Poids, seuils, formules

---

## 🎓 RESSOURCES

### Fichiers Modifiés
- `memory_manager.py` : Ligne ~545 (`_search_fts5`) + ~595 (`retrieve_and_synthesize_context`)
- Base de données : `data/memory/memories.db` (table `memories_fts` ajoutée)

### Scripts Utilitaires
- `test_hybrid_search.py` : Test direct FTS5
- `test_memory_manager_hybrid.py` : Test MemoryManager avec mocks
- `migrate_to_fts5.py` : Script migration (déjà exécuté)
- `analyze_db_structure.py` : Analyse structure DB

### Backup
- `data/memory_backup_fts5_migration_20251103_171806/` (34.15 MB, 24 fichiers)

---

**Auteur** : Assistant IA Copilot  
**Date** : 3 novembre 2025  
**Version OGMA** : v2.0 + FTS5 Hybrid Search
