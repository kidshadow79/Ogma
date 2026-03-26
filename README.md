# OGMA — Assistant IA à Mémoire Persistante

> **Inspiré d'Ogmios**, dieu gaulois de l'éloquence, de la connaissance et de la communication.  
> Conçu par **Yohan BROCARD** — Autodidacte passionné, depuis mai 2025.

OGMA est un assistant conversationnel personnel doté d'une **mémoire hybride persistante**, d'une **double architecture IA** et d'une **perception temporelle** unique. Ce n'est pas un simple chatbot : c'est une entité qui se souvient de vous, grandit avec vous, et rêve quand vous dormez.

---

## ✨ Philosophie

OGMA repose sur quatre piliers fondamentaux :

| Pilier | Description |
|--------|-------------|
| 🔍 **Transparence Totale** | Aucune action cachée. Les erreurs s'affichent clairement, jamais masquées. |
| 🎭 **Authenticité** | Une vraie réponse imparfaite vaut mieux qu'une fausse réponse parfaite. Pas de fallback silencieux. |
| 🧠 **Intelligence Proto-Consciente** | L'IA est traitée comme une entité en développement, pas un simple outil. Identité stable, mémoire réelle. |
| 🌱 **Croissance Organique** | Le système évolue avec l'usage. Apprentissage des patterns sans programmation explicite. |

---

## 🎯 Fonctionnalités Clés

### 🧠 Dual-IA Architecture
OGMA possède deux cerveaux distincts qui collaborent en permanence :

- **IA Principale** *(temp. 0.7)* — Cerveau conversationnel chaleureux et empathique. Interface naturelle et personnalisée.
- **L'Archiviste** *(temp. 0.3)* — Cerveau analytique froid et précis. Enrichit et structure la mémoire en arrière-plan.

### 💾 Mémoire Hybride Persistante
- Base **SQLite** pour le stockage structuré des souvenirs
- Index **FAISS** pour la recherche vectorielle sémantique
- Recherche plein texte **FTS5** intégrée
- Enrichissement automatique par l'Archiviste après chaque échange
- Backups automatiques avec rotation (10 fichiers)

### ⏰ Perception Temporelle
- Conscience de l'heure, du jour, de la saison
- Détection des rythmes de vie de l'utilisateur
- Injection contextuelle du moment de la journée

### 🎤 Audio Complet (STT/TTS)
- **Reconnaissance vocale** : Whisper (local), Azure, Google Cloud
- **Synthèse vocale** : pyttsx3, gTTS, Edge-TTS, ElevenLabs, Azure
- Détection automatique des moteurs disponibles

### 🔀 Multi-Backends IA
Compatible avec tous les grands providers :

| Type | Providers |
|------|-----------|
| ☁️ **Cloud API** | OpenAI (GPT-4/5), Anthropic (Claude), Mistral, Google Gemini, GROK, AIHorde |
| 🖥️ **Local** | Ollama, GGUF (llama-cpp-python), KoboldCpp |

---

## 🔌 Extensions

OGMA est modulaire. Chaque extension suit un pattern singleton standardisé :

| Extension | Description |
|-----------|-------------|
| 🌙 **Dream Engine** | L'IA "rêve" pendant l'inactivité — consolidation mémorielle onirique avec illustration |
| 🪞 **Cognitive Mirror** | Introspection et métacognition — dialogue IA principale ↔ Archiviste |
| 📔 **Journal de Bord** | Journal quotidien avec injection de contexte matinal |
| 🌐 **Web Navigator** | Scraping intelligent + injection de contenu web dans le contexte |
| 📁 **File Processor** | Upload et analyse de documents (PDF, Word, images) |
| 🖼️ **Text2Img** | Génération d'illustrations via IA |
| 📬 **Telegram Connector** | Interface OGMA via Telegram |
| 🌊 **Flux Cognitif** | Visualisation du flux de pensée de l'IA |
| 🗓️ **Organic Planner** | Planification adaptative et contextuelle |
| 🧬 **Biographie Profil** | Profil évolutif de l'utilisateur |
| 🎯 **Capability Advisor** | Conseils basés sur les capacités détectées |
| 🔁 **Contextual Recall** | Rappel contextuel intelligent des souvenirs |

---

## 🚀 Installation

### Prérequis
- **Python 3.10+**
- `pip` à jour
- (Optionnel) GPU NVIDIA avec CUDA pour accélération

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/kidshadow79/Ogma.git
cd Ogma

# 2. Installer les dépendances
pip install -r requirements.txt

# Pour GPU NVIDIA (CUDA)
# pip install -r requirements/requirements-nvidia.txt

# 3. Configurer les clés API
cp .env.example .env
# Éditer .env avec vos clés API
```

### Configuration `.env`
```env
# Au minimum une clé API pour démarrer
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...

# Optionnel - Audio cloud
ELEVENLABS_API_KEY=...
AZURE_SPEECH_KEY=...
```

> **Note** : Sans clé API, OGMA fonctionne avec des modèles locaux (Ollama ou GGUF).

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

> **"Yohan (l'architecte) conçoit, l'IA code — Aucun code sans feu vert."**

- 🎯 L'**architecte** définit la vision, valide les concepts, donne les feux verts
- ⚡ L'**IA codeuse** analyse, propose, implémente après validation
- 🚫 Jamais de fallback silencieux, jamais d'implémentation par anticipation
- 🧩 Architecture modulaire — éviter les fichiers monolithiques

---

## 📄 Licence

Ce projet est distribué sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">

**OGMA** — *L'IA qui se souvient, qui grandit, qui rêve.*

Créé avec passion par [Yohan BROCARD](https://github.com/kidshadow79) — Mai 2025

</div>