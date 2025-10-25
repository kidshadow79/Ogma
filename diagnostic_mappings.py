#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/memory/memories.db')

print('=== DIAGNOSTIC COMPLET MAPPINGS ===')
print()

# 1. Compter les souvenirs totaux
cursor = conn.execute('SELECT COUNT(*) FROM memories')
total_memories = cursor.fetchone()[0]
print(f'Total souvenirs en base: {total_memories}')

# 2. Compter ceux avec faiss_index
cursor = conn.execute('SELECT COUNT(*) FROM memories WHERE faiss_index IS NOT NULL')
mapped_memories = cursor.fetchone()[0]
print(f'Souvenirs avec faiss_index: {mapped_memories}')

# 3. Trouver les trous dans la séquence
cursor = conn.execute('SELECT faiss_index FROM memories WHERE faiss_index IS NOT NULL ORDER BY faiss_index')
positions = [row[0] for row in cursor.fetchall()]
print(f'Positions FAISS utilisées: {len(positions)}')

if positions:
    print(f'Range: {min(positions)} à {max(positions)}')
    
    # Chercher les trous
    missing = []
    for i in range(max(positions) + 1):
        if i not in positions:
            missing.append(i)
    
    if missing:
        print(f'Positions manquantes dans SQLite: {missing[:10]} ({len(missing)} total)')
    else:
        print('Aucun trou détecté dans SQLite')

# 4. Vérifier le protocole spécifiquement
cursor = conn.execute("SELECT id, faiss_index, title FROM memories WHERE title LIKE '%Protocole%'")
protocole = cursor.fetchall()
if protocole:
    for row in protocole:
        print(f'PROTOCOLE: ID={row[0]}, faiss_index={row[1]}, titre={row[2]}')
else:
    print('Protocole non trouvé par titre')

# 5. Souvenirs sans faiss_index
cursor = conn.execute('SELECT COUNT(*) FROM memories WHERE faiss_index IS NULL')
unmapped = cursor.fetchone()[0]
print(f'Souvenirs SANS faiss_index: {unmapped}')

conn.close()