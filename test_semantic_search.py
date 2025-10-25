#!/usr/bin/env python3
"""
Test de recherche sémantique dans le système de mémoire OGMA
"""

import asyncio
import sqlite3
import faiss
import numpy as np
from pathlib import Path

async def test_semantic_search():
    """Test de recherche sémantique"""
    print("🔍 TEST RECHERCHE SÉMANTIQUE MÉMOIRE")
    print("=" * 40)
    
    # Charger l'index FAISS
    index_path = Path("data/memory/faiss.index")
    db_path = Path("data/memory/memories.db")
    
    if not index_path.exists() or not db_path.exists():
        print("❌ Fichiers de mémoire non trouvés")
        return
    
    try:
        # Charger FAISS
        faiss_index = faiss.read_index(str(index_path))
        print(f"✅ Index FAISS chargé: {faiss_index.ntotal} vecteurs")
        
        # Charger mappings depuis SQLite
        mappings = {}
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT faiss_index, id, title, score_impact, type
                FROM memories 
                WHERE faiss_index IS NOT NULL
                ORDER BY score_impact DESC
            """)
            
            for faiss_pos, mem_id, title, score, mem_type in cursor.fetchall():
                mappings[faiss_pos] = {
                    'id': mem_id,
                    'title': title,
                    'score': score,
                    'type': mem_type
                }
        
        print(f"✅ Mappings chargés: {len(mappings)} souvenirs")
        
        # Test avec un vecteur aléatoire (simulation d'une requête)
        # En production, ce serait l'embedding d'une vraie requête
        print(f"\n🎯 Test recherche avec vecteur simulé...")
        
        # Générer un vecteur de test normalisé
        test_vector = np.random.normal(0, 1, (1, 1024)).astype(np.float32)
        test_vector = test_vector / np.linalg.norm(test_vector)
        
        # Recherche des 5 plus proches
        distances, indices = faiss_index.search(test_vector, 5)
        
        print(f"📊 Résultats de recherche:")
        for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            if idx in mappings:
                mem = mappings[idx]
                similarity = 1.0 / (1.0 + dist)
                print(f"  {i+1}. {mem['title'][:50]}...")
                print(f"     Score impact: {mem['score']:.2f}, Similarité: {similarity:.3f}")
                print(f"     Type: {mem['type']}, ID: {mem['id'][:8]}...")
                print()
            else:
                print(f"  {i+1}. Position {idx} non mappée (distance: {dist:.3f})")
        
        # Statistiques de performance
        print(f"📈 STATISTIQUES:")
        print(f"   - Vecteurs indexés: {faiss_index.ntotal}")
        print(f"   - Dimension: {faiss_index.d}")
        print(f"   - Mappings valides: {len(mappings)}")
        print(f"   - Cohérence index: {(len(mappings)/faiss_index.ntotal*100):.1f}%")
        
        # Test de types de souvenirs
        type_counts = {}
        for mem in mappings.values():
            mem_type = mem['type'] or 'None'
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        print(f"\n📊 DISTRIBUTION PAR TYPE:")
        for mem_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(mappings)) * 100
            print(f"   - {mem_type}: {count} souvenirs ({percentage:.1f}%)")
        
        # Test de scores d'impact
        scores = [mem['score'] for mem in mappings.values() if mem['score']]
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"\n💫 DISTRIBUTION SCORES D'IMPACT:")
            print(f"   - Score moyen: {avg_score:.2f}")
            print(f"   - Score maximum: {max_score:.2f}")
            print(f"   - Score minimum: {min_score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test recherche: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_semantic_search())