import sqlite3

conn = sqlite3.connect('data/memory/memories.db')
cursor = conn.cursor()

# Compter souvenirs ego_trait
cursor.execute("SELECT COUNT(*) FROM memories WHERE type='ego_trait'")
count = cursor.fetchone()[0]
print(f"Total souvenirs ego_trait: {count}")

if count > 0:
    cursor.execute("SELECT MIN(id), MAX(id) FROM memories WHERE type='ego_trait'")
    min_id, max_id = cursor.fetchone()
    print(f"ID min: {min_id}")
    print(f"ID max: {max_id}")
    
    # Vérifier après last_scanned_id
    last_scanned = "EGO_20260124_032103_544"
    cursor.execute("SELECT COUNT(*) FROM memories WHERE type='ego_trait' AND id > ?", (last_scanned,))
    remaining = cursor.fetchone()[0]
    print(f"\nSouvenirs après {last_scanned}: {remaining}")
    
    # Afficher quelques exemples
    cursor.execute("SELECT id, created_at FROM memories WHERE type='ego_trait' LIMIT 5")
    print("\nExemples de souvenirs:")
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]})")

conn.close()
