#!/usr/bin/env python3
"""
Extracteur API - Cognitive Mirror Extension
============================================
Extrait les fonctions publiques de extensions/cognitive_mirror/__init__.py
pour génération documentation et tests.
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

class CognitiveMirrorAPIExtractor(ast.NodeVisitor):
    """Visiteur AST pour extraire l'API publique du Cognitive Mirror"""
    
    def __init__(self):
        self.public_functions = []
        
    def visit_FunctionDef(self, node):
        """Visite les fonctions pour extraire API publique"""
        # Ignorer fonctions privées (commence par _)
        if not node.name.startswith('_'):
            func_info = self._extract_function_info(node)
            self.public_functions.append(func_info)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Visite les fonctions async"""
        if not node.name.startswith('_'):
            func_info = self._extract_function_info(node, is_async=True)
            self.public_functions.append(func_info)
        
        self.generic_visit(node)
    
    def _extract_function_info(self, node, is_async=False):
        """Extrait les informations d'une fonction"""
        # Signature
        args = []
        for arg in node.args.args:
            # Avec type annotation si disponible
            if arg.annotation:
                arg_type = ast.unparse(arg.annotation)
                args.append(f"{arg.arg}: {arg_type}")
            else:
                args.append(arg.arg)
        
        # Valeurs par défaut
        defaults = node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            for i, default in enumerate(defaults):
                arg_index = len(args) - num_defaults + i
                if arg_index >= 0 and arg_index < len(args):
                    default_value = ast.unparse(default)
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


def categorize_functions(functions):
    """Catégorise les fonctions par rôle"""
    categories = defaultdict(list)
    
    # Définir catégories explicites basées sur __all__
    v2_api = ['initialize_introspection', 'get_introspection', 'process_user_message', 
              'check_magic_phrases', 'stop_current_introspection']
    
    legacy_api = ['initialize_cognitive_mirror', 'get_cognitive_mirror', 
                  'get_reflection_context', 'start_inactivity_monitoring', 
                  'stop_reflection_session']
    
    common_api = ['cleanup', 'is_available', 'is_enabled', 'toggle_enabled',
                  'get_ui_components', 'get_extension_status']
    
    for func in functions:
        name = func['name']
        
        if name in v2_api:
            categories['API v2.0 (Nouveau)'].append(func)
        elif name in legacy_api:
            categories['API Legacy (Compatibilité)'].append(func)
        elif name in common_api:
            categories['API Commune'].append(func)
        else:
            categories['Autres'].append(func)
    
    return categories


def generate_markdown(categories, total_functions):
    """Génère le rapport Markdown"""
    md_lines = [
        "# Cognitive Mirror - API Publique Extraite",
        "",
        f"**Date d'extraction** : {Path(__file__).stem}",
        f"**Fichier source** : `extensions/cognitive_mirror/__init__.py`",
        f"**Total fonctions publiques** : {total_functions}",
        f"**Version Extension** : v2.0.0 (Introspection)",
        "",
        "---",
        "",
        "## 📊 Statistiques",
        "",
        f"- **Fonctions synchrones** : {sum(1 for cat in categories.values() for f in cat if not f['is_async'])}",
        f"- **Fonctions asynchrones** : {sum(1 for cat in categories.values() for f in cat if f['is_async'])}",
        "",
        "### Répartition par catégorie",
        ""
    ]
    
    for category, functions in sorted(categories.items()):
        md_lines.append(f"- **{category}** : {len(functions)} fonction(s)")
    
    md_lines.extend([
        "",
        "---",
        "",
        "## 📋 Fonctions par Catégorie",
        ""
    ])
    
    # Ordre de catégories logique
    category_order = [
        'API v2.0 (Nouveau)',
        'API Legacy (Compatibilité)',
        'API Commune',
        'Autres'
    ]
    
    for category in category_order:
        if category not in categories:
            continue
        
        functions = categories[category]
        md_lines.extend([
            f"### {category}",
            ""
        ])
        
        for func in sorted(functions, key=lambda f: f['lineno']):
            # Signature
            async_prefix = "async " if func['is_async'] else ""
            args_str = ", ".join(func['args']) if func['args'] else ""
            
            md_lines.extend([
                f"#### `{async_prefix}{func['name']}({args_str})`",
                "",
                f"**Ligne** : {func['lineno']}  ",
                f"**Retour** : `{func['return_type']}`",
                "",
                "**Description** :",
                f"> {func['docstring']}",
                ""
            ])
    
    return "\n".join(md_lines)


def main():
    """Point d'entrée principal"""
    print("🔍 Extraction API - Cognitive Mirror Extension")
    print("=" * 50)
    
    # Localiser __init__.py
    source_file = Path("extensions/cognitive_mirror/__init__.py")
    
    if not source_file.exists():
        print(f"❌ Fichier non trouvé : {source_file}")
        sys.exit(1)
    
    print(f"📄 Analyse : {source_file}")
    
    # Parser le fichier
    with open(source_file, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=str(source_file))
    
    # Extraire les fonctions publiques
    extractor = CognitiveMirrorAPIExtractor()
    extractor.visit(tree)
    
    public_functions = extractor.public_functions
    print(f"   ✅ {len(public_functions)} fonctions publiques extraites")
    
    # Statistiques
    sync_count = sum(1 for f in public_functions if not f['is_async'])
    async_count = sum(1 for f in public_functions if f['is_async'])
    print(f"      - Synchrones: {sync_count}")
    print(f"      - Asynchrones: {async_count}")
    
    # Catégoriser
    categories = categorize_functions(public_functions)
    
    # Générer Markdown
    print("\n📝 Génération rapport Markdown...")
    markdown_content = generate_markdown(categories, len(public_functions))
    
    # Sauvegarder
    output_dir = Path("docs/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "COGNITIVE_MIRROR_API_EXTRACTED.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"   ✅ Rapport sauvegardé : {output_file}")
    
    # Résumé final
    print("\n📊 Résumé")
    print("=" * 50)
    for category, functions in sorted(categories.items()):
        print(f"   {category:<35} : {len(functions)} fonction(s)")
    
    print(f"\n✅ Total : {len(public_functions)} fonctions publiques extraites")


if __name__ == "__main__":
    main()
