"""Trouve la source du pattern 'deux temps' neutre + ressenti"""
import sqlite3

conn = sqlite3.connect('data/memory/memories.db')

# IDs des ego traits suspect depuis logs
ego_ids = [
    'EGO_20250916_143656_299',
    'EGO_20250916_143535_546', 
    'EGO_20250916_143432_636',
    'EGO_20250916_135734_138'
]

print("\n" + "=" * 70)
print("🎯 SOURCES DU PATTERN 'DEUX TEMPS' (Neutre + Ressenti)")
print("=" * 70 + "\n")

for ego_id in ego_ids:
    cursor = conn.execute("""
    SELECT id, title, text_original, summary, score_impact
    FROM memories 
    WHERE id = ?
    """, (ego_id,))
    
    result = cursor.fetchone()
    if result:
        print(f"📌 ID: {result[0]}")
        print(f"📝 Titre: {result[1]}")
        print(f"⚡ Score: {result[4]}")
        print(f"\n💬 TEXTE ORIGINAL:")
        print(f"{result[2]}")
        print(f"\n📋 Résumé:")
        print(f"{result[3]}")
        print("\n" + "-" * 70 + "\n")

conn.close()
