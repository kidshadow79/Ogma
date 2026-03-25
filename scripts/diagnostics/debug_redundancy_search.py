#!/usr/bin/env python3
"""Diagnostic de recherche redondance sur les ego traits"""

import sqlite3
import numpy as np
import faiss

print("=" * 80)
print("🔍 DIAGNOSTIC RECHERCHE REDONDANCE")
print("=" * 80)

# IDs à tester
source_id = 'EGO_20250916_143535_546'
target_id = 'EGO_20250916_135734_138'

# Connexion DB
conn = sqlite3.connect('data/memory/memories.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Récupérer les mémoires
c.execute('SELECT * FROM memories WHERE id IN (?, ?)', (source_id, target_id))
memories = {row['id']: dict(row) for row in c.fetchall()}

source = memories.get(source_id)
target = memories.get(target_id)

if not source or not target:
    print("❌ Mémoires non trouvées!")
    exit(1)

print(f"\n📌 MÉMOIRE SOURCE: {source_id}")
print(f"Titre: {source.get('title', 'N/A')}")
print(f"Texte: {source.get('text_original', 'N/A')}")

print(f"\n📌 MÉMOIRE CIBLE: {target_id}")
print(f"Titre: {target.get('title', 'N/A')}")
print(f"Texte: {target.get('text_original', 'N/A')}")

# Charger l'index FAISS
try:
    index = faiss.read_index('data/memory/faiss_index.bin')
    print(f"\n✅ Index FAISS chargé: {index.ntotal} vecteurs")
except Exception as e:
    print(f"❌ Erreur chargement FAISS: {e}")
    exit(1)

# Récupérer tous les IDs et vecteurs
c.execute('SELECT id, faiss_index FROM memories WHERE faiss_index IS NOT NULL ORDER BY faiss_index')
id_map = {row['faiss_index']: row['id'] for row in c.fetchall()}

# Trouver la position du vecteur source
source_pos = source.get('faiss_index')
target_pos = target.get('faiss_index')

if source_pos is None or target_pos is None:
    print(f"❌ Positions FAISS manquantes!")
    print(f"   Source pos: {source_pos}")
    print(f"   Target pos: {target_pos}")
    exit(1)

print(f"\n📍 Position FAISS source: {source_pos}")
print(f"📍 Position FAISS target: {target_pos}")

# Récupérer le vecteur source depuis l'index
source_vector = index.reconstruct(int(source_pos))
source_vector = source_vector.reshape(1, -1)

# Faire une recherche K-NN
k = 20
distances, indices = index.search(source_vector, k)

print(f"\n📊 TOP {k} RÉSULTATS FAISS (distance L2):")
print("-" * 80)

found_target = False
for i, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
    mem_id = id_map.get(int(idx), 'UNKNOWN')
    is_source = (idx == source_pos)
    is_target = (idx == target_pos)
    
    # Convertir distance L2 en similarité cosinus approximative
    # Pour vecteurs normalisés: distance_L2 = 2 * (1 - cosine_similarity)
    # cosine_sim ≈ 1 - (distance_L2 / 2)
    similarity = max(0, 1 - (dist / 2))
    
    marker = ""
    if is_source:
        marker = "⭐ SOURCE"
    elif is_target:
        marker = "🎯 CIBLE"
        found_target = True
    
    print(f"{i:2d}. {marker}")
    print(f"    ID: {mem_id}")
    print(f"    FAISS index: {idx}")
    print(f"    Distance L2: {dist:.4f}")
    print(f"    Similarité ~: {similarity:.1%} ({similarity:.4f})")

print("\n" + "=" * 80)
if found_target:
    print(f"✅ CIBLE TROUVÉE dans les top {k} résultats FAISS purs")
else:
    print(f"❌ CIBLE NON TROUVÉE dans les top {k} résultats FAISS purs")
    print(f"⚠️  Les embeddings de ces deux textes ne sont PAS considérés comme similaires par FAISS!")

print("=" * 80)

conn.close()
