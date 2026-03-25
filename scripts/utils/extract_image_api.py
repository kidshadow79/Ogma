"""
Extracteur d'API pour Text2Image Extension
==========================================
Extrait les méthodes publiques de l'extension text2img pour génération de documentation.

Analyse:
- extensions/text2img/__init__.py (fonctions de niveau module)
- extensions/text2img/text2img_manager.py (classe Text2ImageManager)

Usage:
    python scripts/extract_image_api.py
"""

import ast
import inspect
from pathlib import Path
from typing import List, Dict, Any

# Chemins des fichiers à analyser
INIT_FILE = Path("extensions/text2img/__init__.py")
MANAGER_FILE = Path("extensions/text2img/text2img_manager.py")
OUTPUT_FILE = Path("docs/api/IMAGE_GEN_API_EXTRACTED.md")


class APIExtractor:
    """Extracteur AST pour fonctions et méthodes publiques"""

    def __init__(self):
        self.functions = []
        self.methods = []

    def extract_from_init(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extrait les fonctions publiques du __init__.py"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Ignorer les fonctions privées
                if node.name.startswith('_'):
                    continue

                # Extraire signature
                args = [arg.arg for arg in node.args.args]
                
                # Extraire docstring
                docstring = ast.get_docstring(node) or "Pas de documentation"

                # Extraire type de retour si présent
                return_type = None
                if node.returns:
                    return_type = ast.unparse(node.returns)

                functions.append({
                    "name": node.name,
                    "args": args,
                    "return_type": return_type,
                    "docstring": docstring,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })

        return functions

    def extract_from_manager(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extrait les méthodes publiques de Text2ImageManager"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        methods = []

        # Trouver la classe Text2ImageManager
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Text2ImageManager":
                # Parcourir les méthodes
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        # Ignorer les méthodes privées
                        if item.name.startswith('_'):
                            continue

                        # Extraire signature (sans self)
                        args = [arg.arg for arg in item.args.args if arg.arg != 'self']
                        
                        # Extraire docstring
                        docstring = ast.get_docstring(item) or "Pas de documentation"

                        # Extraire type de retour si présent
                        return_type = None
                        if item.returns:
                            return_type = ast.unparse(item.returns)

                        methods.append({
                            "name": item.name,
                            "args": args,
                            "return_type": return_type,
                            "docstring": docstring,
                            "is_async": isinstance(item, ast.AsyncFunctionDef)
                        })

        return methods

    def generate_markdown(self, functions: List[Dict], methods: List[Dict]) -> str:
        """Génère la documentation Markdown"""
        
        md = "# API Text2Image Extension - Documentation Extraite\n\n"
        md += f"**Version**: 1.0.0  \n"
        md += f"**Fichiers analysés**: `__init__.py`, `text2img_manager.py`  \n"
        md += f"**Date d'extraction**: {Path(__file__).stat().st_mtime}  \n\n"
        
        md += "## Vue d'ensemble\n\n"
        md += "Extension de génération d'images via IA à partir de prompts textuels.\n\n"
        md += "**Backends supportés**:\n"
        md += "- Pollinations.AI (Stable Diffusion, Flux) - Gratuit et illimité\n"
        md += "- Perchance.org (legacy)\n\n"
        
        # Statistiques
        total_api = len(functions) + len(methods)
        md += f"**Total API**: {total_api} (Fonctions: {len(functions)}, Méthodes: {len(methods)})\n\n"
        
        md += "---\n\n"
        
        # Section 1: Fonctions Extension (__init__.py)
        md += "## 1. API Extension (Niveau Module)\n\n"
        md += "Fonctions publiques dans `extensions/text2img/__init__.py`\n\n"
        
        for func in functions:
            md += f"### `{func['name']}()`\n\n"
            
            # Signature
            args_str = ", ".join(func['args']) if func['args'] else ""
            async_prefix = "async " if func['is_async'] else ""
            return_str = f" -> {func['return_type']}" if func['return_type'] else ""
            md += f"```python\n{async_prefix}def {func['name']}({args_str}){return_str}\n```\n\n"
            
            # Docstring
            md += f"**Documentation**:\n```\n{func['docstring']}\n```\n\n"
            
            md += "---\n\n"
        
        # Section 2: Méthodes Manager
        md += "## 2. API Manager (Text2ImageManager)\n\n"
        md += "Méthodes publiques de la classe `Text2ImageManager`\n\n"
        
        for method in methods:
            md += f"### `{method['name']}()`\n\n"
            
            # Signature
            args_str = ", ".join(method['args']) if method['args'] else ""
            async_prefix = "async " if method['is_async'] else ""
            return_str = f" -> {method['return_type']}" if method['return_type'] else ""
            md += f"```python\n{async_prefix}def {method['name']}({args_str}){return_str}\n```\n\n"
            
            # Docstring
            md += f"**Documentation**:\n```\n{method['docstring']}\n```\n\n"
            
            md += "---\n\n"
        
        # Section 3: Résumé de l'API
        md += "## 3. Résumé de l'API\n\n"
        
        md += "### Fonctions Extension (3)\n"
        md += "| Fonction | Args | Retour | Async |\n"
        md += "|----------|------|--------|-------|\n"
        for func in functions:
            args_count = len(func['args'])
            ret = func['return_type'] or 'None'
            is_async = '✅' if func['is_async'] else '❌'
            md += f"| `{func['name']}` | {args_count} | `{ret}` | {is_async} |\n"
        md += "\n"
        
        md += "### Méthodes Manager (5)\n"
        md += "| Méthode | Args | Retour | Async |\n"
        md += "|---------|------|--------|-------|\n"
        for method in methods:
            args_count = len(method['args'])
            ret = method['return_type'] or 'None'
            is_async = '✅' if method['is_async'] else '❌'
            md += f"| `{method['name']}` | {args_count} | `{ret}` | {is_async} |\n"
        md += "\n"
        
        # Workflow type
        md += "## 4. Workflow de Génération\n\n"
        md += "```python\n"
        md += "# 1. Initialiser l'extension\n"
        md += "initialize_text2img(settings_manager)  # -> bool\n\n"
        md += "# 2. Récupérer le manager\n"
        md += "manager = get_text2img_manager()  # -> Text2ImageManager | None\n\n"
        md += "# 3. Générer une image\n"
        md += "image_bytes, error, metadata = await manager.generate_image(\"fantasy landscape\")\n\n"
        md += "# 4. Sauvegarder (optionnel)\n"
        md += "if image_bytes:\n"
        md += "    filepath, error = manager.save_image(image_bytes, metadata)\n\n"
        md += "# 5. Consulter l'historique\n"
        md += "history = manager.get_history(limit=10)\n"
        md += "```\n\n"
        
        md += "## 5. Patterns de Test\n\n"
        md += "- **Fixtures**: `mock_settings_manager`, `temp_images_dir`, `text2img_manager`\n"
        md += "- **Isolation**: tmp_path pour dossier generated_images\n"
        md += "- **Async**: AsyncMock pour backend.generate_image()\n"
        md += "- **I/O**: Tests end-to-end avec fichiers réels (isolation tmp_path)\n"
        md += "- **Cleanup**: autouse fixture pour reset singleton global\n\n"
        
        return md


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("EXTRACTION API TEXT2IMAGE EXTENSION")
    print("=" * 60)
    print()

    extractor = APIExtractor()

    # Extraire depuis __init__.py
    print(f"📖 Analyse de {INIT_FILE}...")
    functions = extractor.extract_from_init(INIT_FILE)
    print(f"   ✅ {len(functions)} fonctions publiques trouvées")

    # Extraire depuis text2img_manager.py
    print(f"📖 Analyse de {MANAGER_FILE}...")
    methods = extractor.extract_from_manager(MANAGER_FILE)
    print(f"   ✅ {len(methods)} méthodes publiques trouvées")

    # Générer la documentation
    print(f"\n📝 Génération de la documentation...")
    markdown = extractor.generate_markdown(functions, methods)

    # Créer le dossier de sortie si nécessaire
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"   ✅ Documentation sauvegardée: {OUTPUT_FILE}")
    print()
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Total API: {len(functions) + len(methods)}")
    print(f"  - Fonctions extension: {len(functions)}")
    print(f"  - Méthodes manager: {len(methods)}")
    print()
    print("Fichier généré:")
    print(f"  📄 {OUTPUT_FILE}")
    print()


if __name__ == "__main__":
    main()
