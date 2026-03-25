#!/usr/bin/env python3
"""Vérification des souvenirs par défaut dans OGMA"""

import sqlite3
from pathlib import Path

db_path = Path("data/memory/memories.db")

if not db_path.exists():
    print(f"❌ Base de données non trouvée: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Compter les souvenirs
cursor.execute('SELECT COUNT(*) FROM memories')
count = cursor.fetchone()[0]
print(f"\n📊 Total souvenirs: {count}")

if count == 0:
    print("\n✅ CONFIRMATION: Base de données VIDE par défaut")
    print("   Aucun souvenir préchargé - mémoire pure (tabula rasa)")
else:
    print(f"\n📋 Premiers souvenirs (par date de création):")
    cursor.execute('SELECT id, title, created_at FROM memories ORDER BY created_at LIMIT 10')
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. [{row[2]}] {row[1][:70]}")

conn.close()
