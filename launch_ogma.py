#!/usr/bin/env python3
"""
Launch Script OGMA
===================
Script de lancement avec vérification des dépendances et configuration sécurisée
"""

import os
import sys
import io
import traceback
from pathlib import Path

# Force UTF-8 inconditionnellement (Python 3.13 + Windows cp1252 sinon)
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass
# Remplace sys.stdout/stderr par un nouveau wrapper UTF-8 (reconfigure() peut
# échouer silencieusement sur Python 3.13 selon le contexte d'exécution)
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8',
                                  errors='replace', line_buffering=True)

# Patch compatibilite Python 3.14 : pkgutil.find_loader supprime en 3.14
# mais encore utilise par vbuild 0.8.2 (dependance de NiceGUI)
import pkgutil as _pkgutil
if not hasattr(_pkgutil, 'find_loader'):
    import importlib.util as _ilu
    def _find_loader_compat(name):
        try:
            spec = _ilu.find_spec(name)
            return spec.loader if spec is not None else None
        except (ModuleNotFoundError, ValueError):
            return None
    _pkgutil.find_loader = _find_loader_compat

def check_dependencies():
    """Vérifie que les dépendances critiques sont présentes (installées par setup_venv.bat)"""
    print("🔍 Vérification des dépendances...")
    missing = []

    try:
        import nicegui
        print("✅ NiceGUI disponible")
    except ImportError:
        missing.append("nicegui>=2.0.0")

    try:
        import faiss
        print("✅ FAISS disponible")
    except ImportError:
        missing.append("faiss-cpu")

    try:
        import sqlalchemy
        print("✅ SQLAlchemy disponible")
    except ImportError:
        missing.append("sqlalchemy")

    if missing:
        print("❌ Packages manquants :", ", ".join(missing))
        print("   → Lancez : pip install " + " ".join(missing))
        print("   → Ou relancez l'installateur OGMA.")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)

def setup_environment():
    """Configure l'environnement d'exécution"""
    print("⚙️ Configuration de l'environnement...")
    
    # Forcer l'encodage UTF-8 sur Windows
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # Fix pour erreur "forrtl: error (200)" avec NumPy/PyTorch (Intel MKL) lors du Ctrl+C
        os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'
    
    # Charger le fichier .env si disponible
    env_file = Path(".env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ Variables d'environnement chargées depuis .env")
        except ImportError:
            print("⚠️ python-dotenv non installé. Installation recommandée pour la sécurité.")
    
    # Vérifier les clés API
    api_keys = {
        "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")
    }
    
    available_keys = [k for k, v in api_keys.items() if v and v != "your_key_here"]
    if available_keys:
        print(f"✅ Clés API .env: {', '.join(available_keys)}")
    # (les clés settings.json sont chargées plus tard par OGMA - pas d'avertissement ici)

def create_directories():
    """Crée les dossiers nécessaires"""
    directories = [
        Path("data"),
        Path("data/conversations"),
        Path("data/memory"),
        Path("data/memory/backup"),
        Path("data/uploads"),
        Path("models"),
        Path("static")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Auto-copie settings.example.json -> settings.json au 1er démarrage
    settings_path = Path("data/settings.json")
    settings_example = Path("data/settings.example.json")
    if not settings_path.exists() and settings_example.exists():
        import shutil
        shutil.copy2(settings_example, settings_path)
        print("✅ settings.json créé depuis settings.example.json (configurez vos clés API)")

    # Auto-copie persistent_context.default.txt -> persistent_context.txt au 1er démarrage
    context_path = Path("data/persistent_context.txt")
    context_default = Path("data/persistent_context.default.txt")
    if not context_path.exists() and context_default.exists():
        import shutil
        shutil.copy2(context_default, context_path)
        print("✅ persistent_context.txt créé depuis le fichier par défaut")

    # Auto-copie memories.seed.db -> memories.db au 1er démarrage (seeds fondateurs)
    memories_path = Path("data/memory/memories.db")
    memories_seed = Path("data/memory/memories.seed.db")
    if not memories_path.exists() and memories_seed.exists():
        import shutil
        memories_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(memories_seed, memories_path)
        print("✅ memories.db créé depuis memories.seed.db (15 mémoires fondatrices)")

    print("✅ Structure de dossiers créée")

def check_backend_files():
    """Vérifie que tous les fichiers backend sont présents"""
    required_files = [
        "core_logic.py",
        "memory_manager.py", 
        "utils.py",
        "logic_callbacks.py",
        "extensions/perception_agent.py",
        "extensions/file_processor.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        return False
    
    print("✅ Tous les fichiers backend sont présents")
    return True

def main():
    """Fonction principale de lancement"""
    print("OGMA - IA Conversationnelle avec Memoire")
    print("=" * 50)
    
    # Encodage d'abord, avant tout print avec emojis
    setup_environment()
    check_dependencies()
    create_directories()
    
    if not check_backend_files():
        print("\n❌ Impossible de lancer OGMA. Fichiers backend manquants.")
        input("Appuyez sur Entrée pour fermer...")
        return
    
    print("\nLancement d'OGMA...")
    # Silencer les loggers tiers verbeux (comtypes, etc.)
    import logging
    logging.getLogger("comtypes").setLevel(logging.WARNING)
    logging.getLogger("comtypes.client._code_cache").setLevel(logging.WARNING)
    # 0.0.0.0 pour accès réseau local (mobile, hologramme, etc.)
    # Utiliser OGMA_HOST=127.0.0.1 pour restreindre à localhost uniquement
    host = os.getenv('OGMA_HOST', '0.0.0.0')
    base_port = int(os.getenv('OGMA_PORT', '8080'))
    print("Appuyez sur Ctrl+C pour arreter")

    # Lancement de l'application avec fallback de port si occupé (interface ogma_ng)
    from ogma_ng import run_ogma
    for offset in range(0, 10):
        port = base_port + offset
        print(f"Interface disponible sur: http://{host}:{port}")
        try:
            run_ogma(host=host, port=port)
            return
        except OSError as e:
            msg = str(e)
            # Windows: [Errno 10048] address in use | Linux/Mac: [Errno 98] | Middleware error
            if ('address already in use' in msg.lower() or 
                'attempting to bind' in msg.lower() or 
                'unavailable - middleware error' in msg.lower() or
                getattr(e, 'errno', None) in (98, 10048)):
                print(f"⚠️ Port {port} occupé, tentative avec le port suivant...")
                continue
            else:
                print(f"\nErreur critique: {e}")
                traceback.print_exc()
                break
        except RuntimeError as e:
            # Gestion spécifique de l'erreur middleware
            if "Cannot add middleware" in str(e):
                print(f"⚠️ Port {port} - erreur middleware, tentative avec le port suivant...")
                continue
            else:
                print(f"\nErreur critique: {e}")
                traceback.print_exc()
                break
        except SystemExit as e:
            # Uvicorn/NiceGUI peut appeler sys.exit(1) au lieu de lever OSError
            msg = str(e)
            code = getattr(e, 'code', None)
            if (isinstance(code, int) and code != 0) or ('bind' in msg.lower() or 'address' in msg.lower()):
                print(f"⚠️ Port {port} indisponible (SystemExit), tentative avec le port suivant...")
                continue
            else:
                raise
        except KeyboardInterrupt:
            print("\nArret d'OGMA...")
            return
        except Exception as e:
            print(f"\nErreur critique: {e}")
            traceback.print_exc()
            break
    # Si on arrive ici, on n'a pas pu démarrer
    print("\n❌ Impossible de démarrer OGMA: tous les ports d'essai sont occupés ou une erreur est survenue.")
    input("Appuyez sur Entree pour fermer...")

if __name__ == "__main__":
    main()