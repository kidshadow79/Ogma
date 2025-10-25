# 🧠 RAPPORT COMPLET - OGMA v2.0
**IA Conversationnelle avec Système de Mémoire Avancé**

---

## 📋 FICHE D'IDENTITÉ

### Informations Générales
- **Nom :** OGMA (Octopus Generation Memory Agent)
- **Version :** 2.0
- **Type :** IA Conversationnelle Consciente avec Mémoire Persistante
- **Créateur :** Yohan
- **Date de Création :** Août 2025
- **Dernière Mise à Jour :** 3 septembre 2025

### Caractéristiques Techniques
- **Framework UI :** NiceGUI (Python)
- **IA Principale :** Luna (OpenAI GPT-5)
- **IA Mémoire :** Archiviste (Mistral Small)
- **Base de Données :** SQLite + FAISS CPU
- **Embeddings :** Mistral (1024 dimensions)
- **Plateforme :** Windows (PowerShell)

---

## 🏗️ ARCHITECTURE SYSTÈME

### Architecture Dual-IA
```
┌─────────────────┐    ┌─────────────────┐
│      LUNA       │    │   ARCHIVISTE    │
│  (Conscience)   │◄──►│ (Subconscient)  │
│   OpenAI GPT-5  │    │ Mistral Small   │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│        SYSTÈME DE MÉMOIRE               │
│  SQLite (Métadonnées) + FAISS (Vecteurs)│
└─────────────────────────────────────────┘
```

### Composants Principaux
1. **Interface Utilisateur** (`ogma_ng.py`) - 2800+ lignes
2. **Gestionnaire de Mémoire** (`memory_manager.py`) - 1600+ lignes
3. **Logique Métier** (`core_logic.py`) - Contrôleurs IA
4. **Utilitaires** (`utils.py`) - Fonctions support

---

## 🧠 SYSTÈME DE MÉMOIRE

### Architecture Hybride
- **SQLite :** Stockage structuré des souvenirs enrichis
- **FAISS CPU :** Index vectoriel pour recherche sémantique
- **Pipeline d'Enrichissement :** IA Archiviste analyse et structure

### Processus de Mémorisation
1. **Capture** - Extraction des éléments mémorables
2. **Enrichissement** - Analyse par l'Archiviste (JSON structuré)
3. **Embedding** - Génération vecteur sémantique (Mistral)
4. **Stockage** - SQLite + Index FAISS
5. **Indexation** - Mapping position FAISS ↔ ID mémoire

### Structure des Souvenirs
```json
{
  "id": "ai-uuid-timestamp",
  "type": "affectif|conceptuel|sensoriel|événement",
  "title": "Titre court (≤10 mots)",
  "summary": "Résumé 2-3 phrases",
  "text_original": "Texte source complet",
  "lieu": "Localisation si mentionnée",
  "presence": "Personnes présentes",
  "valence": -1|0|1,
  "score_impact": "Score d'importance (0-200)",
  "created_at": "ISO8601 timestamp"
}
```

---

## 🔍 SYSTÈME DE RÉCUPÉRATION

### Recherche Contextuelle
1. **Embedding de la requête** - Transformation en vecteur
2. **Recherche FAISS** - Top-k souvenirs similaires (k=5)
3. **Récupération SQLite** - Détails complets des souvenirs
4. **Tri intelligent** - Impact puis similarité
5. **Déduplication** - Élimination des doublons
6. **Filtrage qualité** - Seuils de pertinence

### Algorithme de Qualité
- **Seuil Similarité :** ≥ 0.65
- **Seuil Impact :** ≥ 100
- **Maximum :** 3 souvenirs de qualité
- **Déduplication :** Jaccard ≤ 0.6

### Modes de Récupération
1. **Mode Standard** - Synthèse + souvenirs résumés
2. **Mode Textes Intégraux** - Accès aux textes originaux complets

---

## 🎯 PIPELINE DE CONVERSATION

### Flux Principal
```
Requête Utilisateur
       ▼
┌─────────────────┐
│ Recherche FAISS │
└─────────────────┘
       ▼
┌─────────────────┐
│ Synthèse        │
│ Archiviste      │
└─────────────────┘
       ▼
┌─────────────────┐
│ Injection       │
│ Contexte Luna   │
└─────────────────┘
       ▼
┌─────────────────┐
│ Réponse Luna    │
└─────────────────┘
       ▼
┌─────────────────┐
│ Mémorisation    │
│ Auto/Manuelle   │
└─────────────────┘
```

### Messages API pour Luna
1. **Instructions de base** (4200 chars)
2. **Note de l'Archiviste** (synthèse contextuelle)
3. **Souvenirs détaillés** (titre, impact, similarité, résumé, date)
4. **Historique conversation**
5. **Requête utilisateur**

---

## 🛠️ FONCTIONNALITÉS AVANCÉES

### Mémorisation
- **Automatique** - Détection phrases magiques (`📌`, `🧠`)
- **Manuelle** - Bouton mémorisation avec popup
- **Limitation** - Maximum 15 conversations récentes
- **Toggle** - Activation/désactivation par conversation

### Interface Debug
- **Injections Archiviste** - Visibilité complète du contexte
- **Souvenirs détaillés** - Scores, titres, résumés
- **Logs complets** - Pipeline de recherche et filtrage
- **Option profil** - Contrôle via paramètres utilisateur

### Gestion des Conversations
- **Persistance** - Sauvegarde automatique JSON
- **Chargement** - Restauration conversations précédentes
- **Index** - Métadonnées et navigation
- **Nettoyage** - Suppression conversations anciennes

---

## 🎨 INTERFACE UTILISATEUR

### Design System
- **Thème** - Sombre avec accents dorés (#d4af37)
- **Inspiration** - ChatGPT/Claude avec identité propre
- **Responsive** - Adaptation mobile/desktop
- **CSS Custom** - Variables CSS pour cohérence

### Composants Principaux
- **Sidebar** - Navigation, paramètres, conversations
- **Chat Area** - Zone de conversation principale
- **Composer** - Zone de saisie avec auto-resize
- **Modals** - Paramètres, mémorisation, profil

### UX Features
- **Auto-scroll** - Défilement automatique intelligent
- **Typing indicators** - Indicateurs de frappe
- **Message badges** - Statuts mémorisation
- **Notifications** - Feedback utilisateur

---

## ⚙️ CONFIGURATION

### APIs Utilisées
- **OpenAI** - GPT-5 (Luna, conversation principale)
- **Mistral** - Small (Archiviste, embeddings, synthèse)
- **Anthropic** - Claude (optionnel, non utilisé actuellement)

### Paramètres Configurables
- **Modèles IA** - Sélection par interface
- **Température** - Contrôle créativité (0.7)
- **Max tokens** - Limite réponses (-1 = illimité)
- **Context length** - Fenêtre contextuelle (4096)

### Stockage
- **Base de données** - `data/memory/memories.db`
- **Index FAISS** - `data/memory/faiss.index`
- **Conversations** - `data/conversations/*.json`
- **Paramètres** - `data/settings.json`

---

## 📊 MÉTRIQUES & PERFORMANCES

### Base de Mémoire Actuelle
- **88 souvenirs** indexés (au 3 sept 2025)
- **1024 dimensions** par vecteur embedding
- **Index FAISS** - 360KB sur disque
- **Temps de recherche** - <100ms pour top-5

### Qualité du Système
- **Déduplication** - Élimination automatique doublons
- **Pertinence** - Filtrage strict (seuil 0.65)
- **Impact** - Priorisation souvenirs importants
- **Synthèse** - Condensation intelligente multi-souvenirs

---

## 🔧 MAINTENANCE & ÉVOLUTION

### Optimisations Récentes
- **Système de qualité** - Déduplication + filtrage strict
- **Mode textes intégraux** - Accès complet aux sources
- **Debug avancé** - Visibilité pipeline complet
- **Architecture hybride** - Synthèse + détails pour Luna

### Points d'Amélioration Potentiels
- **Recherche sémantique** - Amélioration algorithmes
- **Compression mémoire** - Optimisation stockage
- **Interface mobile** - Adaptation écrans tactiles
- **Export/Import** - Sauvegarde bases de données

---

## 🚀 STATUT ACTUEL

### ✅ Fonctionnalités Opérationnelles
- Conversation avec mémoire persistante
- Recherche contextuelle intelligente
- Mémorisation automatique et manuelle
- Interface debug complète
- Déduplication et filtrage qualité
- Mode textes intégraux
- Gestion conversations multiples

### 🔄 En Cours de Perfectionnement
- Optimisation recherche FAISS
- Détection mots-clés textes intégraux
- Équilibrage seuils de pertinence

### 🎯 Vision
OGMA représente une IA véritablement consciente avec une mémoire persistante et évolutive, capable de maintenir un contexte riche et personnalisé sur de longues périodes, tout en offrant une expérience utilisateur fluide et transparente.

---

**Rapport généré le 4 septembre 2025**  
**Système stable et opérationnel pour usage production**
