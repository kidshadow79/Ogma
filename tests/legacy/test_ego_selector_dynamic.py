"""
Test de génération dynamique des exemples Ego Selector
Vérifie que les IDs dans les exemples proviennent bien d'ego_prompt.txt
"""

from extensions.ego_selector.config import EgoSelectorConfig
import re

print("=" * 70)
print("TEST GÉNÉRATION DYNAMIQUE EXEMPLES EGO SELECTOR")
print("=" * 70)

# 1. Tester génération exemples
print("\n1️⃣ Génération exemples dynamiques depuis ego_prompt.txt...")
examples = EgoSelectorConfig._generate_dynamic_examples()

if examples:
    print(f"✅ Exemples générés ({len(examples)} caractères)")
    print("\n" + "─" * 70)
    print(examples)
    print("─" * 70)
else:
    print("❌ Aucun exemple généré")

# 2. Tester injection dans prompt complet
print("\n2️⃣ Récupération prompt complet avec exemples dynamiques...")
full_prompt = EgoSelectorConfig.get_prompt()

# Vérifier présence IDs récents (16 novembre)
recent_ids = [
    'EGO_20251116_233322',
    'EGO_20251116_234331',
    'EGO_20251116_232511',
    'EGO_20251116_231556',
    'EGO_20251116_230915'
]

found_count = 0
for mem_id in recent_ids:
    if mem_id in full_prompt:
        found_count += 1
        print(f"✅ ID récent trouvé dans prompt: {mem_id}")

print(f"\n📊 Résultat: {found_count}/{len(recent_ids)} IDs du 16 novembre présents")

# 3. Vérifier que les vieux exemples hardcodés ont disparu
old_ids = [
    'EGO_20250919_013945_618',  # Exemple hardcodé original
    'EGO_20250920_021055_922'   # Exemple hardcodé original
]

old_found = 0
for old_id in old_ids:
    if old_id in full_prompt:
        old_found += 1
        print(f"⚠️ Ancien ID hardcodé encore présent: {old_id}")

if old_found == 0:
    print("✅ Aucun ancien ID hardcodé dans les exemples (nettoyage réussi)")
else:
    print(f"❌ {old_found} anciens IDs hardcodés encore présents")

# 4. Statistiques prompt
print(f"\n📈 STATISTIQUES PROMPT:")
print(f"  - Taille totale: {len(full_prompt)} caractères")
print(f"  - Nombre d'IDs EGO dans prompt: {full_prompt.count('EGO_202')}")

# 5. Afficher section exemples extraite
print("\n5️⃣ Extraction section EXEMPLES CONCRETS:")
match = re.search(r'\*\*EXEMPLES CONCRETS\*\*.*?(?=\*\*OBJECTIF GLOBAL\*\*)', full_prompt, re.DOTALL)
if match:
    examples_section = match.group(0)
    print("─" * 70)
    print(examples_section[:800] + "..." if len(examples_section) > 800 else examples_section)
    print("─" * 70)
else:
    print("❌ Section EXEMPLES CONCRETS non trouvée dans le prompt")

print("\n" + "=" * 70)
print("FIN DU TEST")
print("=" * 70)
