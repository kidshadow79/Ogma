@echo off
REM Script Windows pour lancer l'analyse rétroactive du Journal v2.0

echo ============================================================
echo  JOURNAL DE BORD v2.0 - Analyse Retroactive
echo ============================================================
echo.

REM Demander le nombre de conversations
set /p NUM_CONV="Nombre de conversations a analyser (defaut=3): "
if "%NUM_CONV%"=="" set NUM_CONV=3

echo.
echo Analyse des %NUM_CONV% dernieres conversations...
echo.

REM Lancer le script Python
python extensions\journal_de_bord\analyze_retroactive.py -n %NUM_CONV%

echo.
echo ============================================================
echo  Analyse terminee !
echo ============================================================
echo.

pause
