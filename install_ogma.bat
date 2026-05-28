@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
title Installation de OGMA

echo =======================================================
echo          OGMA - Programme d'Installation (Pip)
echo =======================================================
echo Ce script va installer les dependances d'Ogma.
echo.

:: Verification de python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.10+ et relancer le script.
    pause
    exit /b 1
)

echo [1/4] Installation du Core (Base requise)
echo.
python -m pip install -r requirements/requirements-core.txt
echo.

echo =======================================================
echo                 MODULES OPTIONNELS
echo =======================================================
echo.

:: Question 1 : Audio
set /p install_audio="Voulez-vous installer le module Audio / Vocal (Micro, Synthese, Bruitages) ? [O/N] : "
if /i "%install_audio%"=="O" (
    echo.
    echo Installation du module Audio...
    python -m pip install -r requirements/requirements-audio.txt
) else (
    echo Module Audio ignore.
)
echo.

:: Question 2 : Vision
set /p install_vision="Voulez-vous installer le module Vision (Webcam OpenCV) ? [O/N] : "
if /i "%install_vision%"=="O" (
    echo.
    echo Installation du module Vision...
    python -m pip install -r requirements/requirements-vision.txt
) else (
    echo Module Vision ignore.
)
echo.

:: Question 3 : Local AI
set /p install_local="Voulez-vous installer les modeles d'IA Locaux (Llama.cpp, Transformers) ? [O/N] : "
if /i "%install_local%"=="O" (
    echo.
    echo Installation du module IA Locale...
    python -m pip install -r requirements/requirements-local-ai.txt
) else (
    echo Module IA Locale ignore.
)

echo.
echo =======================================================
echo Installation terminee ! Vous pouvez maintenant lancer Ogma.
echo =======================================================
pause
