"""
Script d'extraction automatique des signatures API Memory Manager
==================================================================

Extrait toutes les méthodes publiques de memory_manager.py avec:
- Signatures complètes
- Paramètres + types
- Async/sync
- Docstrings

Génère: docs/api/MEMORY_MANAGER_API_EXTRACTED.md
"""

import ast
import inspect
from pathlib import Path
from typing import List, Dict, Any


class APIExtractor(ast.NodeVisitor):
    """Extracteur de signatures via AST Python."""
    
    def __init__(self):
        self.methods = []
        self.current_class = None
    
    def visit_ClassDef(self, node):
        """Visite les définitions de classes."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Visite les définitions de fonctions."""
        self._process_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node):
        """Visite les définitions de fonctions async."""
        self._process_function(node, is_async=True)
    
    def _process_function(self, node, is_async):
        """Traite une fonction/méthode."""
        # Filtrer méthodes privées
        if node.name.startswith('_') and node.name != '__init__':
            return
        
        # Extraire paramètres
        params = []
        for arg in node.args.args:
            param_name = arg.arg
            param_type = ast.unparse(arg.annotation) if arg.annotation else "Any"
            params.append(f"{param_name}: {param_type}")
        
        # Extraire defaults
        defaults = [ast.unparse(d) for d in node.args.defaults]
        
        # Extraire return type
        return_type = ast.unparse(node.returns) if node.returns else "Any"
        
        # Extraire docstring
        docstring = ast.get_docstring(node) or "Non documenté"
        
        method_info = {
            'name': node.name,
            'class': self.current_class,
            'is_async': is_async,
            'params': params,
            'defaults': defaults,
            'return_type': return_type,
            'docstring': docstring,
            'line': node.lineno
        }
        
        self.methods.append(method_info)


def extract_signatures(file_path: Path) -> List[Dict[str, Any]]:
    """Extrait les signatures d'un fichier Python."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    extractor = APIExtractor()
    extractor.visit(tree)
    
    return extractor.methods


def format_signature(method: Dict[str, Any]) -> str:
    """Formate une signature de méthode en Markdown."""
    async_prefix = "async " if method['is_async'] else ""
    params = ",\n    ".join(method['params'])
    
    signature = f"""### `{method['name']}()`

**Ligne** : {method['line']}  
**Classe** : {method['class'] or 'Module'}  
**Type** : {'⚡ Async' if method['is_async'] else '🔄 Sync'}

**Signature** :
```python
{async_prefix}def {method['name']}(
    {params}
) -> {method['return_type']}
```

**Description** :
{method['docstring']}

---

"""
    return signature


def generate_api_doc(methods: List[Dict[str, Any]], output_path: Path):
    """Génère la documentation API complète."""
    # Filtrer et trier
    public_methods = [m for m in methods if not m['name'].startswith('_') or m['name'] == '__init__']
    public_methods.sort(key=lambda x: (x['class'] or '', x['line']))
    
    # Header
    doc = """# Memory Manager - API Extraite Automatiquement

**Source** : `memory_manager.py`  
**Date extraction** : 5 novembre 2025  
**Méthode** : Analyse AST Python

---

## 📋 Table des Matières

"""
    
    # Générer table des matières
    for method in public_methods:
        doc += f"- [{method['name']}()](#-{method['name'].lower().replace('_', '-')})\n"
    
    doc += "\n---\n\n## 📚 Signatures Complètes\n\n"
    
    # Générer signatures
    for method in public_methods:
        doc += format_signature(method)
    
    # Statistiques
    async_count = sum(1 for m in public_methods if m['is_async'])
    sync_count = len(public_methods) - async_count
    
    doc += f"""
## 📊 Statistiques

- **Total méthodes publiques** : {len(public_methods)}
- **Méthodes async** : {async_count} (⚡)
- **Méthodes sync** : {sync_count} (🔄)
- **Classes** : {len(set(m['class'] for m in public_methods if m['class']))}

---

**Note** : Ce document est généré automatiquement. Pour usage détaillé, consulter le code source.
"""
    
    # Écrire fichier
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc)
    
    print(f"✅ Documentation API générée: {output_path}")
    print(f"📊 {len(public_methods)} méthodes publiques extraites")
    print(f"⚡ {async_count} async, 🔄 {sync_count} sync")


if __name__ == "__main__":
    import sys
    
    # Chemins (par défaut ou arguments CLI)
    if len(sys.argv) >= 3:
        source_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2])
    elif len(sys.argv) == 2:
        source_file = Path(sys.argv[1])
        # Générer nom output automatiquement
        module_name = source_file.stem.upper()
        output_file = Path(f"docs/api/{module_name}_API_EXTRACTED.md")
    else:
        # Valeurs par défaut (Memory Manager)
        source_file = Path("memory_manager.py")
        output_file = Path("docs/api/MEMORY_MANAGER_API_EXTRACTED.md")
    
    print(f"🔍 Extraction signatures API {source_file.stem}...")
    print(f"📁 Source: {source_file}")
    print(f"📄 Output: {output_file}")
    
    if not source_file.exists():
        print(f"❌ Fichier introuvable: {source_file}")
        exit(1)
    
    # Extraction
    methods = extract_signatures(source_file)
    
    # Génération documentation
    generate_api_doc(methods, output_file)
    
    print(f"\n✅ Documentation disponible: {output_file}")
    print("\n📋 Prochaines étapes:")
    print(f"1. Examiner {output_file.name}")
    print("2. Identifier méthodes critiques")
    print("3. Adapter tests stricts avec signatures réelles")
