# PLANIFICATION EXTENSION TEMPORAL_GUARDIAN

*Statut : 🚧 CONCEPTION*  
*Date de début : 19 septembre 2025*  
*Objectif : Créer une extension dédiée à la gestion temporelle intelligente dans OGMA*

---

## 🎯 CONTEXTE ET PROBLÉMATIQUE

### Situation actuelle
- ⚠️ **Logique temporelle dispersée** : `temporal_injector.py` + `behavioral_sensor.py` + code éparpillé dans `ogma_ng.py`
- ❌ **Chaînon manquant** : L'archiviste ne reçoit pas d'informations temporelles comme prévu dans la conception originale
- 🔄 **Injection temporelle désactivée** : Le prompt "temps outils subtile gère rythme vie discret" a été retiré

### Conception originale ratée
- **L'archiviste** devait analyser horodatage + temps d'absence + fatigue utilisateur
- **L'archiviste** devait informer l'IA principale des détections temporelles
- **L'IA principale** devait voir l'horodatage seulement au premier échange (éviter obsession temporelle)

---

## 🏗️ VISION EXTENSION TEMPORAL_GUARDIAN

### Objectifs principaux
1. **Centraliser** toute la logique temporelle dans une extension cohérente
2. **Réparer** le lien archiviste ↔ analyse temporelle manquant
3. **Optimiser** l'injection temporelle (tokens, performance)
4. **Étendre** les capacités d'analyse comportementale

### Responsabilités de l'extension
- 🕐 **Horodatage intelligent** (modes conditionnels)
- 📊 **Analyse comportementale** (fatigue, absence, patterns utilisateur)
- 🔄 **Communication archiviste** (bi-directionnelle)
- ⚡ **Optimisation tokens** temporels
- 📈 **Métriques et analytics** temporels
- 🎛️ **Interface configuration** unifiée

---

## 📁 STRUCTURE FINALE SIMPLIFIÉE

```
extensions/temporal_guardian/
├── __init__.py                  # Point d'entrée extension
├── config.py                    # Configuration extension
├── temporal_sensor.py           # Capteur de délais temporels simple
└── archiviste_enricher.py       # Enrichit prompt archiviste avec données temporelles
```

### Détail des composants (Version capteur simple)

#### `temporal_sensor.py` - Capteur de mesure pure
- Mesure délais entre messages utilisateur
- Collecte métadonnées temporelles (heure, session, etc.)
- **AUCUNE interprétation** - juste des données brutes
- Interface simple pour récupérer les mesures

#### `archiviste_enricher.py` - Pont intelligent
- Récupère données du TemporalSensor
- Enrichit le prompt archiviste existant
- Format données pour analyse contextuelle
- **L'archiviste fait toute l'intelligence temporelle**

#### `config.py` - Configuration
- Activation/désactivation extension
- Format des données transmises à l'archiviste
- Paramètres de session (optionnels)

---

## 🔄 FLUX D'INTÉGRATION PRÉVU (ARCHITECTURE FINALE)

### Principe : Capteur mesure + Archiviste interprète

```
1. Message utilisateur → OGMA
2. TemporalSensor mesure délai depuis dernier message
3. TemporalSensor enrichit prompt archiviste avec données brutes :
   - Délai temporel exact (ex: 47 secondes)
   - Heure du message (ex: 22:35)
   - Contexte session (ex: 5e message, session 1h20)
4. Archiviste reçoit ces données + conversation
5. Archiviste interprète organiquement → analyse contextuelle
6. Archiviste guide IA principale si nécessaire
```

### Données brutes transmises à l'archiviste
```
CONTEXTE TEMPOREL:
- Délai depuis dernier message: 47 secondes
- Heure actuelle: 22:35
- Session en cours depuis: 1h20
- Nombre de messages: 5
- Délai moyen session: 12 secondes
```

### Intelligence de l'archiviste (exemples)
L'archiviste peut déduire :
- **47s à 22h35** → "Possiblement fatigué, réponse plus lente"
- **47s sur question complexe** → "Prend le temps de réfléchir, bien"
- **47s après 5s habituels** → "Changement de rythme, pourquoi ?"
- **47s + bâillements dans message** → "Fatigue confirmée"

### Avantages approche capteur simple + archiviste intelligent
- **Séparation responsabilités** : Capteur = mesure, Archiviste = intelligence
- **Flexibilité totale** : L'archiviste adapte selon contexte conversation
- **Évolution naturelle** : L'archiviste apprend les patterns sans code
- **Pas de rigidité** : Aucun seuil fixe, tout est contextuel

---

## ⚠️ POINTS D'ATTENTION ET RISQUES

### Risques techniques identifiés
- **Complexité intégration** : Modifier l'architecture existante sans casser
- **Performance** : Ajouter analyse temporelle sans impacter latence
- **Cohérence** : Maintenir compatibilité avec système d'extensions existant

### Questions ouvertes
- **Fréquence analyse** : À chaque message ou par batch ?
- **Persistance données** : Où stocker historique comportemental ?
- **Seuils adaptatifs** : Comment ajuster automatiquement les détections ?

---

## 📋 PLAN D'IMPLÉMENTATION (VERSION FINALE)

### Phase 1 : Capteur temporel simple
1. ✅ Créer extension `temporal_guardian/`
2. ✅ Développer `temporal_sensor.py` (mesure délais uniquement)
3. ✅ Développer `archiviste_enricher.py` (enrichit prompt archiviste)
4. ✅ Tests intégration archiviste avec données temporelles

### Phase 2 : Validation organique
1. 🔄 Tester réactions archiviste avec contexte temporel
2. 🔄 Affiner format données transmises
3. 🔄 Valider pertinence analyses archiviste
4. 🔄 Optimiser prompt enrichi

### Phase 3 : Raffinements (si nécessaire)
1. ⏸️ Interface configuration (activation/désactivation)
2. ⏸️ Métriques session temporelles
3. ⏸️ Optimisations performance

### Phase 4 : Documentation et finalisation
1. ⏸️ Documentation utilisateur
2. ⏸️ Guide configuration archiviste
3. ⏸️ Tests complets système

---

## 💭 NOTES DE RÉFLEXION

*Cette section sera mise à jour au fur et à mesure des discussions et décisions*

### Décisions prises
- **Approche organique validée** : L'archiviste comme analyste temporel principal
- **Capteur existant identifié** : `BehavioralSensor` déjà implémenté avec patterns temporels
- **BehavioralSensor non utilisé** : Module autonome, pas intégré dans aucune extension actuellement
- **DÉCISION FINALE RÉVISÉE** : Capteur simple → données brutes temporelles → Archiviste intelligent
- **Rôle capteur** : Mesure délais uniquement, pas d'interprétation
- **Rôle archiviste** : Déduction intelligente des causes et contexte

### Idées à valider
- **Analyse conditionnelle** : Analyser seulement si lien temporal ou écart temporel détecté
- **Approche organique** : L'archiviste comme analyste temporel principal avec instructions dédiées

### Problèmes identifiés
- **Rigidité Python vs flexibilité organique** : Seuils fixes vs adaptation naturelle
- **Architecture en question** : Capteur → Archiviste → IA vs Capteur → IA directement
- **Intelligence du capteur** : Préprogrammé vs adaptatif intelligent
- **VALIDATION SEUILS** : Système actuel trop rigide et binaire (30s=réflexion, 120s=absence)
- **Manque de nuances** : Pas de gradation contextuelle ni d'adaptation personnelle

---

*Dernière mise à jour : 19 septembre 2025*

---

## 🧠 FONCTIONNEMENT DU BEHAVIORALSENSOR

### Principe de base
Le `BehavioralSensor` agit comme un **chronomètre intelligent** qui observe les délais entre les messages utilisateur et en déduit des patterns comportementaux.

### Comment ça marche concrètement

#### 1. **Enregistrement des messages**
```python
# À chaque message utilisateur
sensor.register_user_message("Bonjour Luna")
# → Calcule le délai depuis le dernier message
# → Analyse si ce délai révèle un pattern
```

#### 2. **Classification automatique des délais**
- **< 10s** : Normal, aucun événement
- **30s-2min** : Pause réflexion → "L'utilisateur semble prendre le temps de formuler sa réponse"
- **> 2min** : Absence → "Absence de X minutes détectée. L'utilisateur était probablement interrompu"
- **Patterns nocturnes** : Détection fatigue après 22h si délais > habitude

#### 3. **Génération d'événements typés**
```python
BehavioralEvent(
    timestamp=datetime.now(),
    event_type="reflexion",  # absence, fatigue, retour
    duration=45.2,           # 45.2 secondes
    context="Pause réflexive de 45 secondes...",
    severity=0.3             # 0.0-1.0
)
```

#### 4. **Contexte pour l'archiviste**
```python
sensor.get_archiviste_context()
# → "Observations comportementales récentes :
#    • Pause réflexive de 45 secondes. L'utilisateur semble formuler sa réponse.
#    • Absence de 3 minutes détectée. L'utilisateur était probablement interrompu."
```

### Seuils configurables
- **pause_reflexion**: 30s (peut être ajusté selon utilisateur)
- **pause_longue**: 120s (2min pour détecter absence)
- **heure_fatigue**: 22h (surveillance nocturne)
- **facteur_fatigue**: 2.0 (x2 plus lent = fatigue possible)

### Intelligence adaptative
- **Apprentissage baseline** : Calcule le temps de réponse moyen habituel de l'utilisateur
- **Comparaison contextuelle** : "Ralentissement nocturne (15s vs 5s habituels)"
- **Mémoire limitée** : Garde seulement les 50 derniers événements

### Avantages pour l'archiviste
- **Contexte riche** : Comprend si l'utilisateur est pressé, réfléchi, fatigué
- **Adaptation comportementale** : Peut suggérer à Luna un style approprié
- **Détection patterns** : Identifie les rythmes personnels de l'utilisateur