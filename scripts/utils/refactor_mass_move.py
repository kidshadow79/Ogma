#!/usr/bin/env python3
"""
Script de refactoring rapide - Déplacement en masse des fonctions debug/test
"""

import re

# Fonctions UI/modales à déplacer (PHASE 2)
FUNCTIONS_TO_MOVE = [
    '_link_styles',           # 301 lignes - CSS
    '_instructions_modal',    # 102 lignes - Modal
    '_settings_hub_modal',    # 100 lignes - Modal
    '_archi_sensor_modal',    # 75 lignes - Modal
    '_memory_modal',          # 59 lignes - Modal
    '_edit_memory_popup',     # 56 lignes - Modal
    '_memorization_popup',    # 47 lignes - Modal
    '_open_other_backends_popup'  # 28 lignes - Modal
]

def extract_function(content, func_name):
    """Extrait une fonction complète du contenu"""
    lines = content.split('\n')
    start_idx = None

    # Trouver le début de la fonction
    for i, line in enumerate(lines):
        if line.strip().startswith(f'def {func_name}('):
            start_idx = i
            break

    if start_idx is None:
        return None, content

    # Trouver la fin (prochaine fonction ou fin de fichier)
    end_idx = len(lines)
    indent_level = len(lines[start_idx]) - len(lines[start_idx].lstrip())

    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() == '':
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= indent_level and (line.strip().startswith('def ') or line.strip().startswith('class ')):
            end_idx = i
            break

    # Extraire la fonction
    func_lines = lines[start_idx:end_idx]
    func_content = '\n'.join(func_lines)

    # Supprimer du contenu original
    remaining_lines = lines[:start_idx] + lines[end_idx:]
    remaining_content = '\n'.join(remaining_lines)

    return func_content, remaining_content

def clean_emojis(text):
    """Supprime les emojis qui causent des problèmes d'encodage"""
    # Remplacements basiques
    replacements = {
        '🧪': 'TEST',
        '🔧': 'CONFIG',
        '✅': 'OK',
        '❌': 'ERREUR',
        '⚠️': 'ATTENTION',
        '🎯': 'CIBLE',
        '🔄': 'MAJ',
        '👁️': 'VISUEL',
        '✨': 'PULSE',
        '🟢': 'ACTIF',
        '⚫': 'INACTIF',
        '🔍': 'RECHERCHE',
        '🧠': 'COGNITIF',
        '💡': 'IDEE'
    }

    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)

    return text

def main():
    print("=== REFACTORING MASS MOVE ===")

    # Lire le fichier original
    with open('ogma_ng.py', 'r', encoding='utf-8') as f:
        original_content = f.read()

    print(f"Taille originale: {len(original_content.split(chr(10)))} lignes")

    # Lire le fichier de composants
    with open('ogma_ui_components.py', 'r', encoding='utf-8') as f:
        components_content = f.read()

    moved_functions = []
    remaining_content = original_content

    # Déplacer chaque fonction
    for func_name in FUNCTIONS_TO_MOVE:
        print(f"Déplacement de {func_name}...")
        func_content, remaining_content = extract_function(remaining_content, func_name)

        if func_content:
            # Nettoyer les emojis
            func_content_clean = clean_emojis(func_content)
            moved_functions.append(func_content_clean)

            # Ajouter un alias dans le fichier original
            alias = f"""
# FONCTION DÉPLACÉE vers ogma_ui_components.py
def {func_name}(*args, **kwargs):
    \"\"\"DÉPLACÉE: Redirige vers ogma_ui_components.{func_name}()\"\"\"
    from ogma_ui_components import {func_name} as moved_func
    return moved_func(*args, **kwargs)
"""
            remaining_content += alias
            print(f"  OK {func_name} deplacee")
        else:
            print(f"  ERREUR {func_name} non trouvee")

    # Ajouter les fonctions au fichier de composants
    if moved_functions:
        separator = "\n\n# " + "="*70 + "\n# FONCTIONS SUPPLEMENTAIRES DEPLACEES\n# " + "="*70 + "\n\n"
        components_content += separator + '\n\n'.join(moved_functions)

    # Ecrire les fichiers modifies
    with open('ogma_ng.py', 'w', encoding='utf-8') as f:
        f.write(remaining_content)

    with open('ogma_ui_components.py', 'w', encoding='utf-8') as f:
        f.write(components_content)

    print(f"Taille finale ogma_ng.py: {len(remaining_content.split(chr(10)))} lignes")
    print(f"Fonctions deplacees: {len(moved_functions)}")
    print("=== REFACTORING TERMINE ===")

if __name__ == '__main__':
    main()