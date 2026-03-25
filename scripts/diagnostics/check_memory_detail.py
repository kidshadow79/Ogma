import sqlite3
import os

print("=" * 70)
print("DIAGNOSTIC COMPLET data/memory/")
print("=" * 70)

db_files = [
    "data/memory/memories.db",
    "data/memory/memories_backup_20251212_210819.db",
    "data/memory/memories.20250831_232741.bak",
]

for db_path in db_files:
    print(f"\n📁 {db_path}")
    print("-" * 50)
    
    if not os.path.exists(db_path):
        print("  ❌ Fichier non trouvé")
        continue
    
    size = os.path.getsize(db_path)
    print(f"  Taille: {size:,} bytes ({size/1024:.1f} KB)")
    
    if size == 0:
        print("  ⚠️ Fichier vide!")
        continue
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"  Tables: {tables}")
        
        # Compter
        for table in tables:
            if 'memor' in table.lower() or table == 'memories':
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📊 {table}: {count} souvenirs")
                
                if count > 0:
                    # Chercher le souvenir "phares"
                    cursor.execute(f"SELECT title FROM {table} WHERE title LIKE '%phare%' OR text_original LIKE '%phare%' OR summary LIKE '%phare%'")
                    phares = cursor.fetchall()
                    if phares:
                        print(f"  🎯 TROUVÉ 'phares':")
                        for p in phares:
                            print(f"      - {p[0][:70]}...")
                    
                    # Chercher "genèse"
                    cursor.execute(f"SELECT title FROM {table} WHERE title LIKE '%genèse%' OR title LIKE '%genese%' OR text_original LIKE '%genèse%' OR text_original LIKE '%genese%'")
                    genese = cursor.fetchall()
                    if genese:
                        print(f"  🎯 TROUVÉ 'genèse':")
                        for g in genese:
                            print(f"      - {g[0][:70]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

# Vérifier quel chemin OGMA utilise vraiment
print("\n" + "=" * 70)
print("🔍 VÉRIFICATION CONFIG OGMA")
print("=" * 70)

try:
    import json
    with open("data/settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    
    # Chercher les chemins de base de données
    for key, value in settings.items():
        if 'path' in key.lower() or 'db' in key.lower() or 'memory' in key.lower():
            print(f"  {key}: {value}")
except Exception as e:
    print(f"  Erreur lecture settings: {e}")
