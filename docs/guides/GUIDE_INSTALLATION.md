# 🚀 Guide d'Installation OGMA v2.0

## 📋 Prérequis

- **Python 3.9+** (recommandé 3.10 ou 3.11)
- **Windows 10/11** (testé), Linux ou macOS
- **8GB RAM minimum** (16GB recommandé pour Whisper local)
- **Connexion Internet** pour les APIs

## ⚡ Installation Rapide

### Option 1: Installation Complète (Recommandée)
```bash
# Cloner le projet
git clone <repository-url>
cd OGMA

# Installer toutes les dépendances
pip install -r requirements-complete.txt

# Lancer OGMA
python ogma_ng.py
```

### Option 2: Installation Minimale
```bash
# Installer les dépendances essentielles uniquement
pip install -r requirements-minimal.txt

# Lancer OGMA
python ogma_ng.py
```

## 🔧 Configuration

### 1. Variables d'environnement
Créer un fichier `.env` à la racine :
```env
# APIs obligatoires
OPENAI_API_KEY=your_openai_key
MISTRAL_API_KEY=your_mistral_key
ANTHROPIC_API_KEY=your_anthropic_key

# Optionnel
GROQ_API_KEY=your_groq_key
```

### 2. Première utilisation
1. Lancez `python ogma_ng.py`
2. Ouvrez http://localhost:8080
3. Configurez vos modèles dans Paramètres > IA/Modèles
4. Testez le microphone dans Paramètres > Profil > Options Audio

## 🎙️ Fonctionnalités Audio

### Speech-to-Text activé avec :
- **Whisper local** (qualité maximale, hors ligne)
- **Google Speech** (fallback rapide)
- **Contrôle manuel** : Clic pour démarrer/arrêter
- **Transcription intégrale** sans coupure

### Utilisation :
1. Cliquez sur le bouton microphone 🎙️
2. Le bouton devient rouge ⏹️ → Parlez librement
3. Cliquez ⏹️ pour arrêter → Transcription automatique
4. Texte affiché dans le champ de saisie

## 🧠 Système de Mémoire

- **Base vectorielle FAISS** : Recherche sémantique rapide
- **SQLite** : Stockage persistant des conversations
- **Archiviste IA** : Enrichissement contextuel automatique
- **Déduplication** : Évite les répétitions mémorielles

## 🔧 Dépannage

### Problème audio Windows
```bash
# Si PyAudio ne s'installe pas
pip install pipwin
pipwin install pyaudio
```

### Problème Whisper
```bash
# Installation manuelle
pip install openai-whisper torch torchaudio
```

### Problème FAISS
```bash
# Version CPU uniquement
pip install faiss-cpu==1.7.4
```

## 📁 Structure des fichiers

```
OGMA/
├── ogma_ng.py              # Interface principale
├── memory_manager.py       # Système de mémoire
├── audio_manager.py        # Gestion audio
├── core_logic.py          # Logique métier
├── data/
│   ├── settings.json      # Configuration
│   ├── memory/           # Base de données mémoire
│   └── conversations/    # Historique conversations
└── static/
    └── ogma_styles.css   # Styles interface
```

## 🎯 Fonctionnalités Principales

### ✅ Disponibles
- **Interface NiceGUI** moderne et réactive
- **Dual-IA** : Luna (OpenAI) + Archiviste (Mistral)
- **Mémoire hybride** : Vectorielle + SQL
- **Speech-to-Text** : Whisper + contrôle manuel
- **Support multi-formats** : PDF, DOCX, images
- **Mode debug** : Visibilité injections Archiviste

### 🔄 En développement
- **Text-to-Speech** : Synthèse vocale
- **Vision** : Analyse d'images avancée
- **Plugins** : Système d'extensions

## 📞 Support

- **Documentation** : `/GUIDE_DEMARRAGE.md`
- **Configuration** : `/INSTALLATION.md`
- **Migration** : `/MIGRATION_NICEGUI_README.md`

## 🎉 Prêt !

Une fois installé, OGMA sera accessible sur **http://localhost:8080**

Profitez de votre IA conversationnelle avec mémoire et reconnaissance vocale ! 🚀
