import json
from pathlib import Path

# Charger le JSON
with open('data/ego_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

metadata = data['metadata']
groups = data['groups']

print("=" * 60)
print("🧠 ANALYSE EGO_COMPILED.JSON")
print("=" * 60)

# MÉTADONNÉES
print(f"\n📊 MÉTADONNÉES:")
print(f"  - Souvenirs analysés: {metadata['total_memories_scanned']}")
print(f"  - Dernier ID scanné: {metadata['last_scanned_id']}")
print(f"  - Dernière compilation: {metadata['last_compilation']}")

# GROUPES CRÉÉS
print(f"\n🗂️ GROUPES CRÉÉS: {len(groups)} au total")
print("\n" + "-" * 60)

# Séparer seed vs nouveaux
seed_groups = []
new_groups = []

for group_name, group_data in sorted(groups.items()):
    sources = group_data.get('source_memories', [])
    if sources == ['MANUAL_SEED'] or 'MANUAL_SEED' in sources:
        seed_groups.append(group_name)
    else:
        new_groups.append(group_name)

print(f"\n✨ GROUPES SEED (initiaux): {len(seed_groups)}")
for name in seed_groups:
    print(f"  - {name}")

print(f"\n🆕 GROUPES NOUVEAUX (créés par Archiviste): {len(new_groups)}")
for name in new_groups:
    group = groups[name]
    desc = group['description']
    flags_count = len(group['flags'])
    sources_count = len(group.get('source_memories', []))
    print(f"  - {name}")
    print(f"    → {desc}")
    print(f"    → {flags_count} flags, {sources_count} souvenirs sources")

# ANALYSE QUALITATIVE
print("\n" + "=" * 60)
print("🔍 ANALYSE QUALITATIVE")
print("=" * 60)

# Compter flags totaux
total_flags = sum(len(g['flags']) for g in groups.values())
print(f"\n📌 Flags totaux: {total_flags}")

# Vérifier multi-appartenance
all_flags = {}
for group_name, group_data in groups.items():
    for flag_name in group_data['flags'].keys():
        if flag_name not in all_flags:
            all_flags[flag_name] = []
        all_flags[flag_name].append(group_name)

multi_flags = {k: v for k, v in all_flags.items() if len(v) > 1}
print(f"\n🔗 Multi-appartenance: {len(multi_flags)} flags dans plusieurs groupes")
if multi_flags:
    print("\nExemples:")
    for flag, groups_list in list(multi_flags.items())[:5]:
        print(f"  - {flag}: {', '.join(groups_list)}")

# Vérifier variation conviction
all_convictions = []
for group_data in groups.values():
    for flag_data in group_data['flags'].values():
        all_convictions.append(flag_data['conviction'])

unique_convictions = set(all_convictions)
print(f"\n🎚️ Convictions utilisées: {sorted(unique_convictions)}")

# Groupes les plus riches
print("\n🏆 TOP 5 GROUPES (par nombre de flags):")
sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]['flags']), reverse=True)
for i, (name, data) in enumerate(sorted_groups[:5], 1):
    print(f"  {i}. {name}: {len(data['flags'])} flags")

print("\n" + "=" * 60)
