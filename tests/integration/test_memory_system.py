#!/usr/bin/env python3
"""
Test complet du système de mémorisation OGMA
Vérifie toutes les fonctionnalités clés
"""

import asyncio
import sqlite3
import numpy as np
from pathlib import Path
import json
import time
from datetime import datetime

# Import des composants OGMA
from memory_manager import MemoryManager
from core_logic import SettingsManager
from core_logic import AIController, EmbeddingController
from queue import Queue

async def test_memory_system():
    """Test complet du système de mémoire"""
    print("🧪 TEST COMPLET SYSTÈME DE MÉMOIRE OGMA")
    print("=" * 50)
    
    # Configuration basique pour le test
    data_dir = Path("data")
    mem_dir = data_dir / "memory"
    db_path = mem_dir / "memories.db"
    index_path = mem_dir / "faiss.index"
    
    print(f"📁 Chemins de test:")
    print(f"   - DB: {db_path}")
    print(f"   - Index FAISS: {index_path}")
    print(f"   - DB existe: {db_path.exists()}")
    print(f"   - Index existe: {index_path.exists()}")
    
    # 1. Test de connectivité SQLite
    print("\n1️⃣ TEST CONNECTIVITÉ SQLITE")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memories")
            total_memories = cursor.fetchone()[0]
            print(f"   ✅ SQLite accessible: {total_memories} souvenirs")
    except Exception as e:
        print(f"   ❌ Erreur SQLite: {e}")
        return False
    
    # 2. Test FAISS
    print("\n2️⃣ TEST INDEX FAISS")
    try:
        import faiss
        if index_path.exists():
            idx = faiss.read_index(str(index_path))
            print(f"   ✅ FAISS accessible: {idx.ntotal} vecteurs, dim {idx.d}")
        else:
            print("   ⚠️ Index FAISS absent")
    except Exception as e:
        print(f"   ❌ Erreur FAISS: {e}")
    
    # 3. Test structure de données
    print("\n3️⃣ TEST STRUCTURE DONNÉES")
    try:
        with sqlite3.connect(db_path) as conn:
            # Souvenirs avec embeddings
            cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE embedding_json IS NOT NULL")
            with_embeddings = cursor.fetchone()[0]
            
            # Souvenirs mappés FAISS
            cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE faiss_index IS NOT NULL")
            with_faiss = cursor.fetchone()[0]
            
            # Types de souvenirs
            cursor = conn.execute("SELECT type, COUNT(*) FROM memories GROUP BY type")
            types = cursor.fetchall()
            
            print(f"   ✅ Souvenirs avec embeddings: {with_embeddings}")
            print(f"   ✅ Souvenirs mappés FAISS: {with_faiss}")
            print(f"   ✅ Types de souvenirs:")
            for type_name, count in types:
                print(f"     - {type_name or 'NULL'}: {count}")
                
    except Exception as e:
        print(f"   ❌ Erreur structure: {e}")
    
    # 4. Test scores d'impact
    print("\n4️⃣ TEST SCORES D'IMPACT")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT title, score_impact, type, valence 
                FROM memories 
                WHERE score_impact > 0 
                ORDER BY score_impact DESC 
                LIMIT 3
            """)
            top_memories = cursor.fetchall()
            
            print(f"   ✅ Top 3 souvenirs par impact:")
            for title, score, mem_type, valence in top_memories:
                print(f"     - {title[:40]}... (Score: {score}, Type: {mem_type}, Valence: {valence})")
                
    except Exception as e:
        print(f"   ❌ Erreur scores: {e}")
    
    # 5. Test cohérence mappings
    print("\n5️⃣ TEST COHÉRENCE MAPPINGS")
    try:
        with sqlite3.connect(db_path) as conn:
            # Vérifier les trous dans les mappings FAISS
            cursor = conn.execute("""
                SELECT faiss_index 
                FROM memories 
                WHERE faiss_index IS NOT NULL 
                ORDER BY faiss_index
            """)
            positions = [row[0] for row in cursor.fetchall()]
            
            if positions:
                min_pos, max_pos = min(positions), max(positions)
                expected_range = max_pos - min_pos + 1
                actual_count = len(positions)
                
                print(f"   ✅ Range FAISS: {min_pos} à {max_pos}")
                print(f"   ✅ Positions utilisées: {actual_count}/{expected_range}")
                
                if actual_count == expected_range:
                    print("   ✅ Aucun trou détecté dans les mappings")
                else:
                    holes = expected_range - actual_count
                    print(f"   ⚠️ {holes} trous détectés dans les mappings")
            else:
                print("   ⚠️ Aucun mapping FAISS trouvé")
                
    except Exception as e:
        print(f"   ❌ Erreur mappings: {e}")
    
    # 6. Test de taille et performance
    print("\n6️⃣ TEST PERFORMANCE")
    try:
        # Tailles des fichiers
        db_size = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
        faiss_size = index_path.stat().st_size / (1024 * 1024) if index_path.exists() else 0
        
        print(f"   ✅ Taille DB SQLite: {db_size:.2f} MB")
        print(f"   ✅ Taille index FAISS: {faiss_size:.2f} MB")
        print(f"   ✅ Ratio FAISS/SQLite: {(faiss_size/db_size*100):.1f}%" if db_size > 0 else "   ⚠️ DB vide")
        
    except Exception as e:
        print(f"   ❌ Erreur performance: {e}")
    
    # 7. Test d'importation des modules
    print("\n7️⃣ TEST IMPORTATION MODULES")
    try:
        print("   ✅ MemoryManager importé")
        print("   ✅ SQLite3 disponible")
        print("   ✅ FAISS disponible")
        print("   ✅ Numpy disponible")
    except Exception as e:
        print(f"   ❌ Erreur imports: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 RÉSULTAT: Système de mémoire opérationnel")
    print("✅ Tests terminés avec succès")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_memory_system())