"""
Script de vérification de l'intégration Cognitive Mirror dans OGMA
"""

import os
import sys

def check_integration():
    """Vérifie que l'intégration Cognitive Mirror est complète dans OGMA"""
    print("🔍 VÉRIFICATION INTÉGRATION COGNITIVE MIRROR")
    print("=" * 60)
    
    # 1. Vérifier présence des fichiers d'extension
    print("\n1. 📁 Vérification fichiers extension...")
    extension_files = [
        "extensions/cognitive_mirror/__init__.py",
        "extensions/cognitive_mirror/config.py", 
        "extensions/cognitive_mirror/core_cognitive_mirror.py",
        "extensions/cognitive_mirror/inactivity_detector.py",
        "extensions/cognitive_mirror/reflection_manager.py",
        "extensions/cognitive_mirror/ui_components.py",
        "extensions/cognitive_mirror/memory_integration.py"
    ]
    
    for file in extension_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ MANQUANT: {file}")
    
    # 2. Vérifier intégration dans ogma_ng.py
    print("\n2. 🔧 Vérification intégration ogma_ng.py...")
    
    try:
        with open("ogma_ng.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        checks = [
            ("Import extension", "from extensions.cognitive_mirror import initialize_cognitive_mirror"),
            ("Variable globale", "_cognitive_mirror = None"),
            ("Fonction _ensure_cognitive_mirror", "def _ensure_cognitive_mirror():"),
            ("Hook pré-message", "Hook avant traitement du message utilisateur"),
            ("Hook post-message", "Hook après génération de la réponse IA"),
            ("Init main_page", "Cognitive Mirror préinitialisé"),
            ("Overlay UI", "cognitive_mirror.ui_components.create_overlay")
        ]
        
        for desc, pattern in checks:
            if pattern in content:
                print(f"✅ {desc}")
            else:
                print(f"❌ MANQUANT: {desc}")
                
    except Exception as e:
        print(f"❌ Erreur lecture ogma_ng.py: {e}")
    
    # 3. Vérifier intégration dans ogma_headers.py
    print("\n3. 🎛️ Vérification bouton header...")
    
    try:
        with open("ogma_headers.py", "r", encoding="utf-8") as f:
            header_content = f.read()
        
        header_checks = [
            ("Bouton Cognitive Mirror", "cognitive_mirror_btn"),
            ("Fonction toggle", "def toggle_cognitive_mirror"),
            ("Icône psychology_alt", "psychology_alt")
        ]
        
        for desc, pattern in header_checks:
            if pattern in header_content:
                print(f"✅ {desc}")
            else:
                print(f"❌ MANQUANT: {desc}")
                
    except Exception as e:
        print(f"❌ Erreur lecture ogma_headers.py: {e}")
    
    # 4. Test import extension
    print("\n4. 🧪 Test import extension...")
    
    try:
        sys.path.append('.')
        from extensions.cognitive_mirror import initialize_cognitive_mirror, get_cognitive_mirror
        print("✅ Import extension réussi")
        
        # Test config
        from extensions.cognitive_mirror.config import get_config
        config = get_config()
        print(f"✅ Configuration chargée (trigger: {config.get('trigger_delay_no_message')}s)")
        
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
    except Exception as e:
        print(f"❌ Erreur test: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC TERMINÉ")
    print("\nSi tout est ✅, l'intégration devrait fonctionner.")
    print("Si des éléments sont ❌, ils doivent être corrigés.")

if __name__ == "__main__":
    if not os.path.exists("ogma_ng.py"):
        print("❌ Ce script doit être exécuté depuis le dossier OGMA")
        exit(1)
    
    check_integration()