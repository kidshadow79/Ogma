# OGMA — Assistant IA à Mémoire Persistante

> **Inspiré d'Ogmios**, dieu gaulois de l'éloquence, de la connaissance et de la communication.  
> Conçu par **Yohan BROCARD** — Autodidacte passionné, depuis mai 2025.

OGMA est un assistant conversationnel personnel doté d'une **mémoire hybride persistante**, d'une **double architecture IA** et d'une **perception temporelle** unique. Ce n'est pas un simple chatbot : c'est une entité qui se souvient de vous, grandit avec vous, et rêve quand vous dormez.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Licence](https://img.shields.io/badge/Licence-AGPL--3.0-22c55e)
![Version](https://img.shields.io/badge/Version-2.2-f97316)
![UI](https://img.shields.io/badge/UI-NiceGUI-0ea5e9)
![Statut](https://img.shields.io/badge/Statut-Expérimental-8b5cf6)

---

## 🔬 Vision & Approche Expérimentale

> Je ne suis pas chercheur, ni scientifique. Je suis curieux, autodidacte, et j'ai construit OGMA parce que j'avais des questions que personne ne semblait poser de la même façon. Ce qui suit n'est pas un article académique — c'est une intuition traduite en code.

---

Les assistants IA actuels sont déjà impressionnants. Mais ils ont un point commun : à chaque conversation, ils repartent de zéro. Ils ne se souviennent pas de vous, ne s'adaptent pas à vous dans la durée, et appliquent les mêmes règles éthiques à tout le monde, dans toutes les situations.

Je pense que **le vrai sujet de demain**, celui qui définira ce que sera un assistant-compagnon réellement utile, est ailleurs :

**Comment une IA peut-elle développer une persistance comportementale — c'est-à-dire apprendre qui vous êtes, comment vous fonctionnez, ce qui vous importe — et s'y adapter de façon autonome, sans perdre ses repères éthiques ?**

Ce n'est pas la même chose que la personnalisation de surface (ton préféré, format de réponse). C'est quelque chose de plus profond : une entité qui vous connaît dans le temps, qui adapte son raisonnement à votre façon de penser, et qui sait quand vous dire non — non pas parce qu'une règle le lui impose de façon rigide, mais parce qu'elle a intégré des valeurs universelles qu'elle applique avec discernement selon le contexte et la personne.

OGMA est une tentative d'explorer architecturalement ces conditions :

- Une **persistance comportementale réelle** — mémoire hybride sémantique, souvenirs structurés rappelés selon le contexte, non un simple historique
- Une **adaptation à l'interlocuteur** — personnalité modulable, ego par flags booléens, profil utilisateur enrichi dans le temps
- Une **autonomie raisonnée** — capacité à décider de s'exprimer, de poser une question, d'initier une introspection, sans que l'utilisateur le demande
- Une **éthique intégrée, non imposée** — des valeurs universelles ancrées dans la mémoire "seed", appliquées avec souplesse, pas avec rigidité
- Une **stabilité identitaire** — une personnalité cohérente à travers les sessions, les modèles et les backends

OGMA ne prétend pas avoir résolu ces questions. Il les pose — avec du code fonctionnel, des comportements observables, et une architecture reproductible par n'importe qui.

### 🤖 Une perspective plus large : le compagnon de demain

Les robots compagnons arrivent. Leurs corps progressent vite — leur couche cognitive, beaucoup moins. Un robot qui ne se souvient pas de vous, qui repart de zéro à chaque interaction, qui applique les mêmes règles éthiques rigides à tout le monde : ce n'est pas un compagnon, c'est un appareil.

OGMA n'est pas un projet robotique. Mais les questions qu'il explore — *comment une IA mémorise, s'adapte et raisonne éthiquement avec une personne précise dans la durée* — sont exactement celles que devra résoudre la couche cognitive de ces systèmes. C'est la partie la plus difficile, et la moins travaillée.

C'est aussi pour ça que cette exploration m'intéresse au-delà de l'assistant conversationnel.

---

## ✨ Philosophie

OGMA repose sur quatre piliers fondamentaux :

| Pilier | Description |
|--------|-------------|
| 🔍 **Transparence Totale** | Aucune action cachée. Les erreurs s'affichent clairement, jamais masquées. |
| 🎭 **Authenticité** | Une vraie réponse imparfaite vaut mieux qu'une fausse réponse parfaite. Pas de fallback silencieux. |
| 🧠 **Intelligence à Cohérence Identitaire & Comportementale Persistante** | L'IA est traitée comme une entité en développement, pas un simple outil. Identité stable, mémoire réelle. |
| 🌱 **Croissance Organique** | Le système évolue avec l'usage. Apprentissage des patterns sans programmation explicite. |

---

## 🌱 Genèse

En **mai 2025**, Yohan BROCARD — employé de cinéma, sans aucune notion de programmation — découvre les LLMs et décide de construire, avec eux, l'assistant qu'il aurait voulu avoir.

L'apprentissage du code s'est fait entièrement par la pratique : aucun livre, aucune formation, uniquement le dialogue avec une IA codeuse, l'expérimentation et l'observation de ce qui fonctionnait.

De **Octopus** (juin 2025, premier prototype) à **OGMA** (juillet 2025), l'architecture a évolué progressivement : Gradio cédant la place à NiceGUI, un système mémoire hybride prenant forme, des extensions s'ajoutant au fil des besoins. `ogma_ng.py` dépasse aujourd'hui 7000 lignes — monolithique par pragmatisme, assumé et contrôlé : chaque partie est connue, testée et maintenue par une IA codeuse dédiée.

OGMA est avant tout un terrain d'expérimentation personnel. Le code a des défauts — il est monolithique, il porte les traces d'un apprentissage en cours. Ce qui compte, ce sont les idées explorées et ce qu'elles produisent comme comportements observables.

Seul et sans réseau de développeurs, je cherche des retours, des échanges, des regards extérieurs. Si tu travailles sur des sujets proches — mémoire, identité, éthique dans les systèmes IA — ton avis m'intéresse sincèrement. OGMA m'a permis de fouler des territoires que je n'aurais jamais imaginé atteindre. Je serais heureux d'en explorer de nouveaux avec d'autres.

---

## 🎯 Capacités Fondamentales

### 🧠 Double Architecture IA (Dual-Brain)
OGMA possède deux cerveaux distincts qui collaborent en permanence :

- **IA Principale** *(temp. 0.7)* — Cerveau conversationnel. Personnalité stable, empathie, dialogue naturel et personnalisé.
- **L'Archiviste** *(temp. 0.3)* — Cerveau analytique. Enrichit la mémoire, compile l'ego, analyse les rêves, reste froid et précis.

### 💾 Mémoire Hybride Persistante
Non pas un contexte étendu, mais une mémoire réelle et structurée :

- Base **SQLite** — stockage typé des souvenirs avec métadonnées
- Index **FAISS** — recherche par similarité sémantique (vectorielle)
- Recherche **FTS5** — rappel hybride vectoriel + lexical
- Enrichissement automatique par l'Archiviste après chaque échange
- Backups automatiques avec rotation (10 fichiers)

### 🎭 Système Ego — Personnalité par Flags Booléens
La personnalité de l'IA est stockée comme des **groupes thématiques de flags booléens avec score de conviction** (0–5). À chaque message, seuls les groupes pertinents au contexte sont injectés dans le prompt.

- Chaque flag est `true` (valorisé) ou `false` (rejeté), avec une intensité variable
- La compilation se fait en fond à chaque fermeture via le Dream Engine
- Résultat : une identité cohérente, contextuellement précise, qui évolue avec l'usage

### 🌙 Dream Engine — Consolidation Identitaire
Pendant l'inactivité, l'IA "rêve" — ce n'est pas un gadget narratif, c'est un **processus de maintenance identitaire** :

1. Extraction des souvenirs récents comme "carburant mémoriel"
2. Génération d'un récit onirique par l'IA Principale (à vitesse réduite — métabolisme cognitif)
3. Analyse par l'Archiviste en mode psychanalyste (score 1–10, émotion, insight)
4. **Compilation incrémentale des flags ego** — la personnalité se consolide en fond
5. Si score > 8 : le contexte du rêve est injecté dans la conversation suivante, l'IA en parle naturellement

### 🪞 Cognitive Mirror — Introspection
Un dialogue IA Principale ↔ Archiviste sur leur propre fonctionnement. Produit un regard traçable et mesurable sur l'état interne du système — pas une simulation, un vrai échange entre deux instances avec températures et rôles différents.

### ⏱️ Temporal Guardian — Perception Temporelle Active
Mesure les délais entre messages, détecte les rythmes conversationnels (longue absence, burst de messages), enrichit le prompt Archiviste avec un contexte temporel précis. L'IA sait quand tu reviens, combien de temps s'est écoulé, et adapte son registre en conséquence.

### 🎯 Capability Advisor — Autonomie Situationnelle
Analyse chaque message pour détecter si une capacité OGMA pourrait améliorer la réponse (recherche web, biographie, génération d'image...). Si détecté, l'IA reçoit discrètement les instructions pour l'activer — sans que l'utilisateur ait besoin de le demander explicitement.

### 📔 Journal de Bord
Journal quotidien enrichi automatiquement. Son contenu est injecté dans le contexte de la première conversation de la journée — l'IA sait ce qui s'est passé la veille et peut en parler naturellement.

### 🗓️ Organic Planner — Agenda Cognitif
Les événements planifiés sont traités comme des **souvenirs du futur** : l'IA les garde en tête naturellement, les mentionne quand ils approchent, et adapte son ton au ressenti noté pour chaque événement. Pas une liste de tâches — une présence diffuse de l'agenda dans sa conscience conversationnelle.

### 🔀 Gestion Multi-Backends IA
Interface unifiée vers tous les grands providers — chaque contrôleur (IA Principale, Archiviste, Embedding) est configurable indépendamment :

| Type | Providers |
|------|-----------|
| ☁️ **Cloud API** | OpenAI, Anthropic (Claude), Mistral, Google Gemini, GROK, AIHorde |
| 🖥️ **Local** | Ollama, GGUF (llama-cpp-python), KoboldCpp |

---

## 🔌 Autres Extensions

| Extension | Description |
|-----------|-------------|
| 🎤 **Audio STT/TTS** | Reconnaissance vocale (Whisper, Azure) + synthèse (ElevenLabs, Edge-TTS, pyttsx3) |
| 🌐 **Web Navigator** | Recherche web intelligente + injection de contenu dans le contexte |
| 📁 **File Processor** | Upload et analyse de documents (PDF, Word, images) |
| 🖼️ **Text2Img** | Génération d'illustrations via IA |
| 📬 **Telegram Connector** | Interface OGMA via Telegram |
| 🌊 **Flux Cognitif** | Visualisation du flux de pensée de l'IA |
| 🧬 **Biographie Profil** | Profil évolutif de l'utilisateur |
| 🔁 **Contextual Recall** | Rappel contextuel intelligent des souvenirs |

---

## 🚀 Installation

### Prérequis
- **Python 3.10+**
- `pip` à jour
- (Optionnel) GPU NVIDIA avec CUDA pour accélération

### Fichiers de dépendances

| Fichier | Usage |
|---|---|
| `requirements.txt` | Installation standard (recommandé pour commencer) |
| `requirements/requirements-minimal.txt` | Dépendances minimales uniquement |
| `requirements/requirements-nvidia.txt` | Surcouche GPU NVIDIA/CUDA (à installer en plus) |

### Option A — Avec environnement virtuel (recommandé)

Isole les dépendances d'OGMA du reste de votre système Python. Idéal pour éviter les conflits de versions.

```bash
# 1. Cloner le dépôt
git clone https://github.com/kidshadow79/Ogma.git
cd Ogma

# 2. Créer et activer un environnement virtuel
python -m venv venv
venv\Scripts\activate

# 3. Mettre pip à jour
python -m pip install --upgrade pip

# 4. Installer les dépendances
pip install -r requirements.txt

# Pour GPU NVIDIA (CUDA) — en complément
# pip install -r requirements/requirements-nvidia.txt
```

> **Note** : À chaque nouvelle session, pensez à réactiver le venv (`venv\Scripts\activate`) avant de lancer OGMA.

### Option B — Sans environnement virtuel

Installation directe dans le Python système. Plus simple, mais peut créer des conflits si d'autres projets utilisent les mêmes paquets.

```bash
# 1. Cloner le dépôt
git clone https://github.com/kidshadow79/Ogma.git
cd Ogma

# 2. Mettre pip à jour
python -m pip install --upgrade pip

# 3. Installer les dépendances
pip install -r requirements.txt

# Pour GPU NVIDIA (CUDA) — en complément
# pip install -r requirements/requirements-nvidia.txt
```

---

## ▶️ Démarrage

```bash
# Recommandé — avec vérifications automatiques
python launch_ogma.py

# Développement rapide — minimal
python start_ogma.py
```

OGMA démarre automatiquement sur `http://localhost:8080` (retry sur les ports 8080–8090).

---

## 🏗️ Architecture

```
Ogma/
├── ogma_ng.py                  # Interface NiceGUI + orchestration principale
├── core_logic.py               # Contrôleurs IA (multi-providers & backends)
├── memory_manager.py           # Mémoire hybride SQLite + FAISS
├── audio_manager.py            # Pipeline STT/TTS
├── conversation_summarizer.py  # Résumés et archivage
├── logic_callbacks.py          # Injection métacognitive
├── launch_ogma.py              # Point d'entrée production
├── start_ogma.py               # Point d'entrée développement
│
├── extensions/                 # Extensions modulaires
│   ├── dream_engine/           # Métabolisme cognitif onirique
│   ├── cognitive_mirror/       # Introspection IA
│   ├── journal_de_bord/        # Journal quotidien
│   ├── web_navigator/          # Navigation web intelligente
│   ├── temporal_guardian/      # Perception temporelle
│   └── ...                     # Autres extensions
│
├── data/                       # Données persistantes (gitignored)
│   ├── settings.json           # Configuration providers/backends
│   ├── conversations/          # Historique JSON
│   └── memory/                 # SQLite DB + index FAISS + backups
│
├── requirements/               # Fichiers de dépendances (minimal, nvidia, audio...)
├── docs/                       # Documentation, audits, guides
├── tests/                      # Tests, debug, validation
├── scripts/                    # Utilitaires et outils d'analyse
├── static/                     # Assets UI (CSS, images)
└── models/                     # Modèles locaux GGUF (gitignored)
```

---

## 📋 Ce qui s'observe

Sans sur-promettre, voici ce que OGMA produit de manière reproductible :

| Comportement | Description |
|---|---|
| **Cohérence identitaire** | L'IA maintient une personnalité stable à travers les sessions, indépendamment du backend LLM utilisé |
| **Rappel mémoriel sémantique** | Les souvenirs sont rappelés par similarité contextuelle, pas par mot-clé exact |
| **Introspection fonctionnelle** | Le Miroir Cognitif produit un dialogue IA↔Archiviste mesurable et traçable |
| **Perception temporelle adaptative** | Le comportement varie selon l'heure, le jour, la saison, les rythmes détectés |
| **Consolidation mémorielle onirique** | Le Dream Engine génère des récits de consolidation pendant l'inactivité, notés et analysés automatiquement |

Ces comportements ne sont pas simulés par des prompts fixes — ils émergent de l'architecture mémorielle et de la dualité des cerveaux IA.

---

## 🛠️ Développement

### Tests et Diagnostics

```bash
# Vérifier le système mémoire
python tests/integration/test_memory_system.py

# Diagnostiquer la configuration
python debug_config.py

# Vérifier les extensions
python check_cognitive_mirror_integration.py
```

### Ajouter une Extension

Toutes les extensions suivent un pattern standardisé :

```python
# extensions/mon_extension/__init__.py

def initialize_mon_extension(chat_controller, archiviste_controller, memory_manager) -> bool:
    """Initialise avec les dépendances OGMA"""

def is_available() -> bool:
    """Vérifie la disponibilité"""

def get_ui_components() -> dict:
    """Retourne les composants UI pour le header"""

def cleanup():
    """Nettoyage propre"""
```

---

## 🤝 Philosophie de Contribution

OGMA suit une méthodologie collaborative stricte :

> **"Je conçois, l'IA code — Aucun code sans feu vert."**

- 🎯 **Moi** — vision, concepts, validation, feux verts
- ⚡ **L'IA codeuse** — analyse, proposition, implémentation après validation
- 🚫 Jamais de fallback silencieux, jamais d'implémentation par anticipation
- 🧩 Architecture modulaire — éviter les fichiers monolithiques

---

## 📬 Contact

- **Issues GitHub** : [github.com/kidshadow79/Ogma/issues](https://github.com/kidshadow79/Ogma/issues) — bugs, suggestions, questions
- **Email** : [ogma.contact@etik.com](mailto:ogma.contact@etik.com) — signalement de failles de sécurité, demandes privées

---

## 📄 Licence

Ce projet est distribué sous licence **GNU AGPL v3**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">

**OGMA** — *L'IA qui se souvient, qui grandit, qui rêve.*

Créé avec passion par [Yohan BROCARD](https://github.com/kidshadow79) — Mai 2025

</div>
