@echo off
echo =====================================================
echo OCTOPUS v1.8.8 - Installation NVIDIA GPU Optimisee
echo =====================================================
echo.
echo Detection de votre configuration NVIDIA...

:: Vérifier CUDA
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] NVIDIA GPU non detecte ou drivers manquants!
    echo Installez les derniers drivers NVIDIA depuis https://www.nvidia.com/drivers/
    pause
    exit /b 1
)

echo [OK] GPU NVIDIA detecte
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
echo.

:: Vérifier Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python non trouve! Installez Python 3.9+ depuis https://python.org
    pause
    exit /b 1
)

echo [OK] Python detecte
python --version
echo.

:: Installation des dépendances de base
echo Installation des dependances de base...
pip install gradio>=5.42.0 requests>=2.31.0 pandas>=2.0.0 numpy>=1.24.0
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation dependances de base
    pause
    exit /b 1
)

:: Installation PyTorch avec CUDA
echo Installation PyTorch avec support CUDA...
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation PyTorch CUDA
    pause
    exit /b 1
)

:: Installation traitement d'images et documents
echo Installation traitement fichiers...
pip install opencv-python>=4.8.0 Pillow>=10.0.0 pypdf>=3.0.0 python-docx>=0.8.11
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation traitement fichiers
    pause
    exit /b 1
)

:: Installation llama-cpp-python avec CUDA (critique pour GPU)
echo.
echo =====================================================
echo Installation llama-cpp-python avec acceleration CUDA
echo ATTENTION: Cette etape peut prendre 5-10 minutes...
echo =====================================================
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pip install llama-cpp-python --force-reinstall --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation llama-cpp-python CUDA
    echo Tentative installation version CPU...
    pip install llama-cpp-python --force-reinstall --no-cache-dir
)

echo.
echo =====================================================
echo Installation terminee!
echo =====================================================
echo.
echo Verification de l'installation CUDA:
python -c "import torch; print(f'PyTorch CUDA disponible: {torch.cuda.is_available()}'); print(f'Version CUDA: {torch.version.cuda}'); print(f'GPU detectes: {torch.cuda.device_count()}')" 2>nul
echo.

echo Configuration recommandee dans OCTOPUS:
echo - GPU Layers: -1 (toutes les couches sur GPU)
echo - Context Length: 8192 ou plus (RTX 5070ti peut gerer)
echo - Temperature: 0.7 (standard)
echo.

echo Lancez OCTOPUS avec: python app.py
echo Ou utilisez: octopus.bat
pause