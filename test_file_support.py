#!/usr/bin/env python3
"""
Test du support des formats .md et .json dans OGMA
"""

from pathlib import Path
import sys
sys.path.append('.')
from extensions.file_processor import process_file

def test_md_support():
    """Test du support Markdown"""
    print("=== TEST SUPPORT MARKDOWN ===")
    md_file = Path("test_markdown.md")
    
    if not md_file.exists():
        print("❌ Fichier test_markdown.md introuvable")
        return False
    
    try:
        result = process_file(md_file)
        if result and result['type'] == 'text':
            print("✅ Markdown lu avec succès")
            print(f"   Nom: {result['filename']}")
            print(f"   Type: {result['type']}")
            print(f"   Contenu: {len(result['content'])} caractères")
            print(f"   Aperçu: {result['content'][:100]}...")
            return True
        else:
            print("❌ Erreur dans le traitement Markdown")
            return False
    except Exception as e:
        print(f"❌ Exception lors du test MD: {e}")
        return False

def test_json_support():
    """Test du support JSON"""
    print("\n=== TEST SUPPORT JSON ===")
    json_file = Path("test_config.json")
    
    if not json_file.exists():
        print("❌ Fichier test_config.json introuvable")
        return False
    
    try:
        result = process_file(json_file)
        if result and result['type'] == 'text':
            print("✅ JSON lu avec succès")
            print(f"   Nom: {result['filename']}")
            print(f"   Type: {result['type']}")
            print(f"   Contenu: {len(result['content'])} caractères")
            print(f"   Aperçu: {result['content'][:100]}...")
            return True
        else:
            print("❌ Erreur dans le traitement JSON")
            return False
    except Exception as e:
        print(f"❌ Exception lors du test JSON: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test du support des nouveaux formats de fichiers")
    
    md_ok = test_md_support()
    json_ok = test_json_support()
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   Markdown (.md): {'✅' if md_ok else '❌'}")
    print(f"   JSON (.json): {'✅' if json_ok else '❌'}")
    
    if md_ok and json_ok:
        print("\n🎉 Tous les tests passent ! Support MD/JSON activé.")
    else:
        print("\n⚠️ Certains tests ont échoué.")