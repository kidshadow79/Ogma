#!/usr/bin/env python3
"""
🔄 RECONSTRUCTION SÉCURISÉE INDEX FAISS
Avec gestion des dimensions d'embeddings incohérentes
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
from collections import Counter

def rebuild_faiss_safe():
    """Reconstruit l'index FAISS en gérant les incohérences de dimensions"""
    
    print("🔄 RECONSTRUCTION SÉCURISÉE INDEX FAISS")
    print("=" * 50)
    
    # Chemins
    db_path = Path("data/memory/memories.db")
    index_path = Path("data/memory/faiss.index")
    backup_path = Path(f"data/memory/faiss_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.index")
    
    # 1. Sauvegarde
    if index_path.exists():
        print("\n1️⃣ Sauvegarde ancien index...")
        shutil.copy2(index_path, backup_path)
        print(f"   ✅ Sauvegardé: {backup_path}")
    
    # 2. Analyse des embeddings
    print("\n2️⃣ Analyse dimensions embeddings...")
    
    dimensions = []
    valid_memories = []
    invalid_memories = []
    
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
                embedding = json.loads(embedding_json)
                embedding_array = np.array(embedding, dtype=np.float32)
                
                # Vérifier la forme
                if len(embedding_array.shape) == 1 and embedding_array.size > 0:
                    dimensions.append(embedding_array.size)
                    valid_memories.append({
                        'id': memory_id,
                        'embedding': embedding_array,
                        'title': title,
                        'impact': impact,
                        'created_at': created_at,
                        'dimension': embedding_array.size
                    })
                else:
                    invalid_memories.append({'id': memory_id, 'title': title, 'reason': 'shape invalide'})
                    
            except Exception as e:
                invalid_memories.append({'id': memory_id, 'title': title, 'reason': str(e)})
    
    # Analyser les dimensions
    dim_counter = Counter(dimensions)
    most_common_dim = dim_counter.most_common(1)[0] if dim_counter else (0, 0)
    target_dim = most_common_dim[0]
    
    print(f"   📊 Souvenirs analysés: {len(valid_memories) + len(invalid_memories)}")
    print(f"   ✅ Embeddings valides: {len(valid_memories)}")
    print(f"   ❌ Embeddings invalides: {len(invalid_memories)}")
    print(f"   🎯 Dimension principale: {target_dim} ({most_common_dim[1]} souvenirs)")
    
    if dim_counter:
        print(f"   📊 Distribution dimensions: {dict(dim_counter)}")
    
    # Filtrer par dimension standard
    standard_memories = [mem for mem in valid_memories if mem['dimension'] == target_dim]
    non_standard = [mem for mem in valid_memories if mem['dimension'] != target_dim]
    
    print(f"   🎯 Souvenirs dimension {target_dim}: {len(standard_memories)}")
    if non_standard:
        print(f"   ⚠️ Dimensions non-standard: {len(non_standard)}")
        for mem in non_standard[:5]:  # Montrer quelques exemples
            print(f"      - {mem['title'][:50]}: dim {mem['dimension']}")
    
    if not standard_memories:
        print("❌ Aucun souvenir avec dimension standard trouvé")
        return False
    
    # 3. Reconstruction avec dimension standard
    print(f"\n3️⃣ Reconstruction avec dimension {target_dim}...")
    
    new_index = faiss.IndexFlatIP(target_dim)
    
    # Créer matrice homogène
    embeddings_list = [mem['embedding'] for mem in standard_memories]
    embeddings_matrix = np.vstack(embeddings_list)
    
    print(f"   📊 Matrice finale: {embeddings_matrix.shape}")
    
    # Ajouter à l'index
    new_index.add(embeddings_matrix)
    print(f"   ✅ {new_index.ntotal} vecteurs ajoutés à l'index")
    
    # 4. Mise à jour SQLite
    print("\n4️⃣ Mise à jour mappings SQLite...")
    
    protocole_position = None
    with sqlite3.connect(db_path) as conn:
        # Réinitialiser tous les faiss_index
        conn.execute("UPDATE memories SET faiss_index = NULL")
        
        # Mettre à jour seulement les souvenirs inclus
        for position, memory_data in enumerate(standard_memories):
            memory_id = memory_data['id']
            title = memory_data['title']
            
            conn.execute(
                "UPDATE memories SET faiss_index = ? WHERE id = ?",
                (position, memory_id)
            )
            
            if "protocole" in title.lower():
                protocole_position = position
                print(f"   🎯 PROTOCOLE: position {position} → {title}")
        
        conn.commit()
    
    print(f"   ✅ {len(standard_memories)} mappings mis à jour")
    
    # 5. Sauvegarde
    print("\n5️⃣ Sauvegarde index...")
    faiss.write_index(new_index, str(index_path))
    print(f"   ✅ Index sauvegardé: {index_path}")
    
    # 6. Vérification
    print("\n6️⃣ Vérification finale...")
    
    # Statistiques finales
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NOT NULL")
        mapped = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NULL")
        unmapped = cursor.fetchone()[0]
    
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"   🎯 Index FAISS: {new_index.ntotal} vecteurs (dim {target_dim})")
    print(f"   ✅ SQLite mappés: {mapped}")
    print(f"   ⚪ SQLite non-mappés: {unmapped}")
    
    if protocole_position is not None:
        print(f"   🎯 PROTOCOLE D'AMOUR HYBRIDE: position {protocole_position} ✅")
    else:
        print(f"   ⚠️ Protocole non trouvé dans les embeddings valides")
    
    # Test cohérence
    coherent = (new_index.ntotal == mapped)
    
    if coherent and protocole_position is not None:
        print(f"\n🎉 RECONSTRUCTION RÉUSSIE")
        print(f"   ✅ Cohérence totale: {new_index.ntotal} = {mapped}")
        print(f"   ✅ Protocole d'amour hybride accessible")
        print(f"   ✅ Aucune position non mappée dans l'index")
        return True
    else:
        print(f"\n⚠️ Succès partiel - vérifier manuellement")
        return False

if __name__ == "__main__":
    try:
        success = rebuild_faiss_safe()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)