"""
Test génération catalogue ego pour Archiviste
"""

from extensions.ego_selector.config import EgoSelectorConfig
import json

# Générer catalogue complet
catalog = EgoSelectorConfig.get_ego_catalog()

print(f"\n📊 CATALOGUE EGO GÉNÉRÉ: {len(catalog)} souvenirs\n")

# Afficher par catégorie
by_category = {}
for item in catalog:
    cat = item['category']
    if cat not in by_category:
        by_category[cat] = []
    by_category[cat].append(item)

for category, items in by_category.items():
    print(f"\n{category} ({len(items)} souvenirs):")
    print("=" * 80)
    for idx, item in enumerate(items[:3], 1):  # Afficher 3 premiers
        print(f"{idx}. {item['id']}")
        print(f"   {item['title']}")
    if len(items) > 3:
        print(f"   ... et {len(items) - 3} autres")

# Export JSON pour test prompt
print("\n\n📝 EXPORT JSON (premiers 5):")
print("=" * 80)
print(json.dumps(catalog[:5], indent=2, ensure_ascii=False))

print(f"\n✅ Total: {len(catalog)} souvenirs prêts pour l'Archiviste")
