#!/usr/bin/env python3
"""
Extraction API - Cognitive Mirror Extension

Extrait les signatures des méthodes publiques de l'extension Cognitive Mirror
pour faciliter la création de tests unitaires stricts.
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple

def extract_cognitive_mirror_api() -> Dict[str, List[Dict]]:
    """Extrait API de tous les modules Cognitive Mirror."""
    
    base_path = Path("extensions/cognitive_mirror")
    
    # Fichiers principaux à analyser
    files_to_analyze = [
        "__init__.py",
        "introspection_core.py",
        "introspection_orchestrator.py",
        "memory_integration.py",
        "config.py",
        "ui_components.py"
    ]
    
    results = {}
    
    for filename in files_to_analyze:
        filepath = base_path / filename
        if not filepath.exists():
            print(f"⚠️  Fichier non trouvé: {filepath}")
            continue
            
        print(f"📄 Analyse: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            module_functions = []
            
            for node in ast.walk(tree):
                # Fonctions module-level
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Publiques seulement
                        sig = extract_function_signature(node)
                        module_functions.append({
                            'name': node.name,
                            'signature': sig,
                            'is_async': isinstance(node, ast.AsyncFunctionDef),
                            'type': 'function',
                            'line': node.lineno
                        })
                
                # Méthodes classes
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not item.name.startswith('_') or item.name in ['__init__']:
                                sig = extract_function_signature(item, class_name)
                                module_functions.append({
                                    'name': f"{class_name}.{item.name}",
                                    'signature': sig,
                                    'is_async': isinstance(item, ast.AsyncFunctionDef),
                                    'type': 'method',
                                    'class': class_name,
                                    'line': item.lineno
                                })
            
            results[filename] = module_functions
            print(f"  ✅ {len(module_functions)} méthodes extraites")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    return results

def extract_function_signature(node: ast.FunctionDef, class_name: str = None) -> str:
    """Extrait signature lisible d'une fonction."""
    
    args = []
    
    # Arguments positionnels
    for arg in node.args.args:
        arg_name = arg.arg
        if arg_name == 'self' and class_name:
            continue
        
        # Type hint si disponible
        if arg.annotation:
            type_hint = ast.unparse(arg.annotation)
            args.append(f"{arg_name}: {type_hint}")
        else:
            args.append(arg_name)
    
    # Valeurs par défaut
    defaults = node.args.defaults
    if defaults:
        # Associer defaults aux derniers args
        num_defaults = len(defaults)
        for i, default in enumerate(defaults):
            arg_index = len(args) - num_defaults + i
            if arg_index >= 0 and arg_index < len(args):
                default_value = ast.unparse(default)
                args[arg_index] += f" = {default_value}"
    
    # Return type
    return_type = ""
    if node.returns:
        return_type = f" -> {ast.unparse(node.returns)}"
    
    # Construire signature
    sig = f"({', '.join(args)}){return_type}"
    
    return sig

def generate_markdown_report(api_data: Dict[str, List[Dict]]) -> str:
    """Génère rapport Markdown de l'API."""
    
    report = ["# Cognitive Mirror - API Extraite\n"]
    report.append("**Extension**: `extensions/cognitive_mirror/`")
    report.append(f"**Date extraction**: {Path(__file__).stat().st_mtime}")
    report.append("\n---\n")
    
    # Table des matières
    report.append("## 📋 Table des Matières\n")
    for filename in sorted(api_data.keys()):
        anchor = filename.replace('.', '').replace('_', '-')
        report.append(f"- [{filename}](#{anchor})")
    report.append("\n---\n")
    
    # Détails par fichier
    for filename in sorted(api_data.keys()):
        methods = api_data[filename]
        if not methods:
            continue
        
        report.append(f"## 📄 {filename}\n")
        report.append(f"**Méthodes publiques**: {len(methods)}\n")
        
        # Grouper par classe
        classes = {}
        module_funcs = []
        
        for method in methods:
            if method['type'] == 'method':
                class_name = method['class']
                if class_name not in classes:
                    classes[class_name] = []
                classes[class_name].append(method)
            else:
                module_funcs.append(method)
        
        # Fonctions module
        if module_funcs:
            report.append("### Fonctions Module\n")
            for func in sorted(module_funcs, key=lambda x: x['line']):
                async_marker = "⚡ async" if func['is_async'] else "🔄 sync"
                report.append(f"#### {async_marker} `{func['name']}`\n")
                report.append(f"**Ligne**: {func['line']}")
                report.append(f"**Signature**:")
                report.append(f"```python")
                report.append(f"{'async ' if func['is_async'] else ''}def {func['name']}{func['signature']}")
                report.append(f"```\n")
        
        # Méthodes classes
        for class_name in sorted(classes.keys()):
            report.append(f"### Classe: `{class_name}`\n")
            for method in sorted(classes[class_name], key=lambda x: x['line']):
                method_name = method['name'].split('.')[-1]
                async_marker = "⚡ async" if method['is_async'] else "🔄 sync"
                
                report.append(f"#### {async_marker} `{method_name}()`\n")
                report.append(f"**Ligne**: {method['line']}")
                report.append(f"**Signature**:")
                report.append(f"```python")
                report.append(f"{'async ' if method['is_async'] else ''}def {method_name}{method['signature']}")
                report.append(f"```\n")
        
        report.append("---\n")
    
    # Statistiques
    report.append("## 📊 Statistiques\n")
    total_methods = sum(len(methods) for methods in api_data.values())
    async_methods = sum(1 for methods in api_data.values() for m in methods if m['is_async'])
    
    report.append(f"- **Total méthodes publiques**: {total_methods}")
    report.append(f"- **Méthodes async**: {async_methods}")
    report.append(f"- **Méthodes sync**: {total_methods - async_methods}")
    report.append(f"- **Fichiers analysés**: {len(api_data)}")
    
    return "\n".join(report)

def main():
    """Point d'entrée principal."""
    
    print("🔍 Extraction API Cognitive Mirror\n")
    
    # Extraction
    api_data = extract_cognitive_mirror_api()
    
    if not api_data:
        print("❌ Aucune donnée extraite")
        sys.exit(1)
    
    # Génération rapport
    print("\n📝 Génération rapport Markdown...")
    report = generate_markdown_report(api_data)
    
    # Sauvegarde
    output_file = Path("docs/api/COGNITIVE_MIRROR_API_EXTRACTED.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Rapport sauvegardé: {output_file}")
    print(f"📊 Total: {sum(len(m) for m in api_data.values())} méthodes publiques extraites")

if __name__ == "__main__":
    main()
