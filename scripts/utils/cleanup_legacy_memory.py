#!/usr/bin/env python3
"""
Nettoyage sécurisé architecture mémoire OGMA v2.0
Suppression des fichiers JSON legacy obsolètes
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_legacy_memory():
    """Suppression sécurisée des fichiers JSON legacy"""
    
    print("🧹 NETTOYAGE ARCHITECTURE MÉMOIRE OGMA v2.0")
    print("="*60)
    
    # Fichiers à supprimer (legacy JSON)
    legacy_files = [
        "data/memory/memories_sensibles_v10.json",
        "data/memory/memories_sensibles_v10.json.backup", 
        "data/memory/memories_sensibles_v10.json.archive_20250827_122506"
    ]
    
    # Fichiers à préserver (architecture actuelle)
    preserve_files = [
        "data/memory/memories.db",      # Base SQLite active
        "data/memory/faiss.index"       # Index vectoriel actif
    ]
    
    print("📋 VÉRIFICATION PRÉREQUIS:")
    
    # 1. Vérifier que SQLite est opérationnel
    sqlite_path = "data/memory/memories.db"
    if os.path.exists(sqlite_path):
        size_mb = os.path.getsize(sqlite_path) / (1024*1024)
        print(f"  ✅ SQLite opérationnel: {size_mb:.2f} MB")
        
        # Vérifier contenu SQLite
        try:
            import sqlite3
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"  ✅ Mémoires SQLite: {count}")
            
            if count < 50:
                print(f"  ⚠️  WARNING: Seulement {count} mémoires en SQLite")
                response = input("  Continuer malgré le petit nombre ? (y/N): ")
                if response.lower() != 'y':
                    print("  ❌ Nettoyage annulé par sécurité")
                    return False
        except Exception as e:
            print(f"  ❌ Erreur vérification SQLite: {e}")
            return False
    else:
        print("  ❌ SQLite introuvable - ARRÊT SÉCURISÉ")
        return False
    
    # 2. Vérifier FAISS
    faiss_path = "data/memory/faiss.index"  
    if os.path.exists(faiss_path):
        size_mb = os.path.getsize(faiss_path) / (1024*1024)
        print(f"  ✅ FAISS opérationnel: {size_mb:.2f} MB")
    else:
        print("  ⚠️  FAISS introuvable - mais pas critique")
    
    print("\n📁 FICHIERS À SUPPRIMER:")
    total_size = 0
    for file_path in legacy_files:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024*1024)
            total_size += size_mb
            print(f"  🗑️  {file_path}: {size_mb:.2f} MB")
        else:
            print(f"  ❓ {file_path}: Déjà absent")
    
    print(f"\n💾 ESPACE LIBÉRÉ: {total_size:.2f} MB")
    
    # Confirmation finale
    print(f"\n⚠️  CONFIRMATION REQUISE:")
    print(f"   Supprimer {len(legacy_files)} fichiers JSON legacy ?")
    print(f"   Architecture SQLite+FAISS sera préservée")
    print(f"   Espace libéré: {total_size:.2f} MB")
    
    confirm = input("\n🔴 Confirmer la suppression ? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Suppression annulée")
        return False
    
    # 3. SUPPRESSION EFFECTIVE
    print("\n🗑️  SUPPRESSION EN COURS:")
    deleted_count = 0
    deleted_size = 0
    
    for file_path in legacy_files:
        if os.path.exists(file_path):
            try:
                size_mb = os.path.getsize(file_path) / (1024*1024)
                os.remove(file_path)
                print(f"  ✅ Supprimé: {file_path} ({size_mb:.2f} MB)")
                deleted_count += 1
                deleted_size += size_mb
            except Exception as e:
                print(f"  ❌ Erreur suppression {file_path}: {e}")
        else:
            print(f"  ⏭️  Déjà absent: {file_path}")
    
    # 4. VÉRIFICATION POST-SUPPRESSION  
    print(f"\n📊 RÉSULTAT:")
    print(f"   Fichiers supprimés: {deleted_count}")
    print(f"   Espace libéré: {deleted_size:.2f} MB")
    
    # Vérifier que SQLite fonctionne toujours
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"   SQLite toujours opérationnel: {count} mémoires")
    except Exception as e:
        print(f"   ⚠️  Erreur vérification finale SQLite: {e}")
    
    print(f"\n🎯 ARCHITECTURE OPTIMISÉE:")
    print(f"   ✅ SQLite: {sqlite_path}")
    print(f"   ✅ FAISS: {faiss_path}")
    print(f"   🗑️  JSON legacy: Supprimés")
    
    return True

if __name__ == "__main__":
    success = cleanup_legacy_memory()
    if success:
        print(f"\n🏆 NETTOYAGE TERMINÉ AVEC SUCCÈS")
        print(f"    Architecture mémoire OGMA optimisée")
    else:
        print(f"\n❌ NETTOYAGE ANNULÉ")
        print(f"    Fichiers legacy préservés par sécurité")