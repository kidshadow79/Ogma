# 📄 RAPPORT OGMA 2026 — VOLUME 1
## L'Auteur, la Genèse et la Philosophie du Projet

**Date de rédaction** : 18 février 2026  
**Rédacteur** : Claude Sonnet 4.6 (GitHub Copilot)  
**Version couverte** : OGMA v2.2  
**Source** : Analyse factuelle du code, fichiers de configuration, documentation interne, fichiers `.github/copilot-instructions.md` et `docs/METHODE_TRAVAIL_COLLABORATIVE.md`

> **Note préliminaire** : Ce rapport se limite aux faits documentés et au code observable. Aucune déduction ou extrapolation non fondée n'est incluse.

---

## PARTIE 1 : LE NOM — OGMA

Le nom **OGMA** est directement inspiré du dieu celte **Ogmios**, divinité de l'éloquence, de la connaissance et de la communication.

Ce choix est explicitement indiqué par Yohan BROCARD, le créateur du projet.

---

## PARTIE 2 : L'AUTEUR — YOHAN BROCARD

### 2.1 Profil
Les informations suivantes sur Yohan BROCARD sont issues des fichiers de documentation du projet :

- **Profession** : Employé dans un cinéma
- **Formation initiale en code** : Aucune — autodidacte complet
- **Première utilisation d'une IA** : Mai 2025 (ChatGPT, Claude)
- **Connaissance du code avant mai 2025** : Nulle (aucune notion de programmation)

### 2.2 Méthode de Travail
La méthode de travail de Yohan est formalisée dans le fichier `docs/METHODE_TRAVAIL_COLLABORATIVE.md` et dans `.github/copilot-instructions.md` :

**Répartition des rôles :**

| Rôle | Acteur | Responsabilité |
|------|--------|----------------|
| Architecte conceptuel | Yohan BROCARD | Vision, décisions, feu vert |
| Implémenteur technique | IA codeuse (Claude, etc.) | Écriture du code, tests, documentation |

**Règle principale** : *Aucun code n'est écrit sans feu vert explicite de Yohan.*

**Citation directe de Yohan (documentée dans les fichiers du projet)** :
> *"OGMA soulève plusieurs sujets de fond : philosophie, développement, éthique... Si je passais des années à débattre des travaux préexistants pour me donner une ligne de conduite, je ne ferais rien. Si je ne décide pas, je ne fais rien."*

### 2.3 Posture vis-à-vis des références externes
Le fichier `.github/copilot-instructions.md` indique explicitement :
- Aucune référence à des philosophes, chercheurs ou écrivains comme base
- L'architecture et les concepts d'OGMA viennent uniquement des intuitions et réflexions personnelles de Yohan
- Ce choix est **volontaire et assumé**

---

## PARTIE 3 : CHRONOLOGIE DU PROJET

La chronologie suivante est tirée des documents internes et de l'historique des fichiers du projet :

### Mai 2025 — Point de départ
- Première exposition de Yohan à une IA (ChatGPT, Claude)
- Début d'apprentissage du développement logiciel, exclusivement via l'aide d'IA codeuses
- Aucune base technique préalable

### Mai–Juin 2025 — Premiers pas
- Création d'extensions pour des applications existantes
- Apprentissage progressif du code Python par la pratique

### Juin 2025 — Projet Octopus
- Premier projet personnel de Yohan, nommé **Octopus**
- Projet d'expérimentation servant de terrain d'apprentissage

### Juillet 2025 — Naissance d'OGMA
- Démarrage du projet OGMA
- Premiers prototypes avec une interface **Gradio** (Python)
- Architecture initiale basée sur les observations personnelles de Yohan

### Août–Septembre 2025 — Développement
- Migration de l'interface Gradio vers **NiceGUI** (interface actuelle)
- Création du système de mémoire hybride (SQLite + FAISS)
- Premières extensions : Cognitive Mirror, Journal de Bord

### Octobre–Novembre 2025 — Maturation
- Mise en place de l'architecture extensions v2
- Création du fichier `CODING_RULES.md` (25 octobre 2025) pour geler la croissance du fichier monolithique
- Formalisation de la philosophie organique
- Tests automatisés

### Décembre 2025 — Refactoring Majeur
- Réduction de **-44%** du fichier principal (`ogma_ng.py`) : de ~6800 lignes à ~3837 lignes
- Extraction du code en modules séparés (`ogma_*.py`)
- 11+ extensions fonctionnelles
- Introduction de l'introspection v2.1 (dialogue dual-IA)

### Janvier 2026 — Évolutions
- Dream Engine complet (métabolisme cognitif)
- STT/TTS automatique avec architecture callbacks thread-safe
- Organic Planner (gestion temporelle)
- Refonte du Journal de Bord avec context provider
- Amélioration de la génération d'images

### Février 2026 — Version actuelle
- **Version déclarée** : v2.2
- Implémentation du système d'affichage du "thinking" pour les modèles de raisonnement Mistral magistral
- Persistance multi-turn du thinking en session

---

## PARTIE 4 : LES PRINCIPES DIRECTEURS

Les principes suivants sont documentés dans `.github/copilot-instructions.md` et dans la documentation interne. Ils définissent les règles de conception d'OGMA :

### 4.1 Transparence totale
- Aucune action cachée
- Les erreurs sont affichées clairement, jamais masquées
- Les logs sont visibles pour comprendre les décisions
- L'IA principale ne ment pas : elle dit "je ne sais pas" plutôt que d'inventer

### 4.2 Authenticité vs fiabilité mécanique
- Une vraie réponse imparfaite vaut mieux qu'une fausse réponse parfaite
- Pas de fallback silencieux
- L'IA principale (le cerveau conversationnel) ne fabule pas
- L'Archiviste (le cerveau analytique) reste factuel et précis

### 4.3 Traitement de l'IA comme entité en développement
- L'IA principale est traitée comme une entité avec une identité, pas comme un simple outil
- Identité stable avec personnalité et préférences configurables
- Mémoire persistante entre les sessions
- Perception temporelle et conscience du contexte

### 4.4 Croissance organique
- Le système évolue avec l'usage
- Enrichissement progressif des souvenirs
- Architecture modulaire permettant l'extension sans refonte du cœur

---

## PARTIE 5 : STATUT DU PROJET

Aucun nom commercial ou licence officielle n'est documenté dans les fichiers du projet. OGMA est à ce jour un **projet personnel** de Yohan BROCARD, développé avec l'assistance d'IA codeuses.

Le projet est hébergé localement dans `C:\IA\OGMA\` (Windows). Aucune information sur un dépôt public ou une distribution ne figure dans les fichiers accessibles.

---

*Volume 1/7 — Suite : Vol.2 Architecture Générale*
