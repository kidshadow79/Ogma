"""
Script de génération de memories.seed.db
Extrait uniquement les mémoires SEED_* de memories.db
"""
import sqlite3
import shutil
from pathlib import Path

src = Path("data/memory/memories.db")
dst = Path("data/memory/memories.seed.db")

if not src.exists():
    print(f"ERREUR: {src} introuvable")
    exit(1)

shutil.copy2(src, dst)

with sqlite3.connect(dst) as conn:
    cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE id LIKE 'SEED_%'")
    seeds_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE id NOT LIKE 'SEED_%'")
    others_count = cursor.fetchone()[0]
    print(f"Seeds trouvés: {seeds_count}")
    print(f"Autres souvenirs à supprimer: {others_count}")
    conn.execute("DELETE FROM memories WHERE id NOT LIKE 'SEED_%'")
    conn.commit()
    # Compacter
    conn.execute("VACUUM")
    conn.commit()
    cursor = conn.execute("SELECT id, title FROM memories ORDER BY id")
    for row in cursor.fetchall():
        title = row[1][:60] if row[1] else ""
        print(f"  CONSERVÉ: {row[0]} | {title}")

size_kb = dst.stat().st_size // 1024
print(f"\nFichier créé: {dst} ({size_kb} KB)")
