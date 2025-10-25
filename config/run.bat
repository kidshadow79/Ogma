@echo off
chcp 65001
echo OGMA - Demarrage
echo ================
REM Utiliser le lanceur moderne qui vérifie les dépendances et choisit le bon port
python launch_ogma.py
pause