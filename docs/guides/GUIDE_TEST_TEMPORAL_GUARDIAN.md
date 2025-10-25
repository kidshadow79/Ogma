# Guide de Test Temporal Guardian dans OGMA
# ========================================

## ✅ Extension Intégrée et Fonctionnelle

L'extension **Temporal Guardian** est maintenant **complètement intégrée** dans OGMA et prête à tester !

## 🚀 Comment Tester

### 1. Lancer OGMA
```bash
python launch_ogma.py
```

### 2. Activer le Debug Temporel (optionnel)
- Aller dans **Settings** → **Debug**
- Ajouter: `"show_temporal_debug": true`
- Cela affichera les mesures temporelles dans la console

### 3. Scénarios de Test

#### 🔹 Test Basique
1. Envoyer: "Bonjour Luna"
2. Attendre 2-3 secondes
3. Envoyer: "Comment ça va ?"
4. Attendre 5-6 secondes  
5. Envoyer: "Peux-tu m'aider ?"

**Résultat attendu**: L'archiviste reçoit des données temporelles automatiquement.

#### 🔹 Test Fatigue (délais croissants)
1. Message rapide (immediate)
2. Attendre 5s → message 
3. Attendre 15s → message
4. Attendre 30s → message

**Résultat attendu**: Pattern de ralentissement détecté.

#### 🔹 Test Absence/Retour
1. Conversation normale
2. Attendre 2-3 minutes
3. Envoyer: "Excuse-moi, où en étions-nous ?"

**Résultat attendu**: Retour après interruption détecté.

## 🔍 Ce Que Vous Devriez Voir

### Dans la Console (si debug activé)
```
[TemporalGuardian] ✅ Msg #2 | Délai: 3.0s
[TEMPORAL-GUARDIAN] Message #2 | Délai: 3.0s
```

### Dans l'Interface
L'archiviste reçoit automatiquement un contexte enrichi comme :
```
Note de l'Archiviste : [contexte normal]

🕒 14:35 | ⏱️ Délai: 3s | 📊 Session: 15min, 5 messages | 📈 Rythme moyen: 1.8min
```

## 🎯 Validation Réussie Si

1. ✅ **Pas d'erreurs** au démarrage d'OGMA
2. ✅ **Messages temporels** dans la console (si debug activé)
3. ✅ **L'archiviste répond normalement** (pas d'interruption du workflow)
4. ✅ **Contexte temporel invisible** pour l'utilisateur (travaille en arrière-plan)

## ⚙️ Architecture Fonctionnelle

```
[Message Utilisateur] 
    ↓
[TemporalSensor: mesure délais]
    ↓  
[ArchivisteEnricher: enrichit contexte]
    ↓
[Archiviste: analyse + mémoire + TEMPOREL]
    ↓
[IA Principale: réponse enrichie]
```

## 📋 Instructions Archiviste

L'archiviste a maintenant des **instructions temporelles** dans:
`extensions/temporal_guardian/INSTRUCTIONS_ARCHIVISTE_TEMPOREL.md`

Il peut détecter:
- 😴 **Fatigue** (délais croissants)
- 🤔 **Réflexion** (pauses significatives) 
- 🔄 **Retours** (absences puis retour)
- ⚡ **Changements de rythme**

## 🎉 Mission Accomplie

**Objectif initial**: "*c'est l'archiviste qui a l'horodatage et c'est lui qui analyse les temps d'absence et les moments de fatigue de l'utilisateur*"

**✅ RÉALISÉ**: L'archiviste reçoit maintenant automatiquement le contexte temporel avec chaque message et peut analyser les patterns comportementaux !

---

**Note**: L'extension fonctionne de façon **transparente**. L'utilisateur ne voit rien changer, mais l'archiviste est maintenant **temporellement conscient**.