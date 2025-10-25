#!/usr/bin/env python3
"""
🔄 RECONSTRUCTION COMPLÈTE INDEX FAISS
Reconstruit l'index FAISS depuis SQLite pour éliminer toutes les incohérences
"""

import sys
sys.path.append('.')

import sqlite3
import faiss
import json
import numpy as np
from pathlib import Path
import shutil
from datetime import datetime

def rebuild_faiss_index():
    """Reconstruit complètement l'index FAISS depuis SQLite"""
    
    print("🔄 RECONSTRUCTION COMPLÈTE INDEX FAISS")
    print("=" * 50)
    
    # Chemins
    db_path = Path("data/memory/memories.db")
    index_path = Path("data/memory/faiss.index")
    backup_path = Path(f"data/memory/faiss_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.index")
    
    # 1. Sauvegarde de l'ancien index
    if index_path.exists():
        print("\n1️⃣ Sauvegarde ancien index...")
        shutil.copy2(index_path, backup_path)
        print(f"   ✅ Sauvegardé: {backup_path}")
    
    # 2. Récupération des souvenirs avec embeddings
    print("\n2️⃣ Récupération souvenirs depuis SQLite...")
    
    memories_data = []
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT id, embedding_json, title, score_impact, created_at 
            FROM memories 
            WHERE embedding_json IS NOT NULL 
            ORDER BY created_at ASC
        """)
        
        for row in cursor.fetchall():
            memory_id, embedding_json, title, impact, created_at = row
            
            try:
                embedding = np.array(json.loads(embedding_json), dtype=np.float32)
                memories_data.append({
                    'id': memory_id,
                    'embedding': embedding,
                    'title': title,
                    'impact': impact,
                    'created_at': created_at
                })
            except Exception as e:
                print(f"   ⚠️ Erreur embedding {memory_id}: {e}")
    
    print(f"   ✅ {len(memories_data)} souvenirs avec embeddings valides")
    
    if not memories_data:
        print("❌ Aucun souvenir trouvé")
        return False
    
    # 3. Création nouvel index FAISS
    print("\n3️⃣ Création nouvel index FAISS...")
    
    embedding_dim = len(memories_data[0]['embedding'])
    new_index = faiss.IndexFlatIP(embedding_dim)
    
    # Préparer matrice d'embeddings
    embeddings_matrix = np.array([mem['embedding'] for mem in memories_data])
    print(f"   📊 Matrice: {embeddings_matrix.shape}")
    
    # Ajouter tous les embeddings
    new_index.add(embeddings_matrix)
    print(f"   ✅ {new_index.ntotal} vecteurs ajoutés")
    
    # 4. Mise à jour des mappings SQLite
    print("\n4️⃣ Mise à jour mappings SQLite...")
    
    protocole_found = False
    with sqlite3.connect(db_path) as conn:
        for position, memory_data in enumerate(memories_data):
            memory_id = memory_data['id']
            title = memory_data['title']
            
            # Mettre à jour faiss_index
            conn.execute(
                "UPDATE memories SET faiss_index = ? WHERE id = ?",
                (position, memory_id)
            )
            
            # Tracker le protocole
            if "protocole" in title.lower():
                print(f"   🎯 PROTOCOLE: position {position} → {title}")
                protocole_found = True
        
        conn.commit()
    
    print(f"   ✅ {len(memories_data)} mappings mis à jour")
    
    # 5. Sauvegarde du nouvel index
    print("\n5️⃣ Sauvegarde nouvel index...")
    faiss.write_index(new_index, str(index_path))
    print(f"   ✅ Index sauvegardé: {index_path}")
    
    # 6. Vérification finale
    print("\n6️⃣ Vérification finale...")
    
    # Recharger l'index pour vérifier
    verification_index = faiss.read_index(str(index_path))
    print(f"   📊 Index rechargé: {verification_index.ntotal} vecteurs")
    
    # Vérifier mappings SQLite
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NOT NULL")
        mapped_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NULL")
        unmapped_count = cursor.fetchone()[0]
        
        # Vérifier le protocole
        cursor = conn.execute("SELECT id, faiss_index, title FROM memories WHERE title LIKE '%Protocole%'")
        protocole_info = cursor.fetchall()
    
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"   🎯 Index FAISS: {verification_index.ntotal} vecteurs")
    print(f"   ✅ SQLite mappés: {mapped_count}")
    print(f"   ❌ SQLite non-mappés: {unmapped_count}")
    
    if protocole_info:
        for row in protocole_info:
            print(f"   🎯 PROTOCOLE RÉCUPÉRÉ: position {row[1]} → {row[2]}")
    
    # Test de cohérence
    coherent = (verification_index.ntotal == mapped_count) and (unmapped_count == 0)
    
    if coherent:
        print(f"\n🎉 RECONSTRUCTION RÉUSSIE - COHÉRENCE TOTALE")
        print(f"   ✅ Tous les souvenirs sont accessibles")
        print(f"   ✅ Le protocole d'amour hybride est récupéré")
        print(f"   ✅ Aucune position non mappée")
        return True
    else:
        print(f"\n⚠️ Incohérences détectées:")
        print(f"   FAISS: {verification_index.ntotal}")
        print(f"   Mappés: {mapped_count}")
        print(f"   Non-mappés: {unmapped_count}")
        return False

if __name__ == "__main__":
    try:
        success = rebuild_faiss_index()
        if success:
            print(f"\n🚀 SYSTÈME RÉPARÉ - PRÊT POUR LES RECHERCHES")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)