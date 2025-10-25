# 📦 OGMA v2.0 - Guide des Requirements

## 🎯 Fichiers de Requirements Disponibles

### 1. `requirements-complete.txt` (Recommandé)
**Installation complète avec toutes les fonctionnalités**
```bash
pip install -r requirements-complete.txt
```
**Inclut :**
- ✅ Interface NiceGUI complète
- ✅ Toutes les APIs IA (OpenAI, Anthropic, Mistral)
- ✅ Système audio complet (Whisper + Speech Recognition)
- ✅ Mémoire vectorielle (FAISS + SentenceTransformers)
- ✅ Support tous documents (PDF, DOCX, images)
- ✅ Modèles locaux (GGUF, transformers)
- ✅ Extensions et utilitaires

### 2. `requirements-minimal.txt`
**Installation minimale pour démarrer rapidement**
```bash
pip install -r requirements-minimal.txt
```
**Inclut :**
- ✅ Interface NiceGUI
- ✅ APIs essentielles (OpenAI, Mistral, Anthropic)
- ✅ Audio Speech-to-Text (Whisper + PyAudio)
- ✅ Mémoire de base (FAISS + SQLAlchemy)
- ✅ Documents de base (PDF, DOCX)

### 3. `requirements-nicegui.txt` (Legacy)
**Ancien fichier, utilisez les nouveaux**

## 🚀 Installation Recommandée

### Étape 1 : Environnement
```bash
# Créer un environnement virtuel (recommandé)
python -m venv ogma_env
ogma_env\Scripts\activate  # Windows
# source ogma_env/bin/activate  # Linux/Mac
```

### Étape 2 : Installation
```bash
# Installation complète (recommandée)
pip install -r requirements-complete.txt

# OU installation minimale
pip install -r requirements-minimal.txt
```

### Étape 3 : Vérification
```bash
# Tester toutes les dépendances
python test_dependencies.py
```

### Étape 4 : Configuration
```bash
# Copier le template d'environnement
copy .env.template .env  # Windows
# cp .env.template .env  # Linux/Mac

# Éditer .env avec vos clés API
```

### Étape 5 : Lancement
```bash
python ogma_ng.py
# Ouvrir http://localhost:8080
```

## 🔧 Dépendances Critiques

### Audio (Obligatoire pour Speech-to-Text)
- `openai-whisper` : Transcription locale haute qualité
- `pyaudio` : Capture audio temps réel
- `speechrecognition` : Interface unifiée
- `torch` : Backend pour Whisper

### Mémoire (Obligatoire pour IA)
- `faiss-cpu` : Recherche vectorielle
- `sqlalchemy` : Base de données conversations
- `sentence-transformers` : Encodage vectoriel

### Interface (Obligatoire)
- `nicegui>=1.4.0` : Interface web moderne

### APIs IA (Au moins une)
- `openai>=1.0.0` : GPT-4, GPT-5, Whisper API
- `mistralai>=0.4.0` : Archiviste (Mistral Small)
- `anthropic>=0.25.0` : Claude (optionnel)

## 🆘 Dépannage Installation

### Problème PyAudio (Windows)
```bash
pip install pipwin
pipwin install pyaudio
```

### Problème Whisper
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install openai-whisper
```

### Problème FAISS
```bash
pip install faiss-cpu==1.7.4 --no-cache-dir
```

### Problème Anthropic/Mistral
```bash
pip install anthropic mistralai --upgrade
```

## ✅ Validation

Après installation, le test `python test_dependencies.py` doit afficher :
```
🎉 Toutes les dépendances sont installées et fonctionnelles!
✅ OGMA est prêt à être lancé avec: python ogma_ng.py
```

## 📊 État Actuel

D'après le dernier test :
- ✅ **Audio** : Whisper, PyAudio, SpeechRecognition → **FONCTIONNEL**
- ✅ **Mémoire** : FAISS, SQLAlchemy, Pandas → **FONCTIONNEL**
- ✅ **Interface** : NiceGUI → **FONCTIONNEL**
- ✅ **IA principale** : OpenAI → **FONCTIONNEL**
- ⚠️ **APIs secondaires** : Anthropic, Mistral → À installer
- ⚠️ **Documents avancés** : PyPDF, TorchAudio → À installer

## 🎯 Pour une expérience complète

Installez le requirements complet :
```bash
pip install -r requirements-complete.txt
```

**OGMA est déjà fonctionnel avec le système audio manuel qui fonctionne parfaitement !** 🎙️✅
