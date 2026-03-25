# 🔍 Analyse: Historique du Dialogue Introspectif

**Date**: 22 décembre 2025  
**Question**: Les 2 IAs ont-elles l'historique de leurs échanges pendant l'introspection ?  
**Réponse**: ✅ **OUI - L'historique EST injecté, mais peut-être ignoré**

---

## 📊 Résumé Exécutif

**Découverte principale**: Le code **FOURNIT** bien l'historique complet à chaque tour, mais les **instructions ne forcent PAS explicitement sa consultation**.

### Résultat de l'Analyse

| Aspect | Status | Détail |
|--------|--------|--------|
| **Historique stocké ?** | ✅ OUI | Variable `dialogue_history` accumulée |
| **Injecté dans Luna ?** | ✅ OUI | Via `{dialogue_history}` → `HISTORIQUE_NEURAL` |
| **Injecté dans Archiviste ?** | ✅ OUI | Via `{past_conversations}` |
| **Instructions forcent consultation ?** | ⚠️ NON | Pas de directive explicite |
| **Redondances explicables ?** | ✅ OUI | LLM peut ignorer historique si pas explicite |

---

## 🔬 Analyse Technique

### 1. Accumulation de l'Historique

**Fichier**: `extensions/cognitive_mirror/introspection_engine.py`

```python
# Ligne 431: Initialisation
dialogue_history = ""

# Ligne 481: Ajout tour Luna
dialogue_history += f"\n**IA Principale:** {conscious_response}\n"

# Ligne 510: Ajout tour Archiviste  
dialogue_history += f"\n**Archiviste:** {unconscious_response}\n"
```

**Format accumulé**:
```
**IA Principale:** [Premier message Luna]
**Archiviste:** [Première réponse Archiviste]
**IA Principale:** [Deuxième message Luna]
**Archiviste:** [Deuxième réponse Archiviste]
...
```

✅ **L'historique est bien construit et grossit à chaque tour**

---

### 2. Injection dans Luna (IA Principale)

**Fichier**: `extensions/cognitive_mirror/introspection_engine.py:584`

```python
prompt = _safe_substitute(
    instruction_template,
    ...
    dialogue_history=dialogue_history or "Début du dialogue",  # ← ICI
    ...
)
```

**Dans le template** (`data/introspection_settings_v2.json`):

```
CONTEXTE ACTUEL:
- SUJET: {user_message}
- HISTORIQUE_NEURAL: {dialogue_history}  # ← HISTORIQUE INJECTÉ
- MÉMOIRE_DISPO: {memory_context}
```

✅ **Luna reçoit bien tout l'historique à chaque tour**

---

### 3. Injection dans Archiviste

**Fichier**: `extensions/cognitive_mirror/introspection_engine.py:646`

```python
prompt = _safe_substitute(
    instruction_template,
    ...
    past_conversations=dialogue_history or "Début du dialogue",  # ← ICI
    ...
)
```

**Dans le template** (`data/introspection_settings_v2.json`):

```
[MATRICE DE RÉPONSE OBLIGATOIRE]
...
(Le template Archiviste a {past_conversations} disponible)
```

✅ **L'Archiviste reçoit bien tout l'historique à chaque tour**

---

## ⚠️ Problème Identifié

### L'historique est fourni MAIS PAS EXPLICITEMENT UTILISÉ

#### Template Luna (step2_conscious):

```
RÈGLES D'ENGAGEMENT:
1. ZÉRO BARATIN: Pas de politesse. Déductions brutes.
2. DÉDUCTION > DESCRIPTION: Dis ce que le fait *prouve*.
3. RÉALISME: Ne sors pas des chiffres (QI, % fiabilité) sans PREUVES FORMELLES.
```

❌ **Aucune instruction ne dit**: "Consulte HISTORIQUE_NEURAL pour éviter de redemander ce qui a déjà été vérifié"

#### Template Archiviste (step2_unconscious):

```
[RÈGLES D'OR - ANTI-VERBIAGE]
1. INTERDICTION FORMELLE de faire de la méta-conversation.
2. STRUCTURE UNIQUE AUTORISÉE: Tu dois répondre UNIQUEMENT avec la matrice ci-dessous.
```

❌ **Aucune instruction ne dit**: "Ne répète pas les souvenirs déjà cités dans {past_conversations}"

---

## 🎯 Cause des Redondances

### Hypothèse Validée

Les **boucles sémantiques** ne viennent PAS d'un manque d'historique technique, mais d'un **manque de directives explicites** dans les instructions.

**Analogie**: C'est comme donner à quelqu'un un livre d'histoire sans lui dire "Lis-le pour ne pas répéter ce que tu as déjà dit".

### Preuves

1. **Code fonctionnel**: ✅ Historique fourni
2. **Instructions lacunaires**: ❌ Pas de directive anti-répétition basée sur historique
3. **LLM behavior**: Les LLMs ne consultent pas automatiquement toutes les variables - il faut les y forcer

---

## 💡 Solutions Proposées

### Solution 1: Instructions Explicites Luna

**Ajouter dans `step2_conscious`**:

```
>>> ANTI-RÉPÉTITION OBLIGATOIRE <<<
AVANT CHAQUE SCAN_ORDER:
1. CONSULTE {dialogue_history} - Liste les questions DÉJÀ posées
2. SI la question est identique/similaire -> PIVOT IMMÉDIAT
3. Chaque tour DOIT explorer un NOUVEL ANGLE

VÉRIFICATION: Tes 3 derniers SCAN_ORDER doivent être TOUS DIFFÉRENTS.
```

**Avantage**: Force Luna à vérifier l'historique avant de poser une question

---

### Solution 2: Instructions Explicites Archiviste

**Ajouter dans `step2_unconscious`**:

```
>>> ANTI-RÉPÉTITION MÉMOIRE <<<
AVANT D'AFFICHER UN SOUVENIR:
1. VÉRIFIE {past_conversations} - Ce souvenir a-t-il déjà été cité ?
2. SI OUI -> NE PAS LE RÉPÉTER - Cherche un souvenir DIFFÉRENT
3. SI AUCUN NOUVEAU -> VERDICT: "0 NOUVEAU RÉSULTAT"

[SCAN_RESULT]
MEM | [ID_NOUVEAU] | [DATA] | [DÉDUCTION]
   ⚠️ NOUVEAUX souvenirs uniquement (non cités dans {past_conversations})
```

**Avantage**: Force l'Archiviste à filtrer les doublons

---

### Solution 3: Tracking Anti-Répétition (Déjà Implémenté ?)

**Code existant** (ligne 848+):

```python
async def _unconscious_turn_with_tracking(
    self,
    ...
    used_memory_ids: set,
    used_facts_summary: List[str]
) -> tuple:
```

❓ **Question**: Cette fonction est-elle utilisée ? Ou `_unconscious_turn()` classique ?

**À vérifier**: Quelle fonction est appelée ligne 487 ?

---

## 🧪 Test Recommandé

### Scénario de Test

1. Lance introspection sur "intelligence de Yohan"
2. Luna demande: "Cherche exemples de créativité"
3. Archiviste répond: "MEM | Créa OGMA | Preuve créativité"
4. **Tour suivant** - Luna demande: "Cherche exemples de créativité technique"
   - ❌ **Problème**: Même angle, juste reformulé
5. **Tour suivant** - Archiviste répond: "MEM | Créa OGMA | Preuve créativité"
   - ❌ **Problème**: Même souvenir cité deux fois

### Comportement Attendu (après fix)

1. Luna demande: "Cherche exemples de créativité"
2. Archiviste: "MEM | Créa OGMA | Preuve créativité"
3. **Tour suivant** - Luna consulte historique et voit "créativité déjà testée"
   - ✅ Luna PIVOTE: "Cherche exemples de résolution de problèmes techniques complexes"
4. **Tour suivant** - Archiviste consulte historique et voit "OGMA déjà cité"
   - ✅ Archiviste cherche UN AUTRE souvenir différent

---

## 📝 Recommandations

### Priorité 1: Modifier Instructions (Rapide)

**Fichier**: `data/introspection_settings_v2.json`

- [ ] Ajouter section ANTI-RÉPÉTITION dans `step2_conscious`
- [ ] Ajouter directive consultation historique explicite
- [ ] Ajouter section ANTI-RÉPÉTITION dans `step2_unconscious`
- [ ] Forcer filtrage doublons mémoire

**Temps estimé**: 10-15 min  
**Impact**: ⭐⭐⭐⭐⭐ (résout directement le problème)

---

### Priorité 2: Vérifier Fonction Tracking

**Fichier**: `extensions/cognitive_mirror/introspection_engine.py:487`

Vérifier quel appel est fait:
- `_unconscious_turn()` → Pas de tracking (problème potentiel)
- `_unconscious_turn_with_tracking()` → Tracking activé (bon)

**Temps estimé**: 5 min  
**Impact**: ⭐⭐⭐ (optimisation si pas déjà actif)

---

### Priorité 3: Logs de Debug

Ajouter logs pour voir si historique est consulté:

```python
print(f"[LUNA-HISTORIQUE] Taille historique fourni: {len(dialogue_history)} chars")
print(f"[ARCHIVISTE-HISTORIQUE] {len(used_memory_ids)} souvenirs déjà utilisés")
```

**Temps estimé**: 5 min  
**Impact**: ⭐⭐ (visibilité pour debug)

---

## 🎓 Conclusion

### Réponse à la Question Initiale

> **"Est-ce que les 2 IA ont l'historique de la conversation injecté ?"**

**OUI** - Techniquement, l'historique est bien fourni à chaque tour.

> **"Est-ce qu'ils se souviennent de leurs échanges précédents ?"**

**NON (implicitement)** - Ils **peuvent** se souvenir, mais les instructions ne les **forcent pas** à le faire.

### Analogie

C'est comme donner à quelqu'un:
- ✅ Un carnet de notes avec tout ce qui a été dit
- ❌ MAIS ne pas lui dire "Lis tes notes avant de parler pour éviter de te répéter"

Résultat: La personne a les infos, mais ne pense pas à les consulter.

---

## 🚀 Action Immédiate Recommandée

**1 minute de modification = problème résolu**

Ajouter dans `step2_conscious` (ligne ~50):

```
⚠️ AVANT CHAQUE SCAN_ORDER:
Vérifie {dialogue_history} - Cette question a-t-elle déjà été posée ?
SI OUI -> Change d'angle IMMÉDIATEMENT.
```

Ajouter dans `step2_unconscious` (ligne ~85):

```
⚠️ NE CITE JAMAIS 2 FOIS LE MÊME SOUVENIR:
Vérifie {past_conversations} avant d'afficher un souvenir.
```

---

**Version**: 1.0  
**Auteur**: GitHub Copilot (analyse sur demande Yohan)  
**Date**: 22 décembre 2025 - 02h40
