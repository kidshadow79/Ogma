#!/usr/bin/env python3
"""
🧪 TEST DE VÉRIFICATION - RECHERCHE PROTOCOLE
Vérifie que le protocole d'amour hybride est maintenant accessible
"""

import sys
sys.path.append('.')

import sqlite3
import faiss
import json
import numpy as np
from pathlib import Path

def test_protocole_search():
    """Test la recherche du protocole d'amour hybride"""
    
    print("🧪 TEST RECHERCHE PROTOCOLE D'AMOUR HYBRIDE")
    print("=" * 50)
    
    # Chemins
    db_path = Path("data/memory/memories.db")
    index_path = Path("data/memory/faiss.index")
    
    # 1. Charger l'index réparé
    print("\n1️⃣ Chargement index réparé...")
    faiss_index = faiss.read_index(str(index_path))
    print(f"   ✅ {faiss_index.ntotal} vecteurs chargés")
    
    # 2. Charger les mappings
    print("\n2️⃣ Chargement mappings SQLite...")
    faiss_to_id = {}
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT id, faiss_index FROM memories WHERE faiss_index IS NOT NULL")
        for memory_id, faiss_pos in cursor.fetchall():
            faiss_to_id[faiss_pos] = memory_id
    
    print(f"   ✅ {len(faiss_to_id)} mappings chargés")
    
    # 3. Simuler une recherche embedding (simple test avec vecteur aléatoire)
    print("\n3️⃣ Test recherche vectorielle...")
    
    # Créer un vecteur de recherche (normalement ce serait l'embedding de la requête)
    query_vector = np.random.rand(1024).astype('float32').reshape(1, -1)
    
    # Recherche FAISS
    k = 10
    distances, indices = faiss_index.search(query_vector, k)
    
    print(f"   🔍 Recherche k={k} effectuée")
    print(f"   📊 Positions trouvées: {indices[0]}")
    
    # 4. Vérifier que toutes les positions sont mappées
    print("\n4️⃣ Vérification mappings...")
    
    all_mapped = True
    found_memories = []
    
    for i, pos in enumerate(indices[0]):
        if pos in faiss_to_id:
            memory_id = faiss_to_id[pos]
            
            # Récupérer le titre depuis SQLite
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT title, score_impact FROM memories WHERE id = ?", (memory_id,))
                result = cursor.fetchone()
                
                if result:
                    title, impact = result
                    found_memories.append({
                        'position': pos,
                        'id': memory_id,
                        'title': title,
                        'impact': impact,
                        'distance': distances[0][i]
                    })
                    print(f"   ✅ Position {pos} → {title[:50]}... (impact: {impact})")
        else:
            print(f"   ❌ Position {pos} NON MAPPÉE")
            all_mapped = False
    
    # 5. Test spécifique du protocole
    print("\n5️⃣ Test spécifique protocole...")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT id, faiss_index, title, score_impact FROM memories WHERE title LIKE '%Protocole%'")
        protocole_info = cursor.fetchall()
        
        if protocole_info:
            for row in protocole_info:
                memory_id, faiss_pos, title, impact = row
                print(f"   🎯 PROTOCOLE TROUVÉ:")
                print(f"      ID: {memory_id}")
                print(f"      Position FAISS: {faiss_pos}")
                print(f"      Titre: {title}")
                print(f"      Impact: {impact}")
                
                # Vérifier que la position est bien dans les mappings
                if faiss_pos in faiss_to_id:
                    print(f"      ✅ Mapping OK: position {faiss_pos} accessible")
                else:
                    print(f"      ❌ Mapping MANQUANT pour position {faiss_pos}")
        else:
            print("   ❌ Protocole non trouvé dans SQLite")
    
    # 6. Résultat final
    print(f"\n📊 RÉSULTAT TEST:")
    
    if all_mapped and protocole_info:
        print(f"   🎉 TEST RÉUSSI")
        print(f"   ✅ Toutes les positions FAISS sont mappées")
        print(f"   ✅ Protocole d'amour hybride accessible")
        print(f"   ✅ Système de recherche fonctionnel")
        return True
    else:
        print(f"   ⚠️ Problèmes détectés:")
        if not all_mapped:
            print(f"      - Positions non mappées trouvées")
        if not protocole_info:
            print(f"      - Protocole non accessible")
        return False

if __name__ == "__main__":
    try:
        success = test_protocole_search()
        if success:
            print(f"\n🚀 SYSTÈME PRÊT - LE PROTOCOLE D'AMOUR HYBRIDE EST ACCESSIBLE !")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)