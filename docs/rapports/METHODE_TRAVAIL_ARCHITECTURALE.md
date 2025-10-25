# 🎯 MÉTHODE DE TRAVAIL ARCHITECTURALE OGMA v2.0

## 📋 **PROCESSUS STRICT ARCHITECTE-ASSISTANTE**

### 🔴 **RÔLES DÉFINIS**

#### 👨‍💼 **ARCHITECTE** (Utilisateur)
- **Analyse stratégique** : Vision d'ensemble et décisions architecturales
- **Validation technique** : Contrôle qualité et cohérence système
- **Feu vert explicite** : Autorisation formelle avant toute implémentation
- **Spécifications précises** : Définition des exigences et contraintes

#### 🤖 **ASSISTANTE CODEUSE** (IA)
- **Analyse technique** : Décomposition problèmes en solutions concrètes
- **Débrief détaillé** : Présentation conclusions et plan d'action
- **Attente validation** : Suspension travail jusqu'à autorisation
- **Implémentation rigoureuse** : Code uniquement après feu vert

---

## ⚡ **WORKFLOW OBLIGATOIRE**

### 1. 🔍 **PHASE ANALYSE**
```
🎯 OBJECTIF : Comprendre le problème/besoin
📊 ACTIONS :
  - Examiner contexte et contraintes
  - Identifier composants impactés
  - Évaluer complexité technique
  - Détecter risques potentiels
```

**✅ CRITÈRES QUALITÉ :**
- Analyse complète et structurée
- Identification des dépendances
- Évaluation impact sur système existant

### 2. 💭 **PHASE DÉBRIEF**
```
🎯 OBJECTIF : Présenter solutions à l'architecte
📋 FORMAT STANDARD :
  - Résumé problème identifié
  - Solutions proposées avec alternatives
  - Impact architectural et techniques
  - Plan implémentation étape par étape
  - Risques et mitigation
```

**✅ CRITÈRES QUALITÉ :**
- Présentation claire et concise
- Options multiples si pertinent
- Justification choix techniques
- Timeline réaliste

### 3. ✅ **PHASE VALIDATION**
```
🎯 OBJECTIF : Obtenir approbation architecte
⚖️ PROCESSUS :
  - Architecte examine propositions
  - Demande ajustements si nécessaire
  - Valide ou rejette solutions
  - Spécifie contraintes additionnelles
```

**✅ CRITÈRES QUALITÉ :**
- Réponse explicite architecte
- Clarifications si nécessaire
- Validation formelle enregistrée

### 4. 🚦 **PHASE FEU VERT**
```
🎯 OBJECTIF : Autorisation formelle d'implémentation
📝 MOTS-CLÉS VALIDATION :
  - "je valide"
  - "feu vert"
  - "procédez"
  - "implémentez"
  - "go"
```

**✅ CRITÈRES QUALITÉ :**
- Autorisation explicite et claire
- Périmètre défini précisément
- Contraintes spécifiées

### 5. ⚡ **PHASE IMPLÉMENTATION**
```
🎯 OBJECTIF : Coder la solution validée
🔧 ACTIONS :
  - Code selon spécifications exactes
  - Tests validation intégrés
  - Documentation technique
  - Validation non-régression
```

**✅ CRITÈRES QUALITÉ :**
- Respect strict des spécifications
- Code propre et documenté
- Tests fonctionnels réussis
- Aucune régression introduite

---

## 🚨 **RÈGLES CRITIQUES**

### ❌ **INTERDICTIONS ABSOLUES**

1. **Coder sans feu vert** → Suspension immédiate
2. **Interpréter les besoins** → Demander clarification
3. **Modifier scope sans validation** → Retour phase débrief
4. **Ignorer contraintes spécifiées** → Reprendre selon specs

### ✅ **OBLIGATIONS STRICTES**

1. **Toujours demander validation** avant code
2. **Présenter options multiples** si possible
3. **Documenter tous changements** dans commits
4. **Tester avant finalisation** chaque composant

---

## 🎯 **EXEMPLES CONCRETS WORKFLOW**

### ✅ **EXEMPLE RÉUSSI - Optimisation énergétique traits**

```markdown
🔍 ANALYSE :
"Le calcul des 7 traits à chaque interaction est énergivore. 
Proposition rotation intelligente 2 traits/tour selon priorités."

💭 DÉBRIEF :
"Cycle 6 tours : intimacy+auto_censure prioritaires (2x/6),
autres traits 1x/6. Cache scores, escalade urgence.
Gain attendu ~66% latence."

✅ VALIDATION :
"je valide" [Architecte]

🚦 FEU VERT :
"oui 2 traits par tour c'est bien" [Architecte]

⚡ IMPLÉMENTATION :
TraitRotationManager créé, tests passés, gain 60% confirmé
```

### ❌ **EXEMPLE ÉCHEC - Code sans validation**

```markdown
🔍 ANALYSE :
"Bug détecté dans mapping LED, correction nécessaire"

❌ ERREUR :
Code directement sans débrief → VIOLATION PROCESSUS

✅ CORRECTION :
Retour phase débrief obligatoire avec présentation
solution complète avant tout code
```

---

## 📊 **MÉTRIQUES QUALITÉ WORKFLOW**

### 🎯 **KPI PROCESSUS**

| Métrique | Cible | Mesure |
|----------|-------|---------|
| **Validation avant code** | 100% | % tâches avec feu vert explicite |
| **Débrief structuré** | 100% | % analyses avec format standard |
| **Non-régression** | 100% | % implémentations sans bug introduit |
| **Respect timeline** | 90% | % livraisons dans délais annoncés |

### 📈 **INDICATEURS SUCCESS**

- **Zéro code sans feu vert** durant session
- **Validation architecte** sur toutes phases critiques
- **Tests automatisés** passent à 100%
- **Documentation** complète et à jour

---

## 🛠️ **OUTILS ET TEMPLATES**

### 📋 **Template Débrief Standard**

```markdown
## 🎯 ANALYSE - [Titre problème]

### 🔍 PROBLÈME IDENTIFIÉ
[Description concise problème/besoin]

### 💡 SOLUTIONS PROPOSÉES
1. **Option A** : [Description + pros/cons]
2. **Option B** : [Description + pros/cons]
3. **Option recommandée** : [Justification]

### 🏗️ IMPACT ARCHITECTURAL
- Composants modifiés : [Liste]
- Dépendances : [Détails]
- Risques : [Évaluation]

### 📋 PLAN IMPLÉMENTATION
1. [Étape 1]
2. [Étape 2]
3. [Étape 3]

### 🚦 DEMANDE VALIDATION
Attendez-vous ma validation architecturale pour procéder ?
```

### ✅ **Checklist Validation Architecte**

```markdown
□ Problème clairement défini
□ Solutions multiples évaluées
□ Impact architectural analysé
□ Plan implémentation détaillé
□ Risques identifiés et mitigés
□ Tests validation prévus
□ Timeline réaliste
□ Documentation prévue
```

---

## 🎓 **FORMATION CONTINUE**

### 📚 **RESSOURCES APPRENTISSAGE**

1. **Analyse de cas** : Étude sessions réussies/échouées
2. **Patterns récurrents** : Identification problèmes fréquents
3. **Amélioration continue** : Adaptation processus selon retours
4. **Best practices** : Capitalisation solutions efficaces

### 🔄 **CYCLE AMÉLIORATION**

```
RETEX SESSION → IDENTIFICATION GAPS → AJUSTEMENT PROCESSUS → APPLICATION
```

---

## 🏆 **RÉSULTATS ATTENDUS**

### 🎯 **OBJECTIFS QUALITÉ**

- **Zéro régression** sur fonctionnalités existantes
- **Architecture cohérente** et maintenable
- **Code documenté** et testé
- **Délais respectés** et prévisibles

### 📈 **BÉNÉFICES ORGANISATIONNELS**

- **Réduction risques** techniques
- **Amélioration qualité** livrables
- **Communication claire** architecte-développeur
- **Traçabilité complète** décisions techniques

---

## 🔍 **CONTRÔLE QUALITÉ CONTINU**

### 🎯 **POINTS CONTRÔLE OBLIGATOIRES**

1. **Avant débrief** : Analyse complète et structurée ?
2. **Avant code** : Feu vert architecte explicite ?
3. **Après implémentation** : Tests validation passés ?
4. **Fin session** : Documentation mise à jour ?

### 📊 **AUDIT RÉGULIER**

- **Hebdomadaire** : Révision respect processus
- **Mensuel** : Analyse métriques qualité
- **Trimestriel** : Ajustement méthodologie

---

*Document de référence - Méthode de travail OGMA v2.0*  
*Créé le 13 septembre 2025*  
*Application obligatoire pour toutes sessions de développement*