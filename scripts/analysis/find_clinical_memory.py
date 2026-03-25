"""Trouve les souvenirs avec pattern description clinique/visuelle"""
import sqlite3

conn = sqlite3.connect('data/memory/memories.db')

# Recherche 1: Pattern "clinique" ou "description"
print("=" * 70)
print("🔍 RECHERCHE 1: Souvenirs avec 'clinique' ou 'description neutre'")
print("=" * 70)

cursor = conn.execute("""
SELECT id, title, text_original, type, score_impact
FROM memories 
WHERE (text_original LIKE '%clinique%' 
   OR text_original LIKE '%description neutre%'
   OR text_original LIKE '%précision clinique%'
   OR text_original LIKE '%analyse visuelle%'
   OR text_original LIKE '%œil scanner%'
   OR text_original LIKE '%scanner%')
   AND type != 'ego_trait'
ORDER BY created_at DESC
LIMIT 15
""")

results = cursor.fetchall()
print(f'\n✅ {len(results)} souvenirs trouvés\n')

for i, (mem_id, title, text, mem_type, score) in enumerate(results):
    print(f'{i+1}. [{mem_type}] Score: {score}')
    print(f'   ID: {mem_id}')
    print(f'   Titre: {title}')
    print(f'   Texte: {text[:250]}...')
    print()

# Recherche 2: Souvenirs à TRÈS HAUT IMPACT (>150) qui pourraient être systématiquement injectés
print("\n" + "=" * 70)
print("🔥 RECHERCHE 2: Souvenirs HAUT IMPACT (score > 150)")
print("=" * 70)

cursor2 = conn.execute("""
SELECT id, title, summary, score_impact, type
FROM memories 
WHERE score_impact > 150
ORDER BY score_impact DESC
LIMIT 10
""")

high_impact = cursor2.fetchall()
print(f'\n✅ {len(high_impact)} souvenirs haut impact\n')

for i, (mem_id, title, summary, score, mem_type) in enumerate(high_impact):
    print(f'{i+1}. [{mem_type}] Score: {score}')
    print(f'   ID: {mem_id}')
    print(f'   Titre: {title}')
    if summary:
        print(f'   Résumé: {summary[:200]}...')
    print()

conn.close()
