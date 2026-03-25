#!/usr/bin/env python3
"""
Start OGMA - Script simple sans emojis
======================================
"""

import os
import sys
from pathlib import Path

def main():
    print("OGMA - IA Conversationnelle")
    print("=" * 30)
    
    # Forcer l'encodage UTF-8 sur Windows
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # Fix pour erreur "forrtl: error (200)" avec NumPy/PyTorch (Intel MKL) lors du Ctrl+C
        os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'
    
    # Vérification des dépendances critiques
    try:
        import nicegui
        print("NiceGUI disponible")
    except ImportError:
        print("Installation de NiceGUI...")
        os.system(f"{sys.executable} -m pip install nicegui")
    
    try:
        import faiss
        print("FAISS disponible") 
    except ImportError:
        print("Installation de FAISS...")
        os.system(f"{sys.executable} -m pip install faiss-cpu")
    
    # Création des dossiers nécessaires
    directories = [
        Path("data"),
        Path("data/conversations"), 
        Path("data/memory"),
        Path("data/uploads")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("Structure de dossiers creee")
    
    # Lancement de l'application
    print("Lancement d'OGMA...")
    print("Interface: http://localhost:8080")
    
    try:
        # Préférence: interface valide ogma_ng
        from ogma_ng import run_ogma as run_main
        try:
            run_main(host='localhost', port=8080)
        except Exception as e_port:
            print(f"[WARN] Port 8080 indisponible ({e_port}), tentative sur 8081...")
            run_main(host='localhost', port=8081)
    except KeyboardInterrupt:
        print("Arret d'OGMA...")
    except Exception as e:
        print(f"[WARN] ogma_ng a échoué ({e}), tentative avec ogma_app...")
        try:
            from ogma_app import run_ogma as run_app
            run_app(host='localhost', port=8080)
        except Exception as e2:
            print(f"Erreur: {e2}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()