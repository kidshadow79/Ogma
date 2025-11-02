"""
Script de suppression automatique des fonctions dupliquées d'ogma_ng.py
Garde le backup pour restauration si nécessaire
"""

import ast
import sys
from pathlib import Path

# Fonctions à supprimer (présentes dans ogma_ui_conversations.py)
FUNCTIONS_TO_REMOVE = [
    '_message',
    '_load_conversation_index', 
    '_save_conversation_index',
    '_make_conv_id',
    '_make_title_from_text',
    '_generate_smart_title_from_history',
    '_schedule_smart_title_generation',
    '_generate_smart_title_async',
    '_regenerate_title_manual',
    '_check_progressive_summarization',
    '_persist_conversation',
    '_maybe_update_conv_title',
    '_render_full_history',
    '_sidebar',
    '_load_conversation',
    '_new_conversation',
    '_generate_conversation_summary',
    '_memorize_conversation',
    '_mark_conversation_memorized',
    '_is_conversation_memorized',
    '_count_memorized_conversations',
    '_get_memorized_conversations_list',
    '_update_memorized_conversation',
    '_delete_memorized_conversation',
    '_create_edit_interface',
    '_edit_summary_popup',
    '_delete_conversation_modal',
    '_edit_conversation_title_modal',
    '_display_conversation_as_attachment',
    '_display_archived_conversation',
    '_display_search_results',
    '_display_conversation_summary',
    '_display_available_conversations',
    'load_message_for_edit',
]

def find_function_ranges(filepath: Path) -> dict:
    """
    Parse le fichier et trouve les plages de lignes de chaque fonction
    Retourne {nom_fonction: (ligne_debut, ligne_fin)}
    """
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    try:
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe dans {filepath}: {e}")
        return {}
    
    function_ranges = {}
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            start_line = node.lineno  # 1-indexed
            
            # Trouver la ligne de fin en cherchant la prochaine fonction de même niveau
            # ou la fin du fichier
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
            
            function_ranges[func_name] = (start_line, end_line)
    
    return function_ranges

def remove_functions(source_file: Path, output_file: Path, functions_to_remove: list) -> tuple:
    """
    Supprime les fonctions spécifiées du fichier source
    Retourne (success, lines_removed, message)
    """
    print(f"\n📖 Lecture de {source_file}...")
    content = source_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    total_lines = len(lines)
    
    print(f"📊 Fichier original: {total_lines} lignes")
    
    # Trouver les plages de lignes des fonctions
    print(f"\n🔍 Analyse AST...")
    function_ranges = find_function_ranges(source_file)
    
    if not function_ranges:
        return False, 0, "Impossible de parser le fichier"
    
    print(f"✅ {len(function_ranges)} fonctions détectées")
    
    # Identifier les fonctions à supprimer
    to_remove_ranges = []
    for func_name in functions_to_remove:
        if func_name in function_ranges:
            start, end = function_ranges[func_name]
            to_remove_ranges.append((start, end, func_name))
            print(f"  🎯 {func_name}: lignes {start}-{end} ({end - start + 1} lignes)")
    
    if not to_remove_ranges:
        return False, 0, "Aucune fonction à supprimer trouvée"
    
    # Trier par ligne de début (pour supprimer de haut en bas)
    to_remove_ranges.sort(key=lambda x: x[0])
    
    # Créer un set de lignes à supprimer (0-indexed)
    lines_to_remove = set()
    for start, end, func_name in to_remove_ranges:
        for line_num in range(start - 1, end):  # Convertir en 0-indexed
            lines_to_remove.add(line_num)
    
    # Construire le nouveau contenu
    new_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_remove:
            new_lines.append(line)
    
    # Écrire le résultat
    print(f"\n💾 Écriture de {output_file}...")
    output_file.write_text('\n'.join(new_lines), encoding='utf-8')
    
    new_total = len(new_lines)
    removed = total_lines - new_total
    
    print(f"✅ Fichier modifié: {new_total} lignes (-{removed} lignes, -{removed/total_lines*100:.1f}%)")
    
    return True, removed, f"Supprimé {len(to_remove_ranges)} fonctions ({removed} lignes)"

def verify_syntax(filepath: Path) -> bool:
    """Vérifie que le fichier est syntaxiquement correct"""
    try:
        content = filepath.read_text(encoding='utf-8')
        compile(content, str(filepath), 'exec')
        print(f"✅ Syntaxe Python valide: {filepath.name}")
        return True
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe: {e}")
        return False

def main():
    source = Path("ogma_ng.py")
    backup = Path("ogma_ng.BACKUP_AVANT_SUPPRESSION.py")
    output = Path("ogma_ng.py")
    
    if not source.exists():
        print(f"❌ Fichier source introuvable: {source}")
        return 1
    
    if not backup.exists():
        print(f"⚠️ Backup non trouvé, création...")
        backup.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
    
    print("=" * 60)
    print("🗑️  SUPPRESSION AUTOMATIQUE DES FONCTIONS DUPLIQUÉES")
    print("=" * 60)
    
    # Supprimer les fonctions
    success, removed, message = remove_functions(source, output, FUNCTIONS_TO_REMOVE)
    
    if not success:
        print(f"\n❌ Échec: {message}")
        return 1
    
    print(f"\n📋 {message}")
    
    # Vérifier la syntaxe
    print(f"\n🔍 Vérification syntaxe...")
    if not verify_syntax(output):
        print(f"\n❌ ERREUR: Fichier résultant invalide !")
        print(f"🔄 Restauration depuis backup...")
        output.write_text(backup.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"✅ Fichier restauré")
        return 1
    
    print(f"\n" + "=" * 60)
    print(f"✅ SUCCÈS - Fonctions dupliquées supprimées")
    print(f"📁 Backup disponible: {backup}")
    print(f"=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
