# Rapport de Passation - Extension Temporal Guardian

**Date :** 19 septembre 2025  
**Statut :** Partiellement fonctionnelle - Problèmes de timing  
**Version OGMA :** v2.0 NiceGUI

---

## 🎯 Objectif de l'Extension

Créer un système d'analyse temporelle organique où **l'archiviste détecte les temps d'absence et moments de fatigue de l'utilisateur** et en informe l'IA principale pour adapter le comportement conversationnel.

### Vision Initiale
> *"C'est l'archiviste qui a l'horodatage et c'est lui qui analyse les temps d'absence et les moments de fatigue de l'utilisateur et il en informe l'ia principale"*

---

## 📁 Architecture Implémentée

### Structure des Fichiers
```
extensions/temporal_guardian/
├── __init__.py                    # Init module
├── config.py                     # Configuration extension  
├── temporal_sensor.py            # Capteur mesures temporelles
├── archiviste_enricher.py        # Enrichissement prompt archiviste
└── temporal_guardian.py          # Orchestrateur principal
```

### Composants Créés

#### 1. **TemporalSensor** (`temporal_sensor.py`)
- ✅ **FONCTIONNE** : Mesure délais entre messages
- ✅ **FONCTIONNE** : Calcule moyennes et statistiques session
- ✅ **FONCTIONNE** : Persistence des données temporelles
- 📊 **Debug visible** : `[TemporalSensor] #4 | Délai: 107.1s (moy: 59.7s)`

#### 2. **ArchivisteEnricher** (`archiviste_enricher.py`)  
- ✅ **FONCTIONNE** : Enrichit prompts avec contexte temporel
- ✅ **FONCTIONNE** : Format des données temporelles lisible
- 📊 **Debug visible** : `[ArchivisteEnricher] Contexte injecté: 🕒 19:57 | ⏱️ Délai: 1.8min`

#### 3. **TemporalGuardian** (`temporal_guardian.py`)
- ✅ **FONCTIONNE** : Orchestration capteur + enrichisseur  
- ✅ **FONCTIONNE** : Configuration via settings.json
- ✅ **FONCTIONNE** : Mode debug activable

---

## 🔧 Intégration OGMA

### Modifications `ogma_ng.py`

#### Zone d'intégration (lignes ~6410-6490)
```python
# 🕒 TEMPORAL GUARDIAN - Gestion temporelle organique via l'Archiviste
temporal_guardian = _ensure_temporal_guardian()
temporal_result = temporal_guardian.process_user_message(
    user_message=final_message,
    archiviste_prompt=base_archiviste_prompt
)
```

#### Configuration `settings.json`
```json
"temporal_guardian": {
    "enabled": true,
    "debug_mode": true,
    "temporal_context_format": "detailed"
}
```

---

## ✅ Ce Qui Fonctionne

### 1. Mesure Temporelle
- **Capteur actif** : Délais mesurés correctement
- **Statistiques** : Moyennes et totaux calculés
- **Persistence** : Données sauvegardées entre sessions

### 2. Enrichissement Contextuel
- **Prompt archiviste enrichi** avec données temporelles
- **Format lisible** : timestamps, délais, statistiques session
- **Debug complet** : Logs détaillés visibles

### 3. Configuration
- **Settings.json** : Configuration dynamique
- **Mode debug** : Traçabilité complète
- **Activation/désactivation** : Contrôle utilisateur

---

## ❌ Ce Qui Ne Fonctionne Pas

### 1. **PROBLÈME MAJEUR : Timing de l'Alerte**
```
Flux observé (INCORRECT) :
1. Utilisateur envoie message
2. Luna répond immédiatement  
3. ⚠️ Alerte temporelle arrive APRÈS la réponse
```

**Symptômes :**
- Luna donne des réponses "glacées" sans tenir compte du contexte temporel
- L'analyse temporelle apparaît dans les logs APRÈS sa réponse
- Aucune adaptation comportementale visible

### 2. **Problème : Ordre des Messages Système**
L'alerte temporelle est noyée parmi les autres messages système :
```
Messages envoyés à l'API :
1. system: Prompt principal
2. system: Instructions archiviste  
3. system: Souvenirs détaillés
4. system: [ANALYSE TEMPORELLE] <- NOYÉ
5. user: Message utilisateur
```

### 3. **Problème : Analyse Peu Pertinente**
L'archiviste génère des analyses bizarres :
- Parle de "saturations nerveuses" pendant des tests simples
- Contexte temporel mal interprété
- Recommandations non adaptées

---

## 🔍 Diagnostic Technique

### Logs d'Exemple (Dysfonctionnel)
```
[TemporalSensor] #4 | Délai: 107.1s (moy: 59.7s)           ✅ Mesure OK
[ArchivisteEnricher] Contexte injecté: 🕒 19:57...         ✅ Enrichissement OK  
[TEMPORAL-GUARDIAN] 🧠 Analyse directe...                  ✅ Analyse OK
[TEMPORAL-GUARDIAN] 🚨 Alerte préparée pour IA principale  ✅ Alerte préparée
[TEMPORAL-GUARDIAN] ✅ Alerte ajoutée en position finale   ✅ Ajout OK

--- RÉPONSE LUNA (sans tenir compte de l'alerte) ---       ❌ PROBLÈME ICI
Luna: "Salut toi. Tu veux qu'on parle de quoi ?"          ❌ Réponse froide

--- ALERTE ARRIVE APRÈS ---                                ❌ TROP TARD
[SYNCHRONISATION TEMPORELLE] L'utilisateur semble...       ❌ Post-traitement
```

### Hypothèses sur la Cause
1. **Messages système ignorés** par le modèle LLM
2. **Position finale inefficace** - l'alerte arrive trop tard dans la pile
3. **Conflit avec autres systèmes** - injection émotionnelle, souvenirs, etc.
4. **Modèle LLM insensible** aux directives système en fin de liste

---

## 🔄 Tentatives de Correction Effectuées

### Version 1 : Appel Archiviste Asynchrone
❌ **Échec** : L'analyse arrivait après la réponse principale

### Version 2 : Alerte Système Directe  
❌ **Échec** : Message système ajouté mais ignoré par Luna

### Version 3 : Position Finale Forcée
❌ **Échec** : Alerte en dernière position mais toujours inefficace

### Version 4 : Analyse Directe Sans Archiviste
❌ **Échec** : Simplification du système mais même problème de timing

---

## 🚧 Solutions Potentielles à Explorer

### 1. **Injection Dans le Prompt Principal**
Au lieu d'un message système séparé, intégrer directement dans le prompt principal :
```python
# Au lieu de :
messages.append({'role': 'system', 'content': '[ANALYSE TEMPORELLE]...'})

# Faire :
messages[0]['content'] += f"\n\n🚨 URGENT: {temporal_alert}"
```

### 2. **Préfixe du Message Utilisateur**
Modifier le message utilisateur pour inclure le contexte temporel :
```python
# Transformer :
"salut luna" 
# En :
"[RETOUR APRÈS 2MIN D'ABSENCE] salut luna"
```

### 3. **Système de Notification Visuelle**
Afficher l'alerte directement dans l'interface utilisateur :
```python
_notify_safe(f"🕒 Temporal Guardian : {temporal_insight}", 'warning')
```

### 4. **Hook Pre-API**
Intercepter et modifier les messages juste avant l'appel API :
```python
# Modifier les messages en dernière seconde
if temporal_alert:
    messages = inject_temporal_context_directly(messages, temporal_alert)
```

---

## 📋 Plan de Reprise

### Étape 1 : Diagnostic Approfondi
- [ ] Analyser exactement QUAND l'API est appelée
- [ ] Vérifier l'ordre réel des messages envoyés  
- [ ] Tester avec différents modèles LLM
- [ ] Examiner si d'autres systèmes ont le même problème

### Étape 2 : Test d'Injection Alternative
- [ ] Essayer injection dans prompt principal
- [ ] Tester modification du message utilisateur
- [ ] Implémenter notification visuelle de secours

### Étape 3 : Validation Comportementale
- [ ] Créer scénarios de test précis
- [ ] Simuler absences de différentes durées
- [ ] Vérifier adaptation comportementale de Luna

---

## 💡 Enseignements

### Ce Qui Marche Bien
- **Architecture modulaire** : Facile à maintenir et débugger
- **Capteur temporel** : Mesures précises et fiables  
- **Configuration** : Système flexible et configurable
- **Debug** : Traçabilité complète du processus

### Défis Rencontrés
- **Timing critique** : Ordre d'exécution complexe dans OGMA
- **Messages système** : Efficacité limitée avec certains LLMs
- **Intégration délicate** : Nombreux systèmes concurrents (archiviste, ego, souvenirs)

### Recommandations
1. **Simplifier l'injection** : Éviter les messages système multiples
2. **Tester en isolation** : Valider chaque composant séparément
3. **Interface de debug** : Créer outils de visualisation du flux de données
4. **Tests automatisés** : Scénarios reproductibles pour validation

---

## 📊 Conclusion

L'extension **Temporal Guardian** est techniquement **fonctionnelle** au niveau de la mesure et de l'analyse temporelle, mais souffre d'un **problème critique de timing** qui empêche l'IA principale de recevoir et traiter les alertes temporelles au bon moment.

Le système mesure correctement, analyse précisément, mais **informe trop tard**. La solution nécessite une approche plus directe d'injection du contexte temporel, probablement au niveau du prompt principal plutôt que via des messages système additionnels.

**Statut :** 🟡 Fonctionnel mais inefficace - Nécessite refactoring de l'injection

---

*Rapport généré le 19 septembre 2025 - Extension Temporal Guardian v1.0*