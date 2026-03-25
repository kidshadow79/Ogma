#!/usr/bin/env python3
"""
Script de correction automatique tests Memory Manager strict.

Corrige:
1. add_memory() retourne bool, pas ID → utiliser memory_id directement
2. search_memories() retourne dicts avec clé 'id' (pas 'memory_id')
3. Patterns incorrects générés par PowerShell
"""

import re
from pathlib import Path

FILE = Path("tests/unit/test_memory_manager_strict.py")

def fix_add_memory_patterns(content):
    """Corrige patterns add_memory incorrects."""
    
    # Pattern: variable_id_success = await mm.add_memory(variable_id,
    # → variable_id = "CONSTANT"; success = await mm.add_memory(
    
    # Fix: cat_id_success = await mm.add_memory(cat_id,
    content = re.sub(
        r'(\w+)_id_success\s*=\s*await\s+mm\.add_memory\(\1_id,',
        r'\1_id = "SEARCH-CAT"  # Define ID\n        success = await mm.add_memory(',
        content
    )
    
    # Fix incorrect parameter order from PowerShell damage
    content = re.sub(
        r'await\s+mm\.add_memory\((\w+_id),\s*memory_id=',
        r'await mm.add_memory(memory_id=',
        content
    )
    
    return content

def main():
    print(f"📝 Lecture {FILE}...")
    content = FILE.read_text(encoding='utf-8')
    
    print("🔧 Correction patterns add_memory...")
    content = fix_add_memory_patterns(content)
    
    print("💾 Sauvegarde...")
    FILE.write_text(content, encoding='utf-8')
    
    print("✅ Corrections appliquées !")

if __name__ == "__main__":
    main()
