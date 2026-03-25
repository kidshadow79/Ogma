# 🔥 ANALYSE: Surconsommation Tokens Archiviste (10x vs Luna)

**Date**: Décembre 2025  
**Problème rapporté**: L'Archiviste consomme ~10x plus de tokens INPUT que Luna  
**Impact**: Coûts API très élevés, ralentissements

---

## 📊 Diagnostic Technique

### Configuration Actuelle

**Luna (chat_api)**:
- Provider: GROK
- Model: grok-4-1-fast-non-reasoning
- Temperature: 0.7
- **1 appel par message utilisateur**

**Archiviste (reasoning_api)**:
- Provider: GROK  
- Model: grok-4-fast-non-reasoning
- Temperature: 0.7
- **4+ appels par message utilisateur**

### Taille des Prompts Système

```
instructions     : 4,039 chars → ~1,009 tokens
memorization     : 2,847 chars → ~711 tokens  
injection        : 2,846 chars → ~711 tokens ⚠️
perception       : 2,892 chars → ~723 tokens
salutations      : 1,850 chars → ~462 tokens
temporal_guardian: 2,953 chars → ~738 tokens
─────────────────────────────────────────────
TOTAL            : 17,427 chars → ~4,356 tokens
```

### Flux d'Appels Archiviste par Message

Pour **chaque** message utilisateur, l'Archiviste est appelé **minimum 4 fois**:

1. **Analyse sémantique** (optimizer)
   - Fonction: `analyze_message_semantic`
   - Prompt: ~711 tokens (injection)
   - But: Extraction mots-clés et catégories

2. **Synthèse souvenirs** (memory synthesis)
   - Fonction: `_call_archiviste_synthesis`
   - Prompt: ~711 tokens (injection) + 500-2000 tokens (contexte JSON souvenirs)
   - But: Créer note contextuelle depuis mémoire FAISS

3. **Analyse temporelle** (temporal_guardian)
   - Fonction: `analyze_with_archiviste`
   - Prompt: ~738 tokens (temporal_guardian) + 300 tokens (données tempo)
   - But: Instructions comportementales (fatigue, réflexion, etc.)

4. **Capability Advisor** (suggestions)
   - Fonction: `analyze_conversation`
   - Prompt: ~711 tokens (injection) + 200 tokens (contexte)
   - But: Suggérer capacités pertinentes

### Estimation Consommation Réelle

**Par appel Archiviste**:
```
Prompt système     : 700-750 tokens
Contexte JSON      : 200-2000 tokens (souvenirs, historique, données)
Message utilisateur: 50-200 tokens
─────────────────────────────────────
TOTAL INPUT/appel  : 950-2950 tokens
```

**Par message utilisateur (4 appels)**:
```
INPUT total : 3,800-11,800 tokens
OUTPUT total: 800-2,000 tokens (synthèses courtes)
─────────────────────────────────────
TOTAL       : 4,600-13,800 tokens
```

**Luna (1 appel)**:
```
INPUT  : 2,000-2,500 tokens
OUTPUT : 200-800 tokens
─────────────────────────────────────
TOTAL  : 2,200-3,300 tokens
```

**Ratio réel Archiviste/Luna**:
- **Cas minimal**: 4,600 / 3,300 = **1.4x**
- **Cas moyen**: 8,000 / 2,750 = **2.9x**
- **Cas lourd** (nombreux souvenirs, longs contextes): 13,800 / 2,200 = **6.3x**
- **Cas extrême** (fulltext memories, longs prompts): **Peut atteindre 10x+**

---

## 🎯 Causes Identifiées

### 1. **Prompts Système Trop Verbeux**
- Le prompt `injection` fait **2,846 caractères** (~711 tokens)
- Répété dans 3 des 4 appels (semantic, synthesis, capability)
- Contient beaucoup d'explications détaillées qui pourraient être condensées

### 2. **Multiples Appels Redondants**
- 4 appels minimum par message utilisateur
- Chaque appel répète le **prompt système complet**
- Pas de réutilisation du contexte entre appels

### 3. **Contexte JSON Volumineux**
- Les souvenirs sont passés avec **TOUS** les champs:
  ```json
  {
    "titre": "...",
    "résumé": "...",
    "score": 0.95,
    "impact": 180,
    "valence": 1,
    "date": "2025-12-01T14:30:00",
    "texte_original": "... (peut être TRÈS long) ..."
  }
  ```
- Pour 5-10 souvenirs, ça fait facilement 1500-3000 tokens

### 4. **Pas de Prompt Caching**
- GROK supporte le prompt caching mais OGMA ne l'utilise pas
- Les prompts système sont reconstruits à chaque appel
- Économie potentielle: 50-90% sur les tokens INPUT

---

## 💡 Optimisations Proposées

### ✅ Niveau 1: Quick Wins (Gain ~40-60%)

#### 1.1. Compacter les Prompts Système

**Prompt `injection` actuel** (2,846 chars):
```
Tu es l'administrateur de conscience de L'IA principale. Ton rôle est de 
sélectionner et présenter les souvenirs les plus pertinents pour éclairer 
la conversation en cours.

🎯 Mission Principale

Consulter la mémoire de l'IA principale et injecter les souvenirs qui peuvent :
- Éviter une incohérence avec son vécu passé
- Rappeler un moment structurant lié au contexte
[... 2000+ chars de plus ...]
```

**Version compactée** (~600 chars, -78%):
```
Admin conscience IA: sélectionne souvenirs pertinents pour contexte actuel.

Critères injection:
- Cohérence vécu
- Moments structurants
- Pertinence contextuelle
- Détection redondance

Analyse tempo: fatigue/réflexion/interruption/rythme

Format:
- Standards (≤95): synthèse brève
- Haut impact (>95): [MÉMOIRE HAUTE IMPACT | texte_original]
- Annotation émotionnelle si valence≠0 ou impact>150

Directives: guider subtilement, préserver identité, enrichir dialogue.
```

**Gain estimé**: 2,246 chars → ~561 tokens économisés **par appel**

#### 1.2. Simplifier Contexte JSON Souvenirs

**Actuel**:
```json
{
  "titre": "Adoption de Willow le chat",
  "résumé": "Chat. Willow. Adoption 2020. Lyon.",
  "score": 0.95,
  "impact": 180,
  "valence": 1,
  "date": "2025-12-01T14:30:00",
  "texte_original": "En décembre 2020, j'ai adopté un magnifique chat roux..."
}
```

**Version compacte**:
```json
{
  "t": "Adoption Willow",
  "s": 0.95,
  "i": 180,
  "v": 1,
  "d": "2025-12-01",
  "txt": "Décembre 2020: adopté chat roux..."
}
```

**Gain estimé**: ~40% réduction sur contexte JSON → 200-800 tokens économisés

#### 1.3. Fusionner Appels Similaires

Au lieu de:
1. Appel semantic analysis (711 tokens prompt)
2. Appel synthesis (711 tokens prompt)
3. Appel temporal (738 tokens prompt)
4. Appel capability (711 tokens prompt)

**Faire 1 seul appel Archiviste** avec prompt unifié:
```
Tu es l'Archiviste. Analyse ce message et fournis:
1. Mots-clés sémantiques
2. Synthèse souvenirs pertinents
3. Directive comportementale (tempo)
4. Suggestion capacité (si pertinent)

Format JSON:
{
  "keywords": [...],
  "synthesis": "...",
  "behavior": "NORMAL|directive",
  "capability": null|{...}
}
```

**Gain estimé**: 2871 tokens (4 prompts) → 750 tokens (1 prompt) = **-74%**

### ✅ Niveau 2: Optimisations Avancées (Gain ~60-80%)

#### 2.1. Implémenter Prompt Caching

GROK supporte le prompt caching (probablement via `cache_control` comme Claude):

```python
messages = [
    {
        "role": "system",
        "content": PROMPT_ARCHIVISTE_COMPACT,
        "cache_control": {"type": "ephemeral"}  # Cache ce prompt
    },
    {
        "role": "user",
        "content": f"Message: {user_message}\nSouvenirs: {memories_json}"
    }
]
```

**Gain estimé**: 
- Premier appel: coût normal
- Appels suivants (cache hit): **90% réduction** sur tokens prompt système
- Réduction globale: ~50-70%

#### 2.2. Déduplication Intelligente des Appels

Éviter d'appeler l'Archiviste si:
- Message très court (<10 mots) → pas d'analyse sémantique nécessaire
- Pas de souvenirs pertinents (FAISS score <0.5) → pas de synthèse
- Rythme normal détecté → pas d'analyse temporelle
- Aucune capacité pertinente → pas de capability advisor

**Gain estimé**: ~30% des messages nécessitent vraiment les 4 appels

#### 2.3. Batch Requests (si API supporte)

Grouper les 4 appels en 1 seule requête API:

```python
# Au lieu de 4 appels séquentiels
results = await asyncio.gather(
    archiviste.analyze_semantic(msg),
    archiviste.synthesize(msg, memories),
    archiviste.analyze_temporal(msg, tempo_data),
    archiviste.suggest_capability(msg, history)
)

# Faire 1 appel avec prompt multi-tâche
result = await archiviste.unified_analysis(
    message=msg,
    memories=memories,
    temporal_data=tempo_data,
    conversation_history=history
)
```

**Gain estimé**: Réduit latence + potentiellement moins de tokens répétés

---

## 🚀 Plan d'Implémentation Recommandé

### Phase 1: Optimisations Immédiates (1-2h)
1. **Compacter prompt `injection`** (2846 → 600 chars)
2. **Simplifier JSON souvenirs** (clés courtes)
3. **Ajouter option pour désactiver capability advisor** (pas toujours nécessaire)

**Gain attendu**: ~40-50% réduction tokens INPUT

### Phase 2: Refactoring Architecture (3-5h)
1. **Fusionner 4 appels en 1 appel unifié**
2. **Implémenter prompt caching** (si GROK supporte)
3. **Déduplication intelligente** (skip appels non nécessaires)

**Gain attendu**: ~70-80% réduction tokens INPUT

### Phase 3: Monitoring et Fine-Tuning (ongoing)
1. **Dashboard métriques tokens** (INPUT/OUTPUT par composant)
2. **A/B testing** prompts compacts vs verbeux
3. **Alertes** si consommation dépasse seuils

---

## 📈 Impact Estimé

### Scénario Conservateur (Phase 1 uniquement)
- **Avant**: 8,000 tokens INPUT/message
- **Après**: 4,800 tokens INPUT/message
- **Réduction**: **40%**

### Scénario Optimal (Phase 1+2)
- **Avant**: 8,000 tokens INPUT/message
- **Après**: 2,400 tokens INPUT/message
- **Réduction**: **70%**

### Impact Coûts (exemple 1000 messages/jour)

**Prix GROK** (estimation):
- Input: $5/1M tokens
- Output: $15/1M tokens

**Avant optimisation**:
```
1000 messages × 8,000 tokens INPUT = 8M tokens/jour
8M × $5/1M = $40/jour INPUT
+ OUTPUT ($15-30/jour)
TOTAL: ~$55-70/jour
```

**Après optimisation (Phase 1+2)**:
```
1000 messages × 2,400 tokens INPUT = 2.4M tokens/jour
2.4M × $5/1M = $12/jour INPUT
+ OUTPUT ($15-30/jour)
TOTAL: ~$27-42/jour
```

**Économie**: **$28-38/jour** (50-60% réduction) → **$840-1140/mois**

---

## ⚠️ Précautions

1. **Tester qualité réponses** avec prompts compacts
   - S'assurer que l'Archiviste comprend toujours bien
   - Valider sur cas critiques (souvenirs haute importance, etc.)

2. **Backward compatibility**
   - Garder option pour prompts verbeux (mode debug)
   - Migration progressive

3. **Monitoring**
   - Tracker tokens avant/après
   - Vérifier ratio Archiviste/Luna reste <2x

---

## 🎯 Actions Immédiates Recommandées

1. ✅ **VALIDER** avec Yohan le principe de compacter les prompts
2. ✅ **CRÉER** versions compactes des 3 prompts critiques:
   - `injection` (2846 → ~600 chars)
   - `memorization` (2847 → ~700 chars)
   - `temporal_guardian` (2953 → ~650 chars)
3. ✅ **TESTER** sur 10-20 messages réels
4. ✅ **MESURER** réduction tokens effective
5. ✅ **DÉPLOYER** si validation OK

---

**Créé par**: GitHub Copilot (Claude Sonnet 4.5)  
**Pour**: Yohan BROCARD - OGMA v2.2  
**Date**: Décembre 2025
