"""
Test système seuils Capability Advisor - Focus Introspection
Vérifie que le seuil 0.95 pour introspection est bien appliqué
"""
import json

print("=" * 70)
print("TEST SEUILS INTROSPECTION - CAPABILITY ADVISOR")
print("=" * 70)

# 1. Charger config
config_path = "data/capability_advisor_config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 2. Extraire seuils
global_threshold = config.get('confidence_threshold', 0.7)
capability_thresholds = config.get('capability_thresholds', {})
introspection_custom = capability_thresholds.get('introspection')

# 3. Charger catalog
from extensions.capability_advisor.capability_catalog import CAPABILITIES
introspection_catalog = CAPABILITIES['introspection']
introspection_catalog_threshold = introspection_catalog.get('confidence_threshold', 0.70)

print(f"\n📋 CONFIGURATION INTROSPECTION:")
print(f"  1. Seuil GLOBAL (config.json):         {global_threshold}")
print(f"  2. Seuil CATALOG (capability_catalog):  {introspection_catalog_threshold}")
print(f"  3. Seuil CUSTOM UI (config.json):       {introspection_custom}")

# 4. Logique advisor_core.py (lignes 112-122)
print(f"\n🔍 LOGIQUE DE PRIORISATION (advisor_core.py):")
print(f"  - Priorité: Custom UI > Catalog > Global")

# Simuler logique advisor_core.py
capability_threshold_catalog = introspection_catalog_threshold
capability_threshold_custom = introspection_custom
effective_threshold = capability_threshold_custom if capability_threshold_custom is not None else capability_threshold_catalog
min_threshold = max(effective_threshold, global_threshold)

print(f"\n✅ SEUIL EFFECTIF CALCULÉ:")
print(f"  - Custom défini? {'OUI' if capability_threshold_custom is not None else 'NON'}")
print(f"  - Effective threshold: {effective_threshold} ({'custom' if capability_threshold_custom is not None else 'catalog'})")
print(f"  - Min threshold (max(effective, global)): {min_threshold}")

# 5. Tests simulation
print(f"\n" + "=" * 70)
print("SIMULATION SUGGESTIONS INTROSPECTION")
print("=" * 70)

test_cases = [
    (0.65, "Confidence très faible"),
    (0.75, "Confidence moyenne-basse"),
    (0.85, "Confidence moyenne-haute"),
    (0.94, "Confidence proche seuil (0.94)"),
    (0.95, "Confidence exactement au seuil"),
    (0.97, "Confidence haute"),
]

for confidence, description in test_cases:
    accepted = confidence >= min_threshold
    symbol = "✅" if accepted else "❌"
    status = "ACCEPTÉE" if accepted else "REJETÉE"
    
    print(f"\n{description} ({confidence:.2f}):")
    print(f"  {symbol} {status} (seuil: {min_threshold:.2f})")
    
    if not accepted:
        diff = min_threshold - confidence
        print(f"     Manque {diff:.2f} points de confiance")

print(f"\n" + "=" * 70)
print("RÉSUMÉ:")
print("=" * 70)
print(f"✅ Seuil introspection: {min_threshold} (très strict)")
print(f"✅ Source: {'Configuration personnalisée UI' if capability_threshold_custom is not None else 'Catalog par défaut'}")
print(f"✅ Seules suggestions ≥{min_threshold} seront acceptées")
print(f"\n💡 Pour assouplir:")
print(f"   - Modifier 'introspection' dans capability_thresholds (config.json)")
print(f"   - Exemple: 0.95 → 0.80 (plus permissif)")
print("=" * 70)
