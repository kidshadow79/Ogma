"""
Test du prompt Ego Selector optimisé (sans exemples redondants)
Vérifie la réduction de tokens et la clarté des instructions
"""

from extensions.ego_selector.config import EgoSelectorConfig

print("=" * 70)
print("TEST PROMPT EGO SELECTOR OPTIMISÉ")
print("=" * 70)

# Récupérer le prompt optimisé
prompt = EgoSelectorConfig.get_prompt()

# Statistiques
print(f"\n📊 STATISTIQUES:")
print(f"  - Taille totale: {len(prompt)} caractères")
print(f"  - Tokens estimés: ~{len(prompt) // 4} tokens")

# Vérifier présence sections clés
sections_required = [
    "GUIDE DE CATÉGORISATION",
    "IDENTITÉ - Mots-clés:",
    "ÉTHIQUE - Mots-clés:",
    "COMMUNICATION - Mots-clés:",
    "ÉVOLUTION - Mots-clés:",
    "STRATÉGIE DE SÉLECTION"
]

print(f"\n✅ SECTIONS PRÉSENTES:")
for section in sections_required:
    if section in prompt:
        print(f"  ✅ {section}")
    else:
        print(f"  ❌ {section} MANQUANTE")

# Vérifier absence exemples redondants
print(f"\n🔍 VÉRIFICATION NETTOYAGE:")
if "EXEMPLES CONCRETS" in prompt:
    print(f"  ⚠️ Section 'EXEMPLES CONCRETS' encore présente")
else:
    print(f"  ✅ Section 'EXEMPLES CONCRETS' supprimée")

if "EGO_20250919" in prompt or "EGO_20250920" in prompt:
    print(f"  ⚠️ IDs hardcodés encore présents")
else:
    print(f"  ✅ Aucun ID hardcodé (prompt générique)")

# Afficher extrait guide catégorisation
print(f"\n📖 EXTRAIT 'GUIDE DE CATÉGORISATION':")
print("─" * 70)
import re
match = re.search(r'\*\*GUIDE DE CATÉGORISATION\*\*.*?(?=\*\*STRATÉGIE)', prompt, re.DOTALL)
if match:
    guide = match.group(0)
    print(guide[:600] + "..." if len(guide) > 600 else guide)
else:
    print("Section non trouvée")
print("─" * 70)

print("\n" + "=" * 70)
print("FIN DU TEST")
print("=" * 70)
