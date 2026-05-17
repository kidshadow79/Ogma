@echo off
chcp 65001 > nul
echo OGMA - Demarrage
echo ================
REM Utilise le Python du venv avec -X utf8 (force UTF-8 avant tout chargement)
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -X utf8 "%~dp0launch_ogma.py"
) else (
    python -X utf8 launch_ogma.py
)
pause