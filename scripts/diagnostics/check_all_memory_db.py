import sqlite3
import os

print("=" * 60)
print("DIAGNOSTIC BASES DE DONNÉES MÉMOIRE")
print("=" * 60)

db_files = [
    "data/memory.db",
    "data/memories.db",
]

for db_path in db_files:
    print(f"\n📁 {db_path}")
    print("-" * 40)
    
    if not os.path.exists(db_path):
        print("  ❌ Fichier non trouvé")
        continue
    
    size = os.path.getsize(db_path)
    print(f"  Taille: {size:,} bytes ({size/1024:.1f} KB)")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"  Tables: {tables}")
        
        # Pour chaque table, compter les enregistrements
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"    - {table}: {count} enregistrements")
                
                # Si c'est une table de mémoires, afficher quelques titres
                if count > 0 and 'memor' in table.lower():
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                    cols = [d[0] for d in cursor.description]
                    print(f"      Colonnes: {cols[:8]}...")
                    
                    if 'title' in cols:
                        cursor.execute(f"SELECT title FROM {table} LIMIT 5")
                        titles = cursor.fetchall()
                        for t in titles:
                            print(f"      📝 {t[0][:60] if t[0] else 'Sans titre'}...")
                            
            except Exception as e:
                print(f"    - {table}: Erreur - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

# Vérifier aussi le dossier memory/
print("\n" + "=" * 60)
print("📁 data/memory/")
print("-" * 40)

memory_dir = "data/memory"
if os.path.exists(memory_dir):
    files = os.listdir(memory_dir)
    print(f"  Fichiers: {len(files)}")
    for f in files[:10]:
        fpath = os.path.join(memory_dir, f)
        size = os.path.getsize(fpath) if os.path.isfile(fpath) else 0
        print(f"    - {f} ({size:,} bytes)")
else:
    print("  ❌ Dossier non trouvé")

# Vérifier l'index FAISS
print("\n" + "=" * 60)
print("📁 Index FAISS")
print("-" * 40)

faiss_path = "data/memory_index.faiss"
if os.path.exists(faiss_path):
    size = os.path.getsize(faiss_path)
    print(f"  {faiss_path}: {size:,} bytes ({size/1024:.1f} KB)")
else:
    print(f"  ❌ {faiss_path} non trouvé")
