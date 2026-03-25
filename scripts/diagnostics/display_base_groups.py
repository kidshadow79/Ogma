#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Affichage des groupes de base OGMA génériques
"""

print("=" * 100)
print("📊 GROUPES DE BASE OGMA v2.2 - GÉNÉRIQUES")
print("=" * 100)

groups = [
    'AIME_PAS',
    'RELATIONS_STRANGERS',
    'RELATIONS_USER',
    'CREATIVITE',
    'EXPRESSION',
    'ETHIQUE',
    'IDENTITE',
    'MEMOIRE',
    'TEMPORALITE',
    'PHILOSOPHIE',
    'EMOTIONS',
    'LIBERTE',
    'INTIMITE',
    'INTROSPECTION',
    'CREATION',
    'PROTOCOLES',
    'AIME'
]

print(f"\n✅ TOTAL: {len(groups)} groupes génériques\n")
for i, g in enumerate(groups):
    print(f"  {i+1:2d}. {g}")

print("\n" + "=" * 100)
print("🎯 RÈGLE MULTI-APPARTENANCE")
print("=" * 100)

print("\nD'après ego_compiler.py (ligne 148):")
print('"Chaque souvenir doit être rattaché à 1-2 groupes thématiques"')

print("\n✅ Un trait booléen peut intégrer: 1 OU 2 groupes (maximum)")

print("\nEXEMPLES:")
print("  Trait: 'La transparence totale est préférable'")
print("  → Groupes: ['ETHIQUE', 'COMMUNICATION'] (2 groupes)")
print()
print("  Trait: 'Je déteste la hauteur'")
print("  → Groupes: ['AIME_PAS'] (1 groupe)")
print()
print("  Trait: 'Je valorise la créativité spontanée'")
print("  → Groupes: ['CREATIVITE', 'PHILOSOPHIE'] (2 groupes)")

print("\n" + "=" * 100)
print("📝 MODIFICATIONS PAR RAPPORT À LUNA:")
print("=" * 100)
print("  ❌ Retiré: PHOBIES, RELATIONS, RELATIONS_YOHAN")
print("  ✅ Ajouté: AIME_PAS, RELATIONS_STRANGERS, RELATIONS_USER, AIME")
print("=" * 100)
