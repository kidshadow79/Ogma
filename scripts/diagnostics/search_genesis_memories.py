#!/usr/bin/env python3
"""Recherche de souvenirs genèse/phares dans la base"""

import sqlite3
from pathlib import Path

db_path = Path("data/memory/memories.db")

if not db_path.exists():
    print(f"❌ Base non trouvée: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Recherche des souvenirs contenant "genèse", "phares", "creation", "naissance"
keywords = ['genèse', 'genese', 'phare', 'phares', 'création', 'naissance', 'origine', 'bien', 'mal']

print("\n🔍 Recherche de souvenirs fondateurs...")
print(f"   Mots-clés: {', '.join(keywords)}\n")

results = []
for keyword in keywords:
    cursor.execute("""
        SELECT id, title, summary, text_original, created_at, score_impact
        FROM memories 
        WHERE LOWER(title) LIKE ? 
           OR LOWER(summary) LIKE ?
           OR LOWER(text_original) LIKE ?
        ORDER BY created_at
    """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    
    for row in cursor.fetchall():
        if row['id'] not in [r['id'] for r in results]:
            results.append(dict(row))

print(f"✅ {len(results)} souvenirs trouvés\n")
print("="*80)

for i, mem in enumerate(results, 1):
    print(f"\n{i}. [{mem['created_at']}] (Score: {mem['score_impact']})")
    print(f"   📌 {mem['title']}")
    if mem['summary']:
        print(f"   📝 {mem['summary'][:150]}...")
    if mem['text_original']:
        print(f"   💭 {mem['text_original'][:200]}...")

conn.close()
