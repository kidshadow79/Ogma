#!/usr/bin/env python3
import sqlite3

# Recherche du protocole d'amour hybride dans la base de données
conn = sqlite3.connect('data/memory/memories.db')
cursor = conn.execute('''
    SELECT title, summary, score_impact, LENGTH(text_original) as text_len, text_original 
    FROM memories 
    WHERE (title LIKE "%protocole%" OR text_original LIKE "%protocole%" OR text_original LIKE "%amour hybride%") 
    ORDER BY score_impact DESC
''')

results = cursor.fetchall()
print("RÉSULTATS PROTOCOLE AMOUR HYBRIDE:")
print("=" * 50)

if results:
    for i, row in enumerate(results, 1):
        title, summary, impact, text_len, original = row
        print(f"\n{i}. Titre: {title}")
        print(f"   Impact: {impact}")
        print(f"   Longueur: {text_len} chars")
        print(f"   Résumé: {summary[:100]}...")
        if "protocole" in original.lower():
            print(f"   PROTOCOLE TROUVÉ dans le texte!")
            # Extraire autour du mot protocole
            pos = original.lower().find("protocole")
            start = max(0, pos - 50)
            end = min(len(original), pos + 100)
            excerpt = original[start:end]
            print(f"   Extrait: ...{excerpt}...")
else:
    print("Aucun résultat trouvé pour 'protocole' ou 'amour hybride'")

# Recherche élargie pour des termes similaires
print("\n" + "=" * 50)
print("RECHERCHE ÉLARGIE - TERMES CONNEXES:")

cursor2 = conn.execute('''
    SELECT title, summary, score_impact 
    FROM memories 
    WHERE (text_original LIKE "%intime%" OR text_original LIKE "%hybride%" OR text_original LIKE "%rythme%" OR text_original LIKE "%vibration%") 
    ORDER BY score_impact DESC 
    LIMIT 10
''')

results2 = cursor2.fetchall()
for i, row in enumerate(results2, 1):
    title, summary, impact = row
    print(f"{i}. {title} (Impact: {impact})")
    print(f"   {summary[:80]}...")

conn.close()