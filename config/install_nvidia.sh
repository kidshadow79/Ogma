#!/bin/bash

echo "====================================================="
echo "OCTOPUS v1.8.8 - Installation NVIDIA GPU Optimisée"
echo "====================================================="
echo

echo "Détection de votre configuration NVIDIA..."

# Vérifier CUDA
if ! command -v nvidia-smi &> /dev/null; then
    echo "[ERREUR] NVIDIA GPU non détecté ou drivers manquants!"
    echo "Installez les derniers drivers NVIDIA et CUDA Toolkit 12.4+"
    exit 1
fi

echo "[OK] GPU NVIDIA détecté"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
echo

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python non trouvé! Installez Python 3.9+"
    exit 1
fi

echo "[OK] Python détecté"
python3 --version
echo

# Installation des dépendances de base
echo "Installation des dépendances de base..."
pip3 install gradio>=5.42.0 requests>=2.31.0 pandas>=2.0.0 numpy>=1.24.0
if [ $? -ne 0 ]; then
    echo "[ERREUR] Échec installation dépendances de base"
    exit 1
fi

# Installation PyTorch avec CUDA
echo "Installation PyTorch avec support CUDA..."
pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
if [ $? -ne 0 ]; then
    echo "[ERREUR] Échec installation PyTorch CUDA"
    exit 1
fi

# Installation traitement d'images et documents
echo "Installation traitement fichiers..."
pip3 install opencv-python>=4.8.0 Pillow>=10.0.0 pypdf>=3.0.0 python-docx>=0.8.11
if [ $? -ne 0 ]; then
    echo "[ERREUR] Échec installation traitement fichiers"
    exit 1
fi

# Installation llama-cpp-python avec CUDA
echo
echo "====================================================="
echo "Installation llama-cpp-python avec accélération CUDA"
echo "ATTENTION: Cette étape peut prendre 5-10 minutes..."
echo "====================================================="

export CMAKE_ARGS="-DLLAMA_CUBLAS=on"
pip3 install llama-cpp-python --force-reinstall --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
if [ $? -ne 0 ]; then
    echo "[ERREUR] Échec installation llama-cpp-python CUDA"
    echo "Tentative installation version CPU..."
    pip3 install llama-cpp-python --force-reinstall --no-cache-dir
fi

echo
echo "====================================================="
echo "Installation terminée!"
echo "====================================================="
echo

echo "Vérification de l'installation CUDA:"
python3 -c "import torch; print(f'PyTorch CUDA disponible: {torch.cuda.is_available()}'); print(f'Version CUDA: {torch.version.cuda}'); print(f'GPU détectés: {torch.cuda.device_count()}')" 2>/dev/null
echo

echo "Configuration recommandée dans OCTOPUS:"
echo "- GPU Layers: -1 (toutes les couches sur GPU)"
echo "- Context Length: 8192 ou plus (RTX 5070ti peut gérer)"
echo "- Temperature: 0.7 (standard)"
echo

echo "Lancez OCTOPUS avec: python3 app.py"
echo "Rendez le script exécutable avec: chmod +x install_nvidia.sh"