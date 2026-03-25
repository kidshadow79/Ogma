import sqlite3

conn = sqlite3.connect('data/memory.db')
cursor = conn.cursor()

# Nombre de souvenirs
cursor.execute('SELECT COUNT(*) FROM memories')
count = cursor.fetchone()[0]
print(f"Nombre de souvenirs: {count}")

# Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables: {tables}")

# Quelques titres
if count > 0:
    cursor.execute("SELECT id, title FROM memories LIMIT 5")
    for row in cursor.fetchall():
        print(f"  - {row[0][:20]}... | {row[1][:50] if row[1] else 'Sans titre'}")

conn.close()
