"""
Script d'extraction API - Conversation Manager

Extrait toutes les méthodes publiques des modules conversation pour documentation
et planification des tests.

Usage:
    python scripts/extract_conversation_api.py
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple

class ConversationAPIExtractor:
    """Extracteur API pour modules conversation"""
    
    def __init__(self):
        self.conversations_dir = Path("conversations")
        self.output_file = Path("docs/api/CONVERSATION_API_EXTRACTED.md")
        
        # Fichiers à analyser
        self.files_to_analyze = [
            "conversation_utils.py",
            "conversation_index.py",
            "conversation_commands.py",
        ]
        
        # Fichier racine si existe
        self.root_file = Path("conversation_summarizer.py")
        
        self.all_methods = {}  # {filename: [methods]}
        self.total_methods = 0
    
    def extract_methods_from_file(self, file_path: Path) -> List[Tuple[str, int, bool, str]]:
        """
        Extrait les méthodes publiques d'un fichier Python
        
        Returns:
            List[(method_name, line_number, is_async, class_name)]
        """
        methods = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                # Extract functions/methods
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_name = node.name
                    
                    # Filtrer méthodes privées (sauf __init__)
                    if method_name.startswith('_') and method_name != '__init__':
                        continue
                    
                    is_async = isinstance(node, ast.AsyncFunctionDef)
                    line_number = node.lineno
                    
                    # Déterminer classe propriétaire
                    class_owner = None
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            if node in parent.body:
                                class_owner = parent.name
                                break
                    
                    methods.append((method_name, line_number, is_async, class_owner))
            
        except Exception as e:
            print(f"[ERREUR] Impossible d'analyser {file_path}: {e}")
        
        return methods
    
    def generate_markdown_report(self) -> str:
        """Génère le rapport Markdown complet"""
        
        lines = []
        lines.append("# 💬 API Conversation Manager - Extraction Complète\n")
        lines.append(f"**Date**: 2025-11-05")
        lines.append(f"**Modules**: `conversations/`")
        lines.append(f"**Total Méthodes**: {self.total_methods}\n")
        lines.append("---\n")
        
        # Statistiques globales
        lines.append("## 📊 Statistiques Globales\n")
        
        total_async = 0
        total_sync = 0
        files_analyzed = 0
        
        for filename, methods in self.all_methods.items():
            if methods:
                files_analyzed += 1
                for _, _, is_async, _ in methods:
                    if is_async:
                        total_async += 1
                    else:
                        total_sync += 1
        
        lines.append(f"- **Fichiers analysés**: {files_analyzed}")
        lines.append(f"- **Méthodes totales**: {self.total_methods}")
        lines.append(f"- **Méthodes async**: {total_async}")
        lines.append(f"- **Méthodes sync**: {total_sync}\n")
        lines.append("---\n")
        
        # Détail par fichier
        for filename in self.files_to_analyze + [self.root_file.name]:
            if filename not in self.all_methods or not self.all_methods[filename]:
                continue
            
            methods = self.all_methods[filename]
            
            lines.append(f"## 📄 `{filename}`\n")
            lines.append(f"**Méthodes**: {len(methods)}\n")
            
            # Grouper par classe
            methods_by_class = {}
            for method_name, line_no, is_async, class_name in methods:
                if class_name not in methods_by_class:
                    methods_by_class[class_name] = []
                methods_by_class[class_name].append((method_name, line_no, is_async))
            
            # Functions au niveau module
            if None in methods_by_class:
                lines.append("### Fonctions Module\n")
                for method_name, line_no, is_async in methods_by_class[None]:
                    async_tag = "🔄 Async" if is_async else "⚙️ Sync"
                    lines.append(f"- `{method_name}()` - {async_tag} - Ligne {line_no}")
                lines.append("")
                del methods_by_class[None]
            
            # Méthodes par classe
            for class_name, class_methods in methods_by_class.items():
                lines.append(f"### Classe: `{class_name}`\n")
                for method_name, line_no, is_async in class_methods:
                    async_tag = "🔄 Async" if is_async else "⚙️ Sync"
                    lines.append(f"- `{method_name}()` - {async_tag} - Ligne {line_no}")
                lines.append("")
        
        lines.append("---\n")
        lines.append("**Généré automatiquement par**: `scripts/extract_conversation_api.py`")
        
        return "\n".join(lines)
    
    def run(self):
        """Exécute l'extraction complète"""
        print("="*60)
        print("🔍 Extraction API - Conversation Manager")
        print("="*60)
        print()
        
        # Analyser fichiers conversations/
        for filename in self.files_to_analyze:
            file_path = self.conversations_dir / filename
            
            if not file_path.exists():
                print(f"⚠️  Fichier non trouvé: conversations/{filename}")
                continue
            
            print(f"📄 Analyse: conversations/{filename}")
            methods = self.extract_methods_from_file(file_path)
            
            if methods:
                self.all_methods[filename] = methods
                self.total_methods += len(methods)
                print(f"   ✅ {len(methods)} méthodes extraites")
            else:
                print(f"   ⚠️  Aucune méthode publique trouvée")
        
        # Analyser fichier racine conversation_summarizer.py si existe
        if self.root_file.exists():
            print(f"📄 Analyse: {self.root_file.name}")
            methods = self.extract_methods_from_file(self.root_file)
            
            if methods:
                self.all_methods[self.root_file.name] = methods
                self.total_methods += len(methods)
                print(f"   ✅ {len(methods)} méthodes extraites")
        
        print()
        print("📝 Génération rapport Markdown...")
        
        # Générer le rapport
        report = self.generate_markdown_report()
        
        # Sauvegarder
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"   ✅ Rapport sauvegardé: {self.output_file}")
        print()
        print(f"📊 Total: {self.total_methods} méthodes publiques extraites")
        print("="*60)

if __name__ == "__main__":
    extractor = ConversationAPIExtractor()
    extractor.run()
