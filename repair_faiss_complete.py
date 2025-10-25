#!/usr/bin/env python3
"""
🔧 RÉPARATION COMPLÈTE DES MAPPINGS FAISS
Corrige les incohérences entre l'index FAISS et les mappings SQLite
"""

import sys
sys.path.append('.')

import sqlite3
import faiss
import json
import numpy as np
from pathlib import Path

def repair_faiss_mappings():
    """Répare complètement les mappings FAISS/SQLite"""
    
    print("🔧 RÉPARATION COMPLÈTE MAPPINGS FAISS")
    print("=" * 50)
    
    # Chemins
    db_path = Path("data/memory/memories.db")
    index_path = Path("data/memory/faiss.index")
    
    if not db_path.exists():
        print("❌ Base de données non trouvée")
        return False
        
    if not index_path.exists():
        print("❌ Index FAISS non trouvé")
        return False
    
    # 1. Charger l'index FAISS
    print("\n1️⃣ Chargement index FAISS...")
    faiss_index = faiss.read_index(str(index_path))
    faiss_total = faiss_index.ntotal
    print(f"   ✅ {faiss_total} vecteurs chargés")
    
    # 2. Analyser SQLite
    print("\n2️⃣ Analyse base SQLite...")
    with sqlite3.connect(db_path) as conn:
        # Compter les souvenirs avec embeddings
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE embedding_json IS NOT NULL")
        db_with_embeddings = cursor.fetchone()[0]
        
        # Compter les souvenirs avec faiss_index
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NOT NULL")
        db_with_mappings = cursor.fetchone()[0]
        
        print(f"   📊 Souvenirs avec embeddings: {db_with_embeddings}")
        print(f"   📊 Souvenirs avec faiss_index: {db_with_mappings}")
        print(f"   📊 Index FAISS: {faiss_total} positions")
    
    # 3. Récupérer tous les souvenirs avec embeddings
    print("\n3️⃣ Récupération souvenirs avec embeddings...")
    memories_with_embeddings = []
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT id, embedding_json, title, score_impact 
            FROM memories 
            WHERE embedding_json IS NOT NULL 
            ORDER BY created_at ASC
        """)
        
        for row in cursor.fetchall():
            memory_id, embedding_json, title, impact = row
            try:
                embedding = np.array(json.loads(embedding_json), dtype=np.float32)
                memories_with_embeddings.append({
                    'id': memory_id,
                    'embedding': embedding,
                    'title': title,
                    'impact': impact
                })
            except Exception as e:
                print(f"   ⚠️ Erreur embedding {memory_id}: {e}")
    
    print(f"   ✅ {len(memories_with_embeddings)} souvenirs récupérés")
    
    # 4. Vérification cohérence
    if len(memories_with_embeddings) != faiss_total:
        print(f"\n⚠️ INCOHÉRENCE DÉTECTÉE:")
        print(f"   SQLite: {len(memories_with_embeddings)} embeddings")
        print(f"   FAISS: {faiss_total} vecteurs")
        
        if len(memories_with_embeddings) < faiss_total:
            print("   🔄 L'index FAISS sera reconstruit depuis SQLite")
            return rebuild_faiss_from_sqlite(memories_with_embeddings, db_path, index_path)
    
    # 5. Réparation des mappings SQLite
    print("\n5️⃣ Réparation mappings SQLite...")
    repaired_count = 0
    errors = 0
    
    with sqlite3.connect(db_path) as conn:
        for position, memory_data in enumerate(memories_with_embeddings):
            memory_id = memory_data['id']
            
            try:
                # Mettre à jour faiss_index dans SQLite
                conn.execute(
                    "UPDATE memories SET faiss_index = ? WHERE id = ?",
                    (position, memory_id)
                )
                repaired_count += 1
                
                # Log des souvenirs importants
                if "protocole" in memory_data['title'].lower():
                    print(f"   🎯 Protocole mappé: position {position} → {memory_id}")
                
            except Exception as e:
                print(f"   ❌ Erreur {memory_id}: {e}")
                errors += 1
        
        conn.commit()
    
    print(f"   ✅ {repaired_count} mappings réparés")
    if errors:
        print(f"   ⚠️ {errors} erreurs")
    
    # 6. Vérification finale
    print("\n6️⃣ Vérification finale...")
    
    # Vérifier le protocole spécifiquement
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT id, faiss_index, title 
            FROM memories 
            WHERE title LIKE '%Protocole%'
        """)
        
        protocole_results = cursor.fetchall()
        if protocole_results:
            for row in protocole_results:
                print(f"   🎯 {row[2]}: position {row[1]}")
    
    # Statistiques finales
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NULL")
        unmapped_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NOT NULL")
        mapped_count = cursor.fetchone()[0]
    
    print(f"\n📊 RÉSULTAT FINAL:")
    print(f"   ✅ Mappés: {mapped_count}")
    print(f"   ❌ Non-mappés: {unmapped_count}")
    print(f"   🎯 Index FAISS: {faiss_total} positions")
    
    success = (unmapped_count == 0) and (mapped_count == faiss_total)
    if success:
        print(f"\n🎉 RÉPARATION RÉUSSIE - TOUS LES MAPPINGS COHÉRENTS")
    else:
        print(f"\n⚠️ Incohérences restantes à analyser")
    
    return success

def rebuild_faiss_from_sqlite(memories_with_embeddings, db_path, index_path):
    """Reconstruit l'index FAISS depuis SQLite si nécessaire"""
    
    print("\n🔄 RECONSTRUCTION INDEX FAISS...")
    
    if not memories_with_embeddings:
        print("❌ Aucun embedding à reconstruire")
        return False
    
    # Créer nouvel index FAISS
    embedding_dim = len(memories_with_embeddings[0]['embedding'])
    new_index = faiss.IndexFlatIP(embedding_dim)
    
    # Ajouter tous les embeddings
    embeddings_matrix = np.array([mem['embedding'] for mem in memories_with_embeddings])
    new_index.add(embeddings_matrix)
    
    print(f"   ✅ Nouvel index: {new_index.ntotal} vecteurs")
    
    # Sauvegarder le nouvel index
    faiss.write_index(new_index, str(index_path))
    print(f"   💾 Index sauvegardé: {index_path}")
    
    # Mettre à jour les mappings SQLite
    with sqlite3.connect(db_path) as conn:
        for position, memory_data in enumerate(memories_with_embeddings):
            conn.execute(
                "UPDATE memories SET faiss_index = ? WHERE id = ?",
                (position, memory_data['id'])
            )
        conn.commit()
    
    print(f"   ✅ Mappings SQLite mis à jour")
    return True

if __name__ == "__main__":
    try:
        success = repair_faiss_mappings()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)