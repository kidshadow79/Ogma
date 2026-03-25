"""
Analyse des dossiers inutilisés dans OGMA
==========================================

Vérifie si les dossiers backup/test sont référencés dans le code actif.
"""

import os
import re
from pathlib import Path

# Dossiers à analyser
DIRECTORIES_TO_CHECK = [
    "backups",
    "backup_audio_system",
    ".pytest_cache"
]

# Fichiers Python actifs à scanner (exclusions)
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".git",
    "profils_sauvegardes",
    "data",
    "extensions/*/data",
    ".pytest_cache",
    "venv",
    "env"
]

def should_exclude(path: Path) -> bool:
    """Vérifie si le chemin doit être exclu."""
    path_str = str(path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False

def find_python_files(root_dir: Path) -> list:
    """Trouve tous les fichiers Python actifs."""
    python_files = []
    for py_file in root_dir.rglob("*.py"):
        if not should_exclude(py_file):
            python_files.append(py_file)
    return python_files

def search_directory_references(dir_name: str, python_files: list) -> dict:
    """Recherche les références à un dossier dans les fichiers Python."""
    references = {
        "found": False,
        "files": [],
        "lines": []
    }
    
    # Patterns de recherche
    patterns = [
        rf'["\'].*{dir_name}.*["\']',  # Chaînes contenant le nom
        rf'{dir_name}/',               # Path avec /
        rf'{dir_name}\\',              # Path avec \
        rf'Path\(.*{dir_name}.*\)',    # Path()
        rf'os\.path\..*{dir_name}',    # os.path
    ]
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            references["found"] = True
                            references["files"].append(str(py_file))
                            references["lines"].append({
                                "file": py_file.name,
                                "line_num": i,
                                "content": line.strip()
                            })
                            break
        except Exception as e:
            print(f"⚠️  Erreur lecture {py_file}: {e}")
    
    return references

def check_directory_usage(dir_path: Path) -> dict:
    """Vérifie l'utilisation réelle d'un dossier."""
    usage = {
        "exists": dir_path.exists(),
        "size_mb": 0,
        "file_count": 0,
        "last_modified": None,
        "empty": True
    }
    
    if not usage["exists"]:
        return usage
    
    # Compter fichiers et taille
    total_size = 0
    file_count = 0
    last_modified = None
    
    for item in dir_path.rglob("*"):
        if item.is_file():
            file_count += 1
            total_size += item.stat().st_size
            
            # Dernière modification
            mtime = item.stat().st_mtime
            if last_modified is None or mtime > last_modified:
                last_modified = mtime
    
    usage["file_count"] = file_count
    usage["size_mb"] = round(total_size / (1024 * 1024), 2)
    usage["empty"] = file_count == 0
    
    if last_modified:
        from datetime import datetime
        usage["last_modified"] = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M:%S")
    
    return usage

def main():
    print("=" * 70)
    print("🔍 ANALYSE DES DOSSIERS INUTILISÉS - OGMA")
    print("=" * 70)
    print()
    
    root_dir = Path(__file__).parent
    print(f"📁 Racine projet: {root_dir}")
    print()
    
    # Trouver fichiers Python actifs
    print("🔎 Scan fichiers Python actifs...")
    python_files = find_python_files(root_dir)
    print(f"   ✅ {len(python_files)} fichiers Python trouvés")
    print()
    
    # Analyser chaque dossier
    results = {}
    
    for dir_name in DIRECTORIES_TO_CHECK:
        print(f"\n{'=' * 70}")
        print(f"📂 Analyse: {dir_name}")
        print(f"{'=' * 70}")
        
        dir_path = root_dir / dir_name
        
        # Vérifier usage physique
        usage = check_directory_usage(dir_path)
        
        print(f"\n📊 Usage physique:")
        print(f"   - Existe: {'✅ Oui' if usage['exists'] else '❌ Non'}")
        
        if usage['exists']:
            print(f"   - Fichiers: {usage['file_count']}")
            print(f"   - Taille: {usage['size_mb']} MB")
            print(f"   - Vide: {'✅ Oui' if usage['empty'] else '❌ Non'}")
            if usage['last_modified']:
                print(f"   - Dernière modif: {usage['last_modified']}")
        
        # Rechercher références code
        print(f"\n🔍 Références dans code:")
        refs = search_directory_references(dir_name, python_files)
        
        if refs["found"]:
            print(f"   ⚠️  TROUVÉ {len(refs['lines'])} références")
            print(f"\n   Fichiers concernés:")
            unique_files = set(refs["files"])
            for file in unique_files:
                print(f"      - {Path(file).name}")
            
            print(f"\n   Extraits:")
            for ref in refs["lines"][:5]:  # Max 5 exemples
                print(f"      {ref['file']}:{ref['line_num']} → {ref['content'][:60]}...")
        else:
            print(f"   ✅ AUCUNE référence trouvée")
        
        # Verdict
        print(f"\n🎯 VERDICT:")
        
        can_delete = True
        reasons = []
        
        if not usage['exists']:
            print(f"   ℹ️  Dossier inexistant")
            can_delete = False
        elif refs["found"]:
            print(f"   ❌ NE PAS SUPPRIMER - Utilisé dans code")
            can_delete = False
            reasons.append("Références code actives")
        elif not usage['empty']:
            print(f"   ⚠️  VÉRIFIER CONTENU - {usage['file_count']} fichiers ({usage['size_mb']} MB)")
            if usage['size_mb'] > 10:
                reasons.append(f"Gros volume ({usage['size_mb']} MB)")
            else:
                print(f"   ✅ PEUT ÊTRE SUPPRIMÉ (petit volume)")
        else:
            print(f"   ✅ PEUT ÊTRE SUPPRIMÉ - Vide et non utilisé")
        
        results[dir_name] = {
            "usage": usage,
            "references": refs,
            "can_delete": can_delete,
            "reasons": reasons
        }
    
    # Résumé final
    print(f"\n\n{'=' * 70}")
    print("📋 RÉSUMÉ RECOMMANDATIONS")
    print(f"{'=' * 70}\n")
    
    can_delete_list = []
    verify_list = []
    keep_list = []
    
    for dir_name, result in results.items():
        if not result['usage']['exists']:
            continue
        
        if result['references']['found']:
            keep_list.append(dir_name)
        elif result['usage']['empty']:
            can_delete_list.append(dir_name)
        else:
            verify_list.append(dir_name)
    
    if can_delete_list:
        print("✅ SUPPRESSION SÛRE (vide + non utilisé):")
        for dir_name in can_delete_list:
            print(f"   - {dir_name}")
    
    if verify_list:
        print("\n⚠️  VÉRIFICATION MANUELLE (contenu mais non utilisé):")
        for dir_name in verify_list:
            usage = results[dir_name]['usage']
            print(f"   - {dir_name} ({usage['file_count']} fichiers, {usage['size_mb']} MB)")
    
    if keep_list:
        print("\n❌ CONSERVER (utilisé dans code):")
        for dir_name in keep_list:
            print(f"   - {dir_name}")
    
    print("\n" + "=" * 70)
    print("✅ Analyse terminée")
    print("=" * 70)

if __name__ == "__main__":
    main()
