# 📓 Journal de Bord v2.0 - Guide d'Utilisation LIVE DETECTION

## 🎯 Nouveauté : Détection LIVE des États Actifs

Depuis la v2.0, le Journal de Bord détecte **automatiquement** les états actifs pendant vos conversations avec Luna, sans intervention manuelle !

---

## ✨ Comment ça marche ?

### 🔍 Détection Automatique

Après **chaque échange** avec Luna, le système analyse:

1. **Votre message** (ce que vous dites)
2. **La réponse de Luna** (ce qu'elle répond)
3. **Le contexte récent** (10 derniers messages)

### 🎯 Patterns Détectés

Le système détecte 4 catégories d'états:

#### 1. 🏥 **Santé**
```
Démarrage:
- "Je suis malade depuis hier"
- "J'ai attrapé la grippe"
- "Je me sens fatigué"

Résolution:
- "Je suis guéri"
- "Je vais beaucoup mieux"
- "Ça va mieux maintenant"
```

#### 2. 💼 **Projet**
```
Démarrage:
- "Je commence à développer une IA"
- "J'ai lancé un nouveau projet"
- "Je travaille sur une extension"

Résolution:
- "J'ai terminé le projet"
- "Le développement est fini"
- "C'est bouclé"
```

#### 3. 📚 **Apprentissage**
```
Démarrage:
- "Je suis en train d'apprendre Python"
- "J'étudie le machine learning"
- "Je suis un cours sur..."

Résolution:
- "J'ai fini la formation"
- "J'ai terminé le cours"
- "J'ai validé le module"
```

#### 4. 😊 **Humeur**
```
Démarrage:
- "Je suis super motivé"
- "Je me sens stressé"
- "Je suis anxieux"

Résolution:
- "Je me sens beaucoup mieux"
- "Le stress est passé"
- "Je suis plus serein"
```

---

## 🚀 Exemples Concrets

### Exemple 1 : Détection Projet

**Vous**: "J'ai commencé à développer une extension pour OGMA ce matin"

**Luna**: "Super ! C'est quoi le but de cette extension ?"

**→ Système détecte**: État "Développement extension OGMA" (Catégorie: Projet)

**Badge**: 🔔 1 état actif

---

### Exemple 2 : Résolution Santé

**Vous**: "Je suis guéri de ma grippe, ça va beaucoup mieux !"

**Luna**: "Génial ! Tu as retrouvé ton énergie ?"

**→ Système détecte**: Résolution de l'état "Grippe"

**Badge**: État marqué ✅ Résolu

---

### Exemple 3 : Mise à Jour

**Vous**: "Mon projet d'IA avance bien, j'ai fini le module de détection"

**Luna**: "Excellent ! Il reste quoi à faire ?"

**→ Système détecte**: Mise à jour de l'état "Projet IA"

**Badge**: État enrichi avec nouveaux détails

---

## 🔔 Badge États Actifs

Le badge en haut à droite affiche le nombre d'états actifs en temps réel.

### Couleurs

- 🟢 **Vert (0 états)**: Aucun état actif
- 🟡 **Orange (1-3 états)**: Quelques états en cours
- 🔴 **Rouge (4+ états)**: Beaucoup d'états actifs

### Rafraîchissement

Le badge se met à jour **automatiquement** après chaque conversation.

---

## 📊 Option B - Injection Hybride

Le système injecte intelligemment le contexte dans les conversations futures:

### Avec États Actifs
```
📋 Contexte injecté:
✅ États actifs (tous)
✅ 2 dernières conversations
```

### Sans États Actifs
```
📋 Contexte injecté:
✅ 3 dernières conversations
```

**Avantage**: Économie de tokens quand vous avez des états actifs importants !

---

## 🧪 Tester la Détection

### Test 1 : Créer un État

1. Lancez OGMA: `python launch_ogma.py`
2. Envoyez: "Je commence à apprendre le japonais"
3. Vérifiez les logs:
   ```
   [JOURNAL-HOOK] Analyse détection états actifs...
   [JOURNAL-HOOK] ✨ 1 nouveaux états détectés
     → Apprentissage japonais (apprentissage)
   ```
4. Badge: 🔔 1

### Test 2 : Résoudre un État

1. Envoyez: "J'ai terminé mon apprentissage du japonais !"
2. Vérifiez les logs:
   ```
   [JOURNAL-HOOK] ✅ 1 états résolus
     → État #1 marqué résolu
   ```
3. Badge: 🔔 0

---

## 📝 Analyse Rétroactive

Pour créer des états à partir de conversations passées:

```bash
python extensions/journal_de_bord/analyze_retroactive.py -n 3
```

**Options**:
- `-n 5`: Analyser les 5 dernières conversations
- `-n 10`: Analyser les 10 dernières conversations

**Résultat**:
```
📊 RÉSUMÉ DE L'ANALYSE RÉTROACTIVE
✨ Nouveaux états créés: 4
✅ États résolus: 1
🔄 États mis à jour: 2

📋 ÉTATS ACTIFS ACTUELS: 5
  [projet] Développement Journal v2.0
    └─ Créé: 2025-12-20T10:30:00
  [apprentissage] Formation Python avancé
    └─ Créé: 2025-12-19T14:15:00
  ...
```

---

## 🔍 Logs à Surveiller

### Démarrage OGMA
```
[JOURNAL-EXTENSION] LIVE-DETECT Initialisation détecteur états live...
[JOURNAL-EXTENSION] ✅ LiveStateDetector opérationnel
```

### Pendant Conversation
```
[JOURNAL-HOOK] Analyse détection états actifs...
[JOURNAL-HOOK] ✨ 2 nouveaux états détectés
  → Projet IA (projet)
  → Apprentissage ML (apprentissage)
[JOURNAL-HOOK] 🔔 Rafraîchissement badge états actifs...
```

### Injection Contexte
```
[CONTEXT-PROVIDER] MODE-HYBRIDE: 3 états actifs détectés
[CONTEXT-PROVIDER] MODE-HYBRIDE: Injection 2 conversations récentes
```

---

## ⚡ Performance

| Étape | Temps | Coût |
|-------|-------|------|
| Pré-filtrage regex | <1ms | 0 tokens |
| Analyse LLM (si pattern) | ~500-1000ms | 200-400 tokens |
| Création état | ~100ms | 0 tokens |

**Total moyen**: ~600ms par échange (uniquement si pattern détecté)

---

## 🛠️ Troubleshooting

### Le badge ne se met pas à jour

**Solution**:
1. Vérifiez les logs `[JOURNAL-HOOK]`
2. Relancez OGMA
3. Vérifiez que l'extension est activée

### Aucun état détecté

**Causes possibles**:
- Pattern trop vague (ex: "je fais un truc")
- Pas de validation LLM (contexte insuffisant)

**Solution**:
- Soyez plus explicite: "Je commence à développer une IA" au lieu de "je bosse"
- Ajoutez du contexte dans la conversation

### Faux positifs

**Exemple**: "Je pourrais apprendre Python" → Détecté comme état

**Solution**:
- La validation LLM détecte normalement le conditionnel
- Si persistant, signalez le pattern pour amélioration

---

## 📚 Ressources

- **Documentation complète**: [LIVE_DETECTION_SYSTEM.md](LIVE_DETECTION_SYSTEM.md)
- **Migration v1→v2**: [MIGRATION_V1_V2_EXPLICATIONS.md](extensions/journal_de_bord/MIGRATION_V1_V2_EXPLICATIONS.md)
- **Tests**: `extensions/journal_de_bord/test_live_detection.py`

---

## 💡 Astuces

### 1. Créer un État Explicitement

Au lieu de: "Je fais un projet"  
Préférez: "J'ai commencé à développer une extension OGMA pour gérer les tâches"

### 2. Résoudre Clairement

Au lieu de: "C'est bon"  
Préférez: "J'ai terminé le développement de l'extension, c'est déployé"

### 3. Suivre l'Évolution

Mentionnez régulièrement l'avancement:
- "Mon projet avance bien, j'ai fini le module X"
- "Ma grippe va mieux, mais je tousse encore un peu"

---

## 🎉 Profitez !

Le système apprend à vous connaître au fur et à mesure de vos conversations.  
Plus vous êtes explicite, meilleure sera la détection ! 🚀
