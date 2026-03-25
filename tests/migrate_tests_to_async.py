"""
Script de Migration Automatique - Tests Synchrones → Async
============================================================

Transforme automatiquement les tests Memory Manager pour utiliser l'API async.

Changements appliqués:
1. def test_* → async def test_*
2. Ajoute @pytest.mark.asyncio avant chaque test
3. Ajoute await devant appels async (add_memory, search_memories, update_memory, delete_memory)
4. Corrige signatures API:
   - add_memory(text=...) → add_memory(memory_id=..., text_brut=...)
   - search_memories(query=..., k=5) → search_memories(query=..., limit=5)
   - update_memory(metadata=...) → update_memory(memory_id=..., title=..., summary=...)
"""

import re
from pathlib import Path

def migrate_test_file(filepath: Path):
    """Migre un fichier de tests vers async."""
    
    print(f"📝 Migration de: {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_count = 0
    
    # 1. Convertir def test_* → async def test_*
    pattern = r'(\s+)(def test_[a-zA-Z_]+)\('
    def add_async(match):
        nonlocal changes_count
        changes_count += 1
        return f"{match.group(1)}async {match.group(2)}("
    
    content = re.sub(pattern, add_async, content)
    
    # 2. Ajouter @pytest.mark.asyncio avant chaque async def test_
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        # Si ligne suivante contient "async def test_" et ligne actuelle n'est pas le decorator
        if i < len(lines) - 1:
            next_line = lines[i + 1]
            if 'async def test_' in next_line and '@pytest.mark.asyncio' not in line:
                # Détecter l'indentation
                indent_match = re.match(r'^(\s*)', next_line)
                indent = indent_match.group(1) if indent_match else '    '
                
                # Si c'est une docstring, insérer avant
                if '"""' in line or "'''" in line:
                    new_lines.append(line)
                    continue
                # Si ligne vide ou début de classe, ajouter decorator
                elif line.strip() == '' or 'class Test' in line:
                    new_lines.append(line)
                    if line.strip() != '':  # Pas de decorator après ligne vide
                        continue
                    new_lines.append(f"{indent}@pytest.mark.asyncio")
                    changes_count += 1
                    continue
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # 3. Ajouter await devant mock_memory_manager.add_memory(
    content = re.sub(
        r'(\s+)(memory_id|mid|result|success)\s*=\s*mock_memory_manager\.add_memory\(',
        r'\1\2 = await mock_memory_manager.add_memory(',
        content
    )
    changes_count += content.count('await mock_memory_manager.add_memory(') - original_content.count('await mock_memory_manager.add_memory(')
    
    # 4. Ajouter await devant mm1.add_memory( (variable temporaire)
    content = re.sub(
        r'(\s+)(mm1|mm2)\.add_memory\(',
        r'\1await \2.add_memory(',
        content
    )
    
    # 5. Ajouter await devant search_memories(
    content = re.sub(
        r'(\s+)(results?)\s*=\s*(mock_memory_manager|mm)\.search_memories\(',
        r'\1\2 = await \3.search_memories(',
        content
    )
    
    # 6. Ajouter await devant update_memory(
    content = re.sub(
        r'(\s+)(success|updated)\s*=\s*mock_memory_manager\.update_memory\(',
        r'\1\2 = await mock_memory_manager.update_memory(',
        content
    )
    
    # 7. Ajouter await devant delete_memory(
    content = re.sub(
        r'(\s+)(success|deleted)\s*=\s*mock_memory_manager\.delete_memory\(',
        r'\1\2 = await mock_memory_manager.delete_memory(',
        content
    )
    
    # 8. Corriger signature add_memory: text= → text_brut=
    content = content.replace('add_memory(\n        text="', 'add_memory(\n        memory_id="mem_test",\n        text_brut="')
    content = content.replace('add_memory(text="', 'add_memory(memory_id="mem_test", text_brut="')
    
    # 9. Corriger search_memories: k= → limit=
    content = content.replace('search_memories(query=', 'search_memories(query=')
    content = content.replace(', k=', ', limit=')
    
    # 10. Retirer metadata={} car pas supporté par add_memory
    # On va simplement commenter pour l'instant
    content = re.sub(
        r',\s*metadata=\{[^}]*\}',
        r'  # metadata removed (not in real API)',
        content
    )
    
    if content != original_content:
        # Backup original
        backup_path = filepath.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # Écrire version migrée
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Migration réussie: {changes_count} changements")
        print(f"💾 Backup créé: {backup_path.name}")
        return True
    else:
        print(f"⏭️  Aucune modification nécessaire")
        return False


if __name__ == "__main__":
    test_file = Path(__file__).parent / "unit" / "test_memory_manager.py"
    
    if not test_file.exists():
        print(f"❌ Fichier non trouvé: {test_file}")
        exit(1)
    
    print("🚀 MIGRATION TESTS SYNCHRONES → ASYNC")
    print("=" * 60)
    print()
    
    success = migrate_test_file(test_file)
    
    print()
    print("=" * 60)
    if success:
        print("✅ MIGRATION TERMINÉE")
        print()
        print("⚠️  ATTENTION: Vérifications manuelles nécessaires:")
        print("   1. Signatures add_memory() - vérifier memory_id, text_brut")
        print("   2. Signatures update_memory() - vérifier paramètres kwargs")
        print("   3. Tests avec variables temporaires (mm1, mm2)")
        print()
        print("🧪 Commande de test:")
        print("   pytest tests/unit/test_memory_manager.py -v")
    else:
        print("ℹ️  Aucune migration effectuée")
