# 🧠 COGNITIVE MIRROR - Documentation Extension

## Vue d'ensemble

L'extension **Cognitive Mirror** apporte une transparence révolutionnaire à OGMA en permettant aux utilisateurs de voir les conversations internes entre l'IA principale et l'IA-Archiviste. Cette extension répond à la problématique de transparence cognitive en révélant les processus de réflexion interne de l'IA.

## Architecture Modulaire

### 📁 Structure des fichiers

```
extensions/cognitive_mirror/
├── __init__.py                 # Point d'entrée et singleton
├── config.py                   # Configuration centralisée et persistence
├── core_cognitive_mirror.py    # Orchestrateur principal
├── inactivity_detector.py      # Surveillance utilisateur multi-niveau
├── reflection_manager.py       # Simulation conversations IA-Archiviste
├── ui_components.py           # Interface NiceGUI intégrée
└── memory_integration.py      # Système REF souvenirs
```

## 🚀 Fonctionnalités Clés

### 1. Détection d'Inactivité Intelligente
- **Trigger 1**: 30 secondes sans message utilisateur
- **Trigger 2**: 20 secondes sans activité clavier (monitoring Windows)
- **Surveillance adaptative** avec thread à faible priorité
- **Auto-désactivation** si extension OFF

### 2. Sessions Réflexives Simulées
- **Simulation conversation** entre IA principale et IA-Archiviste
- **Contexte enrichi** basé sur la conversation actuelle
- **Timeout intelligent** de 5 minutes par session
- **Limitation tokens** (500 tokens max par réflexion)

### 3. Interface Utilisateur Intégrée
- **Overlay transparent** (30% hauteur conversation)
- **Design esthétique** homogène avec OGMA
- **Animation fluide** (CSS transitions)
- **Contrôles utilisateur** (pause/reprise/fermeture)

### 4. Intégration Mémoire REF
- **Sauvegarde automatique** des insights intéressants
- **Tag "REF"** pour classification
- **Historique accessible** via système mémoire OGMA

## 🔧 Intégration OGMA

### Points d'Intégration

1. **ogma_ng.py**: 
   - Import et initialisation
   - Hooks conversation (avant/après appel IA)
   - Variable globale `_cognitive_mirror`

2. **ogma_headers.py**:
   - Bouton header avec icône `psychology_alt`
   - Toggle fonction avec feedback visuel
   - Positionnement fixed avec extensions existantes

3. **Pipeline conversation**:
   - Hook pré-traitement: enregistrement activité utilisateur
   - Hook post-traitement: enrichissement contexte pour réflexions

### Configuration par Défaut

```json
{
  "trigger_delay_no_message": 30,
  "trigger_delay_no_typing": 20,
  "max_reflection_duration": 300,
  "overlay_height_percent": 30,
  "extension_enabled": false
}
```

## 🎯 Patterns de Design

### 1. Singleton Pattern OGMA
- Instance unique via `get_cognitive_mirror()`
- Initialisation différée avec dépendances
- Thread-safe pour environnement concurrent

### 2. Observer Pattern
- Callbacks pour inactivité détectée
- Hooks pipeline conversation
- Events UI pour interactions utilisateur

### 3. Strategy Pattern
- Détection multi-plateforme (Windows/Linux/macOS)
- Fallback graceful si monitoring indisponible
- Configuration adaptive selon environnement

## 🧪 Tests et Validation

### Test d'Intégration Complet
```bash
python test_cognitive_mirror.py
```

**Validation complète**:
✅ Imports modules  
✅ Configuration chargée  
✅ Initialisation système  
✅ Détecteur inactivité  
✅ Composants UI  

## 🔄 Workflow Utilisateur

1. **Activation**: Clic bouton header Cognitive Mirror
2. **Conversation**: Utilisateur interagit normalement avec OGMA  
3. **Détection**: Extension détecte inactivité (30s sans message)
4. **Réflexion**: Overlay apparaît avec simulation conversation IA-Archiviste
5. **Insights**: Contenus intéressants automatiquement sauvés en mémoire REF
6. **Reprise**: Utilisateur peut reprendre conversation normale

## ⚡ Optimisations Performances

### Surveillance Légère
- **Thread basse priorité** pour monitoring
- **Polling adaptatif** selon activité
- **Désactivation intelligente** si extension OFF

### Ressources Minimales
- **Simulation LLM** uniquement lors d'inactivité
- **Cache contexte** pour éviter retraitement
- **Cleanup automatique** des ressources

### Intégration Non-Invasive
- **Aucun refactoring** OGMA requis
- **Fallback graceful** si extension indisponible
- **Backward compatibility** préservée

## 🎨 Esthétique et UX

### Design System OGMA
- **Cohérence visuelle** avec interface principale
- **Couleurs thématiques** (bleu IA, vert Archiviste)
- **Animations fluides** avec cubic-bezier
- **Typography** Inter font consistency

### Accessibilité
- **Contrôles clavier** pour overlay
- **Indicateurs visuels** clairs (icônes, états)
- **Feedback utilisateur** avec notifications
- **Progressive disclosure** des fonctionnalités avancées

---

## 📋 Résumé Technique

**Extension Cognitive Mirror v1.0.0**
- ✅ **Architecture complète** (7 modules)
- ✅ **Intégration OGMA** (hooks pipeline)
- ✅ **Interface utilisateur** (overlay NiceGUI)
- ✅ **Tests validation** (100% passés)
- ✅ **Documentation complète**

**Prêt pour utilisation en production** ⚡