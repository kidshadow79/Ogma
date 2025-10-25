#!/usr/bin/env python3
"""
Système de synchronisation ego_prompt.txt <-> base de données
Nettoie automatiquement les références orphelines
"""

import re
import sqlite3
from pathlib import Path
from typing import List, Set

def get_existing_ego_traits(db_path: Path) -> Set[str]:
    """Récupère tous les IDs de traits ego existants dans la DB"""
    existing_ids = set()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT id FROM memories WHERE type = 'ego_trait'")
            for (trait_id,) in cursor.fetchall():
                existing_ids.add(f"#MEM_{trait_id}")
    except sqlite3.Error as e:
        print(f"❌ Erreur accès DB: {e}")
    
    return existing_ids

def get_references_in_ego_file(ego_file_path: Path) -> List[str]:
    """Extrait toutes les références #MEM_XXX du fichier ego_prompt.txt"""
    if not ego_file_path.exists():
        return []
    
    content = ego_file_path.read_text(encoding='utf-8')
    return re.findall(r'#MEM_\w+', content)

def clean_orphaned_references(ego_file_path: Path, db_path: Path, dry_run: bool = False) -> dict:
    """
    Nettoie les références orphelines du fichier ego_prompt.txt
    
    Args:
        ego_file_path: Chemin vers ego_prompt.txt
        db_path: Chemin vers la base de données
        dry_run: Si True, ne fait que simuler (pas de modification)
    
    Returns:
        dict: Statistiques de nettoyage
    """
    
    print("🧹 NETTOYAGE DES RÉFÉRENCES ORPHELINES")
    print("=" * 45)
    
    # 1. Récupérer les IDs existants dans la DB
    existing_ids = get_existing_ego_traits(db_path)
    print(f"📊 Traits ego dans la DB: {len(existing_ids)}")
    
    # 2. Récupérer les références dans le fichier ego
    file_references = get_references_in_ego_file(ego_file_path)
    print(f"📄 Références dans ego_prompt.txt: {len(file_references)}")
    
    # 3. Identifier les orphelines
    orphaned_refs = [ref for ref in file_references if ref not in existing_ids]
    valid_refs = [ref for ref in file_references if ref in existing_ids]
    
    print(f"✅ Références valides: {len(valid_refs)}")
    print(f"🗑️ Références orphelines: {len(orphaned_refs)}")
    
    if orphaned_refs:
        print(f"🔍 Références à supprimer:")
        for ref in orphaned_refs:
            print(f"   - {ref}")
    
    # 4. Nettoyer le fichier si nécessaire
    if orphaned_refs and not dry_run:
        content = ego_file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Supprimer chaque référence orpheline
        for ref in orphaned_refs:
            # Supprimer la ligne contenant la référence
            lines = content.split('\n')
            cleaned_lines = [line for line in lines if ref not in line]
            content = '\n'.join(cleaned_lines)
        
        # Sauvegarder le fichier nettoyé
        ego_file_path.write_text(content, encoding='utf-8')
        
        print(f"✅ Fichier ego_prompt.txt nettoyé!")
        print(f"📊 {len(original_content)} → {len(content)} caractères")
    
    elif orphaned_refs and dry_run:
        print(f"🔍 Mode simulation - fichier non modifié")
    
    elif not orphaned_refs:
        print(f"✨ Aucune référence orpheline trouvée - fichier propre!")
    
    return {
        'existing_traits': len(existing_ids),
        'file_references': len(file_references),
        'valid_references': len(valid_refs),
        'orphaned_references': len(orphaned_refs),
        'orphaned_list': orphaned_refs,
        'cleaned': len(orphaned_refs) > 0 and not dry_run
    }

def auto_sync_ego_prompt(ego_file_path: Path, db_path: Path) -> bool:
    """
    Synchronisation automatique complète ego_prompt.txt <-> DB
    
    Returns:
        bool: True si des modifications ont été faites
    """
    
    print("🔄 SYNCHRONISATION AUTOMATIQUE EGO PROMPT")
    print("=" * 45)
    
    # 1. Nettoyer les références orphelines
    cleanup_stats = clean_orphaned_references(ego_file_path, db_path, dry_run=False)
    
    # 2. Vérifier s'il manque des traits ego récents
    existing_ids = get_existing_ego_traits(db_path)
    file_references = get_references_in_ego_file(ego_file_path)
    file_references_set = set(file_references)
    
    missing_refs = existing_ids - file_references_set
    
    if missing_refs:
        print(f"\n📥 TRAITS MANQUANTS DÉTECTÉS:")
        print(f"🔍 {len(missing_refs)} traits existent dans la DB mais pas dans ego_prompt.txt")
        for ref in missing_refs:
            print(f"   - {ref}")
        
        print(f"\n💡 Conseil: Relancez organize_ego_prompt_with_ids() pour les ajouter")
        return True
    
    else:
        print(f"\n✅ Fichier ego_prompt.txt parfaitement synchronisé!")
    
    return cleanup_stats['cleaned']

if __name__ == "__main__":
    # Test du système
    ego_file = Path("./data/ego_prompt.txt")
    db_file = Path("./data/memory/memories.db")
    
    if not ego_file.exists():
        print("❌ Fichier ego_prompt.txt introuvable")
        exit(1)
    
    if not db_file.exists():
        print("❌ Base de données introuvable")
        exit(1)
    
    # Lancer la synchronisation
    modifications_made = auto_sync_ego_prompt(ego_file, db_file)
    
    if modifications_made:
        print("\n🎯 Synchronisation terminée avec modifications")
    else:
        print("\n✨ Aucune modification nécessaire")
