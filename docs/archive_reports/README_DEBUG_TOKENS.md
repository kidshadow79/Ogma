# 🔬 DEBUG TOKENS ARCHIVISTE - MODE D'EMPLOI

## 🎯 Objectif

Mesurer la consommation **réelle** de l'Archiviste pour identifier les optimisations à fort impact.

---

## ✅ Installation Appliquée

Le système de logging a été installé automatiquement dans :

- ✅ `core_logic.py` - Controller avec instrumentation
- ✅ `memory_manager.py` - 5 points de tracking (semantic, enrichment, synthesis, detailed, full)
- ✅ `ego_selector.py` - Sélection ego
- ✅ `extensions/capability_advisor/` - Suggestions capacités
- ✅ `extensions/cognitive_mirror/` - Dialogues introspection
- ✅ `modules/ogma_core/controllers.py` - Flag Archiviste activé

**Marqueurs visibles** : `DEBUG_TOKEN_TRACKING` avec séparateurs `═══` pour désinstallation facile.

---

## 🚀 Utilisation

### 1. Lancer OGMA normalement

```bash
python launch_ogma.py
```

Le logging est **automatiquement activé** si `archiviste_logger.py` détecté.

### 2. Utiliser OGMA normalement

- Faire **10-20 messages** avec Luna
- Varier les interactions :
  - Questions simples
  - Requêtes mémoire
  - Introspection cognitive (dire "il faut que je réfléchisse")
  - Utilisation journal de bord

### 3. Vérifier logs en temps réel

Dans la console OGMA, chaque appel Archiviste affiche :

```
[ARCHIVISTE-LOG] memory_synthesis: 2340 IN + 298 OUT = 2638 tokens
[ARCHIVISTE-LOG] semantic_analysis: 845 IN + 156 OUT = 1001 tokens
[ARCHIVISTE-LOG] capability_advisor: 1050 IN + 201 OUT = 1251 tokens
```

### 4. Générer le rapport final

**Après avoir fermé OGMA** :

```bash
python generate_archiviste_report.py
```

Ou manuellement dans la console Python :

```python
from archiviste_logger import save_and_print_report
save_and_print_report()
```

---

## 📊 Rapport Généré

Le fichier `data/archiviste_monitoring.json` contient :

```json
{
  "summary": {
    "total_calls": 48,
    "total_input_tokens": 98450,
    "total_output_tokens": 12300,
    "total_tokens": 110750,
    "avg_tokens_per_call": 2307,
    "ratio_input_output": 8.0,
    "by_source": {
      "memory_synthesis": {"count": 12, "input_tokens": 28450, "output_tokens": 3580},
      "semantic_analysis": {"count": 12, "input_tokens": 9840, "output_tokens": 1850},
      ...
    },
    "top_consumers": [...]
  },
  "detailed_calls": [...]
}
```

**Console affiche** :

```
📊 RAPPORT CONSOMMATION ARCHIVISTE
========================================
Durée session: 15.3 min
Total appels: 48
Total INPUT: 98,450 tokens
Total OUTPUT: 12,300 tokens
TOTAL GLOBAL: 110,750 tokens
Moyenne/appel: 2307 tokens
Ratio INPUT/OUTPUT: 8.0:1

🔥 TOP CONSOMMATEURS:
  memory_synthesis: 32,030 tokens (28.9%) - 12 appels
  introspection_dialogue: 24,000 tokens (21.7%) - 8 appels
  semantic_analysis: 11,690 tokens (10.6%) - 12 appels
```

---

## 🎯 Interpréter les Résultats

### Ratio INPUT/OUTPUT

- **< 3:1** → Normal, prompts optimisés
- **3-6:1** → Contexte important envoyé (souvenirs, historique)
- **> 6:1** → 🔥 **Problème détecté** - Contexte excessif ou redondant

### Top Consommateurs

Prioriser optimisation si source > 20% du total :

- **memory_synthesis** > 30% → Vérifier longueur `texte_original` dans souvenirs
- **introspection_dialogue** > 25% → Réduire tours de dialogue ou fréquence
- **semantic_analysis** > 15% → Optimiser prompt ou contexte decision

### Moyenne par Appel

- **< 1,500 tokens** → Appels légers, optimisés
- **1,500-3,000 tokens** → Standard OGMA (acceptable)
- **> 3,000 tokens** → 🔥 **Appels lourds** - Chercher contexte excessif

---

## 🔥 Optimisations Recommandées

Selon les résultats du rapport, appliquer dans l'ordre :

1. **Si memory_synthesis > 30%** → Limiter `texte_original` (voir [ANALYSE_CONSOMMATION_ARCHIVISTE_DETAILLEE.md](ANALYSE_CONSOMMATION_ARCHIVISTE_DETAILLEE.md) action #1)

2. **Si ratio INPUT/OUTPUT > 6** → Vérifier historique conversation envoyé (action #2)

3. **Si > 50 appels en 15min** → Envisager fusion appels ou cache (actions #3, #4)

4. **Si introspection_dialogue > 20%** → Réduire fréquence ou tours de dialogue

---

## 🗑️ Désinstallation

Quand l'analyse est terminée, **supprimer le système** :

```bash
# Option 1: Manuelle (5-10 min)
# Suivre DESINSTALLER_DEBUG_TOKENS.md

# Option 2: Automatique (30 sec) - À CRÉER
# python remove_debug_tokens.py
```

**Important** : Sauvegarder le rapport avant :

```bash
Copy-Item data\archiviste_monitoring.json data\RAPPORT_TOKENS_FINAL.json
```

---

## ⚠️ Limitations

- **Estimation tokens** : ~4 chars = 1 token (approximatif ±10%)
- **Pour précision absolue** : Comparer avec logs GROK dashboard
- **Pas de streaming** : Compte tokens finaux uniquement
- **Overhead minime** : ~50ms par appel (négligeable)

---

## 💡 Astuce Pro

Comparer **session courte** (5 msg) vs **session longue** (20 msg) pour détecter croissance non-linéaire (signe d'historique complet envoyé).

**Durée test recommandée** : 1-2h d'usage normal = données fiables
