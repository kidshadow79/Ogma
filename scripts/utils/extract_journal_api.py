"""
🔍 EXTRACTION API - Journal de Bord Extension
Extrait les méthodes publiques de Journal de Bord pour documentation et tests.
"""

import ast
import json
from pathlib import Path
from typing import List, Dict, Any


class JournalAPIExtractor(ast.NodeVisitor):
    """Extracteur AST pour API Journal de Bord"""
    
    def __init__(self):
        self.methods = []
        self.current_class = None
        self.current_file = None
        
    def visit_ClassDef(self, node):
        """Visite classes"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        """Extrait méthodes/fonctions publiques"""
        # Ignore méthodes privées
        if node.name.startswith('_') and not node.name.startswith('__init__'):
            return
            
        # Contexte
        context = self.current_class if self.current_class else "module"
        
        # Extraction signature
        args = [arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')]
        
        # Extraction docstring
        docstring = ast.get_docstring(node) or ""
        
        # Type async
        is_async = isinstance(node, ast.AsyncFunctionDef)
        
        self.methods.append({
            'name': node.name,
            'line': node.lineno,
            'file': self.current_file,
            'context': context,
            'args': args,
            'docstring': docstring,
            'async': is_async
        })
        
    def visit_AsyncFunctionDef(self, node):
        """Extrait méthodes async"""
        self.visit_FunctionDef(node)


def extract_journal_api() -> List[Dict[str, Any]]:
    """Extrait API publique de Journal de Bord"""
    
    print("=" * 60)
    print("🔍 Extraction API - Journal de Bord Extension")
    print("=" * 60)
    print()
    
    # Fichiers sources prioritaires
    journal_files = [
        "extensions/journal_de_bord/__init__.py",
        "extensions/journal_de_bord/core_journal.py",
        "extensions/journal_de_bord/json_manager.py",
        "extensions/journal_de_bord/context_provider.py",
        "extensions/journal_de_bord/entry_generator.py"
    ]
    
    all_methods = []
    
    for source_file_str in journal_files:
        source_file = Path(source_file_str)
        
        if not source_file.exists():
            print(f"⚠️  Fichier {source_file} non trouvé, skip")
            continue
        
        # Parse AST
        print(f"📄 Analyse: {source_file}")
        with open(source_file, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=str(source_file))
            except SyntaxError as e:
                print(f"   ❌ Erreur parsing: {e}")
                continue
        
        # Extraction
        extractor = JournalAPIExtractor()
        extractor.current_file = source_file.name
        extractor.visit(tree)
        
        # Filtrer méthodes publiques
        public_methods = [
            m for m in extractor.methods 
            if not m['name'].startswith('_') or m['name'] == '__init__'
        ]
        
        all_methods.extend(public_methods)
        print(f"   ✅ {len(public_methods)} méthodes publiques extraites")
    
    print()
    return all_methods


def generate_markdown_report(methods: List[Dict[str, Any]]) -> str:
    """Génère rapport Markdown"""
    
    output = []
    output.append("# 📔 Journal de Bord API - Extracted Methods")
    output.append("")
    output.append("**Source**: `extensions/journal_de_bord/`")
    output.append(f"**Total methods**: {len(methods)}")
    output.append("")
    
    # Statistiques
    sync_count = sum(1 for m in methods if not m['async'])
    async_count = sum(1 for m in methods if m['async'])
    
    # Grouper par fichier
    by_file = {}
    for m in methods:
        file = m['file']
        if file not in by_file:
            by_file[file] = []
        by_file[file].append(m)
    
    output.append("## 📊 Statistics")
    output.append("")
    output.append(f"- **Files analyzed**: {len(by_file)}")
    output.append(f"- **Synchronous methods**: {sync_count}")
    output.append(f"- **Asynchronous methods**: {async_count}")
    output.append(f"- **Total**: {len(methods)}")
    output.append("")
    
    # Méthodes par fichier
    output.append("## 📂 Methods by File")
    output.append("")
    
    for file_name in sorted(by_file.keys()):
        file_methods = by_file[file_name]
        output.append(f"### {file_name} ({len(file_methods)} methods)")
        output.append("")
        
        for method in sorted(file_methods, key=lambda x: x['line']):
            name = method['name']
            line = method['line']
            args = method['args']
            docstring = method['docstring']
            is_async = method['async']
            context = method['context']
            
            # Header
            async_marker = " (async)" if is_async else ""
            context_marker = f" [{context}]" if context != "module" else ""
            output.append(f"#### `{name}({', '.join(args)})`{async_marker}{context_marker}")
            output.append("")
            output.append(f"**Line**: {line}")
            output.append("")
            
            # Docstring
            if docstring:
                # Premier paragraphe seulement
                first_para = docstring.split('\n\n')[0].strip()
                output.append(f"**Description**: {first_para}")
                output.append("")
            
            # Signature
            args_str = ', '.join(args) if args else "None"
            output.append(f"**Parameters**: `{args_str}`")
            output.append("")
    
    return '\n'.join(output)


def main():
    """Point d'entrée"""
    
    # Extraction
    methods = extract_journal_api()
    
    if not methods:
        print("❌ Aucune méthode extraite")
        return
    
    # Génération rapport
    print("📝 Génération rapport Markdown...")
    markdown = generate_markdown_report(methods)
    
    # Sauvegarde
    output_dir = Path("docs/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "JOURNAL_DE_BORD_API_EXTRACTED.md"
    
    output_file.write_text(markdown, encoding='utf-8')
    print(f"   ✅ Rapport sauvegardé: {output_file}")
    print()
    
    # Résumé
    print(f"📊 Total: {len(methods)} méthodes publiques extraites")
    print("=" * 60)


if __name__ == "__main__":
    main()
