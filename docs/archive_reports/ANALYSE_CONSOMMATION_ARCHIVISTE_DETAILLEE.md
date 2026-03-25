# 🔍 Analyse Détaillée Consommation Tokens Archiviste

**Date**: 20 Décembre 2025  
**Objectif**: Identifier TOUTES les sources de consommation tokens de l'Archiviste  
**Méthode**: Analyse systématique du code + estimation tokens par composant

---

## 📊 Données Réelles (Usage Explorer GROK)

**Semaine du 14 Dec 25**:
- **Chat grok-4-fast-non-reasoning (Archiviste)**: 46,000,545 tokens
- **Chat grok-4-1-fast-non-reasoning (Luna)**: 4,391,918 tokens
- **Ratio**: **10.5x** plus pour l'Archiviste

**Total période 1-20 Dec**: 69,682,175 tokens

---

## 🔎 Analyse Systématique Complète

### 1. SYSTÈME DE RÉSUMATION CONVERSATION ✅

**Fichier**: `conversation_summarizer.py`

**Comportement actuel**:
- ✅ Système activé et configuré
- 📊 Résumé tous les **10 messages** (configurable)
- 🎯 Cible: 300 tokens par résumé
- 🔄 Fusion progressive (résumé de résumés)

**Appels Archiviste**:
- 1 appel pour créer résumé (tous les 10 messages)
- 1 appel pour fusion résumés (tous les ~50 messages)

**Estimation tokens**:
```
INPUT par résumé:
- Prompt système: ~500 chars → 125 tokens
- 10 messages conversation: ~2000 chars → 500 tokens
TOTAL INPUT: ~625 tokens

OUTPUT par résumé: ~300 tokens (cible)

FRÉQUENCE: 1 appel tous les 10 messages
→ ~62.5 tokens INPUT/message en moyenne
→ ~30 tokens OUTPUT/message en moyenne
```

**Impact global**: ✅ **FAIBLE** (système optimal déjà)

---

### 2. APPELS ARCHIVISTE PAR MESSAGE UTILISATEUR

#### A. Core System (ogma_ng.py)

**Par message utilisateur standard, l'Archiviste est appelé**:

1. **Analyse Sémantique** (Memory Optimizer)
   - Fonction: `analyze_message_semantic()`
   - Input: Prompt ~700 tokens + message user ~100 tokens
   - Output: JSON keywords ~150 tokens
   - **TOTAL: ~800 tokens INPUT, 150 tokens OUTPUT**

2. **Synthèse Mémoire** (Memory Manager)
   - Fonction: `_call_archiviste_synthesis()`
   - Input: Prompt injection ~711 tokens + souvenirs JSON ~500-2000 tokens + message ~100 tokens
   - Output: Synthèse ~200-400 tokens
   - **TOTAL: ~1,311-2,811 tokens INPUT, 200-400 tokens OUTPUT**
   - **⚠️ VARIABLE selon nombre souvenirs**

3. **Analyse Temporelle** (Temporal Guardian)
   - Fonction: `analyze_with_archiviste()`
   - Input: Prompt temporal ~738 tokens + données tempo ~200 tokens
   - Output: Directive comportementale ~100 tokens
   - **TOTAL: ~938 tokens INPUT, 100 tokens OUTPUT**

4. **Capability Advisor**
   - Fonction: `analyze_conversation()`
   - Input: Prompt ~700 tokens + contexte ~300 tokens
   - Output: Suggestion JSON ~200 tokens
   - **TOTAL: ~1,000 tokens INPUT, 200 tokens OUTPUT**

**CUMUL MINIMAL par message**:
- **INPUT: 3,849 tokens**
- **OUTPUT: 650 tokens**
- **TOTAL: 4,499 tokens par message utilisateur**

**CUMUL MAXIMAL** (nombreux souvenirs):
- **INPUT: 5,349 tokens**
- **OUTPUT: 850 tokens**
- **TOTAL: 6,199 tokens par message**

---

#### B. Extensions Actives

##### 🧠 **Cognitive Mirror (Introspection)**

Quand activé par phrase magique "il faut que je réfléchisse":

- **Dialogue Luna ↔ Archiviste** (3-5 tours minimum)
- Chaque tour Archiviste:
  - Input: Prompt ~500 tokens + mémoires ~1000 tokens + contexte dialogue ~500 tokens
  - Output: Réponse analytique ~300-500 tokens
  - **TOTAL/tour: ~2,000 tokens INPUT, 400 tokens OUTPUT**

**Session introspection typique** (5 tours):
- **INPUT: 10,000 tokens**
- **OUTPUT: 2,000 tokens**
- **TOTAL: 12,000 tokens par session introspection**

**⚠️ IMPACT MAJEUR si utilisé fréquemment**

---

##### 📔 **Journal de Bord**

Génération automatique fin de journée:

- **1 appel Archiviste** pour résumé journée complète
- Input: Prompt style ~400 tokens + historique complet journée ~5,000-10,000 tokens
- Output: Résumé structuré ~500-800 tokens
- **TOTAL: ~5,400-10,400 tokens INPUT, 500-800 tokens OUTPUT**

**FRÉQUENCE**: 1x par jour (ou sur demande)

**Impact**: ✅ **MODÉRÉ** (1x/jour acceptable)

---

##### 🎯 **Ego Selector**

Sélection traits ego par message:

- **1 appel Archiviste** pour analyse contextuelle
- Input: Prompt ~500 tokens + catalogue traits ~300 tokens + message ~100 tokens
- Output: Catégories sélectionnées JSON ~100 tokens
- **TOTAL: ~900 tokens INPUT, 100 tokens OUTPUT**

**FRÉQUENCE**: 1x par message utilisateur

**Impact**: ✅ **MODÉRÉ** (déjà compté dans cumul base)

---

##### 🕒 **Archi Sensor** (Détection émotionnelle)

Si activé (pas sûr de l'état actuel):

- **Appels potentiels** pour analyse émotionnelle continue
- À vérifier si réellement actif

---

### 3. SOURCES VOLUMINEUSES IDENTIFIÉES

#### 🔥 **PROBLÈME #1: Souvenirs JSON Complets**

Dans `_call_archiviste_synthesis()`:

```python
memory_context = []
for mem in memories:
    context_entry = {
        "titre": mem.get('title', 'Sans titre'),
        "résumé": mem.get('summary', ''),
        "score": mem.get('similarity_score', 0),
        "impact": mem.get('score_impact', 0),
        "valence": mem.get('valence', 0),
        "date": mem.get('created_at', ''),
        "texte_original": texte_content  # ⚠️ PEUT ÊTRE TRÈS LONG
    }
```

**Si 10 souvenirs avec texte_original de 500 chars chacun**:
- 10 × 500 chars = 5,000 chars = **~1,250 tokens supplémentaires**

**OPTIMISATION POSSIBLE**:
- Limiter texte_original à 200 chars sauf haute importance (>180)
- **Gain estimé: 800-1,000 tokens/message**

---

#### 🔥 **PROBLÈME #2: Historique Conversation?**

À vérifier si l'Archiviste reçoit l'historique complet à chaque appel.

**Si historique 50 messages × 100 tokens = 5,000 tokens supplémentaires**

---

#### 🔥 **PROBLÈME #3: Multiples Appels Redondants**

**4 appels par message** avec prompts système répétés:
- Même si prompts compacts: 4 × 500 tokens = 2,000 tokens

**OPTIMISATION POSSIBLE**:
- Fusionner appels similaires (semantic + synthesis)
- Prompt caching (GROK supporte probablement)
- **Gain estimé: 1,000-1,500 tokens/message**

---

### 4. CUMUL TOKENS GLOBAL ESTIMÉ

#### **Par Message Utilisateur Standard**

```
CORE SYSTEM:
✓ Analyse sémantique:     800 INPUT + 150 OUTPUT
✓ Synthèse mémoire:      2,000 INPUT + 300 OUTPUT  (moyenne)
✓ Analyse temporelle:     900 INPUT + 100 OUTPUT
✓ Capability advisor:    1,000 INPUT + 200 OUTPUT
✓ Ego selector:           900 INPUT + 100 OUTPUT
─────────────────────────────────────────────────
TOTAL CORE:             5,600 INPUT + 850 OUTPUT = 6,450 tokens

RÉSUMATION (1x/10 messages):
✓ Résumé conversation:    625 INPUT + 300 OUTPUT (amortisé = 92.5 tokens/msg)

TOTAL PAR MESSAGE:      ~5,700 INPUT + 1,150 OUTPUT = 6,850 tokens
```

#### **Comparaison Luna (IA Principale)**

```
LUNA (1 appel):
✓ Prompt système:        1,000 tokens
✓ Contexte mémoire:        500 tokens (synthèse Archiviste)
✓ Historique:              300 tokens
✓ Message user:            100 tokens
✓ Réponse:                 500 tokens
─────────────────────────────────────────────────
TOTAL LUNA:             1,900 INPUT + 500 OUTPUT = 2,400 tokens
```

#### **Ratio Archiviste / Luna**

```
5,700 INPUT / 1,900 INPUT = 3.0x
6,850 TOTAL / 2,400 TOTAL = 2.9x
```

**⚠️ Mais données réelles montrent 10.5x...**

**Il manque donc encore ~7x** - Hypothèses:

1. **Introspection fréquente** (12,000 tokens/session × N sessions)
2. **Historique complet envoyé** à l'Archiviste (non comptabilisé)
3. **Souvenirs texte_original plus longs** que estimé
4. **Autres extensions non détectées** consommant Archiviste

---

### 5. ACTIONS D'INVESTIGATION SUPPLÉMENTAIRES

**À VÉRIFIER**:

1. ✅ Activer logs détaillés GROK (si API le permet)
2. ✅ Mesurer taille réelle prompts envoyés (via print debug)
3. ✅ Compter nombre réel appels Archiviste sur 1 journée type
4. ✅ Vérifier si historique conversation complet envoyé
5. ✅ Identifier extensions "cachées" utilisant Archiviste

---

**STATUS**: ✅ **Analyse 85% - Pistes identifiées**

---

## 💡 RECOMMANDATIONS PRIORITAIRES

### 🎯 Actions Immédiates (Impact 40-60%)

#### **1. Limiter texte_original dans Synthèses Mémoire**

**Fichier**: `memory_manager.py` ligne ~1800

**Problème**:
```python
texte_content = original_text  # Score > 140 = texte complet sans limite
```

**Solution**:
```python
# Limiter même haute importance à 500 chars max
if impact_score > 140:
    texte_content = original_text[:500] + "..." if len(original_text) > 500 else original_text
```

**Gain estimé**: **800-1,200 tokens/message** (-15-20%)

---

#### **2. Vérifier Historique Conversation Envoyé**

**À contrôler**: Est-ce que `conversation_history` complet est passé à l'Archiviste?

**Fichier à vérifier**: `memory_manager.py`, `archiviste_memory_optimizer.py`

Si historique complet (50 msgs × 100 tokens = 5,000 tokens), **limiter à 10 derniers messages**.

**Gain estimé**: **3,000-4,000 tokens/message** (-50-70% si confirmé)

---

#### **3. Fusionner Appels Analyse Sémantique + Synthèse**

Ces 2 appels font des choses similaires avec même prompt injection:

**Avant** (2 appels):
- Semantic analysis: 800 INPUT + 150 OUTPUT
- Memory synthesis: 2,000 INPUT + 300 OUTPUT
= **2,800 INPUT + 450 OUTPUT**

**Après** (1 appel fusionné):
- Unified analysis + synthesis: 1,500 INPUT + 400 OUTPUT

**Gain estimé**: **1,300 tokens/message** (-20%)

---

### 🔧 Actions Moyennes (Impact 20-30%)

#### **4. Prompt Caching GROK**

Si GROK supporte le caching (à vérifier docs API):

```python
messages = [
    {
        "role": "system",
        "content": PROMPT_INJECTION,
        "cache_control": {"type": "ephemeral"}  # Cache prompt système
    },
    ...
]
```

**Gain estimé**: **500-800 tokens/message** (-10-15%)

---

#### **5. Skip Capability Advisor si Non Pertinent**

Analyser si vraiment utile à chaque message ou seulement si:
- Message contient question
- Contexte suggère besoin capacité

**Gain estimé**: **300-500 tokens/message** (-5-10% si skip 50% du temps)

---

### 📊 Actions Monitoring (Validation)

#### **6. Activer Logging Détaillé Temporaire**

Ajouter dans `core_logic.py` (méthode `call_chat_api`):

```python
# Avant appel API
input_text = str(messages)
print(f"[ARCHIVISTE-DEBUG] INPUT size: {len(input_text)} chars (~{len(input_text)//4} tokens)")

# Après appel API  
output_text = str(response)
print(f"[ARCHIVISTE-DEBUG] OUTPUT size: {len(output_text)} chars (~{len(output_text)//4} tokens)")
```

Faire **5-10 messages test** et compiler stats réelles.

---

#### **7. Vérifier Dashboard GROK**

**URL probable**: `https://console.x.ai/` ou `https://platform.xai.com/`

Chercher:
- Usage analytics
- API logs détaillés
- Token breakdowns par endpoint

Si accessible, exporter CSV dernière semaine pour analyse.

---

## 🎯 PLAN D'ACTION PROPOSÉ

### Phase 1: Validation (1h)
1. ✅ Activer logging debug (action #6)
2. ✅ Faire 10 messages test normaux
3. ✅ Compiler stats réelles
4. ✅ Vérifier dashboard GROK si accessible

### Phase 2: Quick Wins (2-3h)
1. ✅ Limiter texte_original (action #1)
2. ✅ Vérifier/limiter historique (action #2)
3. ✅ Tester prompt caching si supporté (action #4)

**Gain estimé Phase 2**: **40-60% réduction**

### Phase 3: Optimisations Avancées (1 journée)
1. ✅ Fusionner semantic + synthesis (action #3)
2. ✅ Skip capability advisor conditionnel (action #5)
3. ✅ Audit introspection (si utilisé fréquemment)

**Gain total estimé**: **60-80% réduction consommation**

---

## 📈 Impact Coûts Estimé

**Avant optimisation** (semaine 14 Dec):
- Archiviste: 46M tokens
- Coût ~$230/semaine (@$5/1M)

**Après optimisation 60%**:
- Archiviste: 18.4M tokens
- Coût ~$92/semaine
- **Économie: $138/semaine = $552/mois = $6,624/an**

---

**PROCHAINE ÉTAPE RECOMMANDÉE**:  
✅ Activer logging debug et faire session test pour confirmer hypothèses

**Veux-tu que je crée le patch de logging debug à appliquer ?**
