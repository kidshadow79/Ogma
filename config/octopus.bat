@echo off

start "" python app.py
timeout /t 8 >nul
start chrome http://localhost:7862