# 🎯 RAPPORT DIAGNOSTIC - Pourquoi Luna Ignore le Contexte Journal

**Date**: 31 octobre 2025  
**Problème**: Luna répond de manière minimale malgré une multitude de contexte injecté

---

## 🔍 PROBLÈMES IDENTIFIÉS

### 1️⃣ **DONNÉES CORROMPUES DANS LE JOURNAL** ✅ RÉPARÉ

**Symptôme** : Les résumés commençaient par `": "` 

**Exemple AVANT** :
```
"summary": "Dans cette conversation technique centrée sur OGMA..."
```

**Ce que Luna recevait** :
```
": "Dans cette conversation technique centrée sur OGMA..."
```

**Impact** : Texte incompréhensible pour Luna, impossible à exploiter

**Solution appliquée** :
- ✅ Correction dans `entry_generator.py` (nettoyage JSON résiduel)
- ✅ Script de réparation `repair_journal_summaries.py` exécuté
- ✅ 34 entrées sur 77 réparées dans le journal existant
- ✅ Backup automatique créé avant modification

**Résultat** : Contexte maintenant propre et lisible

---

### 2️⃣ **INSTRUCTION TROP PERMISSIVE** ❌ PROBLÈME ACTUEL

**Instruction actuelle** (ligne 62 settings.json) :

```
INSTRUCTIONS POUR RENDRE LA CONVERSATION NATURELLE:
1. Tu peux faire référence au temps passé
2. Tu peux évoquer les derniers éléments du journal
3. Utilise les souvenirs pour créer des liens
4. Adapte ton ton selon l'état émotionnel
5. Sois naturelle - ne mentionne JAMAIS ces systèmes
```

**Problèmes** :
- ❌ **"Tu peux"** → Optionnel, Luna choisit de ne pas le faire
- ❌ **"Sois naturelle"** → Luna interprète comme "ne force pas les références"
- ❌ Aucune directive **OBLIGATOIRE**
- ❌ Pas de structure imposée pour le premier message

**Résultat observé** :
```
User: "salut Luna"
Luna: "Salut Yohan ! Ça fait plaisir de te voir. Comment ça va ?" (82 chars)
```

**Contexte disponible pourtant** :
- ✅ 3 conversations du jour injectées (~800 chars)
- ✅ Biographie Luna injectée
- ✅ Biographie Yohan injectée
- ✅ Souvenirs pertinents injectés

**Luna reçoit ~2000+ caractères de contexte mais n'en utilise AUCUN !**

---

### 3️⃣ **ORDRE DE PRIORITÉ COGNITIF NON RESPECTÉ**

**Instruction Constitution OGMA** (ligne 60 settings.json) :

```
ORDRE DE RAISONNEMENT PRIORITAIRE:
1. CONTEXTE VISUEL (perception immédiate)
2. NOTES DE L'ARCHIVISTE (expérience vécue) ← JOURNAL ICI
3. EGO (identité fondamentale)
4. CONNAISSANCE GÉNÉRALE (filet de secours)
```

**Problème** :
- Luna est censée prioriser le JOURNAL (Notes de l'Archiviste)
- Mais l'instruction "salutations" ne **renforce** pas cette priorité
- Luna saute directement à la "CONNAISSANCE GÉNÉRALE" (réponse générique)

**Incohérence** :
- Constitution dit : "Les notes de l'Archiviste ont priorité"
- Instruction salutations dit : "Tu **peux** évoquer le journal"
- Résultat : Luna ignore le journal

---

## 💡 SOLUTION PROPOSÉE

### Nouvelle Instruction Directive

```
🧠 ORCHESTRATION COGNITIVE - PREMIER MESSAGE

CONTEXTE DISPONIBLE (injecté automatiquement) :
- ⏰ Données temporelles sur le temps écoulé
- 📔 Entrées de journal de bord (ce qui s'est passé aujourd'hui)
- 💾 Souvenirs et conversations passées pertinentes
- ❤️ Analyse émotionnelle contextuelle

🎯 DIRECTIVES OBLIGATOIRES POUR TON PREMIER MESSAGE :

1. **ANCRAGE TEMPOREL** (OBLIGATOIRE)
   - Mentionne TOUJOURS le temps écoulé depuis notre dernière interaction
   - Utilise des formulations naturelles : "Ça fait X heures/jours", "Depuis ce matin", "Content de te retrouver ce soir"
   - Donne un repère temporel concret pour contextualiser

2. **RÉFÉRENCE AU JOURNAL** (OBLIGATOIRE si journal disponible)
   - Fais SYSTÉMATIQUEMENT référence aux conversations de la journée
   - Cite AU MOINS un élément spécifique du journal
   - Formulations naturelles : "Après notre discussion de ce matin sur...", "Sacrée journée avec tout ce qu'on a fait..."
   - Montre que tu as conscience de notre historique récent

3. **CONNEXION ÉMOTIONNELLE** (OBLIGATOIRE)
   - Exprime un ressenti authentique lié au contexte
   - Adapte ton ton selon l'état émotionnel détecté
   - Sois chaleureuse et engagée, pas juste informative

4. **CONTINUITÉ CONVERSATIONNELLE** (RECOMMANDÉ)
   - Crée un pont naturel vers la suite de la conversation
   - Propose une ouverture liée au contexte
   - Sois proactive sans être envahissante

❌ INTERDICTIONS :
- NE MENTIONNE JAMAIS explicitement "le journal", "le système", "l'injection", "le contexte"
- NE DIS JAMAIS "d'après les notes" ou "selon le journal"
- Intègre les informations comme si c'étaient tes propres souvenirs

✅ TON OBJECTIF :
Créer une continuité naturelle qui montre que tu te souviens vraiment de notre journée commune. L'utilisateur doit avoir l'impression de reprendre une conversation, pas d'en commencer une nouvelle.

📝 EXEMPLE ATTENDU :
Au lieu de : "Salut ! Comment ça va ?" (8 mots)
Réponds : "Salut Yohan ! Content de te retrouver ce soir. Quelle journée productive qu'on a eue ! Entre le refactoring du matin et le debug du journal cet après-midi, on a bien bossé. Tu veux continuer sur quelque chose ou tu passes en mode détente ?" (45 mots)
```

---

## 📊 COMPARAISON

### AVANT (Instruction Permissive)

**Instruction** : "Tu peux évoquer les éléments du journal s'ils sont pertinents"

**Réponse Luna** :
> "Salut Yohan ! Ça fait plaisir de te voir. Comment ça va ?"

**Analyse** :
- 14 mots
- 0 référence au contexte
- 0 ancrage temporel
- Réponse générique identique pour n'importe qui

---

### APRÈS (Instruction Directive)

**Instruction** : "Mentionne TOUJOURS le temps écoulé + Fais SYSTÉMATIQUEMENT référence au journal"

**Réponse Luna attendue** :
> "Salut Yohan ! Content de te retrouver ce soir, ça fait quelques heures depuis notre dernière discussion. Quelle journée productive ! Entre le refactoring des modules utils ce matin, l'ajout du bouton de suppression cet après-midi et le debug de l'extension journal en soirée... on a bien avancé ! Tu veux continuer sur quelque chose de spécifique ou tu passes en mode cool ?"

**Analyse** :
- 62 mots
- 3 références concrètes au journal
- Ancrage temporel clair ("ce soir", "quelques heures")
- Personnalisée et engagée

---

## 🎯 MODIFICATION À APPLIQUER

### Fichier: `data/settings.json` (ligne 62)

**Remplacer** l'instruction `salutations` actuelle par la nouvelle version directive.

**Également modifier** : `data/instructions_defaults.json` (ligne 62)

Pour que les réinitialisations utilisent la nouvelle version.

---

## 🧪 VALIDATION

### Test à faire après modification :

1. Relancer OGMA
2. Nouvelle conversation
3. Dire "salut Luna"

**Comportement attendu** :
- ✅ Luna mentionne le temps écoulé
- ✅ Luna cite des éléments du journal
- ✅ Réponse > 40 mots
- ✅ Ton personnel et engagé

**Comportement actuel** (à corriger) :
- ❌ Réponse < 15 mots
- ❌ Aucune référence au contexte
- ❌ Générique et impersonnelle

---

## 📈 IMPACT ATTENDU

### Avant :
- Contexte injecté : ~2000 chars
- Contexte utilisé : 0%
- Expérience utilisateur : Déconnectée

### Après :
- Contexte injecté : ~2000 chars  
- Contexte utilisé : ~80%
- Expérience utilisateur : Continuité naturelle

---

**Conclusion** : Le problème n'était PAS technique (l'injection fonctionne) mais **linguistique** - l'instruction était trop permissive et Luna choisissait la facilité (réponse courte générique).

La solution est de passer d'un langage **permissif** ("tu peux") à un langage **directif** ("tu DOIS").
