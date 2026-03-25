#!/usr/bin/env python3
"""
Extracteur API - Identity/Profile Manager
=========================================
Extrait les méthodes publiques de profile_manager.py
pour génération documentation et tests.
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

class IdentityAPIExtractor(ast.NodeVisitor):
    """Visiteur AST pour extraire l'API publique du ProfileManager"""
    
    def __init__(self):
        self.public_methods = []
        self.current_class = None
        
    def visit_ClassDef(self, node):
        """Visite les classes pour identifier ProfileManager"""
        if node.name == "ProfileManager":
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = None
        else:
            self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Visite les fonctions/méthodes"""
        if self.current_class == "ProfileManager":
            # Ignorer les méthodes privées (commence par _)
            # Sauf __init__ et __del__ qui sont publics
            is_public = (
                not node.name.startswith('_') or 
                node.name in ('__init__', '__del__')
            )
            
            if is_public:
                method_info = self._extract_method_info(node)
                self.public_methods.append(method_info)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Visite les méthodes async"""
        if self.current_class == "ProfileManager":
            is_public = (
                not node.name.startswith('_') or 
                node.name in ('__init__', '__del__')
            )
            
            if is_public:
                method_info = self._extract_method_info(node, is_async=True)
                self.public_methods.append(method_info)
        
        self.generic_visit(node)
    
    def _extract_method_info(self, node, is_async=False):
        """Extrait les informations d'une méthode"""
        # Signature
        args = []
        for arg in node.args.args:
            if arg.arg != 'self':
                # Avec type annotation si disponible
                if arg.annotation:
                    arg_type = ast.unparse(arg.annotation)
                    args.append(f"{arg.arg}: {arg_type}")
                else:
                    args.append(arg.arg)
        
        # Valeurs par défaut
        defaults = node.args.defaults
        if defaults:
            # Associer defaults aux derniers arguments
            num_defaults = len(defaults)
            for i, default in enumerate(defaults):
                arg_index = len(args) - num_defaults + i
                if arg_index >= 0 and arg_index < len(args):
                    default_value = ast.unparse(default)
                    # Ajouter le default si pas déjà présent
                    if "=" not in args[arg_index]:
                        args[arg_index] = f"{args[arg_index]} = {default_value}"
        
        # Return annotation
        return_type = "Any"
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        # Docstring
        docstring = ast.get_docstring(node) or "Pas de documentation disponible"
        
        # Ligne source
        lineno = node.lineno
        
        return {
            'name': node.name,
            'is_async': is_async,
            'args': args,
            'return_type': return_type,
            'docstring': docstring,
            'lineno': lineno
        }


def categorize_methods(methods):
    """Catégorise les méthodes par fonction"""
    categories = defaultdict(list)
    
    for method in methods:
        name = method['name']
        
        # Catégorisation par nom/fonction
        if name in ('__init__', '__del__'):
            categories['Initialization'].append(method)
        elif 'save' in name.lower() or 'backup' in name.lower():
            categories['Save & Backup'].append(method)
        elif 'load' in name.lower() or 'restore' in name.lower():
            categories['Load & Restore'].append(method)
        elif 'delete' in name.lower() or 'reset' in name.lower():
            categories['Delete & Reset'].append(method)
        elif 'analyze' in name.lower() or 'list' in name.lower():
            categories['Analysis & Info'].append(method)
        elif 'optimize' in name.lower() or 'cleanup' in name.lower():
            categories['Optimization & Maintenance'].append(method)
        else:
            categories['Other'].append(method)
    
    return categories


def generate_markdown(categories, total_methods):
    """Génère le rapport Markdown"""
    md_lines = [
        "# ProfileManager - API Publique Extraite",
        "",
        f"**Date d'extraction** : {Path(__file__).stem}",
        f"**Fichier source** : `profile_manager.py`",
        f"**Total méthodes publiques** : {total_methods}",
        "",
        "---",
        "",
        "## 📊 Statistiques",
        "",
        f"- **Méthodes synchrones** : {sum(1 for cat in categories.values() for m in cat if not m['is_async'])}",
        f"- **Méthodes asynchrones** : {sum(1 for cat in categories.values() for m in cat if m['is_async'])}",
        "",
        "### Répartition par catégorie",
        ""
    ]
    
    for category, methods in sorted(categories.items()):
        md_lines.append(f"- **{category}** : {len(methods)} méthode(s)")
    
    md_lines.extend([
        "",
        "---",
        "",
        "## 📋 Méthodes par Catégorie",
        ""
    ])
    
    # Ordre de catégories logique
    category_order = [
        'Initialization',
        'Save & Backup',
        'Load & Restore',
        'Delete & Reset',
        'Analysis & Info',
        'Optimization & Maintenance',
        'Other'
    ]
    
    for category in category_order:
        if category not in categories:
            continue
        
        methods = categories[category]
        md_lines.extend([
            f"### {category}",
            ""
        ])
        
        for method in sorted(methods, key=lambda m: m['lineno']):
            # Signature
            async_prefix = "async " if method['is_async'] else ""
            args_str = ", ".join(method['args']) if method['args'] else ""
            
            md_lines.extend([
                f"#### `{async_prefix}{method['name']}({args_str})`",
                "",
                f"**Ligne** : {method['lineno']}  ",
                f"**Retour** : `{method['return_type']}`",
                "",
                "**Description** :",
                f"> {method['docstring']}",
                ""
            ])
    
    return "\n".join(md_lines)


def main():
    """Point d'entrée principal"""
    print("🔍 Extraction API - Profile/Identity Manager")
    print("=" * 50)
    
    # Localiser profile_manager.py
    source_file = Path("profile_manager.py")
    
    if not source_file.exists():
        print(f"❌ Fichier non trouvé : {source_file}")
        sys.exit(1)
    
    print(f"📄 Analyse : {source_file}")
    
    # Parser le fichier
    with open(source_file, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=str(source_file))
    
    # Extraire les méthodes publiques
    extractor = IdentityAPIExtractor()
    extractor.visit(tree)
    
    public_methods = extractor.public_methods
    print(f"   ✅ {len(public_methods)} méthodes publiques extraites")
    
    # Statistiques
    sync_count = sum(1 for m in public_methods if not m['is_async'])
    async_count = sum(1 for m in public_methods if m['is_async'])
    print(f"      - Synchrones: {sync_count}")
    print(f"      - Asynchrones: {async_count}")
    
    # Catégoriser
    categories = categorize_methods(public_methods)
    
    # Générer Markdown
    print("\n📝 Génération rapport Markdown...")
    markdown_content = generate_markdown(categories, len(public_methods))
    
    # Sauvegarder
    output_dir = Path("docs/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "PROFILE_MANAGER_API_EXTRACTED.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"   ✅ Rapport sauvegardé : {output_file}")
    
    # Résumé final
    print("\n📊 Résumé")
    print("=" * 50)
    for category, methods in sorted(categories.items()):
        print(f"   {category:<30} : {len(methods)} méthode(s)")
    
    print(f"\n✅ Total : {len(public_methods)} méthodes publiques extraites")


if __name__ == "__main__":
    main()
