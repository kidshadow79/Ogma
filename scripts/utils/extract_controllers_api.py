#!/usr/bin/env python3
"""
Extracteur API - Controllers OGMA (core_logic.py)
=================================================

Extrait l'API publique des contrôleurs IA:
- AIController (chat/archiviste)
- EmbeddingController (vectorisation)
- Managers sous-jacents (Ollama, API, GGUF, KoboldCpp, AIHorde)

Usage: python extract_controllers_api.py
Output: CONTROLLERS_API_EXTRACTED.md

Auteur: Équipe Test OGMA
Date: 2025-11-05
"""

import ast
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional

OGMA_ROOT = Path(__file__).resolve().parent
CORE_LOGIC_FILE = OGMA_ROOT / "core_logic.py"
OUTPUT_FILE = OGMA_ROOT / "docs" / "api" / "CONTROLLERS_API_EXTRACTED.md"

def extract_class_methods(source_code: str, class_name: str) -> List[Dict[str, Any]]:
    """Extrait les méthodes publiques d'une classe via AST"""
    tree = ast.parse(source_code)
    methods = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Ignorer méthodes privées
                    if item.name.startswith('_') and not item.name.startswith('__'):
                        continue
                    
                    # Extraction signature
                    args = []
                    for arg in item.args.args:
                        arg_name = arg.arg
                        if arg_name == 'self':
                            continue
                        
                        # Type annotation si présente
                        arg_type = ""
                        if arg.annotation:
                            arg_type = ast.unparse(arg.annotation)
                        
                        args.append({
                            'name': arg_name,
                            'type': arg_type
                        })
                    
                    # Return type
                    return_type = ""
                    if item.returns:
                        return_type = ast.unparse(item.returns)
                    
                    # Docstring
                    docstring = ast.get_docstring(item) or ""
                    
                    # Async
                    is_async = isinstance(item, ast.AsyncFunctionDef)
                    
                    methods.append({
                        'name': item.name,
                        'args': args,
                        'return_type': return_type,
                        'docstring': docstring,
                        'is_async': is_async,
                        'lineno': item.lineno
                    })
    
    return methods


def generate_markdown(controllers_data: Dict[str, List[Dict]]) -> str:
    """Génère le markdown de documentation"""
    
    md = """# API Controllers OGMA - Documentation Complète

**Date d'extraction**: 2025-11-05  
**Fichier source**: `core_logic.py`  
**Composants**: AIController, EmbeddingController  

---

## Vue d'Ensemble

Les **Controllers OGMA** orchestrent l'intelligence artificielle multi-providers avec:
- **AIController**: Chat conversationnel (IA principale, Archiviste)
- **EmbeddingController**: Vectorisation mémoire

### Architecture Multi-Providers

```
┌────────────────────────────────────────┐
│         AIController                   │
├────────────────────────────────────────┤
│  Backend Router (4 backends)           │
│  ├─> API (OpenAI, Anthropic, etc.)    │
│  ├─> Ollama (local models)            │
│  ├─> GGUF/llama.cpp (VRAM optimize)   │
│  └─> KoboldCpp (community models)     │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│      EmbeddingController               │
├────────────────────────────────────────┤
│  Embedding Router (3 backends)         │
│  ├─> API (OpenAI, Mistral, Google)    │
│  ├─> Ollama (local embeddings)        │
│  └─> GGUF (local embeddings)          │
└────────────────────────────────────────┘
```

---

## API Publique

"""
    
    for class_name, methods in controllers_data.items():
        md += f"### {class_name}\n\n"
        
        # Méthodes publiques
        public_methods = [m for m in methods if not m['name'].startswith('_')]
        
        if not public_methods:
            md += "*Aucune méthode publique*\n\n"
            continue
        
        for method in public_methods:
            # Signature
            async_prefix = "async " if method['is_async'] else ""
            args_str = ", ".join([
                f"{arg['name']}: {arg['type']}" if arg['type'] else arg['name']
                for arg in method['args']
            ])
            
            return_annotation = f" -> {method['return_type']}" if method['return_type'] else ""
            
            md += f"#### `{async_prefix}def {method['name']}({args_str}){return_annotation}`\n\n"
            
            # Docstring
            if method['docstring']:
                md += f"**Description**:  \n{method['docstring']}\n\n"
            
            # Paramètres
            if method['args']:
                md += "**Paramètres**:\n"
                for arg in method['args']:
                    type_info = f" ({arg['type']})" if arg['type'] else ""
                    md += f"- `{arg['name']}`{type_info}\n"
                md += "\n"
            
            # Return
            if method['return_type']:
                md += f"**Retour**: `{method['return_type']}`\n\n"
            
            md += "---\n\n"
    
    return md


def main():
    """Extraction principale"""
    print(f"[EXTRACT] Lecture de {CORE_LOGIC_FILE}...")
    
    if not CORE_LOGIC_FILE.exists():
        print(f"[ERROR] Fichier non trouvé: {CORE_LOGIC_FILE}")
        return
    
    source_code = CORE_LOGIC_FILE.read_text(encoding='utf-8')
    
    # Extraction classes
    controllers = {
        'AIController': extract_class_methods(source_code, 'AIController'),
        'EmbeddingController': extract_class_methods(source_code, 'EmbeddingController'),
    }
    
    # Génération markdown
    print("[GENERATE] Génération de la documentation...")
    markdown = generate_markdown(controllers)
    
    # Sauvegarde
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(markdown, encoding='utf-8')
    
    print(f"[SUCCESS] Documentation générée: {OUTPUT_FILE}")
    
    # Stats
    total_methods = sum(len(methods) for methods in controllers.values())
    print(f"[STATS] {len(controllers)} classes, {total_methods} méthodes extraites")


if __name__ == '__main__':
    main()
