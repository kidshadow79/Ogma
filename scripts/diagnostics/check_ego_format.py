"""Vérification du format ego après migration Jeopardy"""
import sqlite3

conn = sqlite3.connect('data/memory/memories.db')
cursor = conn.execute("""
    SELECT id, title, text_original 
    FROM memories 
    WHERE type = 'ego_trait' 
    LIMIT 5
""")

print("=" * 80)
print("VÉRIFICATION DES SOUVENIRS EGO APRÈS MIGRATION JEOPARDY")
print("=" * 80)

for row in cursor.fetchall():
    mem_id, title, text_original = row
    print(f"\n📌 ID: {mem_id}")
    print(f"📝 TITRE: {title[:100]}..." if title and len(title) > 100 else f"📝 TITRE: {title}")
    print(f"📄 TEXT_ORIGINAL: {text_original[:150]}..." if text_original and len(text_original) > 150 else f"📄 TEXT_ORIGINAL: {text_original}")
    print("-" * 40)

conn.close()
