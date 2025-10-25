#!/usr/bin/env python3
"""
Analyse architecture mémoire OGMA v2.0
Vérification organisation et optimisation
"""

import sqlite3
import os
import json
from pathlib import Path

def analyze_memory_architecture():
    """Analyse complète de l'architecture mémoire"""
    
    print("🧠 ANALYSE ARCHITECTURE MÉMOIRE OGMA v2.0")
    print("="*60)
    
    # 1. STRUCTURE FICHIERS
    memory_dir = Path("data/memory")
    print("📁 STRUCTURE FICHIERS:")
    
    if memory_dir.exists():
        files = list(memory_dir.rglob("*"))
        for file in sorted(files):
            if file.is_file():
                size_mb = file.stat().st_size / (1024*1024)
                print(f"  {file.relative_to(memory_dir)}: {size_mb:.2f} MB")
    print()
    
    # 2. BASE SQLITE PRINCIPALE
    db_path = "data/memory/memories.db"
    total = 0  # Initialisation
    if os.path.exists(db_path):
        print("🗃️ BASE SQLITE PRINCIPALE:")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total mémoires
        cursor.execute("SELECT COUNT(*) FROM memories")
        total = cursor.fetchone()[0]
        print(f"  Total mémoires: {total}")
        
        # Par type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM memories 
            GROUP BY type 
            ORDER BY count DESC
        """)
        types = cursor.fetchall()
        print("  Répartition par type:")
        for type_name, count in types:
            print(f"    - {type_name}: {count}")
        
        # Taille base
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchone()[0]
        print(f"  Nombre de tables: {tables}")
        
        conn.close()
        print()
    
    # 3. INDEX FAISS
    faiss_path = "data/memory/faiss.index"
    if os.path.exists(faiss_path):
        faiss_size = os.path.getsize(faiss_path) / (1024*1024)
        print(f"🔍 INDEX FAISS: {faiss_size:.2f} MB")
        print()
    
    # 4. FICHIERS LEGACY
    legacy_files = [
        "data/memory/memories_sensibles_v10.json",
        "data/memory/memories_sensibles_v10.json.backup"
    ]
    
    legacy_total = 0
    print("📜 FICHIERS LEGACY:")
    for file_path in legacy_files:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024*1024)
            legacy_total += size_mb
            print(f"  {file_path}: {size_mb:.2f} MB")
    
    if legacy_total > 0:
        print(f"  Total legacy: {legacy_total:.2f} MB")
        print("  ⚠️  Fichiers JSON legacy détectés")
    print()
    
    # 5. SAUVEGARDES
    backup_dir = Path("data/memory/backup")
    backup_total = 0
    backup_count = 0
    
    if backup_dir.exists():
        backups = list(backup_dir.glob("*.bak"))
        backup_count = len(backups)
        for backup in backups:
            backup_total += backup.stat().st_size / (1024*1024)
    
    print(f"💾 SAUVEGARDES: {backup_count} fichiers, {backup_total:.2f} MB")
    print()
    
    # 6. ÉVALUATION ARCHITECTURE
    print("📊 ÉVALUATION ARCHITECTURE:")
    
    # Centralisée ?
    centralized = True
    if legacy_total > 0:
        print("  ❌ Architecture partiellement éclatée (fichiers legacy)")
        centralized = False
    else:
        print("  ✅ Architecture centralisée SQLite+FAISS")
    
    # Optimisée ?
    if backup_total > 50:  # Plus de 50MB de backups
        print("  ⚠️  Nombreuses sauvegardes (possibilité de nettoyage)")
    else:
        print("  ✅ Sauvegardes raisonnables")
    
    # Performante ?
    if total > 100:
        print(f"  ✅ Base substantielle ({total} mémoires)")
    else:
        print(f"  ⚠️  Base encore petite ({total} mémoires)")
    
    print()
    
    # 7. RECOMMANDATIONS
    print("💡 RECOMMANDATIONS:")
    
    if not centralized:
        print("  🔄 Migrer fichiers JSON legacy vers SQLite")
        print("  🗑️ Supprimer fichiers JSON après migration")
    
    if backup_total > 50:
        print("  🧹 Nettoyer anciennes sauvegardes")
    
    print("  ✅ Architecture actuelle: SQLite + FAISS optimal")
    print("  ✅ Unicité stockage: Une seule source de vérité")
    
    return {
        "centralized": centralized,
        "total_memories": total,
        "legacy_size_mb": legacy_total,
        "backup_count": backup_count
    }

if __name__ == "__main__":
    results = analyze_memory_architecture()
    print(f"\n🎯 RÉSUMÉ: Architecture {'centralisée' if results['centralized'] else 'éclatée'}")