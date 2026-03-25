#!/usr/bin/env python3
"""
Script de compilation OGMA v2.0 en exécutable portable
Crée un .exe standalone avec toutes les dépendances
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def compile_ogma():
    """Compile OGMA en exécutable portable"""
    print("🚀 Compilation OGMA v2.0 en .exe")
    print("=" * 40)
    
    # Vérifier PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller disponible")
    except ImportError:
        print("❌ PyInstaller manquant, installation...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Paramètres de compilation
    main_script = "ogma_ng.py"
    app_name = "OGMA_v2.0"
    
    # Dossiers à inclure
    data_folders = [
        "--add-data", "static;static",
        "--add-data", "data;data", 
        "--add-data", "models;models",
        "--add-data", "extensions;extensions"
    ]
    
    # Modules cachés critiques
    hidden_imports = [
        "--hidden-import", "torch",
        "--hidden-import", "whisper", 
        "--hidden-import", "faiss",
        "--hidden-import", "sentence_transformers",
        "--hidden-import", "pyaudio",
        "--hidden-import", "speech_recognition",
        "--hidden-import", "nicegui",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "openai",
        "--hidden-import", "anthropic",
        "--hidden-import", "mistralai"
    ]
    
    # Options de compilation
    compile_options = [
        "pyinstaller",
        "--onefile",                    # Un seul fichier .exe
        "--windowed",                   # Pas de console
        "--name", app_name,             # Nom de l'exécutable
        "--icon", "static/ogma_logo.ico" if Path("static/ogma_logo.ico").exists() else None,
        "--clean",                      # Nettoyer avant compilation
        "--noconfirm",                 # Pas de confirmation
    ]
    
    # Filtrer les None
    compile_options = [opt for opt in compile_options if opt is not None]
    
    # Ajouter dossiers et imports
    compile_options.extend(data_folders)
    compile_options.extend(hidden_imports)
    compile_options.append(main_script)
    
    print(f"📦 Compilation de {main_script} → {app_name}.exe")
    print("⏳ Cela peut prendre plusieurs minutes...")
    
    # Lancer la compilation
    try:
        result = subprocess.run(compile_options, check=True, capture_output=True, text=True)
        print("✅ Compilation réussie !")
        
        # Localiser l'exécutable
        exe_path = Path("dist") / f"{app_name}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📁 Exécutable créé : {exe_path}")
            print(f"📏 Taille : {size_mb:.1f} MB")
            
            # Créer package portable
            create_portable_package(exe_path, app_name)
            
        else:
            print("❌ Exécutable non trouvé dans dist/")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur de compilation : {e}")
        print("📋 Sortie d'erreur :")
        print(e.stderr)
        return False
    
    return True

def create_portable_package(exe_path, app_name):
    """Crée un package portable complet"""
    print(f"\n📦 Création du package portable...")
    
    # Dossier de package
    package_dir = Path(f"{app_name}_Portable")
    package_dir.mkdir(exist_ok=True)
    
    # Copier l'exécutable
    shutil.copy2(exe_path, package_dir / f"{app_name}.exe")
    
    # Copier les fichiers essentiels
    essential_files = [
        ".env.template",
        "README_REQUIREMENTS.md",
        "GUIDE_INSTALLATION.md",
        "requirements.txt",
        "requirements/requirements-minimal.txt"
    ]
    
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, package_dir)
    
    # Créer un README pour le package
    readme_content = f"""# {app_name} - Version Portable

## 🚀 Utilisation
1. Copiez ce dossier où vous voulez
2. Créez un fichier .env avec vos clés API (voir .env.template)
3. Lancez {app_name}.exe
4. Ouvrez http://localhost:8080 dans votre navigateur

## 📁 Contenu
- {app_name}.exe : Application principale
- .env.template : Template pour configuration API
- README_REQUIREMENTS.md : Guide des dépendances
- GUIDE_INSTALLATION.md : Guide d'installation complet

## 🔧 Configuration
Renommez .env.template en .env et ajoutez vos clés API :
```
OPENAI_API_KEY=your_key_here
MISTRAL_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

## 🎙️ Fonctionnalités
- Interface web moderne (NiceGUI)
- IA conversationnelle avec mémoire
- Speech-to-Text (Whisper)
- Support PDF, DOCX, images
- Recherche vectorielle intelligente

Créé avec PyInstaller - Version portable autonome
"""
    
    (package_dir / "README.txt").write_text(readme_content, encoding='utf-8')
    
    print(f"✅ Package portable créé : {package_dir}/")
    print(f"📋 Contenu :")
    for item in package_dir.iterdir():
        size = item.stat().st_size / (1024 * 1024) if item.is_file() else 0
        icon = "📁" if item.is_dir() else "📄"
        print(f"   {icon} {item.name}" + (f" ({size:.1f} MB)" if size > 1 else ""))

def main():
    """Fonction principale"""
    print("🔧 OGMA v2.0 - Compilateur Portable")
    print("Crée un exécutable .exe standalone transportable\n")
    
    # Vérifier qu'on est dans le bon dossier
    if not Path("ogma_ng.py").exists():
        print("❌ ogma_ng.py non trouvé. Lancez depuis le dossier OGMA.")
        sys.exit(1)
    
    # Compiler
    if compile_ogma():
        print("\n🎉 Compilation terminée avec succès !")
        print("💡 Votre application est maintenant portable et autonome.")
        print("📦 Copiez le dossier *_Portable sur n'importe quel PC Windows.")
        print("🚀 Aucune installation requise sur la machine cible !")
    else:
        print("❌ Échec de la compilation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
