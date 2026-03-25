# Guide d'Installation OGMA v2.x

## 📋 Prérequis
- **Python 3.9+** (recommandé: Python 3.11)
- **Windows 10/11** ou **Linux/macOS**
- **8 GB RAM minimum** (16 GB recommandé)

## 🚀 Installation Rapide

### Option 1: Installation Standard (CPU + API)
```bash
pip install -r requirements.txt
python launch_ogma.py
```

### Option 2: Installation Minimale (sans audio lourd)
```bash
pip install -r requirements/requirements-minimal.txt
python launch_ogma.py
```

### Option 3: Installation GPU NVIDIA
```bash
pip install -r requirements.txt
pip install -r requirements/requirements-nvidia.txt
```

## 🎯 Configurations Recommandées

### RTX 5070ti (24 GB VRAM)
- **GPU Layers**: -1 (toutes les couches)
- **Context Length**: 8192-16384
- **Batch Size**: 512-1024
- **Modèles recommandés**: 
  - Llama 3.1 8B/70B
  - Mistral 7B/22B
  - Qwen 2.5 7B/14B

### RTX 4090 (24 GB VRAM)
- **GPU Layers**: -1
- **Context Length**: 4096-8192
- **Modèles recommandés**: Llama 3.1 8B, Mistral 7B

### RTX 4080/4070ti (12-16 GB VRAM)
- **GPU Layers**: 30-40
- **Context Length**: 4096
- **Modèles recommandés**: Llama 3.1 8B (Q4_K_M)

### CPU uniquement
- **GPU Layers**: 0
- **Context Length**: 2048-4096
- **Modèles recommandés**: Modèles quantifiés Q4_K_M/Q5_K_M

## 🔧 Configuration Post-Installation

### 1. Premier Lancement
```bash
python app.py
```
- L'interface s'ouvre sur `http://localhost:7860`
- Configurez vos API dans l'onglet "⚙️ Config"

### 2. Configuration des API
- **OpenAI**: Ajoutez votre clé API
- **Anthropic**: Ajoutez votre clé Claude
- **Ollama**: Installez Ollama et démarrez le service
- **GGUF**: Placez vos modèles dans `/models/`

### 3. Configuration GPU (NVIDIA)
1. Allez dans "⚙️ Config" → "💬 IA Chat" ou "🧠 IA Mémoire"
2. Sélectionnez "GGUF/llama.cpp"
3. Réglez "GPU Layers" selon votre carte
4. Choisissez votre modèle GGUF

## 🐛 Dépannage

### Problème: llama-cpp-python ne détecte pas le GPU
```bash
# Réinstallation forcée avec CUDA
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### Problème: Erreur CUDA out of memory
- Réduisez "GPU Layers"
- Diminuez "Context Length"  
- Utilisez un modèle plus petit (Q4_K_M vs Q6_K)

### Problème: Agent de perception ne fonctionne pas
- Vérifiez votre webcam
- Installez: `pip install opencv-python`
- Configurez l'index de la webcam dans "🎭 Perception"

## 📁 Structure des Dossiers
```
OCTOPUS/
├── data/               # Données utilisateur
│   ├── conversations/ # Historique des chats
│   ├── memory/        # Base de souvenirs
│   └── uploads/       # Fichiers uploadés
├── models/            # Modèles GGUF locaux
├── extensions/        # Modules d'extension
└── requirements*.txt  # Fichiers de dépendances
```

## ⚡ Optimisations Performances

### Variables d'environnement (optionnel)
```bash
# Windows
set CUDA_VISIBLE_DEVICES=0
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Linux/Mac
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
```

### Paramètres avancés GGUF
- **n_batch**: 512 (RTX 5070ti), 256 (RTX 4090)
- **n_threads**: Nombre de cœurs CPU -2
- **mlock**: True (pour éviter le swap sur gros modèles)

## 📞 Support
- **Problèmes**: Créez une issue sur GitHub
- **Documentation**: Consultez `/Protocoles_perception_et_définitions.txt`
- **Communauté**: Discord/Forum (liens dans le repo)