#!/usr/bin/env python3
"""
extract_memory_api.py
---------------------
Extracteur API pour le Memory Manager d'OGMA.
Analyse memory_manager.py et génère la documentation Markdown des méthodes publiques.

Usage:
    python scripts/extract_memory_api.py
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any


class MemoryAPIExtractor(ast.NodeVisitor):
    """Extracteur de méthodes publiques du MemoryManager."""
    
    def __init__(self):
        self.public_methods = []
        self.current_class = None
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visite une définition de classe."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visite une définition de fonction."""
        self._process_function(node, is_async=False)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visite une définition de fonction asynchrone."""
        self._process_function(node, is_async=True)
        
    def _process_function(self, node, is_async: bool):
        """Traite une fonction/méthode."""
        # Filtre: méthodes publiques uniquement (pas de _prefix, sauf __init__)
        if self.current_class == "MemoryManager":
            if node.name.startswith('_') and node.name not in ('__init__', '__del__'):
                return  # Méthode privée, on ignore
                
            # Extrait signature
            signature = self._extract_signature(node, is_async)
            
            # Extrait docstring
            docstring = ast.get_docstring(node) or ""
            
            # Extrait type de retour
            return_type = self._extract_return_type(node)
            
            method_info = {
                'name': node.name,
                'signature': signature,
                'docstring': docstring,
                'return_type': return_type,
                'is_async': is_async,
                'line_number': node.lineno
            }
            
            self.public_methods.append(method_info)
    
    def _extract_signature(self, node, is_async: bool) -> str:
        """Extrait la signature complète de la fonction."""
        args = []
        
        # Arguments positionnels
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # Arguments keyword-only
        if node.args.kwonlyargs:
            args.append("*")
            for arg in node.args.kwonlyargs:
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                args.append(arg_str)
        
        # Signature complète
        async_prefix = "async " if is_async else ""
        return f"{async_prefix}def {node.name}({', '.join(args)})"
    
    def _extract_return_type(self, node) -> str:
        """Extrait le type de retour annoté."""
        if node.returns:
            return ast.unparse(node.returns)
        return "Any"


def generate_markdown(methods: List[Dict[str, Any]], output_path: Path):
    """Génère le fichier Markdown de documentation."""
    
    # Trier par ligne (ordre d'apparition dans le fichier)
    methods.sort(key=lambda m: m['line_number'])
    
    # Statistiques
    total_methods = len(methods)
    async_methods = sum(1 for m in methods if m['is_async'])
    sync_methods = total_methods - async_methods
    
    lines = [
        "# Memory Manager API - Extraction Complète",
        "",
        "**Date d'extraction**: 2025-11-05",
        "**Source**: `memory_manager.py`",
        "**Classe**: `MemoryManager`",
        "",
        f"## 📊 Statistiques",
        "",
        f"- **Total méthodes publiques**: {total_methods}",
        f"- **Méthodes synchrones**: {sync_methods}",
        f"- **Méthodes asynchrones**: {async_methods}",
        "",
        "---",
        "",
        "## 📚 API Publique",
        ""
    ]
    
    # Grouper par catégorie
    categories = {
        'Initialization': ['__init__', 'save_index', 'cleanup', '__del__'],
        'Memory CRUD': ['add_memory', 'update_memory', 'delete_memory', 'delete_all_memories', 'get_memory_by_id', 'get_memory_count', 'get_all_memories_data'],
        'Search & Retrieval': ['search_memories', 'retrieve_and_synthesize_context', 'retrieve_synthesis_and_memories', 'retrieve_hybrid_optimized', 'retrieve_mixed_context', 'retrieve_full_texts_context'],
        'Ego & Identity': ['store_ego_trait', 'sync_ego_prompt_references'],
        'Maintenance': ['rebuild_faiss_index', 'repair_mapping_inconsistencies', 'reembed_memory', 're_enrich_memory', 'diagnose_search_quality']
    }
    
    # Index des méthodes par nom
    methods_by_name = {m['name']: m for m in methods}
    
    # Générer par catégorie
    for category, method_names in categories.items():
        category_methods = [methods_by_name[name] for name in method_names if name in methods_by_name]
        
        if category_methods:
            lines.append(f"### {category}")
            lines.append("")
            
            for method in category_methods:
                # Titre avec badge async
                async_badge = " `async`" if method['is_async'] else ""
                lines.append(f"#### `{method['name']}()`{async_badge}")
                lines.append("")
                
                # Signature
                lines.append("```python")
                signature_line = method['signature']
                if method['return_type'] != 'Any':
                    signature_line += f" -> {method['return_type']}"
                lines.append(signature_line)
                lines.append("```")
                lines.append("")
                
                # Docstring
                if method['docstring']:
                    # Nettoyer la docstring
                    docstring_lines = method['docstring'].strip().split('\n')
                    lines.append("**Description**:")
                    lines.append("")
                    for doc_line in docstring_lines:
                        lines.append(doc_line.strip())
                    lines.append("")
                else:
                    lines.append("*Pas de documentation disponible.*")
                    lines.append("")
                
                # Ligne de séparation
                lines.append("---")
                lines.append("")
    
    # Méthodes non catégorisées
    categorized_names = set()
    for names in categories.values():
        categorized_names.update(names)
    
    uncategorized = [m for m in methods if m['name'] not in categorized_names]
    
    if uncategorized:
        lines.append("### Autres Méthodes Publiques")
        lines.append("")
        
        for method in uncategorized:
            async_badge = " `async`" if method['is_async'] else ""
            lines.append(f"#### `{method['name']}()`{async_badge}")
            lines.append("")
            
            lines.append("```python")
            signature_line = method['signature']
            if method['return_type'] != 'Any':
                signature_line += f" -> {method['return_type']}"
            lines.append(signature_line)
            lines.append("```")
            lines.append("")
            
            if method['docstring']:
                docstring_lines = method['docstring'].strip().split('\n')
                for doc_line in docstring_lines:
                    lines.append(doc_line.strip())
                lines.append("")
            else:
                lines.append("*Pas de documentation disponible.*")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    # Écriture du fichier
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("🔍 Extraction API - Memory Manager")
    print("=" * 60)
    print()
    
    # Chemins
    project_root = Path(__file__).parent.parent
    source_file = project_root / "memory_manager.py"
    output_file = project_root / "docs" / "api" / "MEMORY_MANAGER_API_EXTRACTED.md"
    
    # Vérification
    if not source_file.exists():
        print(f"❌ Fichier source introuvable: {source_file}")
        sys.exit(1)
    
    # Lecture et parsing
    print(f"📄 Analyse: {source_file.relative_to(project_root)}")
    source_code = source_file.read_text(encoding='utf-8')
    
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe: {e}")
        sys.exit(1)
    
    # Extraction
    extractor = MemoryAPIExtractor()
    extractor.visit(tree)
    
    print(f"   ✅ {len(extractor.public_methods)} méthodes publiques extraites")
    
    # Statistiques
    async_count = sum(1 for m in extractor.public_methods if m['is_async'])
    sync_count = len(extractor.public_methods) - async_count
    
    print(f"      - Synchrones: {sync_count}")
    print(f"      - Asynchrones: {async_count}")
    
    # Génération Markdown
    print()
    print("📝 Génération rapport Markdown...")
    generate_markdown(extractor.public_methods, output_file)
    print(f"   ✅ Rapport sauvegardé: {output_file.relative_to(project_root)}")
    
    print()
    print(f"📊 Total: {len(extractor.public_methods)} méthodes publiques extraites")
    print("=" * 60)


if __name__ == '__main__':
    main()
