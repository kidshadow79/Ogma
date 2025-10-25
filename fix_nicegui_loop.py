# fix_nicegui_loop.py

"""
Fix pour les boucles infinies NiceGUI et problèmes Client
"""

import os
import sys
from pathlib import Path

def analyze_ogma_nicegui_issue():
    """Analyse le problème NiceGUI spécifique dans OGMA"""
    
    ogma_file = Path("ogma_ng.py")
    if not ogma_file.exists():
        print("❌ ogma_ng.py non trouvé")
        return False
    
    print("🔍 Analyse du problème NiceGUI dans ogma_ng.py...")
    
    # Lire le fichier
    try:
        with open(ogma_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Erreur lecture: {e}")
        return False
    
    # Rechercher les zones problématiques
    problematic_patterns = [
        "_process_subconscience_messages",
        "main_page() appelée",
        "ui.element('span')",
        "client.check_existence",
        "test_element = ui.element"
    ]
    
    issues_found = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        for pattern in problematic_patterns:
            if pattern in line:
                issues_found.append((i, pattern, line.strip()))
    
    if issues_found:
        print("🚨 PROBLÈMES TROUVÉS:")
        for line_num, pattern, line_content in issues_found:
            print(f"   Ligne {line_num}: {pattern}")
            print(f"      {line_content[:100]}...")
        
        return True
    else:
        print("✅ Aucun pattern problématique trouvé")
        return False

def create_emergency_patch():
    """Crée un patch d'urgence pour OGMA"""
    
    print("🚑 Création patch d'urgence...")
    print("💡 Ce patch désactive temporairement _process_subconscience_messages")
    print("💡 qui semble causer les boucles infinies NiceGUI")
    
    # Créer directement le patch simple
    try:
        # Lire ogma_ng.py
        ogma_file = Path("ogma_ng.py")
        if not ogma_file.exists():
            print("❌ ogma_ng.py non trouvé")
            return False
        
        # Backup
        backup_file = Path("ogma_ng.py.backup")
        if not backup_file.exists():
            import shutil
            shutil.copy2(ogma_file, backup_file)
            print(f"✅ Backup créé: {backup_file}")
        
        # Lire contenu
        with open(ogma_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patch simple: désactiver la fonction problématique
        if "def _process_subconscience_messages(self):" in content:
            old_func = "def _process_subconscience_messages(self):"
            new_func = "def _process_subconscience_messages(self):\n        return  # PATCH: fonction désactivée pour éviter boucles"
            
            content = content.replace(old_func, new_func)
            print("🔧 Fonction _process_subconscience_messages désactivée")
        else:
            print("⚠️ Fonction _process_subconscience_messages non trouvée")
        
        # Sauvegarder
        with open(ogma_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Patch d'urgence appliqué")
        print("🧪 Testez: python launch_ogma.py")
        print("🔄 Restaurer: copiez ogma_ng.py.backup vers ogma_ng.py")
        return True
        
    except Exception as e:
        print(f"❌ Erreur patch: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("🩹 === FIX BOUCLES NICEGUI ===")
        print()
        print("USAGE:")
        print("  python fix_nicegui_loop.py analyze    # Analyser problèmes")
        print("  python fix_nicegui_loop.py patch      # Créer patch d'urgence")
        print("  python fix_nicegui_loop.py status     # État système")
        print()
        print("ÉTAPES RECOMMANDÉES:")
        print("1. analyze - Identifier les problèmes")  
        print("2. patch - Créer solution d'urgence")
        print("3. Tester avec monitoring")
        return
    
    command = sys.argv[1].lower()
    
    if command == "analyze":
        analyze_ogma_nicegui_issue()
    elif command == "patch":
        create_emergency_patch()
    elif command == "status":
        print("📊 Vérification état système...")
        
        # Vérifier backups
        backups = []
        for backup_file in ["ogma_ng.py.backup", "data/settings.backup"]:
            if Path(backup_file).exists():
                backups.append(backup_file)
        
        if backups:
            print(f"💾 Backups disponibles: {', '.join(backups)}")
        else:
            print("⚠️ Aucun backup trouvé")
        
        # Vérifier OGMA actif
        try:
            import requests
            response = requests.get("http://127.0.0.1:8080", timeout=2)
            print("🟢 OGMA accessible sur http://127.0.0.1:8080")
        except:
            print("🔴 OGMA non accessible")
    else:
        print(f"❌ Commande inconnue: {command}")

if __name__ == "__main__":
    main()