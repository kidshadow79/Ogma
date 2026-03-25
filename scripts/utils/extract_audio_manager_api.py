"""
Script d'extraction API - Audio Manager

Extrait automatiquement les signatures de méthodes publiques
du module audio_manager.py pour faciliter la création des tests.

Usage:
    python scripts/extract_audio_manager_api.py
"""

import ast
from pathlib import Path
from typing import List, Dict, Set

def extract_methods_from_file(file_path: Path) -> List[Dict]:
    """Extrait les méthodes publiques d'un fichier Python via AST."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=str(file_path))
        except SyntaxError as e:
            print(f"❌ Erreur parsing {file_path}: {e}")
            return []
    
    methods = []
    
    for node in ast.walk(tree):
        # Fonctions de module (level 0)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            methods.append({
                'name': node.name,
                'type': 'async' if isinstance(node, ast.AsyncFunctionDef) else 'sync',
                'args': [arg.arg for arg in node.args.args],
                'line': node.lineno,
                'scope': 'module'
            })
        
        # Méthodes de classe
        elif isinstance(node, ast.ClassDef):
            class_name = node.name
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith('_') or item.name == '__init__':
                        methods.append({
                            'name': f"{class_name}.{item.name}",
                            'type': 'async' if isinstance(item, ast.AsyncFunctionDef) else 'sync',
                            'args': [arg.arg for arg in item.args.args],
                            'line': item.lineno,
                            'scope': 'class'
                        })
    
    return methods


def generate_markdown_report(methods: List[Dict], output_file: Path):
    """Génère un rapport Markdown de l'API."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 📊 Audio Manager API - Référence Complète\n\n")
        f.write("**Généré automatiquement** via extraction AST\n\n")
        f.write("---\n\n")
        
        # Statistiques
        total = len(methods)
        async_count = sum(1 for m in methods if m['type'] == 'async')
        sync_count = total - async_count
        module_funcs = sum(1 for m in methods if m['scope'] == 'module')
        class_methods = total - module_funcs
        
        f.write("## 📈 Statistiques\n\n")
        f.write(f"- **Total méthodes publiques** : {total}\n")
        f.write(f"- **Fonctions module** : {module_funcs}\n")
        f.write(f"- **Méthodes classe** : {class_methods}\n")
        f.write(f"- **Async** : {async_count}\n")
        f.write(f"- **Sync** : {sync_count}\n\n")
        
        f.write("---\n\n")
        
        # Table des matières
        f.write("## 📋 Table des Matières\n\n")
        f.write("- [Fonctions Module](#fonctions-module)\n")
        f.write("- [Classe AudioManager](#classe-audiomanager)\n\n")
        f.write("---\n\n")
        
        # Fonctions module
        module_methods = [m for m in methods if m['scope'] == 'module']
        if module_methods:
            f.write("## Fonctions Module\n\n")
            for method in sorted(module_methods, key=lambda x: x['line']):
                args_str = ', '.join(method['args'])
                type_badge = "🔄 Async" if method['type'] == 'async' else "⚡ Sync"
                f.write(f"### `{method['name']}()`\n\n")
                f.write(f"- **Type** : {type_badge}\n")
                f.write(f"- **Signature** : `{method['name']}({args_str})`\n")
                f.write(f"- **Ligne** : {method['line']}\n\n")
        
        # Méthodes de classe
        class_methods_list = [m for m in methods if m['scope'] == 'class']
        if class_methods_list:
            f.write("## Classe AudioManager\n\n")
            for method in sorted(class_methods_list, key=lambda x: x['line']):
                args_str = ', '.join(method['args'])
                type_badge = "🔄 Async" if method['type'] == 'async' else "⚡ Sync"
                f.write(f"### `{method['name']}()`\n\n")
                f.write(f"- **Type** : {type_badge}\n")
                f.write(f"- **Signature** : `{method['name']}({args_str})`\n")
                f.write(f"- **Ligne** : {method['line']}\n\n")
        
        f.write("---\n\n")
        f.write(f"**Total** : {total} méthodes publiques extraites\n")


def main():
    """Point d'entrée principal."""
    print("="*60)
    print("🔍 Extraction API - Audio Manager")
    print("="*60)
    
    # Chemins
    repo_root = Path(__file__).parent.parent
    audio_manager_file = repo_root / "audio_manager.py"
    output_file = repo_root / "docs" / "api" / "AUDIO_MANAGER_API_EXTRACTED.md"
    
    # Vérifier existence
    if not audio_manager_file.exists():
        print(f"❌ Fichier non trouvé: {audio_manager_file}")
        return
    
    # Créer dossier output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Extraction
    print(f"\n📄 Analyse: {audio_manager_file.relative_to(repo_root)}")
    methods = extract_methods_from_file(audio_manager_file)
    print(f"   ✅ {len(methods)} méthodes extraites")
    
    # Génération rapport
    print(f"\n📝 Génération rapport Markdown...")
    generate_markdown_report(methods, output_file)
    print(f"   ✅ Rapport sauvegardé: {output_file.relative_to(repo_root)}")
    
    # Récapitulatif
    print(f"\n📊 Total: {len(methods)} méthodes publiques extraites")
    print("="*60)


if __name__ == "__main__":
    main()
