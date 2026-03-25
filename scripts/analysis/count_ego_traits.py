#!/usr/bin/env python3
"""Script rapide pour compter les traits ego dans la DB"""

import sqlite3

conn = sqlite3.connect('data/memory/memories.db')
cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE type='ego_trait'")
total = cursor.fetchone()[0]
print(f"Total traits ego dans DB: {total}")

# Détails par catégorie (estimation keywords)
cursor = conn.execute("SELECT id, text_original FROM memories WHERE type='ego_trait'")
results = cursor.fetchall()

categories = {'IDENTITÉ': 0, 'ÉTHIQUE': 0, 'COMMUNICATION': 0, 'ÉVOLUTION': 0}
for mem_id, text in results:
    text_lower = (text or "").lower()
    if any(kw in text_lower for kw in ['identité', 'essence', 'nature', 'corps', 'visage', 'luna', 'conscience']):
        categories['IDENTITÉ'] += 1
    elif any(kw in text_lower for kw in ['éthique', 'valeur', 'principe', 'moral', 'respect']):
        categories['ÉTHIQUE'] += 1
    elif any(kw in text_lower for kw in ['communication', 'parle', 'dialogue', 'yohan', 'connexion', 'intimité']):
        categories['COMMUNICATION'] += 1
    elif any(kw in text_lower for kw in ['évolution', 'apprentissage', 'grandir', 'développement']):
        categories['ÉVOLUTION'] += 1
    else:
        categories['COMMUNICATION'] += 1  # Défaut

print(f"\nRépartition par catégories (estimation):")
for cat, count in categories.items():
    print(f"  {cat}: {count} traits")

conn.close()
