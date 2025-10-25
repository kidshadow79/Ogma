# 🤖 OGMA - Assistant Conversationnel Organique

> Conçu par **Yohan BROCARD** - Assistant IA avec mémoire persistante et perception temporelle

## 📁 Structure du Projet

### 🔥 **Fichiers Principaux** (Racine)
```
ogma_ng.py              # 🚀 Application principale NiceGUI
app.py                  # 🔄 Interface Gradio legacy (compatibilité)
core_logic.py           # 🧠 Contrôleurs IA et backends (API/Ollama/GGUF/Kobold)
memory_manager.py       # 💾 Mémoire persistante (SQLite + FAISS)
audio_manager.py        # 🎤 Gestion audio STT/TTS
conversation_summarizer.py # 📝 Résumés et archivage conversations
logic_callbacks.py      # 🎯 Injection métacognitive (affinité/auto-censure)
```

### 🗂️ **Dossiers Organisés**

#### 📚 `docs/` - Documentation
- **`audits/`** - Audits techniques et fonctionnels
- **`guides/`** - Guides d'installation et d'utilisation  
- **`rapports/`** - Rapports d'analyse et de développement

#### 🧪 `tests/` - Tests et Validation
- **`debug/`** - Scripts de débogage (debug_*.py)
- **`validation/`** - Scripts de validation (validate_*.py)  
- **`integration/`** - Tests d'intégration (test_*.py)

#### 🛠️ `scripts/` - Utilitaires
- **`analysis/`** - Scripts d'analyse (intimacy, phases, audit)
- **`utils/`** - Outils et utilitaires (nettoyage, migration, réparation)

#### ⚙️ `config/` - Configuration
- **`requirements*.txt`** - Dépendances Python
- **`install_*.bat/sh`** - Scripts d'installation
- **`*.bat`** - Scripts de lancement

#### 🔧 **Autres Dossiers**
- **`extensions/`** - Extensions (Temporal Guardian, Archi Sensor, etc.)
- **`models/`** - Modèles locaux (GGUF, etc.)
- **`data/`** - Données persistantes (DB, embeddings)
- **`static/`** - Assets UI (CSS, images)

---

## 🚀 Démarrage Rapide

```bash
# Lancer OGMA (NiceGUI - Recommandé)
python ogma_ng.py

# Ou version legacy (Gradio)
python app.py
```

## 🎯 Fonctionnalités Principales

- 🧠 **Double IA** : Chat principal + Archiviste enrichisseur
- 💾 **Mémoire Vectorielle** : SQLite + FAISS avec pipeline de mémorisation
- ⏰ **Perception Temporelle** : Temporal Guardian avec capteur de rythme
- 🎨 **Interface Moderne** : NiceGUI avec thinking repliable et TTS
- 🔀 **Multi-Backends** : API (OpenAI/Mistral/Anthropic/Google), Ollama, GGUF, KoboldCpp
- 🎤 **Audio Complet** : STT/TTS avec moteurs multiples (local/cloud)

## 📊 État du Refactoring

- **Fichier principal** : `ogma_ng.py` (~5880 lignes)
- **Objectif** : Réduction à ~4000 lignes (-50%)
- **Prochaine étape** : Phase 1 du refactoring (fonctions UI)

---

*Cette structure organisée facilite la navigation, la maintenance et le développement d'OGMA.*