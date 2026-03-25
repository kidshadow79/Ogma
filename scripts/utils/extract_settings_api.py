"""
🔍 EXTRACTION API - Settings Manager
Extrait les méthodes publiques de SettingsManager pour documentation et tests.
"""

import ast
import json
from pathlib import Path
from typing import List, Dict, Any


class SettingsAPIExtractor(ast.NodeVisitor):
    """Extracteur AST pour API Settings Manager"""
    
    def __init__(self):
        self.methods = []
        self.current_class = None
        
    def visit_ClassDef(self, node):
        """Visite classes (SettingsManager)"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        """Extrait méthodes publiques"""
        # Ignore méthodes privées
        if node.name.startswith('_'):
            return
            
        # Contexte
        context = self.current_class if self.current_class else "module"
        
        # Extraction signature
        args = [arg.arg for arg in node.args.args if arg.arg != 'self']
        
        # Extraction docstring
        docstring = ast.get_docstring(node) or ""
        
        # Type async
        is_async = isinstance(node, ast.AsyncFunctionDef)
        
        self.methods.append({
            'name': node.name,
            'line': node.lineno,
            'context': context,
            'args': args,
            'docstring': docstring,
            'async': is_async
        })
        
    def visit_AsyncFunctionDef(self, node):
        """Extrait méthodes async"""
        self.visit_FunctionDef(node)


def extract_settings_api() -> List[Dict[str, Any]]:
    """Extrait API publique de SettingsManager"""
    
    print("=" * 60)
    print("🔍 Extraction API - Settings Manager")
    print("=" * 60)
    print()
    
    # Fichier source
    source_file = Path("core_logic.py")
    
    if not source_file.exists():
        print(f"❌ Fichier {source_file} non trouvé")
        return []
    
    # Parse AST
    print(f"📄 Analyse: {source_file}")
    with open(source_file, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=str(source_file))
    
    # Extraction
    extractor = SettingsAPIExtractor()
    extractor.visit(tree)
    
    # Filtrer uniquement SettingsManager
    settings_methods = [
        m for m in extractor.methods 
        if m['context'] == 'SettingsManager'
    ]
    
    print(f"   ✅ {len(settings_methods)} méthodes extraites (SettingsManager)")
    print()
    
    return settings_methods


def generate_markdown_report(methods: List[Dict[str, Any]]) -> str:
    """Génère rapport Markdown"""
    
    output = []
    output.append("# 📋 Settings Manager API - Extracted Methods")
    output.append("")
    output.append("**Source**: `core_logic.py`")
    output.append(f"**Total methods**: {len(methods)}")
    output.append("")
    
    # Statistiques
    sync_count = sum(1 for m in methods if not m['async'])
    async_count = sum(1 for m in methods if m['async'])
    
    output.append("## 📊 Statistics")
    output.append("")
    output.append(f"- **Synchronous methods**: {sync_count}")
    output.append(f"- **Asynchronous methods**: {async_count}")
    output.append(f"- **Total**: {len(methods)}")
    output.append("")
    
    # Méthodes par ordre d'apparition
    output.append("## 🔧 Methods")
    output.append("")
    
    for method in sorted(methods, key=lambda x: x['line']):
        name = method['name']
        line = method['line']
        args = method['args']
        docstring = method['docstring']
        is_async = method['async']
        
        # Header
        async_marker = " (async)" if is_async else ""
        output.append(f"### `{name}({', '.join(args)})`{async_marker}")
        output.append("")
        output.append(f"**Line**: {line}")
        output.append("")
        
        # Docstring
        if docstring:
            output.append(f"**Description**: {docstring.strip()}")
            output.append("")
        
        # Signature
        args_str = ', '.join(args) if args else "None"
        output.append(f"**Parameters**: `{args_str}`")
        output.append("")
    
    return '\n'.join(output)


def main():
    """Point d'entrée"""
    
    # Extraction
    methods = extract_settings_api()
    
    if not methods:
        print("❌ Aucune méthode extraite")
        return
    
    # Génération rapport
    print("📝 Génération rapport Markdown...")
    markdown = generate_markdown_report(methods)
    
    # Sauvegarde
    output_dir = Path("docs/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "SETTINGS_API_EXTRACTED.md"
    
    output_file.write_text(markdown, encoding='utf-8')
    print(f"   ✅ Rapport sauvegardé: {output_file}")
    print()
    
    # Résumé
    print(f"📊 Total: {len(methods)} méthodes publiques extraites")
    print("=" * 60)


if __name__ == "__main__":
    main()
